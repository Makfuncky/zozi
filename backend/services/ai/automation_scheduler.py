"""Automation Scheduler Service.

Orchestrates periodic finance automation tasks:
- Run full automation suite
- Cash position snapshots
- VAT remittance calculations
- Period report generation
- Statement generation (supplier)
- Alert engine

All functions are thin orchestration layers over domain services.
"""

import logging
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def run_full_automation(
    db: Session,
    country_code: str = None,
    period_year: int = None,
    period_month: int = None,
) -> dict:
    """Run the complete automation suite for a country and period.

    Orchestrates: cash snapshot, VAT remittance, period reports,
    supplier statements, and alerts.
    """
    results = {}

    results["cash_snapshot"] = take_cash_snapshot(db, country_code)

    period_year = period_year or datetime.utcnow().year
    period_month = period_month or datetime.utcnow().month

    results["vat_remittance"] = compute_vat_remittance(db, period_year, period_month, country_code)
    results["period_reports"] = generate_period_reports(db, period_year, period_month, country_code)
    results["supplier_statements"] = generate_supplier_statements(db, period_year, period_month, country_code)
    results["alerts"] = run_alert_engine(db, country_code)

    results["as_of"] = datetime.utcnow().isoformat()
    results["country_code"] = country_code

    return results


def take_cash_snapshot(db: Session, country_code: str = None) -> dict:
    """Take a cash position snapshot.

    Aggregates cash balances from operating and gateway accounts.
    """
    from services.treasury_service import get_cash_position
    return get_cash_position(db, country_code=country_code)


def compute_vat_remittance(
    db: Session,
    period_year: int,
    period_month: int,
    country_code: str = None,
) -> dict:
    """Compute VAT remittance for a specific period.

    Returns VAT collected and VAT paid for the given period.
    """
    from services.treasury_service import get_vat_liability

    period_start = date(period_year, period_month, 1)

    vat_data = get_vat_liability(db, country_code=country_code)

    result = {
        "period_year": period_year,
        "period_month": period_month,
        "period_start": period_start.isoformat(),
        "vat_collected": 0.0,
        "vat_paid": 0.0,
        "net_liability": 0.0,
        "by_country": [],
    }

    if vat_data.get("by_country"):
        for country_data in vat_data["by_country"]:
            if country_code is None or country_data.get("country_code") == country_code:
                result["vat_collected"] = country_data.get("vat_collected", 0)
                result["vat_paid"] = country_data.get("vat_paid", 0)
                result["net_liability"] = country_data.get("net_liability", 0)
            if country_code is None or country_data.get("country_code") == country_code:
                result["by_country"].append(country_data)

    return result


def generate_period_reports(
    db: Session,
    period_year: int,
    period_month: int,
    country_code: str = None,
) -> dict:
    """Generate financial reports for a period.

    Returns income statement, balance sheet, and cash flow statement.
    """
    from services.financial_reports_service import (
        generate_income_statement,
        generate_balance_sheet,
        generate_cash_flow_statement,
    )

    period_start = date(period_year, period_month, 1)

    if period_month == 12:
        period_end = date(period_year, 12, 31)
    else:
        next_month = period_month + 1
        next_year = period_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        period_end = date(next_year, next_month, 1) - timedelta(days=1)

    reports = {}

    try:
        is_report = generate_income_statement(db, period_start, period_end, "OMR", country_code)
        reports["income_statement"] = is_report.to_dict() if hasattr(is_report, 'to_dict') else {}
    except Exception as e:
        logger.warning("Income statement generation failed: %s", e)
        reports["income_statement"] = {"error": str(e)}

    try:
        bs_report = generate_balance_sheet(db, period_end, "OMR", country_code)
        reports["balance_sheet"] = bs_report.to_dict() if hasattr(bs_report, 'to_dict') else {}
    except Exception as e:
        logger.warning("Balance sheet generation failed: %s", e)
        reports["balance_sheet"] = {"error": str(e)}

    try:
        cf_report = generate_cash_flow_statement(db, period_start, period_end, "OMR", country_code)
        reports["cash_flow_statement"] = cf_report.to_dict() if hasattr(cf_report, 'to_dict') else {}
    except Exception as e:
        logger.warning("Cash flow statement generation failed: %s", e)
        reports["cash_flow_statement"] = {"error": str(e)}

    reports["period_year"] = period_year
    reports["period_month"] = period_month
    reports["country_code"] = country_code

    return reports


