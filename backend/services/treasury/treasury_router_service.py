"""
Treasury Router Service - Database operations for treasury and payout approval routers.
All SQLAlchemy DB access is centralized here.
"""

import logging
from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from data.models import (
    LogisticsPartner,
    LogisticsPartnerPayout,
    Payout,
    PayoutBatch,
    PayoutBatchItem,
    User,
)
from utils.datetime_utils import utcnow
from utils.audit_log import audit_log, AuditAction
from services.core.write_helpers import commit_only

logger = logging.getLogger(__name__)


def _resolve_supplier_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for supplier IDs."""
    if not entity_ids:
        return {}
    users = db.query(User).filter(User.id.in_(entity_ids)).all()
    return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}


def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    """Return {entity_id: display_name} for logistics partner IDs."""
    if not entity_ids:
        return {}
    partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
    return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}


def _serialize_payout(p: Payout) -> dict[str, Any]:
    return {
        "id": cast(int, p.id),
        "supplier_id": cast(int | None, p.supplier_id),
        "order_id": cast(int | None, p.order_id),
        "amount": float(cast(Decimal, p.amount or 0)),
        "currency": cast(str | None, p.currency) or "OMR",
        "method": cast(str | None, p.method) or "",
        "status": cast(str | None, p.status) or "",
        "reference": cast(str | None, p.reference),
        "notes": cast(str | None, p.notes),
        "country_code": cast(str | None, p.country_code) or "",
        "created_at": cast(Any, p.created_at).isoformat() if getattr(p, "created_at", None) else None,
        "processed_at": cast(Any, p.processed_at).isoformat() if getattr(p, "processed_at", None) else None,
    }


def _serialize_batch_item(item: PayoutBatchItem) -> dict[str, Any]:
    return {
        "id": cast(int, item.id),
        "entity_type": cast(str, item.entity_type),
        "entity_id": cast(int, item.entity_id),
        "amount": float(cast(Decimal, item.amount or 0)),
        "currency": cast(str | None, item.currency) or "OMR",
        "reference": cast(str | None, item.reference),
        "status": cast(str | None, item.status) or "",
    }


def _serialize_batch(batch: PayoutBatch) -> dict[str, Any]:
    return {
        "id": cast(int, batch.id),
        "batch_number": cast(str, batch.batch_number),
        "country_code": cast(str, batch.country_code),
        "total_amount": float(cast(Decimal, batch.total_amount or 0)),
        "item_count": cast(int, batch.item_count or 0),
        "status": cast(str, batch.status),
        "notes": cast(str | None, batch.notes),
        "created_at": cast(Any, batch.created_at).isoformat() if getattr(batch, "created_at", None) else None,
        "items": [],
    }


def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
    """Return batch items with resolved entity_name fields."""
    items = list(batch.items or [])
    supplier_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "supplier"}
    logistics_ids = {cast(int, it.entity_id) for it in items if cast(str, it.entity_type) == "logistics"}
    supplier_names = _resolve_supplier_names(supplier_ids, db)
    logistics_names = _resolve_logistics_names(logistics_ids, db)

    enriched = []
    for item in items:
        e = _serialize_batch_item(item)
        eid = cast(int, item.entity_id)
        etype = cast(str, item.entity_type)
        if etype == "supplier":
            e["entity_name"] = supplier_names.get(eid, f"Supplier #{eid}")
        elif etype == "logistics":
            e["entity_name"] = logistics_names.get(eid, f"Partner #{eid}")
        else:
            e["entity_name"] = f"#{eid}"
        enriched.append(e)
    return enriched


def _load_unbatched_payouts(
    db: Session, page: int, page_size: int
) -> tuple[list[dict[str, Any]], int]:
    """Return paginated individual Payout records with supplier names."""
    query = db.query(Payout).filter(Payout.status.in_(["pending", "draft"]))
    total = query.count()
    payouts = query.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    supplier_ids = {cast(int, p.supplier_id) for p in payouts if p.supplier_id}
    supplier_names = _resolve_supplier_names(supplier_ids, db) if supplier_ids else {}

    result = []
    for payout in payouts:
        s = _serialize_payout(payout)
        sid = cast(int | None, payout.supplier_id)
        s["supplier_name"] = supplier_names.get(cast(int, sid), f"Supplier #{sid}") if sid else None
        result.append(s)
    return result, total


def _load_pending_batches_with_items(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
    """Return paginated batches in draft/pending status with enriched items."""
    query = db.query(PayoutBatch).options(joinedload(PayoutBatch.items)).filter(
        PayoutBatch.status.in_(["draft", "pending"])
    )
    total = query.count()
    batches = query.order_by(PayoutBatch.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for batch in batches:
        s = _serialize_batch(batch)
        s["items"] = _enrich_batch_items(batch, db)
        result.append(s)
    return result, total


def get_pending_payouts(
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review.

    Pagination is applied independently to batches and unbatched payouts.
    """
    batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
    unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

    logistics_payout_q = db.query(LogisticsPartnerPayout).filter(
        LogisticsPartnerPayout.status.in_(["pending", "draft"]),
    )
    logistics_payout_total = logistics_payout_q.count()
    logistics_payouts = logistics_payout_q.order_by(LogisticsPartnerPayout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    logistics_ids = {cast(int, lp.partner_id) for lp in logistics_payouts if lp.partner_id}
    logistics_names = _resolve_logistics_names(logistics_ids, db) if logistics_ids else {}

    unbatched_logistics = []
    for lp in logistics_payouts:
        pid = cast(int | None, lp.partner_id)
        unbatched_logistics.append({
            "id": cast(int, lp.id),
            "partner_id": pid,
            "partner_name": logistics_names.get(cast(int, pid), f"Partner #{pid}") if pid else None,
            "amount": float(cast(Decimal, lp.amount or 0)),
            "currency": cast(str | None, lp.currency) or "OMR",
            "status": cast(str | None, lp.status) or "",
            "reference": cast(str | None, lp.reference),
            "notes": cast(str | None, lp.notes),
            "created_at": cast(Any, lp.created_at).isoformat() if getattr(lp, "created_at", None) else None,
        })

    total_amount = sum(b["total_amount"] for b in batches)
    total_items = sum(b["item_count"] for b in batches)

    return {
        "pending_batches": batches,
        "unbatched_payouts": unbatched,
        "unbatched_logistics_payouts": unbatched_logistics,
        "summary": {
            "total_batches": batch_total,
            "total_amount": round(total_amount, 2),
            "total_items": total_items,
            "pending_payouts_count": payout_total,
            "pending_logistics_payouts_count": logistics_payout_total,
        },
        "pagination": {"page": page, "page_size": page_size},
    }


def approve_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    current_admin: User | None = None,
) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status not in ("pending", "draft"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve payout in '{payout.status}' status.",
        )
    payout.status = "approved"
    if notes:
        payout.notes = (payout.notes or "") + f"\nApproved: {notes}"

    commit_only(db)
    if current_admin:
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "approve", "amount": float(cast(Decimal, payout.amount or 0))},
        )
    return {"message": "Payout approved", "payout_id": payout_id, "status": "approved"}


