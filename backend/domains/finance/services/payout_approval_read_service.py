"""Payout-approval read service.

Owns the read/aggregation behind the Admin Payout Approval Dashboard so the
router stays free of ``db.query`` calls. The shape returned by ``get_pending_payouts``
is identical to the former inline implementation in ``routers/public_treasury_payments.py``.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from sqlalchemy.orm import Session, joinedload

from domains.accounts.models.user import User
from domains.finance.models.finance import FinanceAutomationLog
from domains.finance.models.finance import PayoutBatch
from domains.finance.models.finance import PayoutBatchItem
from domains.logistics.models.logistics import LogisticsPartner
from domains.payments.models.payments import LogisticsPartnerPayout
from domains.payments.models.payments import Payout


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
    if not entity_ids:
        return {}
    users = db.query(User).filter(User.id.in_(entity_ids)).all()
    return {cast(int, u.id): cast(str, u.username or u.email or f"Supplier #{u.id}") for u in users}


def _resolve_logistics_names(entity_ids: set[int], db: Session) -> dict[int, str]:
    if not entity_ids:
        return {}
    partners = db.query(LogisticsPartner).filter(LogisticsPartner.id.in_(entity_ids)).all()
    return {cast(int, p.id): cast(str, p.name or f"Partner #{p.id}") for p in partners}


def _enrich_batch_items(batch: PayoutBatch, db: Session) -> list[dict[str, Any]]:
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


def get_pending_payouts(db: Session, page: int, page_size: int) -> dict[str, Any]:
    """Return all pending payout batches and unbatched payouts for admin review."""
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


def list_payouts(db: Session, country_code: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List payouts for a country with pagination (returns ORM rows)."""
    q = db.query(Payout).filter(Payout.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def list_pending_payouts(db: Session, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List all pending payouts (RLS-scoped by request context if set)."""
    q = db.query(Payout).filter(Payout.status == "pending")
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def list_pending_payouts_by_country(db: Session, country_code: str, page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """List pending payouts for a specific country."""
    q = db.query(Payout).filter(Payout.status == "pending", Payout.country_code == country_code.upper())
    total = q.count()
    rows = q.order_by(Payout.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": rows, "total": total, "page": page, "page_size": page_size}


def get_payout_approval_history(db: Session, limit: int = 20) -> list[dict[str, Any]]:
    """Recent FinanceAutomationLog entries for the auto-payout background job."""
    history = (
        db.query(FinanceAutomationLog)
        .filter(FinanceAutomationLog.kind.in_(["auto_payout", "auto_logistics_payout"]))
        .order_by(FinanceAutomationLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": h.id,
            "kind": h.kind,
            "records_processed": h.records_processed,
            "records_changed": h.records_changed,
            "detail": h.detail,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]
