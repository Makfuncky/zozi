"""
Admin Payout Approval Router
=============================
Endpoints for the Admin Payout Approval Dashboard — lists all pending payouts
and batches with supplier/logistics context, and provides an approve/reject/dispatch
workflow.

Routes (mounted at /admin/payout-approval):
  GET  /pending                       → pending payouts + batches with enrichment
  POST /payouts/{payout_id}/approve   → approve an individual (unbatched) payout
  POST /payouts/{payout_id}/reject    → reject an individual payout
  POST /batches/{batch_id}/approve    → approve a batch (draft→approved)
  POST /batches/{batch_id}/reject     → reject a batch
  POST /batches/{batch_id}/dispatch   → mark batch + its payouts as paid

Read/serialization helpers live here (routers -> models reads are permitted for
enrichment); all session writes are delegated to
``controllers.treasury.payout_approval_controller``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from db.database import get_db
from models import (
    LogisticsPartner,
    LogisticsPartnerPayout,
    Payout,
    PayoutBatch,
    PayoutBatchItem,
    SupplierSettlement,
    User,
)
from utils.dependencies import require_admin
from controllers.treasury.payout_approval_controller import (
    approve_payout as approve_payout_action,
    reject_payout as reject_payout_action,
    approve_batch as approve_batch_action,
    reject_batch as reject_batch_action,
    dispatch_batch as dispatch_batch_action,
)

router = APIRouter(prefix="/api/v1/admin")


class ActionRequest(BaseModel):
    notes: str | None = None


# ── Helpers ──────────────────────────────────────────────────────────────────


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
        "items": [_serialize_batch_item(item) for item in (batch.items or [])],
    }


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


def _load_unbatched_payouts(db: Session, page: int, page_size: int) -> tuple[list[dict[str, Any]], int]:
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
        enriched_items = _enrich_batch_items(batch, db)
        s = _serialize_batch(batch)
        s["items"] = enriched_items
        result.append(s)
    return result, total


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/pending")
def get_pending_payouts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review.

    Pagination is applied independently to batches and unbatched payouts.
    """
    batches, batch_total = _load_pending_batches_with_items(db, page, page_size)
    unbatched, payout_total = _load_unbatched_payouts(db, page, page_size)

    # ── Also load standalone logistics partner payouts ──
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


# ── Individual payout actions ────────────────────────────────────────────────


@router.post("/payouts/{payout_id}/approve")
def approve_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve an individual pending payout record."""
    return approve_payout_action(db, payout_id, current_admin, payload)


@router.post("/payouts/{payout_id}/reject")
def reject_payout(
    payout_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reject an individual pending payout record."""
    return reject_payout_action(db, payout_id, current_admin, payload)


# ── Batch-level actions ──────────────────────────────────────────────────────


@router.post("/batches/{batch_id}/approve")
def approve_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Approve a payout batch — moves it from draft → approved."""
    return approve_batch_action(db, batch_id, current_admin, payload)


@router.post("/batches/{batch_id}/reject")
def reject_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Reject a payout batch — moves it from draft → rejected."""
    return reject_batch_action(db, batch_id, current_admin, payload)


@router.post("/batches/{batch_id}/dispatch")
def dispatch_batch(
    batch_id: int,
    payload: ActionRequest | None = None,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Dispatch (mark as paid) an approved payout batch."""
    return dispatch_batch_action(db, batch_id, current_admin, payload)
