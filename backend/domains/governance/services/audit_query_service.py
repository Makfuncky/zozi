"""Read-only audit view for the `audit_logs` table.

Moved out of `controllers/audit_controller.py` (rule **W3** — a controller must
not be imported as shared logic). DB access belongs in `services/**` per the
circuit contract, so the audit *query* surface lives here while the audit
*write* primitive lives in `utils.audit` (importable from every layer).
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from models import AuditLog

__all__ = ["get_audit_logs", "get_unique_actions"]

_MAX_PAGE_SIZE = 200


def _apply_filters(
    query,
    *,
    action_filter: Optional[str],
    user_id_filter: Optional[int],
    resource_type_filter: Optional[str],
    resource_id_filter: Optional[str],
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    search: Optional[str],
):
    if action_filter:
        query = query.filter(AuditLog.action == action_filter)
    if user_id_filter:
        query = query.filter(AuditLog.user_id == user_id_filter)
    if resource_type_filter:
        query = query.filter(AuditLog.entity_type == resource_type_filter)
    if resource_id_filter not in (None, ""):
        text = str(resource_id_filter)
        query = query.filter(AuditLog.entity_id == int(text)) if text.isdigit() else query.filter(False)
    if start_date:
        query = query.filter(AuditLog.created_at >= start_date)
    if end_date:
        query = query.filter(AuditLog.created_at <= end_date)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.action.ilike(like),
                AuditLog.ip_address.ilike(like),
                AuditLog.entity_type.ilike(like),
            )
        )
    return query


def get_audit_logs(
    db: Session,
    page: int = 1,
    page_size: int = 50,
    action_filter: Optional[str] = None,
    user_id_filter: Optional[int] = None,
    resource_type_filter: Optional[str] = None,
    resource_id_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    cursor_id: Optional[int] = None,
) -> dict[str, Any]:
    """Return a page of audit log rows.

    Pass ``cursor_id`` (the ``id`` of the last row of the previous page) to use
    keyset pagination — the performance policy in ARCHITECTURE_DIAGRAM.md §10.5
    forbids ``OFFSET`` on hot lists. ``page`` remains supported for the existing
    admin UI contract.
    """
    page = max(1, int(page or 1))
    page_size = max(1, min(int(page_size or 50), _MAX_PAGE_SIZE))

    base = _apply_filters(
        db.query(AuditLog),
        action_filter=action_filter,
        user_id_filter=user_id_filter,
        resource_type_filter=resource_type_filter,
        resource_id_filter=resource_id_filter,
        start_date=start_date,
        end_date=end_date,
        search=search,
    )

    total = base.order_by(None).count()

    ordered = base.order_by(AuditLog.id.desc())
    if cursor_id:
        items = ordered.filter(AuditLog.id < int(cursor_id)).limit(page_size).all()
    else:
        items = ordered.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, math.ceil(total / page_size)) if total else 1,
        "next_cursor": getattr(items[-1], "id", None) if items else None,
    }


def get_unique_actions(db: Session) -> list[str]:
    rows = db.query(AuditLog.action).distinct().order_by(AuditLog.action).all()
    return [r[0] for r in rows if r[0]]
