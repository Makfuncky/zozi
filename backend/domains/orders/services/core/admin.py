
# -------------------------------------------------------------------
# FROM: admin_orders_service.py
# -------------------------------------------------------------------

"""Auto-migrated service logic from routers/admin_orders.py."""
from __future__ import annotations

import math

from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from modules.admin.routers.admin_controller import (
    archive_entity,
    bulk_archive_entities,
    bulk_restore_entities,
    hard_delete_entity,
    restore_entity,
    update_order_status,
)

from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    ArchiveRequest,
    BulkActionRequest,
    BulkStatusUpdateRequest,
    OrderStatusUpdate,
)

from domains.governance.models.user import User
from domains.orders.models.orders import Order

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin, require_super_admin

from infrastructure.utils.rls_interceptor import set_rls_context

def list_all_orders(country_code: str, page: int, size: int, status: str, include_deleted: bool, _: User, db: Session):
    if country_code == "*":
        set_rls_context(None, is_restricted=False)
    else:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(Order)
        if status:
            q = q.filter(Order.status == status)
        if not include_deleted:
            q = q.filter(Order.is_deleted == False)
        total = q.count()
        items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
        return {"items": items, "total": total, "page": page, "pages": math.ceil(total / size) if total else 1}
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def update_status(country_code: str, order_id: int, payload: OrderStatusUpdate, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        acting_user = {
            "id": current_user.id,
            "username": current_user.username,
            "role": current_user.role,
        }
        result = update_order_status(order_id, payload.status, acting_user, db)
        return {
            "message": "Updated",
            "from": result.get("old_status"),
            "to": result.get("new_status", payload.status),
        }
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def archive_order(country_code: str, order_id: int, payload: ArchiveRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return archive_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
            payload.reason if payload else None,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def restore_order(country_code: str, order_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return restore_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def bulk_archive_orders(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_archive_entities(
            "order",
            payload.ids,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
            payload.reason,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def bulk_restore_orders(country_code: str, payload: BulkActionRequest, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return bulk_restore_entities(
            "order",
            payload.ids,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def bulk_update_order_status(country_code: str, payload: BulkStatusUpdateRequest, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        updated = 0
        for oid in payload.ids:
            o = db.query(Order).filter(Order.id == oid).first()
            if o:
                o.status = payload.status
                updated += 1
        db.commit()
        return {"message": f"Status updated for {updated} orders", "updated": updated}
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()

def delete_order_permanent(country_code: str, order_id: int, _: User, db: Session, current_user: User):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return hard_delete_entity(
            "order",
            order_id,
            {"id": current_user.id, "username": current_user.username, "role": current_user.role},
            db,
        )
    finally:
        from infrastructure.utils.rls_interceptor import clear_rls_context
        clear_rls_context()




# -------------------------------------------------------------------
# FROM: admin_orders_read_service.py
# -------------------------------------------------------------------

"""Read helpers for admin order listing.

Extracted from ``routers/admin_orders_status.py`` so the router stays a thin
HTTP layer (W1: routers must not issue DB queries directly). The router sets
the country RLS context; this service only builds and runs the query.
"""

import math

from sqlalchemy.orm import Session

from domains.orders.models.orders import Order


def list_orders_paginated(
    db: Session,
    *,
    page: int,
    size: int,
    status: str | None = None,
    include_deleted: bool = False,
) -> dict:
    """Paginated admin order list (country scoping applied via RLS in the router)."""
    q = db.query(Order)
    if status:
        q = q.filter(Order.status == status)
    if not include_deleted:
        q = q.filter(Order.is_deleted == False)
    total = q.count()
    items = q.order_by(Order.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": math.ceil(total / size) if total else 1,
    }


# -------------------------------------------------------------------
# FROM: admin_orders_write_service.py
# -------------------------------------------------------------------

"""Admin orders write service — transaction ownership for admin bulk order flows.

Layer-1 code (routers / controllers) must never drive session transaction state
directly; it delegates here so that only ``services/`` owns DB transactions.
"""

from sqlalchemy.orm import Session
import structlog
from domains.orders.models.orders import Order
logger = structlog.get_logger(__name__)


def bulk_update_order_status(db: Session, ids: list, status: str) -> dict:
    """Set ``status`` on every order id in ``ids`` that still exists.

    Behaviour-preserving extraction of the inline loop formerly in
    ``routers.admin_orders_status.bulk_update_order_status``: one commit per
    request, count of actually-updated rows returned as-is.
    """
    updated = 0
    for oid in ids:
        o = db.query(Order).filter(Order.id == oid).first()
        if o:
            o.status = status
            updated += 1
    db.commit()
    return {"message": f"Status updated for {updated} orders", "updated": updated}


def discard_bulk_delete_transaction(db: Session) -> None:
    """Discard pending session state after a bulk delete removed nothing.

    ``services.orders.orders_write_service.delete_order_with_savepoint`` commits
    each successful deletion and rolls its own savepoint back on failure, so when
    no order at all could be deleted there is nothing worth keeping: drop whatever
    is still pending on the session.
    """
    db.rollback()

