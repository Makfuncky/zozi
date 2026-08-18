"""Admin coupons controller (CONTROLLERS layer).

Canonical coordinator for admin coupon management. Delegates to
``services.admin.coupons_service``.

HTTP contract declared with ``core.route_contract`` decorators.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.route_contract import delete, get, post, put

from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

from services.admin.coupons_service import (
    create_coupon,
    delete_coupon,
    list_coupons,
    update_coupon,
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
    "/api/v1/admin/coupons/{country_code}",
    deps=["db", "admin"],
    query=["search", "page", "page_size"],
    tags=["admin-coupons"],
)
def list_coupons_route(
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
        return list_coupons(db, skip=offset, limit=page_size, search=search)
    finally:
        clear_rls_context()


@post(
    "/api/v1/admin/coupons/{country_code}",
    deps=["db", "admin"],
    tags=["admin-coupons"],
)
def create_coupon_route(
    country_code: str,
    code: str = "",
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_type: str = "percentage",
    discount_value: float = 0,
    maximum_discount: Optional[float] = None,
    minimum_order: float = 0,
    usage_limit: Optional[int] = None,
    per_user_limit: Optional[int] = None,
    is_active: bool = True,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        data = {
            "code": code,
            "title": title,
            "description": description,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "maximum_discount": maximum_discount,
            "minimum_order": minimum_order,
            "usage_limit": usage_limit,
            "per_user_limit": per_user_limit,
            "is_active": is_active,
            "starts_at": starts_at,
            "expires_at": expires_at,
        }
        return create_coupon(data, _actor(current_user), db)
    finally:
        clear_rls_context()


@put(
    "/api/v1/admin/coupons/{country_code}/{coupon_id}",
    deps=["db", "admin"],
    tags=["admin-coupons"],
)
def update_coupon_route(
    country_code: str,
    coupon_id: int,
    code: Optional[str] = None,
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_type: Optional[str] = None,
    discount_value: Optional[float] = None,
    maximum_discount: Optional[float] = None,
    minimum_order: Optional[float] = None,
    usage_limit: Optional[int] = None,
    per_user_limit: Optional[int] = None,
    is_active: Optional[bool] = None,
    starts_at: Optional[str] = None,
    expires_at: Optional[str] = None,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        data = {
            "code": code,
            "title": title,
            "description": description,
            "discount_type": discount_type,
            "discount_value": discount_value,
            "maximum_discount": maximum_discount,
            "minimum_order": minimum_order,
            "usage_limit": usage_limit,
            "per_user_limit": per_user_limit,
            "is_active": is_active,
            "starts_at": starts_at,
            "expires_at": expires_at,
        }
        return update_coupon(coupon_id, data, _actor(current_user), db)
    finally:
        clear_rls_context()


@delete(
    "/api/v1/admin/coupons/{country_code}/{coupon_id}",
    deps=["db", "admin"],
    tags=["admin-coupons"],
)
def delete_coupon_route(
    country_code: str,
    coupon_id: int,
    current_user=None,
    db: Session = None,
):
    _with_rls(country_code, db)
    try:
        return delete_coupon(coupon_id, _actor(current_user), db)
    finally:
        clear_rls_context()
