"""Admin suppliers controller (CONTROLLERS layer).

Canonical coordinator for admin supplier verification / management. Enforces
country RLS and delegates to ``services.admin.suppliers_service``.

HTTP contract declared with ``core.route_contract`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.route_contract import get, post

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.suppliers_service import (
    bulk_manage_suppliers,
    bulk_supplier_verification,
    get_all_suppliers,
    get_pending_suppliers,
    get_supplier_comparison,
    reject_supplier,
    verify_supplier,
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
    "/api/v1/admin/suppliers/{country_code}",
    deps=["db", "admin"],
    query=["search", "page", "page_size"],
    tags=["admin-suppliers"],
)
def list_suppliers(
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
        return get_all_suppliers(db, limit=page_size, skip=offset, q=search)
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/suppliers/{country_code}/pending",
    deps=["db", "admin"],
    query=["page", "page_size"],
    tags=["admin-suppliers"],
)
def list_pending_suppliers(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_pending_suppliers(db, limit=page_size, offset=offset)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/suppliers/{country_code}/{supplier_id}/verify",
    deps=["db", "admin"],
    tags=["admin-suppliers"],
)
def verify_supplier_route(
    country_code: str,
    supplier_id: int,
    note: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return verify_supplier(supplier_id, note, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/suppliers/{country_code}/{supplier_id}/reject",
    deps=["db", "admin"],
    tags=["admin-suppliers"],
)
def reject_supplier_route(
    country_code: str,
    supplier_id: int,
    note: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return reject_supplier(supplier_id, note, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/suppliers/{country_code}/bulk/verify",
    deps=["db", "admin"],
    tags=["admin-suppliers"],
)
def bulk_verify_suppliers_route(
    country_code: str,
    ids: list[int] = None,
    action: str = "approve",
    note: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_supplier_verification(ids or [], action, note, _actor(current_user), db)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/suppliers/{country_code}/bulk/manage",
    deps=["db", "admin"],
    tags=["admin-suppliers"],
)
def bulk_manage_suppliers_route(
    country_code: str,
    ids: list[int] = None,
    action: str = "approve",
    note: Optional[str] = None,
    badge_level: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return bulk_manage_suppliers(
            ids or [], action, note, _actor(current_user), db, badge_level=badge_level
        )
    finally:
        clear_rls_context()


@get(
    "/api/v1/admin/suppliers/{country_code}/comparison",
    deps=["db", "admin"],
    query=["page", "page_size"],
    tags=["admin-suppliers"],
)
def supplier_comparison(
    country_code: str,
    page: int = 1,
    page_size: int = 50,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        offset = max(0, (page - 1) * page_size)
        return get_supplier_comparison(db, limit=page_size, offset=offset)
    finally:
        clear_rls_context()
