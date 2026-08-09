"""Coupons controller (CONTROLLERS layer).

Coordinates coupon business rules (normalization, active/eligibility checks,
duplicate prevention, usage-history guards) and delegates ALL persistence to
``services.commerce.coupons_read_service`` / ``coupons_write_service``. It must
not issue ``db.query`` directly and must not perform commits.

``current_user`` is a ``User`` ORM object (returned by
``utils.dependencies.get_current_user``); role/identity are read via attributes,
never dict-style access.

All field references use the live ``Coupon`` model columns (``discount_value``,
``minimum_order``, ``usage_limit``), not the legacy ``value`` / ``min_order`` /
``max_uses`` aliases.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Coupon
from utils.audit import audit_log
from utils.datetime_utils import utcnow
from utils.money import round_money, to_decimal

from services.commerce.coupons_read_service import (
    get_coupon_by_code_active as service_get_by_code,
    get_coupon_by_id as service_get_by_id,
    get_coupon_usage_count as service_usage_count,
    list_coupons as service_list,
)
from services.commerce.coupons_write_service import (
    create_coupon as service_create,
    delete_coupon as service_delete,
)
import structlog
logger = structlog.get_logger(__name__)


def _user_id(current_user) -> int:
    return int(current_user.id)


def _serialize_coupon(coupon: Coupon) -> dict:
    """Plain-dict view of a Coupon using only real model columns.

    Returned to the HTTP layer instead of an ORM object so serialization never
    depends on a live session (the object is detached once the request scope
    closes).
    """
    return {
        "id": coupon.id,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": float(coupon.discount_value) if coupon.discount_value is not None else None,
        "minimum_order": float(coupon.minimum_order) if coupon.minimum_order is not None else None,
        "maximum_discount": float(coupon.maximum_discount) if coupon.maximum_discount is not None else None,
        "usage_limit": coupon.usage_limit,
        "usage_count": coupon.usage_count,
        "is_active": coupon.is_active,
        "starts_at": coupon.starts_at.isoformat() if coupon.starts_at else None,
        "expires_at": coupon.expires_at.isoformat() if coupon.expires_at else None,
        "country_code": coupon.country_code,
        "created_at": coupon.created_at.isoformat() if coupon.created_at else None,
    }


def _user_role(current_user) -> str:
    return str(getattr(current_user, "role", "") or "")


def _calculate_discount(coupon: Coupon, order_total: Decimal) -> Decimal:
    if str(getattr(coupon, "discount_type", "") or "").lower() == "percent":
        return round_money(order_total * to_decimal(coupon.discount_value) / Decimal("100"))
    return round_money(min(to_decimal(coupon.discount_value), order_total))


def _build_quote(code: str, order_total: Decimal, coupon: Coupon) -> dict:
    normalized_total = round_money(order_total)
    discount = _calculate_discount(coupon, normalized_total)
    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount,
        "new_total": round_money(normalized_total - discount),
        "coupon": coupon,
    }


def build_coupon_quote(code: str, order_total: Decimal, db: Session) -> dict:
    """Public quote builder used by the orders pipeline.

    Preserves the original ``(code, order_total, db)`` signature exactly so the
    orders controller import chain is unaffected. Returns a dict with a
    ``coupon`` ORM reference that callers serialise themselves.
    """
    coupon = service_get_by_code(db, code)
    if coupon is None:
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    now = utcnow()
    if coupon.expires_at and coupon.expires_at < now:
        raise HTTPException(status_code=410, detail="Coupon has expired")
    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
        raise HTTPException(status_code=410, detail="Coupon has reached max uses")
    if round_money(order_total) < to_decimal(coupon.minimum_order):
        raise HTTPException(
            status_code=422,
            detail=f"Minimum order for this coupon is {coupon.minimum_order} AED",
        )
    return _build_quote(code, order_total, coupon)


def validate_coupon(code: str, order_total: Decimal, db: Session) -> dict:
    """Customer-facing validation. Returns a serialisable dict (no ORM refs)."""
    coupon = service_get_by_code(db, code)
    if coupon is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": float(order_total), "coupon": None}
    now = utcnow()
    if coupon.expires_at and coupon.expires_at < now:
        return {"valid": False, "discount_amount": 0.0, "new_total": float(order_total), "coupon": None}
    if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
        return {"valid": False, "discount_amount": 0.0, "new_total": float(order_total), "coupon": None}
    if round_money(order_total) < to_decimal(coupon.minimum_order):
        return {"valid": False, "discount_amount": 0.0, "new_total": float(order_total), "coupon": None}
    quote = _build_quote(code, order_total, coupon)
    return {
        "valid": True,
        "discount_amount": float(quote["discount_amount"]),
        "new_total": float(quote["new_total"]),
        "coupon": {
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value),
        },
    }


def list_coupons(
    db: Session, limit: int = 200, cursor: Optional[int] = None
) -> List[dict]:
    return [_serialize_coupon(c) for c in service_list(db, limit=limit, cursor=cursor)]


def create_coupon(
    code: str,
    discount_type: str,
    discount_value: Decimal,
    minimum_order: Decimal,
    max_uses: Optional[int],
    is_active: bool,
    current_user,
    db: Session,
) -> dict:
    if _user_role(current_user) not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    normalized_code = (code or "").strip().upper()
    if not normalized_code:
        raise HTTPException(status_code=422, detail="Coupon code is required")
    if service_get_by_code(db, normalized_code) is not None:
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    if discount_type not in ("percent", "fixed"):
        raise HTTPException(status_code=422, detail="discount_type must be 'percent' or 'fixed'")

    coupon = service_create(
        db,
        code=normalized_code,
        discount_type=discount_type,
        discount_value=round_money(discount_value),
        minimum_order=round_money(minimum_order),
        usage_limit=max_uses,
        is_active=is_active,
    )
    audit_log(
        db,
        actor_id=_user_id(current_user),
        action="coupon_created",
        entity="coupon",
        entity_key=str(coupon.id),
        details={
            "code": coupon.code,
            "discount_type": coupon.discount_type,
            "username": getattr(current_user, "username", None),
            "role": _user_role(current_user),
        },
    )
    return _serialize_coupon(coupon)


def delete_coupon(coupon_id: int, current_user, db: Session) -> dict:
    if _user_role(current_user) not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail="Admin only")
    coupon = service_get_by_id(db, coupon_id)
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")
    usage_count = service_usage_count(db, coupon.id)
    if usage_count:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} usage record(s). Archive or disable it instead of deleting.",
        )
    coupon_id = coupon.id
    coupon_code = coupon.code
    try:
        service_delete(db, coupon)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("delete_coupon_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Coupon is still referenced by other records. Archive or disable it instead of deleting.",
        ) from None

    audit_log(
        db,
        actor_id=_user_id(current_user),
        action="coupon_deleted",
        entity="coupon",
        entity_key=str(coupon_id),
        details={
            "code": coupon_code,
            "username": getattr(current_user, "username", None),
            "role": _user_role(current_user),
        },
    )
    return {"detail": "Coupon deleted"}