def generate_supplier_statements(
    db: Session,
    period_year: int,
    period_month: int,
    country_code: str = None,
) -> dict:
    """Generate supplier statements for a period.

    Returns summary of orders, payouts, and outstanding payables.
    """
    period_start = date(period_year, period_month, 1)

    if period_month == 12:
        period_end = date(period_year, 12, 31)
    else:
        next_month = period_month + 1
        next_year = period_year
        if next_month > 12:
            next_month = 1
            next_year += 1
        period_end = date(next_year, next_month, 1) - timedelta(days=1)

    statements = []

    from data.models import SupplierProfile, Order, OrderItem, CommissionAgreement, Product

    suppliers = db.query(SupplierProfile).all()

    for supplier in suppliers:
        supplier_id = supplier.id

        total_sales = Decimal("0")
        order_count = 0

        items = db.query(OrderItem).join(
            Order, OrderItem.order_id == Order.id
        ).filter(
            OrderItem.supplier_id == supplier_id,
            Order.created_at >= period_start,
            Order.created_at <= period_end,
        ).all()

        for item in items:
            total_sales += item.price * item.quantity if item.price else Decimal("0")
            order_count += 1

        agreement = db.query(CommissionAgreement).filter(
            CommissionAgreement.supplier_id == supplier_id,
            CommissionAgreement.is_active == True,
        ).first()

        commission_rate = Decimal(str(agreement.commission_rate)) if agreement and agreement.commission_rate else Decimal("0")
        total_commission = total_sales * commission_rate

        statements.append({
            "supplier_id": supplier_id,
            "supplier_name": supplier.business_name or f"Supplier {supplier_id}",
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "sales": float(total_sales),
            "total_commission": float(total_commission),
            "commission_rate": float(commission_rate),
            "order_count": order_count,
        })

    return {
        "period_year": period_year,
        "period_month": period_month,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "total_suppliers": len(statements),
        "statements": statements,
        "country_code": country_code,
    }


def run_alert_engine(db: Session, country_code: str = None) -> dict:
    """Run the alert engine to detect issues requiring attention.

    Returns a list of active alerts for the specified country.
    """
    alerts = []

    from data.models import (
        BankReconciliation,
        BankStatementLine,
        FraudAlert,
    )

    unmapped_lines = db.query(BankStatementLine).filter(
        BankStatementLine.status == "unmapped",
    )
    if country_code:
        unmapped_lines = unmapped_lines.filter(BankStatementLine.country_code == country_code)

    for line in unmapped_lines.all():
        alerts.append({
            "type": "unmapped_bank_line",
            "severity": "medium",
            "message": f"Bank statement line {line.id} is unmapped",
            "entity_id": line.id,
            "country_code": line.country_code,
        })

    fraud_alerts = db.query(FraudAlert).filter(
        FraudAlert.status.in_(["active", "investigating"]),
    )
    if country_code:
        fraud_alerts = fraud_alerts.filter(FraudAlert.country_code == country_code)

    for alert in fraud_alerts.all():
        alerts.append({
            "type": "fraud_alert",
            "severity": "critical",
            "message": f"Fraud alert #{alert.id}: {alert.alert_type}",
            "alert_id": alert.id,
            "alert_type": alert.alert_type,
        })

    return {
        "country_code": country_code,
        "total_alerts": len(alerts),
        "alerts": alerts,
    }