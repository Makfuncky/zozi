"""Dispute management and supplier notification preference workflows."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Notification, SupplierDispute, SupplierNotificationPreference
from services.write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
)


_ALLOWED_DISPUTE_TYPES = {"return", "verification", "invoice", "payout", "other"}
_ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
_ALLOWED_STATUSES = {"pending", "under_review", "resolved", "rejected", "closed"}

_PREF_FIELDS = (
    "notify_new_order",
    "notify_low_stock",
    "notify_payout_processed",
    "notify_doc_expiry",
    "notify_return_updates",
    "notify_dispute_updates",
    "in_app_enabled",
    "email_enabled",
    "push_enabled",
)


def _as_int(value: object | None) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _supplier_id_from_user(current_user: dict) -> int:
    user_id = _as_int(current_user.get("id"))
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authenticated user")
    role = str(current_user.get("role") or "").strip().lower()
    if role != "supplier":
        raise HTTPException(status_code=403, detail="Supplier role required")
    return user_id


def _json_loads(value: object | None, fallback: Any) -> Any:
    if value in (None, ""):
        return fallback
    if isinstance(value, (list, dict)):
        return value
    try:
        parsed = json.loads(str(value))
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback
    if parsed is None:
        return fallback
    return parsed


def _serialize_dispute(row: SupplierDispute) -> dict[str, Any]:
    return {
        "id": row.id,
        "supplier_id": row.supplier_id,
        "dispute_type": row.dispute_type,
        "priority": row.priority,
        "status": row.status,
        "title": row.title,
        "description": row.description,
        "return_request_id": row.return_request_id,
        "verification_id": row.verification_id,
        "invoice_id": row.invoice_id,
        "related_order_id": row.related_order_id,
        "evidence_urls": _json_loads(row.evidence_urls, []),
        "metadata": _json_loads(row.metadata_json, {}),
        "supplier_notes": row.supplier_notes,
        "admin_notes": row.admin_notes,
        "resolution_notes": row.resolution_notes,
        "resolved_by": row.resolved_by,
        "resolved_at": row.resolved_at.isoformat() if row.resolved_at else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _serialize_preferences(row: SupplierNotificationPreference) -> dict[str, Any]:
    return {
        "supplier_id": row.supplier_id,
        "notify_new_order": bool(row.notify_new_order),
        "notify_low_stock": bool(row.notify_low_stock),
        "notify_payout_processed": bool(row.notify_payout_processed),
        "notify_doc_expiry": bool(row.notify_doc_expiry),
        "notify_return_updates": bool(row.notify_return_updates),
        "notify_dispute_updates": bool(row.notify_dispute_updates),
        "in_app_enabled": bool(row.in_app_enabled),
        "email_enabled": bool(row.email_enabled),
        "push_enabled": bool(row.push_enabled),
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def _get_or_create_preferences(supplier_id: int, db: Session) -> SupplierNotificationPreference:
    prefs = (
        db.query(SupplierNotificationPreference)
        .filter(SupplierNotificationPreference.supplier_id == supplier_id)
        .first()
    )
    if prefs:
        return prefs

    prefs = SupplierNotificationPreference(supplier_id=supplier_id)
    add_and_flush(db, prefs)
    commit_and_refresh(db, prefs)
    return prefs


def get_supplier_notification_preferences(current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = _supplier_id_from_user(current_user)
    prefs = _get_or_create_preferences(supplier_id, db)
    return _serialize_preferences(prefs)


def update_supplier_notification_preferences(
    payload: dict[str, Any],
    current_user: dict,
    db: Session,
) -> dict[str, Any]:
    supplier_id = _supplier_id_from_user(current_user)
    prefs = _get_or_create_preferences(supplier_id, db)

    for field in _PREF_FIELDS:
        if field not in payload:
            continue
        setattr(prefs, field, bool(payload.get(field)))

    commit_and_refresh(db, prefs)
    return _serialize_preferences(prefs)


def create_supplier_dispute(payload: dict[str, Any], current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = _supplier_id_from_user(current_user)

    dispute_type = str(payload.get("dispute_type") or "other").strip().lower()
    if dispute_type not in _ALLOWED_DISPUTE_TYPES:
        raise HTTPException(status_code=422, detail=f"dispute_type must be one of {sorted(_ALLOWED_DISPUTE_TYPES)}")

    description = str(payload.get("description") or "").strip()
    if not description:
        raise HTTPException(status_code=422, detail="description is required")

    priority = str(payload.get("priority") or "medium").strip().lower()
    if priority not in _ALLOWED_PRIORITIES:
        raise HTTPException(status_code=422, detail=f"priority must be one of {sorted(_ALLOWED_PRIORITIES)}")

    title = str(payload.get("title") or "").strip() or f"{dispute_type.replace('_', ' ').title()} dispute"

    evidence_urls = payload.get("evidence_urls") or []
    if not isinstance(evidence_urls, list):
        raise HTTPException(status_code=422, detail="evidence_urls must be an array")
    sanitized_evidence = [str(url).strip() for url in evidence_urls if str(url).strip()][:20]

    dispute = SupplierDispute(
        supplier_id=supplier_id,
        created_by=supplier_id,
        dispute_type=dispute_type,
        priority=priority,
        status="pending",
        title=title[:255],
        description=description,
        return_request_id=_as_int(payload.get("return_request_id")),
        verification_id=_as_int(payload.get("verification_id")),
        invoice_id=_as_int(payload.get("invoice_id")),
        related_order_id=_as_int(payload.get("related_order_id")),
        evidence_urls=json.dumps(sanitized_evidence),
        metadata_json=json.dumps(payload.get("metadata") or {}),
        supplier_notes=(str(payload.get("supplier_notes") or "").strip() or None),
    )
    add_and_flush(db, dispute)
    commit_and_refresh(db, dispute)

    add_and_flush(db, 
        Notification(
            user_id=supplier_id,
            type="dispute",
            title="Dispute submitted",
            message=f"Dispute #{dispute.id} has been submitted for admin review.",
            link="/supplier/disputes",
            is_read=False,
        )
    )
    commit_only(db)

    return _serialize_dispute(dispute)


def list_supplier_disputes(
    current_user: dict,
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    supplier_id = _supplier_id_from_user(current_user)

    query = db.query(SupplierDispute).filter(SupplierDispute.supplier_id == supplier_id)
    if status:
        normalized_status = status.strip().lower()
        if normalized_status in _ALLOWED_STATUSES:
            query = query.filter(SupplierDispute.status == normalized_status)
    if priority:
        normalized_priority = priority.strip().lower()
        if normalized_priority in _ALLOWED_PRIORITIES:
            query = query.filter(SupplierDispute.priority == normalized_priority)

    total = query.count()
    items = (
        query.order_by(SupplierDispute.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
        .all()
    )
    page_size = min(max(limit, 1), 500)
    return {
        "data": [_serialize_dispute(item) for item in items],
        "total": total,
        "page": (max(offset, 0) // page_size) + 1,
        "pageSize": page_size,
    }


def get_supplier_dispute(dispute_id: int, current_user: dict, db: Session) -> dict[str, Any]:
    supplier_id = _supplier_id_from_user(current_user)
    dispute = (
        db.query(SupplierDispute)
        .filter(SupplierDispute.id == dispute_id, SupplierDispute.supplier_id == supplier_id)
        .first()
    )
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return _serialize_dispute(dispute)


def list_admin_disputes(
    db: Session,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    supplier_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    query = db.query(SupplierDispute)
    if supplier_id is not None:
        query = query.filter(SupplierDispute.supplier_id == supplier_id)
    if status:
        normalized_status = status.strip().lower()
        if normalized_status in _ALLOWED_STATUSES:
            query = query.filter(SupplierDispute.status == normalized_status)
    if priority:
        normalized_priority = priority.strip().lower()
        if normalized_priority in _ALLOWED_PRIORITIES:
            query = query.filter(SupplierDispute.priority == normalized_priority)

    total = query.count()
    items = (
        query.order_by(SupplierDispute.created_at.desc())
        .offset(max(offset, 0))
        .limit(min(max(limit, 1), 500))
        .all()
    )
    page_size = min(max(limit, 1), 500)
    return {
        "data": [_serialize_dispute(item) for item in items],
        "total": total,
        "page": (max(offset, 0) // page_size) + 1,
        "pageSize": page_size,
    }


def get_admin_dispute(dispute_id: int, db: Session) -> dict[str, Any]:
    dispute = db.query(SupplierDispute).filter(SupplierDispute.id == dispute_id).first()
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")
    return _serialize_dispute(dispute)


def update_admin_dispute(dispute_id: int, payload: dict[str, Any], current_admin: dict, db: Session) -> dict[str, Any]:
    dispute = db.query(SupplierDispute).filter(SupplierDispute.id == dispute_id).first()
    if dispute is None:
        raise HTTPException(status_code=404, detail="Dispute not found")

    status = payload.get("status")
    if status is not None:
        normalized_status = str(status).strip().lower()
        if normalized_status not in _ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail=f"status must be one of {sorted(_ALLOWED_STATUSES)}")
        dispute.status = normalized_status
        if normalized_status in {"resolved", "rejected", "closed"}:
            dispute.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
            dispute.resolved_by = _as_int(current_admin.get("id"))

    priority = payload.get("priority")
    if priority is not None:
        normalized_priority = str(priority).strip().lower()
        if normalized_priority not in _ALLOWED_PRIORITIES:
            raise HTTPException(status_code=422, detail=f"priority must be one of {sorted(_ALLOWED_PRIORITIES)}")
        dispute.priority = normalized_priority

    if "admin_notes" in payload:
        dispute.admin_notes = (str(payload.get("admin_notes") or "").strip() or None)
    if "resolution_notes" in payload:
        dispute.resolution_notes = (str(payload.get("resolution_notes") or "").strip() or None)

    commit_and_refresh(db, dispute)

    add_and_flush(db, 
        Notification(
            user_id=dispute.supplier_id,
            type="dispute_update",
            title=f"Dispute #{dispute.id} updated",
            message=f"Your dispute status is now {dispute.status.replace('_', ' ')}.",
            link="/supplier/disputes",
            is_read=False,
        )
    )
    commit_only(db)

    return _serialize_dispute(dispute)


def bulk_update_admin_disputes(
    dispute_ids: list[int],
    action: str,
    value: Optional[str],
    current_admin: dict,
    db: Session,
) -> dict[str, Any]:
    normalized_action = str(action or "").strip().lower()
    if normalized_action not in {"set_status", "set_priority"}:
        raise HTTPException(status_code=422, detail="action must be 'set_status' or 'set_priority'")

    ids = [int(item) for item in dispute_ids if int(item) > 0]
    if not ids:
        raise HTTPException(status_code=422, detail="dispute_ids must contain at least one id")

    rows = db.query(SupplierDispute).filter(SupplierDispute.id.in_(ids)).all()
    if not rows:
        return {"updated": 0, "total_requested": len(ids), "missing_ids": ids}

    admin_id = _as_int(current_admin.get("id"))
    normalized_value = str(value or "").strip().lower()
    if normalized_action == "set_status":
        if normalized_value not in _ALLOWED_STATUSES:
            raise HTTPException(status_code=422, detail=f"value must be one of {sorted(_ALLOWED_STATUSES)} for set_status")
        for row in rows:
            row.status = normalized_value
            if normalized_value in {"resolved", "rejected", "closed"}:
                row.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
                row.resolved_by = admin_id
    else:
        if normalized_value not in _ALLOWED_PRIORITIES:
            raise HTTPException(status_code=422, detail=f"value must be one of {sorted(_ALLOWED_PRIORITIES)} for set_priority")
        for row in rows:
            row.priority = normalized_value

    commit_only(db)

    found_ids = {row.id for row in rows}
    missing_ids = [item for item in ids if item not in found_ids]
    return {
        "updated": len(rows),
        "total_requested": len(ids),
        "missing_ids": missing_ids,
    }

