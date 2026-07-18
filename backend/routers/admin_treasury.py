"""Admin Treasury Router — bridges frontend /admin/treasury/* calls to TreasuryEngine."""
from __future__ import annotations
import json
import logging
from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Body as FastAPIBody, Path
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func

from db.database import get_db
from models import (
    JournalEntry, JournalEntryLine, Account, AccountBalance, User,
    PayoutBatch, PayoutBatchItem, TreasuryAccount, VATRemittance,
    GatewaySettlementSchedule, CashPositionSnapshot, CashFlowForecast,
    BankTransaction, Invoice, SupplierSettlement, TransactionLedger,
)
from models.admin import LogisticsCODRemittanceReceipt
from models.payments import Payout, Payment, LogisticsPartnerPayout
from models.logistics import LogisticsPartner
from models.orders import Order as OrderModel
from models.employee_models import Employee
from services.treasury_engine import TreasuryEngine
from controllers.auth_controller import get_current_user
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from utils.constants import (
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
    TREASURY_ROLES, PAYOUT_STATUSES, SETTLEMENT_STATUSES,
    BATCH_STATUSES, COD_REMITTANCE_STATUSES, GATEWAY_SETTLEMENT_STATUSES,
    CASH_ACCOUNT, PAYABLES_ACCOUNT, OUTPUT_VAT_ACCOUNT, INPUT_VAT_ACCOUNT,
)

router = APIRouter()

def get_engine(db: Session = Depends(get_db)) -> TreasuryEngine:
    return TreasuryEngine(db)

def require_treasury_access(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user.get("role", "").lower() not in TREASURY_ROLES:
        raise HTTPException(status_code=403, detail="Treasury access required")
    return current_user

# ── Dashboard / Metrics ────────────────────────────────────────────────

@router.get("/metrics")
def admin_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    total_debits = db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
        .where(JournalEntryLine.side == "debit")
    ).scalar() or Decimal("0")

    total_credits = db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
        .where(JournalEntryLine.side == "credit")
    ).scalar() or Decimal("0")

    total_entries = db.query(JournalEntry).count()

    return {
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "net_balance": float(total_credits - total_debits),
        "total_entries": total_entries,
    }

# ── General Ledger ─────────────────────────────────────────────────────

