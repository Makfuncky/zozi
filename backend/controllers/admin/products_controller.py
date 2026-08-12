"""Admin products controller (CONTROLLERS layer).

Canonical coordinator for admin product management. Enforces country RLS and
delegates persistence to ``services.admin.products_service`` and the shared
archive helpers in ``services.admin.misc_service`` / ``services.admin.bulk_ops_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators so the
auto-router emits the admin product routers.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import delete, get, post, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.misc_service import (
    archive_entity,
    restore_entity,
)
from services.admin.bulk_ops_service import (
    bulk_archive_entities,
    bulk_restore_entities,
)
from services.admin.products_service import (
    approve_product,
    bulk_delete_products_admin,
    delete_product_admin,
    get_all_products,
    get_pending_products,
    reject_product,
    restore_product_admin,
    toggle_product_badge,
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
    "/api/v1/admin/products/{country_code}",
    deps=["db", "admin"],
    query=["search", "filter_value", "page", "page_size"],
    tags=["admin-products"],
)
def list_products(
    country_code: str,
    search: Optional[str] = None,
    filter_value: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_all_products(
            db,
            limit=page_size,
            offset=offset,
            search=search,
            filter_value=filter_value,
        )
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/products/{country_code}/pending",
    deps=["db", "admin"],
    query=["page", "page_size"],
    tags=["admin-products"],
)
def list_pending_products(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_pending_products(db, limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/approve",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def approve_product_route(
    country_code: str,
    product_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return approve_product(product_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/reject",
    deps=["db", "admin"],
    body=None,
    tags=["admin-products"],
)
def reject_product_route(
    country_code: str,
    product_id: int,
    note: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return reject_product(product_id, note, _actor(current_user), db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/products/{country_code}/{product_id}",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def delete_product_route(
    country_code: str,
    product_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return delete_product_admin(product_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/restore",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def restore_product_route(
    country_code: str,
    product_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return restore_product_admin(product_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/badge",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def toggle_product_badge_route(
    country_code: str,
    product_id: int,
    field: str = "is_featured",
    value: bool = True,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return toggle_product_badge(
            product_id, field, value, _actor(current_user), db
        )
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/bulk/delete",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def bulk_delete_products_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_delete_products_admin(ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/archive",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def archive_product_route(
    country_code: str,
    product_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return archive_entity("product", product_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/{product_id}/unarchive",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def unarchive_product_route(
    country_code: str,
    product_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return restore_entity("product", product_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/bulk/archive",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def bulk_archive_products_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_archive_entities("product", ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/products/{country_code}/bulk/restore",
    deps=["db", "admin"],
    tags=["admin-products"],
)
def bulk_restore_products_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_restore_entities("product", ids or [], _actor(current_user), db)
    finally:
        clear_rls_context()
