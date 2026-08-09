from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_

from models import (
    TreasuryAccount, CashPositionSnapshot, CashFlowForecast,
    VATRemittance, JournalEntry, Account, AccountBalance,
    ARInvoice, Customer, Vendor, PurchaseOrder,
    ImportShipment, GatewaySettlementSchedule,
    FinanceAutomationLog, FinanceAuditLog, FiscalPeriod,
    Order, OrderItem, JournalEntryLine, SupplierSettlement,
)
from db.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from services.finance_automation import run_daily_automation as run_finance_daily
from services.financial_reports_service import (
    generate_income_statement, generate_balance_sheet, generate_cash_flow_statement,
    save_report,
)
from services.gateway_reconciliation_service import run_gateway_3way_reconciliation
from services.payout_batch_service import (
    generate_supplier_payout_batches,
    generate_logistics_payout_batches,
)
from services.credit_control_service import enforce_auto_credit_holds
from services.ai_automation_service import (
    run_ai_bank_reconciliation,
    process_email_inbox,
    batch_categorize_all,
)
from services.period_close_service import close_period
from utils.datetime_utils import utcnow as _utcnow

from utils.config import settings

logger = logging.getLogger(__name__)


def _log_automation(db: Session, kind: str, processed: int, changed: int,
                     detail: dict = None, country_code: str = None) -> None:
    try:
        db.add(FinanceAutomationLog(
            kind=kind, records_processed=processed, records_changed=changed,
            detail=detail, country_code=country_code,
        ))
        db.commit()
    except Exception as e:
        logger.warning("automation log failed: %s", e)


# ── Daily Cash Position Snapshot ──


def take_cash_snapshot(db: Session, country_code: str = None) -> dict:
    q = db.query(TreasuryAccount).filter(TreasuryAccount.is_active == True)
    if country_code:
        q = q.filter(TreasuryAccount.country_code == country_code)
    accounts = q.all()
    now = _utcnow()
    for a in accounts:
        snap = CashPositionSnapshot(
            snapshot_time=now, account_id=a.id,
            balance=a.balance, currency=a.currency or "OMR",
            country_code=a.country_code,
        )
        db.add(snap)
    db.commit()
    total_cash = sum(float(a.balance or 0) for a in accounts)
    _log_automation(db, "cash_snapshot", len(accounts), len(accounts),
                    {"total_cash": total_cash}, country_code)
    return {"snapshotted": len(accounts), "total_cash": total_cash,
            "timestamp": now.isoformat()}


# ── VAT Aggregation ──


def compute_vat_remittance(db: Session, period_year: int, period_month: int,
                            country_code: str = None) -> dict:
    from datetime import datetime as dt
    from dateutil.relativedelta import relativedelta
    period_start = dt(period_year, period_month, 1)
    period_end = period_start + relativedelta(months=1)
    output_vat_account = db.query(Account).filter(Account.code == "2040").first()
    input_vat_account = db.query(Account).filter(Account.code == "2050").first()
    vat_collected = Decimal("0")
    vat_paid = Decimal("0")
    if output_vat_account:
        bal = db.query(AccountBalance).filter(
            AccountBalance.account_id == output_vat_account.id,
        ).first()
        if bal:
            vat_collected = bal.balance or Decimal("0")
    if input_vat_account:
        bal = db.query(AccountBalance).filter(
            AccountBalance.account_id == input_vat_account.id,
        ).first()
        if bal:
            vat_paid = bal.balance or Decimal("0")
    net_due = vat_collected - vat_paid
    if net_due < 0:
        net_due = Decimal("0")
    existing = db.query(VATRemittance).filter(
        VATRemittance.country_code == country_code,
        VATRemittance.period_start == period_start,
        VATRemittance.period_end == period_end,
    ).first()
    if existing:
        existing.vat_collected_amount = vat_collected
        existing.vat_adjustment_amount = vat_paid
        existing.amount_due = net_due
        existing.calculated_at = _utcnow()
    else:
        rem = VATRemittance(
            period_start=period_start,
            period_end=period_end,
            vat_collected_amount=vat_collected,
            vat_adjustment_amount=vat_paid,
            amount_due=net_due,
            amount=net_due,
            status="calculated",
            currency=settings.default_currency,
            country_code=country_code,
        )
        db.add(rem)
    db.commit()
    _log_automation(db, "vat_aggregation", 1, 1,
                    {"period": f"{period_year}-{period_month:02d}",
                     "vat_collected": float(vat_collected),
                     "vat_paid": float(vat_paid),
                     "net_due": float(net_due)}, country_code)
    return {"period": f"{period_year}-{period_month:02d}",
            "vat_collected": float(vat_collected),
            "vat_paid": float(vat_paid),
            "net_due": float(net_due)}


