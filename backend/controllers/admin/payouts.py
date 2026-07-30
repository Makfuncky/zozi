"""Admin payout management controller."""
from __future__ import annotations

from typing import Any, List, Optional, cast
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from models import Payout, TransactionLedger, SupplierSettlement, LogisticsSettlement, Notification
from utils.audit import audit_log, AuditAction


def list_pending_payouts(db: Session, limit: int = 200, offset: int = 0) -> list:
    payouts = (
        db.query(Payout)
        .options(joinedload(Payout.supplier))
        .filter(Payout.status.in_(["pending", "processing"]))
        .order_by(Payout.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 200))
        .all()
    )
    return [
        {
            "id": payout.id,
            "supplier_id": payout.supplier_id,
            "supplier_username": payout.supplier.username if payout.supplier else None,
            "amount": float(cast(Any, getattr(payout, "amount")) or 0),
            "status": payout.status,
            "method": payout.method,
            "reference": payout.reference_id,
            "notes": payout.notes,
            "created_at": payout.created_at,
            "processed_at": payout.processed_at,
        }
        for payout in payouts
    ]


def _refresh_order_finance_settlement_status(order_id: int, db: Session) -> None:
    entries = db.query(TransactionLedger).filter(TransactionLedger.order_id == order_id).limit(1000).all()
    if not entries:
        return

    supplier_pairs = [(entry.supplier_id, order_id) for entry in entries if entry.supplier_id]
    logistics_pairs = [
        (entry.logistics_partner_id, order_id)
        for entry in entries
        if entry.logistics_partner_id
    ]

    supplier_settlements = {
        (row.supplier_id, row.order_id): row
        for row in db.query(SupplierSettlement)
        .filter(
            SupplierSettlement.order_id == order_id,
            SupplierSettlement.supplier_id.in_([p[0] for p in supplier_pairs]),
        )
        .all()
    }

    logistics_settlements = {
        (row.partner_id, row.order_id): row
        for row in db.query(LogisticsSettlement)
        .filter(
            LogisticsSettlement.order_id == order_id,
            LogisticsSettlement.partner_id.in_([p[0] for p in logistics_pairs]),
        )
        .all()
    }

    for entry in entries:
        if str(getattr(entry, "settlement_status", "") or "") == "refunded":
            continue

        supplier_settlement = supplier_settlements.get((entry.supplier_id, order_id))
        logistics_settlement = logistics_settlements.get((entry.logistics_partner_id, order_id)) if entry.logistics_partner_id else None

        supplier_done = bool(supplier_settlement and supplier_settlement.status == "settled")
        logistics_done = True if entry.logistics_partner_id is None else bool(
            logistics_settlement and logistics_settlement.status == "settled"
        )

        if supplier_done and logistics_done:
            entry.settlement_status = "fully_settled"
        elif supplier_done:
            entry.settlement_status = "supplier_settled"
        elif logistics_done:
            entry.settlement_status = "logistics_settled"
        else:
            entry.settlement_status = "pending"


def _sync_supplier_settlements_for_payout(
    payout_id: int,
    new_status: str,
    processed_at: datetime | None,
    db: Session,
) -> None:
    settlements = db.query(SupplierSettlement).filter(SupplierSettlement.payout_id == payout_id).all()
    if not settlements:
        return

    touched_order_ids: set[int] = set()
    now = processed_at or datetime.now(timezone.utc).replace(tzinfo=None)

    for settlement in settlements:
        touched_order_ids.add(cast(int, settlement.order_id))

        if new_status == "completed":
            settlement.status = "settled"
            settlement.settled_at = now
        elif new_status == "rejected":
            settlement.status = "eligible" if settlement.eligible_at and settlement.eligible_at <= now else "pending"
            settlement.payout_id = None
            settlement.settled_at = None
            settlement.bank_transaction_id = None
        else:
            settlement.status = "processing"
            settlement.settled_at = None

    for order_id in touched_order_ids:
        _refresh_order_finance_settlement_status(order_id, db)


def verify_payout(
    payout_id: int,
    data: dict,
    acting_user: dict,
    db: Session,
) -> dict:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")

    new_status = str(data.get("status", "")).strip().lower()
    if new_status not in {"processing", "completed", "rejected"}:
        raise HTTPException(status_code=422, detail="status must be one of: processing, completed, rejected")

    setattr(payout, "status", new_status)
    setattr(
        payout,
        "reference_id",
        str(data.get("reference", "")).strip()
        or cast(str | None, getattr(payout, "reference_id"))
        or build_transfer_reference(
            db,
            kind="supplier_payout",
            entity_id=int(cast(int, getattr(payout, "supplier_id"))),
            record_id=int(cast(int, getattr(payout, "id"))),
        ),
    )
    setattr(payout, "notes", str(data.get("notes", "")).strip() or cast(str | None, getattr(payout, "notes")))
    processed_at: datetime | None = None
    if new_status in {"completed", "rejected"}:
        processed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        setattr(payout, "processed_at", processed_at)
    else:
        setattr(payout, "processed_at", None)

    _sync_supplier_settlements_for_payout(payout_id, new_status, processed_at, db)

    supplier_id = cast(int | None, getattr(payout, "supplier_id"))
    if supplier_id:
        message = (
            f"Your payout request #{payout.id} is now {new_status}."
            if new_status != "completed"
            else f"Your payout request #{payout.id} has been completed."
        )
        db.add(
            Notification(
                user_id=supplier_id,
                type="payout",
                title="Payout Update",
                message=message,
                link="/supplier/payouts",
            )
        )

    db.commit()
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="payout",
        resource_id=cast(int, getattr(payout, "id")),
        details={"status": new_status, "reference": cast(str | None, getattr(payout, "reference_id"))},
        status="success",
    )
    return {
        "id": payout.id,
        "status": payout.status,
        "reference": payout.reference_id,
        "notes": payout.notes,
        "processed_at": payout.processed_at,
    }


