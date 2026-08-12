"""Admin users controller (CONTROLLERS layer).

Canonical coordinator for admin user / staff management. Enforces country RLS
and delegates to ``services.admin.users_service``.

HTTP contract declared with ``routers.generated.auto_router`` decorators.
"""
from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from db.schemas import CreateStaffAccount, UpdateStaffAccount
from routers.generated.auto_router import delete, get, post, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.users_service import (
    bulk_delete_users_admin,
    bulk_toggle_users_active,
    bulk_update_staff_accounts,
    bulk_update_users_role,
    create_staff_account,
    delete_staff_account,
    delete_user_admin,
    force_reset_password_admin,
    get_all_users,
    list_staff_accounts,
    toggle_user_active,
    update_staff_account,
    update_user_role,
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


def _require_super(actor: dict):
    if actor.get("role") not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Super admin only")


@get(
    "/api/v1/admin/users/{country_code}",
    deps=["db", "admin"],
    query=["search", "page", "page_size"],
    tags=["admin-users"],
)
def list_users(
    country_code: str,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_all_users(db, limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/users/{country_code}/staff",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def list_staff(
    country_code: str,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return list_staff_accounts(db)
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/users/{country_code}/{user_id}/role",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def update_user_role_route(
    country_code: str,
    user_id: int,
    role: str = "customer",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return update_user_role(user_id, role, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/{user_id}/toggle-active",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def toggle_user_active_route(
    country_code: str,
    user_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return toggle_user_active(user_id, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/bulk/toggle-active",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def bulk_toggle_users_active_route(
    country_code: str,
    ids: list[int] = None,
    is_active: bool = False,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_toggle_users_active(ids or [], is_active, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/bulk/role",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def bulk_update_users_role_route(
    country_code: str,
    ids: list[int] = None,
    role: str = "customer",
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_update_users_role(ids or [], role, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/staff",
    deps=["db", "admin"],
    body=CreateStaffAccount,
    tags=["admin-users"],
)
def create_staff_account_route(
    country_code: str,
    payload: CreateStaffAccount,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return create_staff_account(payload, actor, db)
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/users/{country_code}/staff/{user_id}",
    deps=["db", "admin"],
    body=UpdateStaffAccount,
    tags=["admin-users"],
)
def update_staff_account_route(
    country_code: str,
    user_id: int,
    payload: UpdateStaffAccount,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return update_staff_account(user_id, payload, actor, db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/users/{country_code}/staff/{user_id}",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def delete_staff_account_route(
    country_code: str,
    user_id: int,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return delete_staff_account(user_id, actor, db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/staff/bulk",
    deps=["db", "admin"],
    query=["ids"],
    body=UpdateStaffAccount,
    tags=["admin-users"],
)
def bulk_update_staff_accounts_route(
    country_code: str,
    ids: list[int] = None,
    payload: UpdateStaffAccount = None,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return bulk_update_staff_accounts(ids or [], payload, actor, db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/{user_id}/reset-password",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def force_reset_password_route(
    country_code: str,
    user_id: int,
    new_password: str = "",
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return force_reset_password_admin(user_id, new_password, actor, db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/users/{country_code}/{user_id}",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def delete_user_route(
    country_code: str,
    user_id: int,
    delete_orders: bool = False,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return delete_user_admin(user_id, actor, db, delete_orders=delete_orders)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/users/{country_code}/bulk/delete",
    deps=["db", "admin"],
    tags=["admin-users"],
)
def bulk_delete_users_route(
    country_code: str,
    ids: list[int] = None,
    current_user=None,
    db: Session = None,
):
    actor = _actor(current_user)
    _require_super(actor)
    _with_rls(country_code, db)
    try:
        return bulk_delete_users_admin(ids or [], actor, db)
    finally:
        clear_rls_context()
