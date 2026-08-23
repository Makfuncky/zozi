"""Category admin controller (CONTROLLERS layer).

Canonical coordinator for admin category management. Enforces the country
RLS context and delegates persistence to
services.catalog.category_admin_{read,write}_service and the shared
controllers.admin.admin_controller archive helpers.

The HTTP contract is declared with ``infrastructure.routing.route_contract`` decorators
so the auto-router emits ``routers/admin_catalog_category_admin.py``.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.schemas import ArchiveRequest, BulkActionRequest
from infrastructure.routing.route_contract import delete, get, post, put

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

from domains.governance.services.settings.misc_service import archive_entity
from domains.catalog.services.bulk_ops_write_service import bulk_archive_entities
from domains.catalog.services.bulk_ops_write_service import bulk_restore_entities
from domains.governance.services.settings.misc_service import restore_entity
from domains.catalog.services.category_admin_read_service import list_categories_paginated
from domains.catalog.services.category_admin_write_service import create_category as svc_create_category
from domains.catalog.services.category_admin_write_service import delete_category as svc_delete_category
from domains.catalog.services.category_admin_write_service import reorder_categories as svc_reorder_categories
from domains.catalog.services.category_admin_write_service import update_category as svc_update_category


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
    """Enter country-restricted RLS context (caller must clear in finally)."""
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)


@get(
    "/api/v1/admin/categories/{country_code}",
    deps=["db", "admin"],
    query=["include_deleted", "page", "page_size"],
    tags=["admin-categories"],
)
def list_categories(
    country_code: str,
    include_deleted: bool = False,
    page: int = 1,
    page_size: int = 20,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return list_categories_paginated(
            db,
            country_code=country_code.upper(),
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )
    finally:
        clear_rls_context()


@post("/api/v1/admin/categories/{country_code}", deps=["db", "admin"], tags=["admin-categories"])
def create_category(
    country_code: str,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    parent_id: Optional[int] = None,
    sort_order: int = 0,
    description: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    return svc_create_category(
        db,
        country_code,
        name=name,
        slug=slug,
        parent_id=parent_id,
        sort_order=sort_order,
        description=description,
    )


@put(
    "/api/v1/admin/categories/{country_code}/{category_id}",
    deps=["db", "admin"],
    tags=["admin-categories"],
)
def update_category(
    country_code: str,
    category_id: int,
    name: Optional[str] = None,
    slug: Optional[str] = None,
    parent_id: Optional[int] = None,
    sort_order: Optional[int] = None,
    description: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    return svc_update_category(
        db,
        country_code,
        category_id,
        name=name,
        slug=slug,
        parent_id=parent_id,
        sort_order=sort_order,
        description=description,
    )


@post(
    "/api/v1/admin/categories/{country_code}/{category_id}/archive",
    deps=["db", "admin"],
    body=ArchiveRequest,
    tags=["admin-categories"],
)
def archive_category(
    country_code: str,
    category_id: int,
    payload: ArchiveRequest,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return archive_entity(
            "category",
            category_id,
            _actor(current_user),
            db,
            payload.reason if payload else None,
        )
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/categories/{country_code}/{category_id}/restore",
    deps=["db", "admin"],
    tags=["admin-categories"],
)
def restore_category(
    country_code: str,
    category_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return restore_entity("category", category_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/categories/{country_code}/reorder",
    deps=["db", "admin"],
    tags=["admin-categories"],
)
def reorder_categories(
    country_code: str,
    order: Optional[dict] = None,
    current_user=None,
    db: Session = None,
):
    return svc_reorder_categories(db, country_code, order)


@post(
    "/api/v1/admin/categories/{country_code}/bulk/archive",
    deps=["db", "admin"],
    body=BulkActionRequest,
    tags=["admin-categories"],
)
def bulk_archive_categories(
    country_code: str,
    payload: BulkActionRequest,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_archive_entities(
            "category", payload.ids, _actor(current_user), db, payload.reason
        )
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/categories/{country_code}/bulk/restore",
    deps=["db", "admin"],
    body=BulkActionRequest,
    tags=["admin-categories"],
)
def bulk_restore_categories(
    country_code: str,
    payload: BulkActionRequest,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_restore_entities("category", payload.ids, _actor(current_user), db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/categories/{country_code}/{category_id}",
    deps=["db", "admin"],
    tags=["admin-categories"],
)
def delete_category(
    country_code: str,
    category_id: int,
    current_user=None,
    db: Session = None,
):
    return svc_delete_category(db, country_code, category_id)
