"""Admin orders controller (CONTROLLERS layer).

Canonical coordinator for admin order management. Enforces country RLS and
delegates persistence to ``services.admin.orders_service`` and the shared
archive helpers in ``services.admin.misc_service`` / ``services.admin.bulk_ops_service``.

HTTP contract declared with ``core.route_contract`` decorators so the
auto-router emits the admin order routers.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from fastapi import HTTPException
from core.route_contract import delete, get, post, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.misc_service import (
    archive_entity,
    hard_delete_entity,
    restore_entity,
)
from services.admin.bulk_ops_service import (
    bulk_archive_entities,
    bulk_restore_entities,
)
from services.admin.orders_service import (
    bulk_delete_orders_admin,
    bulk_update_order_status_admin,
    delete_order_admin,
    get_all_orders,
    refund_order,
    update_order_status,
    update_order_tracking,
)


def _actor(current_user) -> dict:
    if isinstance(current_user, dict):
        return {
            "id": current_user.get("id"),
            "username": current_user.get("username"),
            "role": current_user.get("role"),
        }
    return {
        "id": getattr(current_user, "id", None),
        "username": getattr(current_user, "username", None),
        "role": getattr(current_user, "role", None),
    }


def _with_rls(country_code: str, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/orders/{country_code}",
    deps=["db", "admin"],
    query=["search", "status", "page", "page_size", "date_range", "min_amount", "max_amount", "missing_tracking_only"],
    tags=["admin-orders"],
)
def list_orders(
    country_code: str,
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    date_range: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    missing_tracking_only: bool = False,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_all_orders(
            db,
            limit=page_size,
            offset=offset,
            search=search,
            status=status,
            date_range=date_range,
            min_amount=min_amount,
            max_amount=max_amount,
            missing_tracking_only=missing_tracking_only,
        )
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/orders/{country_code}/{order_id}/status",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def update_order_status_route(
    country_code: str,
    order_id: int,
    status: str = "processing",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return update_order_status(order_id, status, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/{order_id}/archive",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def archive_order_route(
    country_code: str,
    order_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return archive_entity("order", order_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/{order_id}/restore",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def restore_order_route(
    country_code: str,
    order_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return restore_entity("order", order_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/bulk/archive",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def bulk_archive_orders_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_archive_entities("order", ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/bulk/restore",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def bulk_restore_orders_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_restore_entities("order", ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/bulk/status",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def bulk_update_order_status_route(
    country_code: str,
    ids: list[int] = None,
    status: str = "processing",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_update_order_status_admin(ids or [], status, _actor(current_user), db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/orders/{country_code}/{order_id}",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def delete_order_route(
    country_code: str,
    order_id: int,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    if actor.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Super admin only")
    _with_rls(country_code, db)
    try:
        return hard_delete_entity("order", order_id, actor, db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/{order_id}/refund",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def refund_order_route(
    country_code: str,
    order_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return refund_order(order_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/orders/{country_code}/{order_id}/tracking",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def update_order_tracking_route(
    country_code: str,
    order_id: int,
    tracking_number: str = "",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return update_order_tracking(order_id, tracking_number, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/orders/{country_code}/bulk/delete",
    deps=["db", "admin"],
    tags=["admin-orders"],
)
def bulk_delete_orders_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_delete_orders_admin(ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()