# ── Automated Financial Report Generation ──


def generate_period_reports(db: Session, period_year: int, period_month: int,
                             country_code: str = None) -> dict:
    period_start = datetime(period_year, period_month, 1)
    if period_month == 12:
        period_end = datetime(period_year + 1, 1, 1)
    else:
        period_end = datetime(period_year, period_month + 1, 1)
    results = {}
    for report_type in ("income_statement", "balance_sheet", "cash_flow"):
        try:
            if report_type == "income_statement":
                data = generate_income_statement(db, period_start, period_end, country_code=country_code)
            elif report_type == "balance_sheet":
                data = generate_balance_sheet(db, period_start, period_end, country_code=country_code)
            else:
                data = generate_cash_flow_statement(db, period_start, period_end, country_code=country_code)
            saved = save_report(db, report_type=report_type, period_start=period_start,
                                 period_end=period_end, data=data,
                                 country_code=country_code)
            results[report_type] = {"id": saved.id, "status": "generated"}
        except Exception as e:
            logger.warning("Report %s generation failed: %s", report_type, e)
            results[report_type] = {"error": str(e)}
    _log_automation(db, "period_reports", len(results),
                    sum(1 for v in results.values() if "id" in v),
                    {"period": f"{period_year}-{period_month:02d}"}, country_code)
    return results


# ── Distributor Statement Generation ──


def generate_distributor_statements(db: Session, period_year: int, period_month: int,
                                     country_code: str = None) -> list[dict]:
    period_start = datetime(period_year, period_month, 1)
    if period_month == 12:
        period_end = datetime(period_year + 1, 1, 1)
    else:
        period_end = datetime(period_year, period_month + 1, 1)
    customers = db.query(Customer).filter(Customer.is_active == True)
    if country_code:
        customers = customers.filter(Customer.country_code == country_code)
    statements = []
    for customer in customers.all():
        invoices = db.query(ARInvoice).filter(
            ARInvoice.customer_id == customer.id,
            ARInvoice.invoice_date >= period_start,
            ARInvoice.invoice_date < period_end,
        ).all()
        if not invoices:
            continue
        total_invoiced = sum(float(i.amount or 0) for i in invoices)
        total_paid = sum(
            float(i.amount or 0) for i in invoices if i.status == "paid"
        )
        total_outstanding = total_invoiced - total_paid
        statement_data = {
            "customer_id": customer.id,
            "customer_name": customer.name,
            "customer_email": customer.contact_email,
            "period": f"{period_year}-{period_month:02d}",
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "total_outstanding": total_outstanding,
            "invoice_count": len(invoices),
            "invoices": [
                {
                    "invoice_number": i.invoice_number,
                    "date": i.invoice_date.isoformat() if i.invoice_date else None,
                    "due_date": i.due_date.isoformat() if i.due_date else None,
                    "amount": float(i.amount or 0),
                    "status": i.status,
                }
                for i in invoices
            ],
        }
        statements.append(statement_data)
        
        # Send statement email to distributor
        try:
            from services.transactional_email_service import enqueue_distributor_statement_email
            enqueue_distributor_statement_email(
                customer.id, statement_data["period"], statement_data
            )
        except Exception as e:
            logger.warning("Failed to send statement email for customer %s: %s", customer.id, e)
    
    _log_automation(db, "distributor_statements", len(statements), len(statements),
                    {"period": f"{period_year}-{period_month:02d}"}, country_code)
    return statements


