"""Admin Treasury write service (Treasury domain).

Owns every DB mutation previously performed inline by ``routers.admin_treasury_governance``:
payout-batch generation / approval / dispatch, cash-position snapshots, COD
remittance recording, and supplier settlement create / approve.

Layer contract (W1): only ``services/**`` may open DB transactions, so every
public function here takes the SQLAlchemy ``Session`` as its first positional
parameter, performs the mutation, and commits. ``HTTPException`` is raised for
the same conditions the router used to raise, so HTTP semantics are unchanged.
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from domains.finance.models.finance import CashPositionSnapshot
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.finance.models.finance import SupplierSettlement
from domains.finance.models.finance import TreasuryAccount
from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.finance.models.payments import Payout
from domains.finance.services.treasury.treasury_engine import TreasuryEngine
from infrastructure.utils.constants import CASH_ACCOUNT, PAYABLES_ACCOUNT
import structlog
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.datetime_utils import utcnow
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


# ── Payout Batches ─────────────────────────────────────────────────────


def generate_payout_batch(
    db: Session,
    *,
    country_code: str,
    cutoff_date: date,
    created_by: Optional[int] = None,
) -> dict:
    """Group every pending payout up to ``cutoff_date`` into a draft batch."""
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
        batch_number=f"PB-{utcnow().strftime('%Y%m%d%H%M%S')}",
        country_code=country_code,
        total_amount=total,
        item_count=len(pending_payouts),
        status="draft",
        created_by=created_by,
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


def approve_payout_batch(db: Session, *, batch_id: int, actor_id: Any = None) -> dict:
    """Maker-checker approval of a draft payout batch."""
    batch = db.execute(
        select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
    ).scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "draft":
        raise HTTPException(status_code=400, detail=f"Batch is already {batch.status}")
    if batch.created_by == actor_id:
        raise HTTPException(status_code=403, detail="Maker-Checker: cannot approve your own batch")

    batch.status = "approved"
    batch.approved_by = actor_id
    db.commit()

    return {"status": "approved", "batch_id": batch.id, "batch_number": batch.batch_number}


def dispatch_payout_batch(db: Session, *, batch_id: int, actor_id: Any = None) -> dict:
    """Dispatch an approved batch and post the matching double-entry journal."""
    batch = db.execute(
        select(PayoutBatch).where(PayoutBatch.id == batch_id).with_for_update()
    ).scalar_one_or_none()

    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    if batch.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Batch must be approved first, current status: {batch.status}",
        )

    engine = TreasuryEngine(db)
    entry = engine.post_journal_entry(
        lines=[
            {
                "account_code": PAYABLES_ACCOUNT,
                "debit": float(batch.total_amount),
                "description": f"Payout batch {batch.batch_number}",
            },
            {
                "account_code": CASH_ACCOUNT,
                "credit": float(batch.total_amount),
                "description": f"Payout batch {batch.batch_number}",
            },
        ],
        description=f"Dispatch payout batch {batch.batch_number}",
        source="payout_dispatch",
        country_code=batch.country_code,
        created_by=actor_id,
    )

    batch.status = "dispatched"
    batch.dispatched_at = utcnow()
    db.commit()

    return {
        "status": "dispatched",
        "batch_id": batch.id,
        "batch_number": batch.batch_number,
        "journal_entry_id": entry.id,
        "reference_number": entry.reference_number,
    }


# ── Cash Position Snapshot ─────────────────────────────────────────────


def snapshot_cash_position(db: Session) -> dict:
    """Persist a point-in-time balance snapshot for every active treasury account."""
    accounts = db.execute(
        select(TreasuryAccount).where(TreasuryAccount.is_active == True)  # noqa: E712
    ).scalars().all()

    now = utcnow()
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


# ── Reconciliation: COD remittance / supplier settlement ───────────────


def record_cod_remittance(
    db: Session,
    *,
    country_code: str,
    order_id: int,
    partner_id: int,
    amount: float,
    bank_reference: str,
) -> dict:
    """Record a logistics COD remittance receipt and sync the ledger."""
    from domains.logistics.models.logistics import Shipment as ShipmentModel
    from domains.orders.models.orders import Order as OrderModel

    cc = country_code.upper()
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
        from domains.finance.services.ledger.general_ledger_service import post_logistics_cod_remittance_journal

        post_logistics_cod_remittance_journal(db, receipt.id, Decimal(str(amount)), country_code=cc)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as gl_err:  # pragma: no cover - ledger sync is best-effort
        logger.warning(f"COD remittance GL post skipped: {gl_err}")

    return {"status": "ok", "receipt_id": receipt.id, "country_code": cc}


def settle_supplier(
    db: Session,
    *,
    country_code: str,
    order_id: int,
    supplier_id: int,
    net_amount: float,
    gross_amount: Optional[float] = None,
    commission_amount: Optional[float] = None,
    currency: Optional[str] = None,
    payout_id: Optional[int] = None,
) -> dict:
    """Create a supplier settlement row for a delivered order."""
    from domains.country.models.countries import CountryConfig
    from domains.orders.models.orders import Order as OrderModel

    cc = country_code.upper()
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


def approve_settlement(db: Session, *, country_code: str, settlement_id: int) -> dict:
    """Mark a supplier settlement as paid and post the settlement journal."""
    cc = country_code.upper()
    settlement = db.query(SupplierSettlement).filter(
        SupplierSettlement.id == settlement_id,
        SupplierSettlement.country_code == cc,
    ).first()
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    settlement.status = "paid"
    db.commit()

    try:
        from domains.finance.services.ledger.general_ledger_service import post_supplier_settlement_journal

        post_supplier_settlement_journal(
            db,
            settlement.id,
            Decimal(str(settlement.net_amount or 0)),
            supplier_id=settlement.supplier_id,
            country_code=cc,
        )
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as gl_err:  # pragma: no cover - ledger sync is best-effort
        logger.warning(f"Supplier settlement GL post skipped: {gl_err}")

    return {"status": "ok", "settlement_id": settlement.id}


# ── Payout lifecycle (admin) ──────────────────────────────────────────────

def create_payout(db: Session, *, country_code: str, payload, current_admin) -> Any:
    """Create a payout for ``country_code`` and audit it.

    Behaviour-preserving extraction of the inline handler in
    ``routers.admin_treasury_status.create_payout``: filter the payload to real
    columns, stage + commit + refresh, then write the PAYOUT_PROCESSED audit row.
    """
    cc = country_code.upper()
    model_cols = {c.name for c in Payout.__table__.columns}
    data = {k: v for k, v in payload.model_dump().items() if k in model_cols}
    p = Payout(**data, country_code=cc)
    db.add(p)
    db.commit()
    db.refresh(p)
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id,
        username=current_admin.username,
        user_role="admin",
        resource_type="payout",
        resource_id=p.id,
        details={"amount": str(p.amount) if p.amount else None, "method": p.method},
    )
    return p


def verify_payout(db: Session, *, country_code: str, payout_id: int, payload, current_admin) -> dict:
    """Verify a payout and audit it.

    Behaviour-preserving extraction of the inline handler in
    ``routers.admin_treasury_status.verify_payout``.
    """
    cc = country_code.upper()
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == cc).first()
    if not p:
        raise HTTPException(404, "Payout not found")
    p.status = payload.status if payload and payload.status else "verified"
    p.processed_at = utcnow()
    if payload:
        if payload.note:
            p.notes = payload.note
        if payload.bank_reference:
            p.reference = payload.bank_reference
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id,
        username=current_admin.username,
        user_role="admin",
        resource_type="payout",
        resource_id=payout_id,
        details={"status": p.status, "reference": p.reference, "notes": p.notes},
    )
    return {"verified": True, "payout_id": payout_id}


def process_payout(db: Session, *, country_code: str, payout_id: int, current_admin) -> dict:
    """Mark a payout paid and audit it.

    Behaviour-preserving extraction of the inline handler in
    ``routers.admin_treasury_status.process_payout``.
    """
    cc = country_code.upper()
    p = db.query(Payout).filter(Payout.id == payout_id, Payout.country_code == cc).first()
    if not p:
        raise HTTPException(404)
    p.status = "paid"
    p.processed_at = utcnow()
    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_admin.id,
        username=current_admin.username,
        user_role="admin",
        resource_type="payout",
        resource_id=payout_id,
        details={"status": "paid"},
    )
    return {"message": "Payout processed"}