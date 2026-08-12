"""Admin permissions controller (CONTROLLERS layer).

Canonical coordinator for staff permission / role management. Delegates to
``services.admin.permissions_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from routers.generated.auto_router import get, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.permissions_service import (
    get_hierarchy_permissions,
    get_staff_permission_catalog,
    update_role_permissions,
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
    "/api/v1/admin/permissions/{country_code}/catalog",
    deps=["db", "admin"],
    tags=["admin-permissions"],
)
def permission_catalog(
    country_code: str,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_staff_permission_catalog()
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/permissions/{country_code}/hierarchy",
    deps=["db", "admin"],
    tags=["admin-permissions"],
)
def permission_hierarchy(
    country_code: str,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return get_hierarchy_permissions(_actor(current_user))
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/permissions/{country_code}/roles/{role}",
    deps=["db", "admin"],
    tags=["admin-permissions"],
)
def update_role_permissions_route(
    country_code: str,
    role: str,
    permissions: list[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return update_role_permissions(role, permissions or [], db, _actor(current_user))
    finally:
        clear_rls_context()