@router.get("/ledger")
def admin_treasury_ledger(
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(DEFAULT_PAGE_SIZE),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    entries = db.execute(
        select(JournalEntry)
        .where(JournalEntry.entry_date >= start_date, JournalEntry.entry_date <= end_date)
        .options(joinedload(JournalEntry.lines))
        .order_by(JournalEntry.entry_date.desc())
        .limit(min(limit, MAX_PAGE_SIZE))
    ).unique().scalars().all()

    result = []
    for e in entries:
        total_debit = sum(
            float(line.amount) for line in e.lines if line.side == "debit"
        )
        total_credit = sum(
            float(line.amount) for line in e.lines if line.side == "credit"
        )
        result.append({
            "id": e.id,
            "reference_number": getattr(e, "reference_number", ""),
            "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
            "description": e.description or "",
            "source": e.source or "",
            "total_debit": total_debit,
            "total_credit": total_credit,
        })
    return result

# ── Trial Balance ──────────────────────────────────────────────────────

@router.get("/reports/trial-balance")
def admin_trial_balance(
    as_of_date: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    rows = engine.get_trial_balance()
    return rows

# ── Cash Position ──────────────────────────────────────────────────────

@router.get("/cash-position")
def admin_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    accounts = db.execute(
        select(TreasuryAccount).where(TreasuryAccount.is_active == True)
    ).scalars().all()

    return [
        {
            "account_name": a.name,
            "balance": float(a.balance),
            "gl_code": a.gl_account_code or a.slug,
        }
        for a in accounts
    ]

# ── Payout Batches ────────────────────────────────────────────────────

@router.get("/payouts/batches")
def admin_payout_batches(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    batches = db.execute(
        select(PayoutBatch)
        .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
        .order_by(PayoutBatch.created_at.desc())
        .limit(MAX_PAGE_SIZE)
    ).unique().scalars().all()

    return [
        {
            "id": b.id,
            "batch_number": b.batch_number,
            "country_code": b.country_code,
            "total_amount": float(b.total_amount),
            "status": b.status,
            "created_at": b.created_at.isoformat(),
            "created_by": b.created_by,
            "created_by_name": b.creator.full_name if b.creator else None,
            "approved_by": b.approved_by,
            "approved_by_name": b.approver.full_name if b.approver else None,
        }
        for b in batches
    ]


@router.post("/payouts/batches/generate")
def admin_generate_payout_batch(
    country_code: str = FastAPIBody(...),
    cutoff_date: date = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models.payments import Payout
    from models.suppliers import SupplierProfile

    pending_payouts = db.execute(
        select(Payout).where(
            Payout.country_code == country_code,
            Payout.status == "pending",
            Payout.created_at <= cutoff_date,
        )
    ).scalars().all()

    if not pending_payouts:
        raise HTTPException(status_code=404, detail="No pending payouts found for the given criteria")

    total = sum(p.amount for p in pending_payouts)
    batch = PayoutBatch(
        batch_number=f"PB-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        country_code=country_code,
        total_amount=total,
        item_count=len(pending_payouts),
        status="draft",
        created_by=current_user.get("id"),
    )
    db.add(batch)
    db.flush()

    for payout in pending_payouts:
        item = PayoutBatchItem(
            batch_id=batch.id,
            entity_type="payout",
            entity_id=payout.id,
            amount=payout.amount,
            reference=getattr(payout, "reference_number", None),
        )
        db.add(item)
        payout.status = "batched"
    db.commit()
    db.refresh(batch)

    return {
        "id": batch.id,
        "batch_number": batch.batch_number,
        "country_code": batch.country_code,
        "total_amount": float(batch.total_amount),
        "item_count": batch.item_count,
        "status": batch.status,
    }


@router.post("/payouts/batches/{batch_id}/approve")
def admin_approve_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    batch = db.execute(
        select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
    ).scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "draft":
        raise HTTPException(status_code=400, detail=f"Batch is already {batch.status}")
    if batch.created_by == current_user.get("id"):
        raise HTTPException(status_code=403, detail="Maker-Checker: cannot approve your own batch")

    batch.status = "approved"
    batch.approved_by = current_user.get("id")
    db.commit()

    return {"status": "approved", "batch_id": batch.id, "batch_number": batch.batch_number}


@router.post("/payouts/batches/{batch_id}/dispatch")
def admin_dispatch_payout_batch(
    batch_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    batch = db.execute(
        select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
    ).scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "approved":
        raise HTTPException(status_code=400, detail=f"Batch must be approved first, current status: {batch.status}")

    engine = TreasuryEngine(db)
    entry = engine.post_journal_entry(
        lines=[
            {"account_code": PAYABLES_ACCOUNT, "debit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
            {"account_code": CASH_ACCOUNT, "credit": float(batch.total_amount), "description": f"Payout batch {batch.batch_number}"},
        ],
        description=f"Dispatch payout batch {batch.batch_number}",
        source="payout_dispatch",
        country_code=batch.country_code,
        created_by=current_user.get("id"),
    )

    batch.status = "dispatched"
    batch.dispatched_at = datetime.utcnow()
    db.commit()

    return {
        "status": "dispatched",
        "batch_id": batch.id,
        "batch_number": batch.batch_number,
        "journal_entry_id": entry.id,
        "reference_number": entry.reference_number,
    }

# ── VAT Remittance ─────────────────────────────────────────────────────

@router.get("/reports/vat-liability")
def admin_vat_liability(
    country_code: Optional[str] = Query(None),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    output_vat = db.execute(
        select(func.coalesce(func.sum(AccountBalance.balance), 0))
        .join(Account, AccountBalance.account_id == Account.id)
        .where(Account.code == OUTPUT_VAT_ACCOUNT)
    ).scalar() or Decimal("0")

    input_vat = db.execute(
        select(func.coalesce(func.sum(AccountBalance.balance), 0))
        .join(Account, AccountBalance.account_id == Account.id)
        .where(Account.code == INPUT_VAT_ACCOUNT)
    ).scalar() or Decimal("0")

    return {
        "output_vat": float(output_vat),
        "input_vat": float(input_vat),
        "net_vat_due": float(output_vat - input_vat),
        "country_code": country_code,
        "period": period,
    }

# ── COD Remittances ────────────────────────────────────────────────────

@router.get("/cod-remittances")
def admin_cod_remittances(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models.logistics import LogisticsPartner

    query = (
        select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
        .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
    )
    if status:
        query = query.where(LogisticsCODRemittanceReceipt.status == status)
    query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(MAX_PAGE_SIZE)

    rows = db.execute(query).all()

    return [
        {
            "id": r.id,
            "logistics_partner_id": r.partner_id,
            "logistics_partner_name": partner_name or "Unknown",
            "amount_remitted": float(r.amount or 0),
            "amount_expected": float(r.amount or 0),
            "status": r.status,
            "remitted_at": r.created_at.isoformat() if r.created_at else None,
            "bank_reference": None,
            "proof_url": None,
        }
        for r, partner_name in rows
    ]

# ── Gateway Reconciliation ─────────────────────────────────────────────

@router.get("/reconciliation/gateway-summary")
def admin_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    schedules = db.execute(
        select(GatewaySettlementSchedule)
        .order_by(GatewaySettlementSchedule.settlement_date.desc())
        .limit(100)
    ).scalars().all()

    from collections import defaultdict
    by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

    for s in schedules:
        key = str(s.gateway_id)
        by_gateway[key]["total_expected"] += float(s.amount or 0)
        by_gateway[key]["count"] += 1
        if s.status == "settled":
            by_gateway[key]["total_settled"] += float(s.amount or 0)
        if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
            by_gateway[key]["last_date"] = s.settlement_date

    return [
        {
            "gateway_code": gid,
            "total_settled": data["total_settled"],
            "total_expected": data["total_expected"],
            "discrepancy": data["total_expected"] - data["total_settled"],
            "count": data["count"],
            "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
        }
        for gid, data in by_gateway.items()
    ]

# ── Cash Position Snapshot ────────────────────────────────────────────

@router.post("/cash-position/snapshot")
def admin_snapshot_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    accounts = db.execute(
        select(TreasuryAccount).where(TreasuryAccount.is_active == True)
    ).scalars().all()

    now = datetime.utcnow()
    for a in accounts:
        snap = CashPositionSnapshot(
            snapshot_time=now,
            account_id=a.id,
            balance=a.balance,
            currency=a.currency or "USD",
        )
        db.add(snap)
    db.commit()

    return {"status": "snapshot_recorded", "accounts_snapshotted": len(accounts)}

# ── Cash Flow Forecast (stub) ─────────────────────────────────────────

@router.get("/forecasts")
def admin_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    forecasts = db.execute(
        select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
    ).scalars().all()

    return [
        {
            "id": f.id,
            "forecast_date": f.forecast_date.isoformat(),
            "period_start": f.period_start.isoformat(),
            "period_end": f.period_end.isoformat(),
            "net_cash_flow": float(f.net_cash_flow),
            "opening_balance": float(f.opening_balance),
            "closing_balance": float(f.closing_balance),
        }
        for f in forecasts
    ]


# ── Country-scoped variants ───────────────────────────────────────────
# The frontend Treasury page scopes every panel to a selected country code.
# These routes mirror the global ones but filter by the country where the
# underlying tables carry a `country_code` column.

@router.get("/consolidated/metrics")
def consolidated_treasury_metrics(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    total_accounts = db.query(TreasuryAccount).count()
    total_je = db.query(JournalEntry).count()
    total_batches = db.query(PayoutBatch).count()
    total_invoices = db.query(Invoice).count()
    return {
        "total_accounts": total_accounts,
        "total_journal_entries": total_je,
        "total_payout_batches": total_batches,
        "total_invoices": total_invoices,
    }


@router.get("/consolidated/ledger")
def consolidated_treasury_ledger(
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    entries = db.query(JournalEntry).order_by(JournalEntry.created_at.desc()).limit(limit).all()
    return [
        {
            "id": e.id,
            "description": e.description,
            "entry_type": e.entry_type,
            "amount": float(e.amount),
            "status": e.status,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]


@router.get("/consolidated/reports/trial-balance")
def consolidated_trial_balance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    accounts = db.query(Account).filter(Account.is_active == True).order_by(Account.code).all()
    return [
        {
            "id": a.id,
            "code": a.code,
            "name": a.name,
            "normal_side": a.normal_side,
            "total_debits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "debit").scalar() or 0),
            "total_credits": float(db.query(func.coalesce(func.sum(JournalEntryLine.amount), 0)).filter(JournalEntryLine.account_id == a.id, JournalEntryLine.side == "credit").scalar() or 0),
        }
        for a in accounts
    ]


@router.get("/consolidated/cash-position")
def consolidated_cash_position(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    accounts = db.query(TreasuryAccount).filter(TreasuryAccount.is_active == True).all()
    total = sum(float(a.balance or 0) for a in accounts)
    return {
        "accounts": [
            {
                "id": a.id,
                "name": a.name,
                "balance": float(a.balance or 0),
                "currency": a.currency or "USD",
            }
            for a in accounts
        ],
        "total_balance": total,
    }


@router.get("/consolidated/payouts/batches")
def consolidated_payout_batches(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    batches = db.query(PayoutBatch).order_by(PayoutBatch.created_at.desc()).limit(limit).all()
    return [
        {
            "id": b.id,
            "batch_ref": b.batch_number,
            "status": b.status,
            "total_amount": float(b.total_amount or 0),
            "item_count": b.item_count,
            "country_code": b.country_code,
            "created_at": b.created_at.isoformat(),
        }
        for b in batches
    ]


@router.get("/consolidated/reports/vat-liability")
def consolidated_vat_liability(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    vats = db.query(VATRemittance).order_by(VATRemittance.period_start.desc()).limit(12).all()
    return [
        {
            "id": v.id,
            "country_code": v.country_code,
            "period_start": v.period_start.isoformat(),
            "period_end": v.period_end.isoformat(),
            "total_collected": float(v.vat_collected_amount or 0),
            "total_deducted": float(v.vat_adjustment_amount or 0),
            "net_due": float(v.amount_due or 0),
            "status": v.status,
        }
        for v in vats
    ]


@router.get("/consolidated/cod-remittances")
def consolidated_cod_remittances(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models import Shipment as ShipmentModel
    receipts = db.query(LogisticsCODRemittanceReceipt).order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "shipment_id": r.shipment_id,
            "order_id": (db.query(ShipmentModel.order_id).filter(ShipmentModel.id == r.shipment_id).scalar() if r.shipment_id else None),
            "partner_id": r.partner_id,
            "amount": float(r.amount),
            "bank_reference": r.bank_reference,
            "status": r.status,
            "country_code": r.country_code,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in receipts
    ]


@router.get("/consolidated/reconciliation/gateway-summary")
def consolidated_gateway_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    schedules = db.query(GatewaySettlementSchedule).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(12).all()
    return [
        {
            "id": s.id,
            "gateway": s.gateway_id,
            "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
            "amount": float(s.amount or 0),
            "currency": s.currency,
            "status": s.status,
        }
        for s in schedules
    ]


@router.get("/consolidated/forecasts")
def consolidated_cash_forecasts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    forecasts = db.execute(
        select(CashFlowForecast).order_by(CashFlowForecast.forecast_date.desc()).limit(12)
    ).scalars().all()
    return [
        {
            "id": f.id,
            "forecast_date": f.forecast_date.isoformat(),
            "period_start": f.period_start.isoformat(),
            "period_end": f.period_end.isoformat(),
            "net_cash_flow": float(f.net_cash_flow),
            "opening_balance": float(f.opening_balance),
            "closing_balance": float(f.closing_balance),
        }
        for f in forecasts
    ]


# ── Reconciliation Pipeline ──────────────────────────────────────────
# Full reconciliation flow: Order → Payment → Logistics → Treasury → Supplier
# IMPORTANT: consolidated routes MUST come before {country_code} routes
# to avoid FastAPI matching "consolidated" as a country_code parameter.


@router.get("/consolidated/reconciliation/pipeline")
def consolidated_reconciliation_pipeline(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models.orders import Order as OrderModel
    from models.payments import Payment as PaymentModel, Payout

    pipeline = []
    orders = db.query(OrderModel).filter(
        OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
    ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

    for order in orders:
        payment = db.query(PaymentModel).filter(PaymentModel.order_id == order.id).first()
        settlement = db.query(SupplierSettlement).filter(SupplierSettlement.order_id == order.id).first()
        payout = db.query(Payout).filter(Payout.id == settlement.payout_id).first() if (settlement and settlement.payout_id) else None

        pipeline.append({
            "order_id": order.id,
            "order_status": order.status,
            "order_total": float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0),
            "country_code": order.country_code or "",
            "payment_method": payment.payment_method if payment else None,
            "payment_status": payment.status if payment else None,
            "supplier_settlement_status": settlement.status if settlement else None,
            "supplier_payout_status": payout.status if payout else None,
            "stage": _resolve_stage(order, payment, None, settlement, payout),
        })

    return {"pipeline": pipeline, "total": len(pipeline), "consolidated": True}


@router.get("/{country_code}/metrics")
def country_treasury_metrics(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    cc = country_code.upper()
    total_debits = db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .where(JournalEntryLine.side == "debit", JournalEntry.country_code == cc)
    ).scalar() or Decimal("0")
    total_credits = db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.amount), 0))
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .where(JournalEntryLine.side == "credit", JournalEntry.country_code == cc)
    ).scalar() or Decimal("0")
    total_entries = db.query(JournalEntry).filter(JournalEntry.country_code == cc).count()
    return {
        "total_credits": float(total_credits),
        "total_debits": float(total_debits),
        "net_balance": float(total_credits - total_debits),
        "total_entries": total_entries,
        "country_code": cc,
    }


@router.get("/{country_code}/ledger")
def country_treasury_ledger(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    cc = country_code.upper()
    entries = db.execute(
        select(JournalEntry)
        .where(
            JournalEntry.entry_date >= start_date,
            JournalEntry.entry_date <= end_date,
            JournalEntry.country_code == cc,
        )
        .options(joinedload(JournalEntry.lines))
        .order_by(JournalEntry.entry_date.desc())
        .limit(limit)
    ).unique().scalars().all()
    result = []
    for e in entries:
        result.append({
            "id": e.id,
            "reference_number": getattr(e, "reference_number", ""),
            "entry_date": e.entry_date.isoformat() if hasattr(e, "entry_date") and e.entry_date else "",
            "description": e.description or "",
            "source": e.source or "",
            "total_debit": sum(float(line.amount) for line in e.lines if line.side == "debit"),
            "total_credit": sum(float(line.amount) for line in e.lines if line.side == "credit"),
        })
    return result


@router.get("/{country_code}/reports/trial-balance")
def country_trial_balance(
    country_code: str = Path(..., description="ISO country code"),
    as_of_date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    return engine.get_trial_balance()


@router.get("/{country_code}/cash-position")
def country_cash_position(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    cc = country_code.upper()
    accounts = db.execute(
        select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code == cc)
    ).scalars().all()
    if not accounts:
        accounts = db.execute(
            select(TreasuryAccount).where(TreasuryAccount.is_active == True, TreasuryAccount.country_code.is_(None))
        ).scalars().all()
    return [
        {"account_name": a.name, "balance": float(a.balance), "gl_code": a.gl_account_code or a.slug}
        for a in accounts
    ]


@router.get("/{country_code}/payouts/batches")
def country_payout_batches(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    cc = country_code.upper()
    batches = db.execute(
        select(PayoutBatch)
        .options(joinedload(PayoutBatch.creator), joinedload(PayoutBatch.approver))
        .where(PayoutBatch.country_code == cc)
        .order_by(PayoutBatch.created_at.desc())
        .limit(100)
    ).unique().scalars().all()
    return [
        {
            "id": b.id,
            "batch_number": b.batch_number,
            "country_code": b.country_code,
            "total_amount": float(b.total_amount),
            "status": b.status,
            "created_at": b.created_at.isoformat(),
            "created_by": b.created_by,
            "created_by_name": b.creator.full_name if b.creator else None,
            "approved_by": b.approved_by,
            "approved_by_name": b.approver.full_name if b.approver else None,
        }
        for b in batches
    ]


@router.get("/{country_code}/reports/vat-liability")
def country_vat_liability(
    country_code: str = Path(..., description="ISO country code"),
    period: str = Query("current"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    output_vat = db.execute(
        select(func.coalesce(func.sum(AccountBalance.balance), 0))
        .join(Account, AccountBalance.account_id == Account.id)
        .where(Account.code == OUTPUT_VAT_ACCOUNT)
    ).scalar() or Decimal("0")
    input_vat = db.execute(
        select(func.coalesce(func.sum(AccountBalance.balance), 0))
        .join(Account, AccountBalance.account_id == Account.id)
        .where(Account.code == INPUT_VAT_ACCOUNT)
    ).scalar() or Decimal("0")
    return {
        "output_vat": float(output_vat),
        "input_vat": float(input_vat),
        "net_vat_due": float(output_vat - input_vat),
        "country_code": country_code.upper(),
        "period": period,
    }


@router.get("/{country_code}/cod-remittances")
def country_cod_remittances(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models.logistics import LogisticsPartner

    cc = country_code.upper()
    query = (
        select(LogisticsCODRemittanceReceipt, LogisticsPartner.name)
        .outerjoin(LogisticsPartner, LogisticsCODRemittanceReceipt.partner_id == LogisticsPartner.id)
        .where(LogisticsCODRemittanceReceipt.country_code == cc)
    )
    if status:
        query = query.where(LogisticsCODRemittanceReceipt.status == status)
    query = query.order_by(LogisticsCODRemittanceReceipt.created_at.desc()).limit(100)
    rows = db.execute(query).all()
    return [
        {
            "id": r.id,
            "logistics_partner_id": r.partner_id,
            "logistics_partner_name": partner_name or "Unknown",
            "amount_remitted": float(r.amount or 0),
            "amount_expected": float(r.amount or 0),
            "status": r.status,
            "remitted_at": r.created_at.isoformat() if r.created_at else None,
            "bank_reference": None,
            "proof_url": None,
        }
        for r, partner_name in rows
    ]


@router.get("/{country_code}/reconciliation/gateway-summary")
def country_gateway_summary(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    cc = country_code.upper()
    schedules = db.execute(
        select(GatewaySettlementSchedule)
        .where(GatewaySettlementSchedule.country_code == cc)
        .order_by(GatewaySettlementSchedule.settlement_date.desc())
        .limit(100)
    ).scalars().all()

    from collections import defaultdict
    by_gateway = defaultdict(lambda: {"total_settled": 0, "total_expected": 0, "count": 0, "last_date": None})

    for s in schedules:
        key = str(s.gateway_id)
        by_gateway[key]["total_expected"] += float(s.amount or 0)
        by_gateway[key]["count"] += 1
        if s.status == "settled":
            by_gateway[key]["total_settled"] += float(s.amount or 0)
        if not by_gateway[key]["last_date"] or (s.settlement_date and s.settlement_date > by_gateway[key]["last_date"]):
            by_gateway[key]["last_date"] = s.settlement_date

    return [
        {
            "gateway_code": gid,
            "total_settled": data["total_settled"],
            "total_expected": data["total_expected"],
            "discrepancy": data["total_expected"] - data["total_settled"],
            "count": data["count"],
            "last_settlement_date": data["last_date"].isoformat() if data["last_date"] else None,
        }
        for gid, data in by_gateway.items()
    ]


# ── Consolidated (All-Country) Endpoints ──────────────────────────────
# These provide a cross-country view for super-admin / treasury.


@router.get("/{country_code}/reconciliation/pipeline")
def admin_reconciliation_pipeline(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    cc = country_code.upper()
    try:
        from models.orders import Order as OrderModel, OrderItem
        from models.payments import Payment as PaymentModel, Payout
        from models.logistics import LogisticsPartner
        from models.admin import LogisticsCODRemittanceReceipt
        from services.commission_engine import get_effective_rate

        pipeline = []
        orders = db.query(OrderModel).filter(
            OrderModel.country_code == cc,
            OrderModel.status.in_(["shipped", "delivered", "completed", "dispatched"])
        ).order_by(OrderModel.updated_at.desc()).limit(limit).all()

        for order in orders:
            order_total = float(getattr(order, "total_amount", None) or getattr(order, "total", 0) or 0)
            payment = db.query(PaymentModel).filter(
                PaymentModel.order_id == order.id
            ).first()

            from models import Shipment
            shipment = db.query(Shipment).filter(
                Shipment.order_id == order.id
            ).first()

            logistics_partner_name = None
            if shipment and shipment.carrier_name:
                logistics_partner_name = shipment.carrier_name

            cod_receipt = None
            if payment and payment.payment_method == "cod":
                cod_receipt = db.query(LogisticsCODRemittanceReceipt).filter(
                    LogisticsCODRemittanceReceipt.order_id == order.id
                ).first()

            settlement = db.query(SupplierSettlement).filter(
                SupplierSettlement.order_id == order.id
            ).first()

            payout = None
            if settlement:
                payout = db.query(Payout).filter(
                    Payout.id == settlement.payout_id
                ).first() if settlement.payout_id else None

            supplier_id = None
            first_item = db.query(OrderItem).filter(OrderItem.order_id == order.id).first()
            if first_item:
                supplier_id = first_item.supplier_id

            commission_preview = None
            if supplier_id:
                try:
                    rate = get_effective_rate(supplier_id=supplier_id, product_id=None, db=db)
                    commission_preview = {
                        "rate": float(rate.applied_rate),
                        "amount": float(rate.applied_rate) * order_total if hasattr(rate, 'applied_rate') else 0,
                    }
                except Exception:
                    pass

            pipeline.append({
                "order_id": order.id,
                "order_status": order.status,
                "order_total": order_total,
                "supplier_id": supplier_id,
                "payment_method": payment.payment_method if payment else None,
                "payment_status": payment.status if payment else None,
                "payment_amount": float(payment.amount) if payment else None,
                "logistics_partner": logistics_partner_name,
                "cod_remitted": float(cod_receipt.amount) if cod_receipt else None,
                "cod_remittance_status": cod_receipt.status if cod_receipt else None,
                "supplier_settlement_status": settlement.status if settlement else None,
                "supplier_settlement_id": settlement.id if settlement else None,
                "supplier_net_amount": float(settlement.net_amount) if settlement else None,
                "supplier_payout_status": payout.status if payout else None,
                "supplier_payout_amount": float(payout.amount) if payout else None,
                "commission": commission_preview,
                "stage": _resolve_stage(order, payment, cod_receipt, settlement, payout),
            })

        if status == "settled":
            pipeline = [p for p in pipeline if p["supplier_settlement_status"] in ("paid", "settled")]
        elif status == "unsettled":
            pipeline = [p for p in pipeline if not p["supplier_settlement_status"]]

        return {"pipeline": pipeline, "total": len(pipeline), "country_code": cc}
    finally:
        clear_rls_context()


def _resolve_stage(order, payment, cod_receipt, settlement, payout) -> str:
    if payout and payout.status == "paid":
        return "supplier_paid"
    if settlement and settlement.status in ("paid", "settled"):
        return "supplier_settled"
    if payout and payout.status == "processing":
        return "payout_processing"
    if cod_receipt and cod_receipt.status == "remitted":
        return "cod_remitted"
    if cod_receipt and cod_receipt.status == "pending":
        return "cod_pending"
    if payment and payment.status == "completed":
        return "payment_received"
    if order.status in ("shipped", "delivered", "dispatched"):
        return "order_dispatched"
    return "pending"


@router.post("/{country_code}/reconciliation/record-cod-remittance")
def admin_record_cod_remittance(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    partner_id: int = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    bank_reference: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    cc = country_code.upper()
    try:
        from models.orders import Order as OrderModel
        from models import Shipment as ShipmentModel
        shipment = db.query(ShipmentModel).filter(ShipmentModel.order_id == order_id).first()
        receipt = LogisticsCODRemittanceReceipt(
            shipment_id=shipment.id if shipment else None,
            partner_id=partner_id,
            amount=amount,
            bank_reference=bank_reference,
            status="remitted",
            country_code=cc,
        )
        db.add(receipt)
        db.flush()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            setattr(order, "settlement_status", "cod_remitted")
        db.commit()
        db.refresh(receipt)
        # Keep the double-entry ledger in sync with the reconciliation engine.
        try:
            from services.general_ledger_service import post_logistics_cod_remittance_journal
            post_logistics_cod_remittance_journal(db, receipt.id, Decimal(str(amount)), country_code=cc)
        except Exception as gl_err:
            logger.warning(f"COD remittance GL post skipped: {gl_err}")
        return {"status": "ok", "receipt_id": receipt.id, "country_code": cc}
    finally:
        clear_rls_context()


@router.post("/{country_code}/reconciliation/settle-supplier")
def admin_settle_supplier(
    country_code: str = Path(..., description="ISO country code"),
    order_id: int = FastAPIBody(...),
    supplier_id: int = FastAPIBody(...),
    net_amount: float = FastAPIBody(...),
    gross_amount: Optional[float] = FastAPIBody(None),
    commission_amount: Optional[float] = FastAPIBody(None),
    currency: Optional[str] = FastAPIBody(None),
    payout_id: Optional[int] = FastAPIBody(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    cc = country_code.upper()
    try:
        from models.orders import Order as OrderModel
        from models.countries import CountryConfig
        gross = gross_amount if gross_amount is not None else net_amount
        resolved_currency = currency or "USD"
        ccfg = db.query(CountryConfig).filter(CountryConfig.code == cc).first()
        if ccfg and ccfg.currency:
            resolved_currency = ccfg.currency
        settlement = SupplierSettlement(
            order_id=order_id,
            supplier_id=supplier_id,
            gross_amount=gross,
            commission_amount=commission_amount,
            net_amount=net_amount,
            status="settled",
            payout_id=payout_id,
            currency=resolved_currency,
            country_code=cc,
        )
        db.add(settlement)
        db.flush()
        order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
        if order:
            setattr(order, "settlement_status", "settled")
        db.commit()
        db.refresh(settlement)
        return {"status": "ok", "settlement_id": settlement.id, "country_code": cc}
    finally:
        clear_rls_context()


@router.post("/{country_code}/reconciliation/approve-settlement")
def admin_approve_settlement(
    country_code: str = Path(..., description="ISO country code"),
    settlement_id: int = FastAPIBody(..., embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        settlement = db.query(SupplierSettlement).filter(
            SupplierSettlement.id == settlement_id,
            SupplierSettlement.country_code == country_code.upper(),
        ).first()
        if not settlement:
            raise HTTPException(status_code=404, detail="Settlement not found")
        settlement.status = "paid"
        db.commit()
        try:
            from services.general_ledger_service import post_supplier_settlement_journal
            post_supplier_settlement_journal(
                db,
                settlement.id,
                Decimal(str(settlement.net_amount or 0)),
                supplier_id=settlement.supplier_id,
                country_code=country_code.upper(),
            )
        except Exception as gl_err:
            logger.warning(f"Supplier settlement GL post skipped: {gl_err}")
        return {"status": "ok", "settlement_id": settlement.id}
    finally:
        clear_rls_context()


# ── Reconciliation: Gateway Exceptions ──────────────────────────────────

@router.get("/reconciliation/gateway-exceptions")
def admin_gateway_exceptions(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    issues = db.execute(
        select(GatewaySettlementSchedule).where(
            GatewaySettlementSchedule.status.in_(["pending", "flagged"])
        ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
    ).scalars().all()
    return [
        {
            "id": s.id,
            "gateway_id": s.gateway_id,
            "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
            "amount": float(s.amount or 0),
            "currency": s.currency,
            "status": s.status,
            "country_code": getattr(s, "country_code", None),
        }
        for s in issues
    ]


@router.get("/{country_code}/reconciliation/gateway-exceptions")
def country_gateway_exceptions(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        issues = db.execute(
            select(GatewaySettlementSchedule).where(
                GatewaySettlementSchedule.status.in_(["pending", "flagged"]),
                GatewaySettlementSchedule.country_code == country_code.upper(),
            ).order_by(GatewaySettlementSchedule.settlement_date.desc()).limit(100)
        ).scalars().all()
        return [
            {
                "id": s.id,
                "gateway_id": s.gateway_id,
                "settlement_date": s.settlement_date.isoformat() if s.settlement_date else None,
                "amount": float(s.amount or 0),
                "currency": s.currency,
                "status": s.status,
                "country_code": s.country_code,
            }
            for s in issues
        ]
    finally:
        clear_rls_context()


# ── Payments: Transactions ──────────────────────────────────────────────

@router.get("/payments/transactions")
def admin_payment_transactions(
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    query = (
        select(Payment)
        .where(Payment.created_at >= start_date, Payment.created_at <= end_date)
        .order_by(Payment.created_at.desc())
    )
    if gateway:
        query = query.where(Payment.provider == gateway)
    if status:
        query = query.where(Payment.status == status)
    rows = db.execute(query.limit(200)).scalars().all()
    return [
        {
            "id": p.id,
            "order_id": p.order_id,
            "amount": float(p.amount),
            "payment_method": p.payment_method,
            "provider": p.provider,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "country_code": p.country_code,
        }
        for p in rows
    ]


@router.get("/{country_code}/payments/transactions")
def country_payment_transactions(
    country_code: str = Path(..., description="ISO country code"),
    start_date: date = Query(...),
    end_date: date = Query(...),
    gateway: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = (
            select(Payment)
            .where(
                Payment.country_code == country_code.upper(),
                Payment.created_at >= start_date,
                Payment.created_at <= end_date,
            )
            .order_by(Payment.created_at.desc())
        )
        if gateway:
            query = query.where(Payment.provider == gateway)
        if status:
            query = query.where(Payment.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "order_id": p.order_id,
                "amount": float(p.amount),
                "payment_method": p.payment_method,
                "provider": p.provider,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    finally:
        clear_rls_context()


# ── Payouts: Supplier & Logistics ───────────────────────────────────────

@router.get("/supplier-payouts")
def admin_supplier_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    from models.suppliers import SupplierProfile
    query = (
        select(Payout, SupplierProfile)
        .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
        .order_by(Payout.created_at.desc())
    )
    if status:
        query = query.where(Payout.status == status)
    rows = db.execute(query.limit(200)).all()
    return [
        {
            "id": p.id,
            "supplier_id": p.supplier_id,
            "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
            "amount": float(p.amount),
            "currency": p.currency,
            "method": p.method,
            "status": p.status,
            "reference": p.reference,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "country_code": p.country_code,
        }
        for p, s in rows
    ]


@router.get("/{country_code}/supplier-payouts")
def country_supplier_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        from models.suppliers import SupplierProfile
        query = (
            select(Payout, SupplierProfile)
            .outerjoin(SupplierProfile, Payout.supplier_id == SupplierProfile.id)
            .where(Payout.country_code == country_code.upper())
            .order_by(Payout.created_at.desc())
        )
        if status:
            query = query.where(Payout.status == status)
        rows = db.execute(query.limit(200)).all()
        return [
            {
                "id": p.id,
                "supplier_id": p.supplier_id,
                "supplier_name": s.company_name if s else f"Supplier #{p.supplier_id}",
                "amount": float(p.amount),
                "currency": p.currency,
                "method": p.method,
                "status": p.status,
                "reference": p.reference,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p, s in rows
        ]
    finally:
        clear_rls_context()


@router.get("/logistics-payouts")
def admin_logistics_payouts(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    query = select(LogisticsPartnerPayout).order_by(LogisticsPartnerPayout.created_at.desc())
    if status:
        query = query.where(LogisticsPartnerPayout.status == status)
    rows = db.execute(query.limit(200)).scalars().all()
    return [
        {
            "id": p.id,
            "partner_id": p.partner_id,
            "amount": float(p.amount),
            "currency": p.currency,
            "status": p.status,
            "reference_id": p.reference_id,
            "period_start": p.period_start.isoformat() if p.period_start else None,
            "period_end": p.period_end.isoformat() if p.period_end else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "country_code": p.country_code,
        }
        for p in rows
    ]


@router.get("/{country_code}/logistics-payouts")
def country_logistics_payouts(
    country_code: str = Path(..., description="ISO country code"),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        query = (
            select(LogisticsPartnerPayout)
            .where(LogisticsPartnerPayout.country_code == country_code.upper())
            .order_by(LogisticsPartnerPayout.created_at.desc())
        )
        if status:
            query = query.where(LogisticsPartnerPayout.status == status)
        rows = db.execute(query.limit(200)).scalars().all()
        return [
            {
                "id": p.id,
                "partner_id": p.partner_id,
                "amount": float(p.amount),
                "currency": p.currency,
                "status": p.status,
                "reference_id": p.reference_id,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "country_code": p.country_code,
            }
            for p in rows
        ]
    finally:
        clear_rls_context()


# ── Reports: Supplier Earnings ──────────────────────────────────────────

@router.get("/reports/supplier-earnings")
def admin_supplier_earnings(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    rows = db.execute(
        select(
            SupplierSettlement.supplier_id,
            func.sum(SupplierSettlement.gross_amount).label("gross"),
            func.sum(SupplierSettlement.commission_amount).label("commission"),
            func.sum(SupplierSettlement.net_amount).label("net"),
        ).group_by(SupplierSettlement.supplier_id)
    ).all()
    return [
        {
            "supplier_id": r.supplier_id,
            "gross": float(r.gross or 0),
            "commission": float(r.commission or 0),
            "net": float(r.net or 0),
        }
        for r in rows
    ]


@router.get("/{country_code}/reports/supplier-earnings")
def country_supplier_earnings(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        rows = db.execute(
            select(
                SupplierSettlement.supplier_id,
                func.sum(SupplierSettlement.gross_amount).label("gross"),
                func.sum(SupplierSettlement.commission_amount).label("commission"),
                func.sum(SupplierSettlement.net_amount).label("net"),
            ).where(SupplierSettlement.country_code == country_code.upper())
            .group_by(SupplierSettlement.supplier_id)
        ).all()
        return [
            {
                "supplier_id": r.supplier_id,
                "gross": float(r.gross or 0),
                "commission": float(r.commission or 0),
                "net": float(r.net or 0),
            }
            for r in rows
        ]
    finally:
        clear_rls_context()


# ── Liabilities Exposure ────────────────────────────────────────────────

@router.get("/liabilities/exposure")
def admin_liabilities_exposure(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2040": "vat_payable"}
    exposure = {}
    for code, label in codes.items():
        bal = db.execute(
            select(func.coalesce(func.sum(AccountBalance.balance), 0))
            .join(Account, AccountBalance.account_id == Account.id)
            .where(Account.code == code)
        ).scalar() or Decimal("0")
        exposure[label] = float(bal)
    return exposure


@router.get("/{country_code}/liabilities/exposure")
def country_liabilities_exposure(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        codes = {"2010": "supplier_payables", "2020": "logistics_payables", "2030": "vat_payable"}
        exposure = {}
        for code, label in codes.items():
            bal = db.execute(
                select(func.coalesce(func.sum(AccountBalance.balance), 0))
                .join(Account, AccountBalance.account_id == Account.id)
                .where(Account.code == code, AccountBalance.country_code == country_code.upper())
            ).scalar() or Decimal("0")
            exposure[label] = float(bal)
        return exposure
    finally:
        clear_rls_context()


# ── Ledger: Manual Adjustment & Pending ─────────────────────────────────

@router.post("/ledger/manual-adjustment")
def admin_manual_adjustment(
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    threshold = Decimal("10000")
    amount_dec = Decimal(str(amount))
    lines = [
        {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
        {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
    ]
    if amount_dec > threshold:
        pending = engine.submit_pending_entry(
            lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
        )
        return {"status": "pending_approval", "pending_id": pending["pending_id"]}
    entry = engine.post_journal_entry(
        lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
    )
    return {"entry_id": entry.id, "reference_number": entry.reference_number}


@router.post("/{country_code}/ledger/manual-adjustment")
def country_manual_adjustment(
    country_code: str = Path(..., description="ISO country code"),
    debit_account: str = FastAPIBody(...),
    credit_account: str = FastAPIBody(...),
    amount: float = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    created_by: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        engine = TreasuryEngine(db)
        threshold = Decimal("10000")
        amount_dec = Decimal(str(amount))
        lines = [
            {"account_code": debit_account, "debit": float(amount_dec), "description": reason},
            {"account_code": credit_account, "credit": float(amount_dec), "description": reason},
        ]
        if amount_dec > threshold:
            pending = engine.submit_pending_entry(
                lines=lines, description=reason, created_by=created_by, source="manual_adjustment",
                country_code=country_code.upper(),
            )
            return {"status": "pending_approval", "pending_id": pending["pending_id"]}
        entry = engine.post_journal_entry(
            lines=lines, description=reason, source="manual_adjustment", created_by=created_by,
            country_code=country_code.upper(),
        )
        return {"entry_id": entry.id, "reference_number": entry.reference_number}
    finally:
        clear_rls_context()


@router.get("/ledger/pending")
def admin_pending_entries(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    return {"entries": engine.list_pending_entries()}


@router.get("/{country_code}/ledger/pending")
def country_pending_entries(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        engine = TreasuryEngine(db)
        all_entries = engine.list_pending_entries()
        filtered = [e for e in all_entries if e.get("country_code") == country_code.upper()]
        return {"entries": filtered}
    finally:
        clear_rls_context()


@router.post("/ledger/pending/{pending_id}/approve")
def admin_approve_pending(
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    result = engine.approve_pending_entry(pending_id, approver_id)
    return result


@router.post("/{country_code}/ledger/pending/{pending_id}/approve")
def country_approve_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    approver_id: int = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        engine = TreasuryEngine(db)
        result = engine.approve_pending_entry(pending_id, approver_id)
        return result
    finally:
        clear_rls_context()


@router.post("/ledger/pending/{pending_id}/reject")
def admin_reject_pending(
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    result = engine.reject_pending_entry(pending_id, rejected_by, reason)
    return result


@router.post("/{country_code}/ledger/pending/{pending_id}/reject")
def country_reject_pending(
    country_code: str = Path(..., description="ISO country code"),
    pending_id: int = Path(...),
    rejected_by: int = FastAPIBody(...),
    reason: str = FastAPIBody(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        engine = TreasuryEngine(db)
        result = engine.reject_pending_entry(pending_id, rejected_by, reason)
        return result
    finally:
        clear_rls_context()


# ── Orphan Detector ─────────────────────────────────────────────────────

@router.post("/detect-orphans")
def admin_detect_orphans(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    engine = TreasuryEngine(db)
    alerts = engine.run_orphan_detector()
    return {"alerts": alerts, "count": len(alerts)}


@router.post("/{country_code}/detect-orphans")
def country_detect_orphans(
    country_code: str = Path(..., description="ISO country code"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_treasury_access),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        engine = TreasuryEngine(db)
        alerts = engine.run_orphan_detector()
        filtered = [a for a in alerts if a.get("country_code") == country_code.upper()]
        return {"alerts": filtered, "count": len(filtered)}
    finally:
        clear_rls_context()


@router.get("/payroll/equity")
def payroll_equity(db: Session = Depends(get_db)):
    """Pay-equity snapshot by department (avg male vs female salary)."""
    rows = (
        db.query(
            Employee.department,
            Employee.gender,
            func.avg(Employee.salary),
        ).filter(Employee.salary.isnot(None), Employee.department.isnot(None))
        .group_by(Employee.department, Employee.gender)
        .all()
    )
    by_dept = {}
    for dept, gender, avg_sal in rows:
        by_dept.setdefault(dept, {})[gender or "unknown"] = float(avg_sal or 0)
    metrics = []
    for dept, vals in by_dept.items():
        avg_male = vals.get("male", 0.0)
        avg_female = vals.get("female", 0.0)
        if avg_male > 0 and avg_female > 0:
            disparity = (avg_male - avg_female) / avg_male * 100
        else:
            disparity = 0.0
        metrics.append({
            "category": dept,
            "avg_male": round(avg_male, 2),
            "avg_female": round(avg_female, 2),
            "disparity_percent": round(disparity, 2),
            "flagged": disparity > 10,
        })
    return metrics


@router.get("/{country_code}/payroll")
def country_payroll(country_code: str, db: Session = Depends(get_db)):
    """Aggregate payroll totals for a country (employee headcount + gross/tax/net)."""
    rows = (
        db.query(func.count(Employee.id), func.coalesce(func.sum(Employee.salary), 0))
        .filter(Employee.country_code == country_code.upper())
        .all()
    )
    employee_count = int(rows[0][0] or 0)
    total_gross = float(rows[0][1] or 0)
    total_tax = round(total_gross * 0.05, 2)
    total_net = round(total_gross - total_tax, 2)
    return {
        "employee_count": employee_count,
        "total_gross": round(total_gross, 2),
        "total_tax": total_tax,
        "total_net": total_net,
    }


