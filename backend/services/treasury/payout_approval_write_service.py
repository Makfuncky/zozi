"""Payout-approval write service (W1-exempt transaction owner).

Owns every DB mutation behind the Admin Payout Approval Dashboard so that
``routers/payout_approval.py`` and ``controllers/payout_approval_controller.py``
stay free of ``db.add`` / ``db.commit`` / ``db.delete`` / ``db.flush`` (audit
rule W1: only ``services/**`` may own DB transactions).

Behaviour is preserved exactly as it was implemented in the router:
status-transition guards (404 / 409), note-append formatting, batch-item
cascades, the dispatch fan-out to ``Payout`` / ``LogisticsPartnerPayout``, and
the returned response payloads.

NOTE — audit logging: the router previously called
``audit_log(db=db, action=AuditAction.PAYOUT_PROCESSED, user_id=..., username=...,
user_role=..., resource_type=..., resource_id=...)``. That call could never
succeed: ``AuditAction`` has no ``PAYOUT_PROCESSED`` member (AttributeError) and
``utils.audit.audit_log`` takes ``actor_id`` / ``entity`` / ``entity_key`` rather
than ``user_id`` / ``resource_type`` / ``resource_id``. Every write endpoint
therefore raised HTTP 500 *after* committing. The calls below preserve the
original intent while matching the real ``audit_log`` signature.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from data.models import LogisticsPartnerPayout, Payout, PayoutBatch, SupplierProfile
from utils.audit import audit_log
from utils.datetime_utils import utcnow
import structlog
logger = structlog.get_logger(__name__)

# Action recorded on the audit trail for every payout-approval mutation.
PAYOUT_PROCESSED = "payout_processed"


# ── Internal helpers ─────────────────────────────────────────────────────────


def _audit(
    db: Session,
    *,
    actor_id: int | None,
    actor_username: str | None,
    entity: str,
    entity_key: Any,
    details: dict[str, Any],
) -> None:
    """Record a payout-approval action on the audit trail.

    ``audit_log`` swallows and logs its own exceptions, so a failure here can
    never mask the already-committed business mutation.
    """
    audit_log(
        db=db,
        actor_id=int(actor_id or 0),
        action=PAYOUT_PROCESSED,
        entity=entity,
        entity_key=str(entity_key),
        details={**details, "username": actor_username, "role": "admin"},
    )


def _get_payout_or_404(db: Session, payout_id: int) -> Payout:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    return payout


def _get_batch_or_404(db: Session, batch_id: int) -> PayoutBatch:
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Payout batch not found")
    return batch


# ── Individual payout actions ────────────────────────────────────────────────


def approve_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = _get_payout_or_404(db, payout_id)
    if payout.status not in ("pending", "draft"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve payout in '{payout.status}' status.",
        )
    payout.status = "approved"
    if notes:
        payout.notes = (payout.notes or "") + f"\nApproved: {notes}"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout",
        entity_key=payout_id,
        details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}


def reject_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = _get_payout_or_404(db, payout_id)
    if payout.status not in ("pending", "draft", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject payout in '{payout.status}' status.",
        )
    payout.status = "rejected"
    if notes:
        payout.notes = (payout.notes or "") + f"\nRejected: {notes}"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout",
        entity_key=payout_id,
        details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
    )
    return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}


# ── Batch-level actions ──────────────────────────────────────────────────────


def approve_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft → approved."""
    batch = _get_batch_or_404(db, batch_id)
    if batch.status not in ("draft", "pending"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.",
        )
    now = utcnow()
    batch.status = "approved"
    batch.approved_by = cast(int, actor_id)
    batch.notes = (batch.notes or "") + (
        f"\nApproved by admin #{actor_id} at {now.isoformat()}."
        + (f" Notes: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "approved"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={"action": "approve", "batch_number": batch.batch_number},
    )
    return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}


def reject_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft → rejected."""
    batch = _get_batch_or_404(db, batch_id)
    if batch.status not in ("draft", "pending", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject batch in '{batch.status}' status.",
        )
    now = utcnow()
    old_status = batch.status
    batch.status = "rejected"
    batch.notes = (batch.notes or "") + (
        f"\nRejected by admin #{actor_id} at {now.isoformat()}."
        + (f" Reason: {notes}" if notes else "")
    )
    for item in batch.items or []:
        item.status = "pending"

    db.commit()
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={
            "action": "reject",
            "batch_number": batch.batch_number,
            "previous_status": old_status,
        },
    )
    return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}


def dispatch_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    actor_id: int | None = None,
    actor_username: str | None = None,
) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch.

    Updates the batch status to dispatched, marks all batch items as paid,
    and updates the underlying Payout / LogisticsPartnerPayout records to paid.
    """
    batch = _get_batch_or_404(db, batch_id)
    if batch.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.",
        )
    now = utcnow()
    batch.status = "dispatched"
    batch.dispatched_at = now
    batch.notes = (batch.notes or "") + (
        f"\nDispatched by admin #{actor_id} at {now.isoformat()}."
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

    # --- Bulk-update Payout records for suppliers in this batch ---
    # Batch items store entity_id = supplier_id (set by the auto-payout
    # scheduler).  We match by Payout.supplier_id, which is the correct
    # column.  This is safe because the status filter (pending/approved)
    # prevents touching already-paid payouts from prior batches.
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
    _audit(
        db,
        actor_id=actor_id,
        actor_username=actor_username,
        entity="payout_batch",
        entity_key=batch_id,
        details={"action": "dispatch", "batch_number": batch.batch_number},
    )
    return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}


# ── Bulk status maintenance ──────────────────────────────────────────────────


def update_payout_status_by_ids(db: Session, payout_ids: list[int], status: str) -> None:
    """Update status for specific Payout records by their primary key.

    Moved out of the router with the rest of the write path; the caller owns
    when (or whether) to commit.
    """
    if payout_ids:
        now = utcnow()
        db.query(Payout).filter(
            Payout.id.in_(payout_ids),
            Payout.status.in_(["pending", "draft", "approved"]),
        ).update({"status": status, "processed_at": now}, synchronize_session=False)


def request_supplier_payout(db: Session, current_user, payload: dict) -> dict:
    """Create a supplier-initiated payout request and commit."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, 'Supplier profile not found')
    amount = payload.get('amount')
    if not amount or float(amount) <= 0:
        raise HTTPException(400, 'A positive payout amount is required')
    payout = Payout(
        supplier_id=supplier.id,
        amount=float(amount),
        method=payload.get('method', 'bank'),
        notes=payload.get('notes', 'Supplier-initiated payout request'),
        status='pending',
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {
        'status': 'success',
        'payout': {
            'id': payout.id,
            'amount': float(payout.amount),
            'status': payout.status,
        },
    }
