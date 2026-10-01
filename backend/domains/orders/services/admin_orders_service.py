"""Auto-migrated service logic from routers/admin_orders.py."""
from __future__ import annotations

import math

from fastapi import Depends, Path, Query

from sqlalchemy.orm import Session

from domains.governance.ports import archive_entity, bulk_archive_entities, bulk_restore_entities, hard_delete_entity, restore_entity
from domains.orders.services.orders_service import update_order_status
from domains.orders.services.core.admin import list_orders_paginated
from domains.orders.services.core.bulk import bulk_update_order_status as core_bulk_update_order_status

from infrastructure.database.database import get_db

from infrastructure.database.schemas import (
    ArchiveRequest,
    BulkActionRequest,
    BulkStatusUpdateRequest,
    OrderStatusUpdate,
)

from domains.accounts.models.user import User
from domains.orders.models.orders import Order

from infrastructure.utils.country_rls import get_country_or_404

from infrastructure.utils.dependencies import require_admin, require_super_admin

from infrastructure.database.rls_interceptor import set_rls_context

def list_all_orders(country_code: str, page: int, size: int, status: str, include_deleted: bool, _: User, db: Session):
    if country_code == "*":
        set_rls_context(None, is_restricted=False)
    else:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        result = list_orders_paginated(
            db,
            page=page,
            size=size,
            status=status if status else None,
            include_deleted=include_deleted,
        )
        result["pages"] = math.ceil(result["total"] / size) if result["total"] else 1
        return result
    finally:
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
        clear_rls_context()

def bulk_update_order_status(country_code: str, payload: BulkStatusUpdateRequest, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return core_bulk_update_order_status(payload.ids, payload.status, db)
    finally:
        from infrastructure.database.rls_interceptor import clear_rls_context
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
        from infrastructure.database.rls_interceptor import clear_rls_context
        clear_rls_context()