# ── Supplier Statement Generation ──


def generate_supplier_statements(db: Session, period_year: int, period_month: int,
                                  country_code: str = None) -> list[dict]:
    period_start = datetime(period_year, period_month, 1)
    if period_month == 12:
        period_end = datetime(period_year + 1, 1, 1)
    else:
        period_end = datetime(period_year, period_month + 1, 1)
    vendors = db.query(Vendor).filter(Vendor.is_active == True)
    if country_code:
        vendors = vendors.filter(Vendor.country_code == country_code)
    statements = []
    for vendor in vendors.all():
        bills = db.query(JournalEntry).join(
            JournalEntryLine, JournalEntry.id == JournalEntryLine.entry_id
        ).filter(
            JournalEntry.reference_type == "grn",
            JournalEntry.entry_date >= period_start,
            JournalEntry.entry_date < period_end,
            JournalEntryLine.account_code == "2010",
        ).all()
        total_amount = sum(
            float(abs(jl.amount or 0))
            for je in bills
            for jl in je.lines if jl.account_code == "2010"
        ) if bills else 0
        if not total_amount:
            continue
        statements.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "vendor_email": vendor.contact_email,
            "period": f"{period_year}-{period_month:02d}",
            "total_amount": total_amount,
            "transaction_count": len(bills),
        })
    _log_automation(db, "supplier_statements", len(statements), len(statements),
                    {"period": f"{period_year}-{period_month:02d}"}, country_code)
    return statements


# ── Automated Alerts Engine ──


