"""Payout approval workflow service (Law 2: domain owns the transaction).

Mirrors the admin payout-approval router's mutate endpoints so the HTTP layer
stays a thin wrapper. Reads (the /pending dashboard) remain in the router as the
accepted read-layer.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload

from domains.finance.models.finance import PayoutBatch, PayoutBatchItem
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import LogisticsPartnerPayout, Payout
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.datetime_utils import utcnow


def approve_payout(payout_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException_not_found("Payout not found")
    if payout.status not in ("pending", "draft"):
        raise HTTPException_conflict(f"Cannot approve payout in '{payout.status}' status.")
    payout.status = "approved"
    if notes:
        payout.notes = (payout.notes or "") + f"\nApproved: {notes}"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}


def reject_payout(payout_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException_not_found("Payout not found")
    if payout.status not in ("pending", "draft", "approved"):
        raise HTTPException_conflict(f"Cannot reject payout in '{payout.status}' status.")
    payout.status = "rejected"
    if notes:
        payout.notes = (payout.notes or "") + f"\nRejected: {notes}"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout",
        resource_id=payout_id,
        details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}


def _load_batch(batch_id: int, db: Session) -> PayoutBatch:
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException_not_found("Payout batch not found")
    return batch


def approve_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Approve a payout batch — draft → approved."""
    batch = _load_batch(batch_id, db)
    if batch.status not in ("draft", "pending"):
        raise HTTPException_conflict(
            f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved."
        )
    now = utcnow()
    batch.status = "approved"
    batch.approved_by = cast(int, admin_id)
    batch.notes = (batch.notes or "") + (
        f"\nApproved by admin #{admin_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "approved"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "approve", "batch_number": batch.batch_number},
    )
    return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}


def reject_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Reject a payout batch — draft → rejected."""
    batch = _load_batch(batch_id, db)
    if batch.status not in ("draft", "pending", "approved"):
        raise HTTPException_conflict(f"Cannot reject batch in '{batch.status}' status.")
    now = utcnow()
    old_status = batch.status
    batch.status = "rejected"
    batch.notes = (batch.notes or "") + (
        f"\nRejected by admin #{admin_id} at {now.isoformat()}."
        + (f" Reason: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "pending"
    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "reject", "batch_number": batch.batch_number, "previous_status": old_status},
    )
    return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}


def dispatch_batch(batch_id: int, notes: str | None, admin_id: int, admin_username: str, db: Session) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch."""
    batch = _load_batch(batch_id, db)
    if batch.status != "approved":
        raise HTTPException_conflict(
            f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched."
        )
    now = utcnow()
    batch.status = "dispatched"
    batch.dispatched_at = now
    batch.notes = (batch.notes or "") + (
        f"\nDispatched by admin #{admin_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )

    supplier_payout_ids: list[int] = []
    logistics_payout_ids: list[int] = []

    for item in batch.items or []:
        item.status = "paid"
        etype = cast(str, item.entity_type)
        eid = cast(int, item.entity_id)
        if etype == "supplier":
            supplier_payout_ids.append(eid)
        elif etype == "logistics":
            logistics_payout_ids.append(eid)

    if supplier_payout_ids:
        db.query(Payout).filter(
            Payout.supplier_id.in_(supplier_payout_ids),
            Payout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    if logistics_payout_ids:
        db.query(LogisticsPartnerPayout).filter(
            LogisticsPartnerPayout.partner_id.in_(logistics_payout_ids),
            LogisticsPartnerPayout.status.in_(["pending", "approved"]),
        ).update({"status": "paid", "processed_at": now}, synchronize_session=False)

    db.commit()
    audit_log(
        db=db, action=AuditAction.PAYOUT_PROCESSED,
        user_id=admin_id, username=admin_username,
        user_role="admin", resource_type="payout_batch",
        resource_id=batch_id,
        details={"action": "dispatch", "batch_number": batch.batch_number},
    )
    return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}


def HTTPException_not_found(detail: str):
    from fastapi import HTTPException
    return HTTPException(status_code=404, detail=detail)


def HTTPException_conflict(detail: str):
    from fastapi import HTTPException
    return HTTPException(status_code=409, detail=detail)