def reject_payout(
    db: Session,
    payout_id: int,
    notes: str | None = None,
    current_admin: User | None = None,
) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    if payout.status not in ("pending", "draft", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject payout in '{payout.status}' status.",
        )
    payout.status = "rejected"
    if notes:
        payout.notes = (payout.notes or "") + f"\nRejected: {notes}"

    commit_only(db)
    if current_admin:
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout",
            resource_id=payout_id,
            details={"action": "reject", "amount": float(cast(Decimal, payout.amount or 0))},
        )
    return {"message": "Payout rejected", "payout_id": payout_id, "status": "rejected"}


def approve_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    current_admin: User | None = None,
) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft → approved."""
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Payout batch not found")
    if batch.status not in ("draft", "pending"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot approve batch in '{batch.status}' status. Only draft/pending batches can be approved.",
        )
    now = utcnow()
    batch.status = "approved"
    if current_admin:
        batch.approved_by = cast(int, current_admin.id)
    batch.notes = (batch.notes or "") + (
        f"\nApproved by admin #{current_admin.id} at {now.isoformat()}."
        if current_admin else ""
    )
    if notes:
        batch.notes = (batch.notes or "") + f" Notes: {notes}"
    for item in batch.items or []:
        item.status = "approved"

    commit_only(db)
    if current_admin:
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "approve", "batch_number": batch.batch_number},
        )
    return {"message": "Batch approved", "batch_id": batch_id, "status": "approved"}


def reject_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    current_admin: User | None = None,
) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft → rejected."""
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Payout batch not found")
    if batch.status not in ("draft", "pending", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot reject batch in '{batch.status}' status.",
        )
    now = utcnow()
    old_status = batch.status
    batch.status = "rejected"
    if current_admin:
        batch.notes = (batch.notes or "") + (
            f"\nRejected by admin #{current_admin.id} at {now.isoformat()}."
        )
    if notes:
        batch.notes = (batch.notes or "") + f" Reason: {notes}"
    for item in batch.items or []:
        item.status = "pending"

    commit_only(db)
    if current_admin:
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "reject", "batch_number": batch.batch_number, "previous_status": old_status},
        )
    return {"message": "Batch rejected", "batch_id": batch_id, "status": "rejected"}


def dispatch_batch(
    db: Session,
    batch_id: int,
    notes: str | None = None,
    current_admin: User | None = None,
) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch.

    Updates the batch status to dispatched, marks all batch items as paid,
    and updates the underlying Payout / LogisticsPartnerPayout records to paid.
    """
    batch = (
        db.query(PayoutBatch)
        .options(joinedload(PayoutBatch.items))
        .filter(PayoutBatch.id == batch_id)
        .first()
    )
    if not batch:
        raise HTTPException(status_code=404, detail="Payout batch not found")
    if batch.status != "approved":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot dispatch batch in '{batch.status}' status. Only approved batches can be dispatched.",
        )
    now = utcnow()
    batch.status = "dispatched"
    batch.dispatched_at = now
    if current_admin:
        batch.notes = (batch.notes or "") + (
            f"\nDispatched by admin #{current_admin.id} at {now.isoformat()}."
        )
    if notes:
        batch.notes = (batch.notes or "") + f" Notes: {notes}"

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

    commit_only(db)
    if current_admin:
        audit_log(
            db=db, action=AuditAction.PAYOUT_PROCESSED,
            user_id=current_admin.id, username=current_admin.username,
            user_role="admin", resource_type="payout_batch",
            resource_id=batch_id,
            details={"action": "dispatch", "batch_number": batch.batch_number},
        )
    return {"message": "Batch dispatched", "batch_id": batch_id, "status": "dispatched"}