def run_alert_engine(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    alerts.extend(_check_cash_balance(db, country_code))
    alerts.extend(_check_gateway_settlements(db, country_code))
    alerts.extend(_check_cod_remittances(db, country_code))
    alerts.extend(_check_ar_overdue(db, country_code))
    alerts.extend(_check_fx_exposure(db, country_code))
    alerts.extend(_check_orphan_journals(db, country_code))
    alerts.extend(_check_pending_payouts(db, country_code))
    _log_automation(db, "alert_engine", len(alerts), len(alerts), {"alerts": alerts}, country_code)
    return alerts


def _check_cash_balance(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    cash_accounts = db.query(TreasuryAccount).filter(
        TreasuryAccount.slug.in_(["cash_operating", "cash_on_hand"])
    )
    if country_code:
        cash_accounts = cash_accounts.filter(TreasuryAccount.country_code == country_code)
    for acct in cash_accounts.all():
        if acct.balance and float(acct.balance) < 0:
            alerts.append({
                "severity": "critical", "type": "cash_negative",
                "message": f"Cash account '{acct.name}' has negative balance: {float(acct.balance)}",
                "country_code": acct.country_code,
            })
    return alerts


def _check_gateway_settlements(db: Session, country_code: str = None) -> list[dict]:
    from datetime import timedelta
    alerts = []
    q = db.query(GatewaySettlementSchedule).filter(
        GatewaySettlementSchedule.status == "captured",
        GatewaySettlementSchedule.settlement_date.isnot(None),
    )
    if country_code:
        q = q.filter(GatewaySettlementSchedule.country_code == country_code)
    for sched in q.all():
        if sched.settlement_date:
            days_since = (date.today() - sched.settlement_date.date()).days
            if days_since > 3:
                alerts.append({
                    "severity": "warning", "type": "gateway_delayed",
                    "message": f"Gateway settlement delayed >T+3 for schedule #{sched.id} ({days_since} days)",
                    "amount": float(sched.amount or 0),
                    "country_code": sched.country_code,
                })
    return alerts


def _check_cod_remittances(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    from models import Order
    q = db.query(Order).filter(
        Order.payment_method == "cod",
        Order.status == "delivered",
    )
    if country_code:
        q = q.filter(Order.country_code == country_code)
    for order in q.all():
        if order.delivered_at:
            days_since = (date.today() - order.delivered_at.date()).days
            if days_since > 7:
                alerts.append({
                    "severity": "warning", "type": "cod_unremitted",
                    "message": f"COD not remitted for Order #{order.id} ({days_since} days since delivery)",
                    "amount": float(order.total or 0), "country_code": order.country_code,
                })
    return alerts


def _check_ar_overdue(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    q = db.query(ARInvoice).filter(
        ARInvoice.status.in_(["issued", "partially_paid"]),
        ARInvoice.due_date.isnot(None),
    )
    if country_code:
        q = q.filter(ARInvoice.country_code == country_code)
    for inv in q.all():
        if inv.due_date:
            days_overdue = (date.today() - inv.due_date.date()).days
            if days_overdue > 30:
                alerts.append({
                    "severity": "warning", "type": "ar_overdue_30",
                    "message": f"AR Invoice #{inv.invoice_number} overdue {days_overdue} days",
                    "customer_id": inv.customer_id, "amount": float(inv.amount or 0),
                    "country_code": inv.country_code,
                })
    return alerts


def _check_fx_exposure(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    q = db.query(ImportShipment).filter(
        ImportShipment.status.in_(["in_transit", "customs_cleared"]),
        ImportShipment.exchange_rate.isnot(None),
    )
    if country_code:
        q = q.filter(ImportShipment.country_code == country_code)
    for s in q.all():
        rate = float(s.exchange_rate or 1)
        if rate > 1.03 or rate < 0.97:
            alerts.append({
                "severity": "warning", "type": "fx_exposure",
                "message": f"FX rate moved >3% for shipment {s.shipment_ref} (rate: {rate})",
                "amount": float(s.total_landed_cost or s.product_cost_total or 0),
                "country_code": s.country_code,
            })
    return alerts


def _check_orphan_journals(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    from services.treasury_engine import TreasuryEngine
    try:
        orphans = TreasuryEngine(db).run_orphan_detector()
        if orphans:
            alerts.append({
                "severity": "critical", "type": "orphan_journals",
                "message": f"{len(orphans)} orphan journal entries detected",
                "orphans": orphans[:10],
                "country_code": country_code,
            })
    except Exception as e:
        logger.warning("orphan check failed: %s", e)
    return alerts


def _check_pending_payouts(db: Session, country_code: str = None) -> list[dict]:
    alerts = []
    from models import PayoutBatch
    q = db.query(PayoutBatch).filter(
        PayoutBatch.status.in_(["generated", "supplier_approved"]),
        PayoutBatch.created_at.isnot(None),
    )
    if country_code:
        q = q.filter(PayoutBatch.country_code == country_code)
    for batch in q.all():
        hours_pending = (_utcnow() - batch.created_at).total_seconds() / 3600
        if hours_pending > 48:
            alerts.append({
                "severity": "warning", "type": "payout_pending",
                "message": f"Payout batch #{batch.id} pending >48 hours (status: {batch.status})",
                "amount": float(batch.total_amount or 0), "country_code": batch.country_code,
            })
    return alerts


# ── Master Automation Runner ──


def run_full_automation(db: Session, country_code: str = None,
                         period_year: int = None, period_month: int = None) -> dict:
    today = date.today()
    py = period_year or today.year
    pm = period_month or today.month
    results = {}
    results["daily_finance"] = run_finance_daily(db, as_of=today, country_code=country_code)
    results["cash_snapshot"] = take_cash_snapshot(db, country_code)
    results["vat"] = compute_vat_remittance(db, py, pm, country_code)
    results["alerts"] = run_alert_engine(db, country_code)
    
    # Gateway reconciliation (#4, #5, #7)
    results["gateway_reconciliation"] = run_gateway_3way_reconciliation(db, country_code)
    
    # Smart payout batch generation (#14)
    results["supplier_payouts"] = generate_supplier_payout_batches(db, country_code)
    results["logistics_payouts"] = generate_logistics_payout_batches(db, country_code)
    
    # Credit limit enforcement (#24)
    results["credit_control"] = enforce_auto_credit_holds(db, country_code)
    
    # FX revaluation (#17) - daily for open import shipments
    try:
        from services.import_service import run_fx_revaluation
        results["fx_revaluation"] = run_fx_revaluation(db, country_code=country_code)
    except Exception as e:
        logger.warning("FX revaluation failed: %s", e)
        results["fx_revaluation"] = {"error": str(e)}
    
    # 3-way match scan (#10) - daily for unmatched POs
    try:
        from services.trading_service import scan_unmatched_pos
        results["three_way_match"] = scan_unmatched_pos(db, country_code=country_code)
    except Exception as e:
        logger.warning("3-way match scan failed: %s", e)
        results["three_way_match"] = {"error": str(e)}
    
    # Dunning engine (#12) - weekly on Mondays
    if today.weekday() == 0:  # Monday
        try:
            from services.trading_service import run_dunning_engine
            results["dunning"] = run_dunning_engine(db)
        except Exception as e:
            logger.warning("Dunning engine failed: %s", e)
            results["dunning"] = {"error": str(e)}
    
    # E-commerce auto-invoice on delivery (#11) - daily
    try:
        from services.trading_service import auto_invoice_ecommerce_orders
        results["ecommerce_invoice"] = auto_invoice_ecommerce_orders(db, country_code=country_code)
    except Exception as e:
        logger.warning("E-commerce auto-invoice failed: %s", e)
        results["ecommerce_invoice"] = {"error": str(e)}
    
    # COD batch reconciliation (#5) - daily
    try:
        from services.gateway_reconciliation_service import reconcile_all_cod_deposits
        results["cod_reconciliation"] = reconcile_all_cod_deposits(db, country_code=country_code)
    except Exception as e:
        logger.warning("COD reconciliation failed: %s", e)
        results["cod_reconciliation"] = {"error": str(e)}

    # AI Bank Reconciliation (#6) - daily
    try:
        results["ai_bank_reconciliation"] = run_ai_bank_reconciliation(db, country_code)
    except Exception as e:
        logger.warning("AI bank reconciliation failed: %s", e)
        results["ai_bank_reconciliation"] = {"error": str(e)}

    # Email inbox processing (#8) - every 5 minutes equivalent (daily batch)
    try:
        results["email_inbox"] = process_email_inbox(db, country_code)
    except Exception as e:
        logger.warning("Email inbox processing failed: %s", e)
        results["email_inbox"] = {"error": str(e)}

    # AI Expense Categorization (#27) - daily batch
    try:
        results["ai_categorization"] = batch_categorize_all(db, country_code)
    except Exception as e:
        logger.warning("AI categorization failed: %s", e)
        results["ai_categorization"] = {"error": str(e)}

    if today.day == 1:
        prev = today.replace(day=1) - timedelta(days=1)
        results["reports"] = generate_period_reports(db, prev.year, prev.month, country_code)
        results["distributor_statements"] = generate_distributor_statements(
            db, prev.year, prev.month, country_code)
        results["supplier_statements"] = generate_supplier_statements(
            db, prev.year, prev.month, country_code)
        
        # Period close (#28) - auto-close previous period on month-end
        try:
            from services.period_close_service import close_period
            from models import FiscalPeriod
            prev_period = db.query(FiscalPeriod).filter(
                FiscalPeriod.period_year == prev.year,
                FiscalPeriod.period_month == prev.month,
                FiscalPeriod.country_code == country_code,
            ).first()
            if prev_period and prev_period.status == "open":
                results["period_close"] = close_period(db, prev_period.id, closed_by=1)
            else:
                results["period_close"] = {"status": "no_open_period", "period": f"{prev.year}-{prev.month:02d}"}
        except Exception as e:
            logger.warning("Period close failed: %s", e)
            results["period_close"] = {"error": str(e)}
        
        _log_automation(db, "month_end_close", 1, 1,
                        {"period": f"{prev.year}-{prev.month:02d}"}, country_code)
    return results