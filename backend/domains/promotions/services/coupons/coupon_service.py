"""
Promotions — Coupon Service (canonical).

Merged from:
  - domains/orders/services/coupons_service.py
  - domains/orders/services/coupons_read_service.py
  - domains/orders/services/coupons_write_service.py
  - domains/orders/services/commerce_coupons_read_service.py
  - domains/orders/services/commerce_coupons_write_service.py
  - domains/orders/services/customer_coupons_create_service.py
  - domains/orders/services/customer_coupons_mgmt_service.py
  - domains/catalog/services/coupons_service.py
  - domains/catalog/services/coupons_read_service.py
  - domains/catalog/services/coupons_write_service.py
  - domains/customers/services/coupons_service.py
  - domains/customers/services/coupons_read_service.py
  - domains/customers/services/coupons_write_service.py
  - domains/_parked/commerce_coupons_read_service.py
  - domains/_parked/commerce_coupons_write_service.py
  - domains/_parked/coupons_legacy_write_service.py
  - domains/_parked/customer_coupons_create_service.py
  - domains/_parked/customer_coupons_mgmt_service.py

All coupon business logic lives here. Routers (in modules/) must not query
the ORM directly — they call these service functions.
"""
from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.catalog.models.promotions import Coupon
from domains.governance.models.admin import CouponUsage
from domains.catalog.models.products import Product
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
from kernel.money import round_money, to_decimal
import structlog

logger = structlog.get_logger(__name__)

# Field aliases for backward compatibility with different payload formats
_FIELD_ALIASES = {
    "value": "discount_value",
    "min_order": "minimum_order",
    "max_uses": "usage_limit",
    "min_order_amount": "minimum_order",
}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_coupon_code(code: str) -> str:
    return (code or "").strip().upper()


def _to_decimal(value: object, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return Decimal(default)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _to_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _normalize_discount_type(value: object) -> Optional[str]:
    return {
        "percent": "percent",
        "percentage": "percent",
        "fixed": "fixed",
        "fixed_amount": "fixed",
        "amount": "fixed",
    }.get(str(value or "").strip().lower())


def _normalize_fields(fields: dict) -> dict:
    """Map legacy field names to canonical Coupon attributes."""
    data: dict[str, Any] = {}
    for key, value in fields.items():
        mapped = _FIELD_ALIASES.get(key, key)
        if hasattr(Coupon, mapped):
            data[mapped] = value
    return data


def _get_coupon_by_code(db: Session, code: str) -> Coupon:
    """Fetch active coupon by code or raise 404."""
    coupon = db.query(Coupon).filter(
        Coupon.code == _normalize_coupon_code(code),
        Coupon.is_active.is_(True),
    ).first()
    if not coupon:
        logger.info("Coupon code %s not found or inactive", code)
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    return coupon


def _validate_coupon_for_total(coupon: Coupon, order_total: Decimal) -> None:
    """Raise if coupon is expired, exhausted, or below minimum order."""
    if coupon.expires_at and coupon.expires_at < utcnow():
        raise HTTPException(status_code=410, detail="Coupon has expired")
    # Support both old (max_uses/uses_count) and new (usage_limit/usage_count) field names
    usage_limit = getattr(coupon, "usage_limit", None) or getattr(coupon, "max_uses", None)
    usage_count = getattr(coupon, "usage_count", None) or getattr(coupon, "uses_count", 0)
    if usage_limit is not None and (usage_count or 0) >= usage_limit:
        raise HTTPException(status_code=410, detail="Coupon has reached max uses")
    minimum_order = getattr(coupon, "minimum_order", None) or getattr(coupon, "min_order", 0)
    if order_total < to_decimal(minimum_order):
        raise HTTPException(
            status_code=422,
            detail=f"Minimum order for this coupon is {minimum_order} AED",
        )


def _calculate_discount(coupon: Coupon, order_total: Decimal) -> Decimal:
    """Compute discount amount from coupon type."""
    discount_value = getattr(coupon, "discount_value", None) or getattr(coupon, "value", 0)
    if coupon.discount_type == "percent":
        raw = round_money(order_total * to_decimal(discount_value) / Decimal("100"))
        maximum = getattr(coupon, "maximum_discount", None)
        return min(raw, to_decimal(maximum)) if maximum is not None else raw
    return round_money(min(to_decimal(discount_value), order_total))


def _calculate_total_from_items(items: List[Any], db: Session) -> Decimal:
    """Compute order subtotal from line items."""
    if not items:
        raise HTTPException(status_code=422, detail="Order must include at least one item")
    product_ids = {item.product_id for item in items}
    products = {
        product.id: product
        for product in db.query(Product).filter(
            Product.id.in_(product_ids),
            Product.is_deleted.is_(False),
        ).all()
    }
    subtotal = Decimal("0.00")
    for item in items:
        product = products.get(item.product_id)
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        price = getattr(product, "price", None)
        if price is None:
            raise HTTPException(status_code=422, detail=f"Product {item.product_id} has no price")
        subtotal += to_decimal(price) * item.quantity
    return round_money(subtotal)


def _delete_coupon_record(coupon: Coupon, current_user: dict, db: Session) -> dict:
    """Delete coupon after checking no usage records exist."""
    usage_count = db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).count()
    if usage_count:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} usage record(s). Archive or disable it instead of deleting.",
        )
    coupon_id = coupon.id
    coupon_code = coupon.code
    try:
        db.delete(coupon)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Coupon is still referenced by other records.",
        ) from None
    audit_log(
        db,
        action=AuditAction.COUPON_DELETED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="coupon",
        resource_id=coupon_id,
        details={"code": coupon_code},
    )
    return {"detail": "Coupon deleted"}


# ---------------------------------------------------------------------------
# Read operations
# ---------------------------------------------------------------------------

def get_coupon_by_code_active(db: Session, code: str) -> Optional[Coupon]:
    """Return the active, non-deleted coupon for ``code``."""
    normalized = _normalize_coupon_code(code)
    return (
        db.query(Coupon)
        .filter(Coupon.code == normalized, Coupon.is_active.is_(True), Coupon.is_deleted.is_(False))
        .first()
    )


def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.id == coupon_id).first()


def get_coupon_usage_count(db: Session, coupon_id: int) -> int:
    return int(
        db.query(func.count(CouponUsage.id))
        .filter(CouponUsage.coupon_id == coupon_id)
        .scalar()
        or 0
    )


def list_coupons(
    db: Session,
    limit: int = SAFE_QUERY_LIMIT,
    cursor: Optional[int] = None,
) -> List[Coupon]:
    """Keyset (cursor) pagination over active, non-deleted coupons."""
    query = db.query(Coupon).filter(Coupon.is_deleted.is_(False))
    if cursor is not None:
        query = query.filter(Coupon.id < int(cursor))
    return query.order_by(Coupon.id.desc()).limit(min(max(1, limit), SAFE_QUERY_LIMIT)).all()


def list_coupons_paginated(db: Session, cursor: int | None = None, page_size: int = 20) -> dict:
    """Keyset pagination returning ``{data, next_cursor, total, page_size}``."""
    total = db.query(Coupon).filter(Coupon.is_deleted.is_(False)).count()
    query = db.query(Coupon).filter(Coupon.is_deleted.is_(False))
    if cursor is not None:
        query = query.filter(Coupon.id < int(cursor))
    coupons = query.order_by(Coupon.id.desc()).limit(min(max(1, page_size), 100)).all()
    next_cursor = coupons[-1].id if coupons else None
    return {"data": coupons, "next_cursor": next_cursor, "total": total, "page_size": page_size}


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def build_coupon_quote(code: str, order_total: Decimal, db: Session) -> dict:
    """Return discount breakdown for a coupon code + order total."""
    normalized_total = round_money(order_total)
    coupon = _get_coupon_by_code(db, code)
    _validate_coupon_for_total(coupon, normalized_total)
    discount = _calculate_discount(coupon, normalized_total)
    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount,
        "new_total": round_money(normalized_total - discount),
    }


def validate_coupon_code(db: Session, code: str, order_total: object) -> dict:
    """Validate a coupon code against an order total. Returns discount breakdown."""
    code = str(code or "").strip()
    if not code or order_total is None:
        raise HTTPException(status_code=422, detail="code and order_total are required")
    coupon = db.query(Coupon).filter(Coupon.code == code, Coupon.is_active.is_(True)).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")
    now = utcnow()
    total = _to_decimal(order_total)
    minimum_order_raw = getattr(coupon, "minimum_order", None) or getattr(coupon, "min_order", 0)
    minimum_order = _to_decimal(minimum_order_raw)
    usage_limit = getattr(coupon, "usage_limit", None) or getattr(coupon, "max_uses", None)
    usage_count = getattr(coupon, "usage_count", None) or getattr(coupon, "uses_count", 0)
    discount_value_raw = getattr(coupon, "discount_value", None) or getattr(coupon, "value", 0)
    if coupon.starts_at and coupon.starts_at > now:
        raise HTTPException(status_code=400, detail="Coupon not active yet")
    if coupon.expires_at and coupon.expires_at < now:
        raise HTTPException(status_code=400, detail="Coupon expired")
    if usage_limit is not None and _to_int(usage_count) >= _to_int(usage_limit):
        raise HTTPException(status_code=400, detail="Usage limit reached")
    if total < minimum_order:
        raise HTTPException(status_code=422, detail=f"Minimum order {minimum_order}")
    discount_type = str(coupon.discount_type or "").lower()
    discount = (
        total * _to_decimal(discount_value_raw) / Decimal("100")
        if discount_type in {"percent", "percentage"}
        else _to_decimal(discount_value_raw)
    )
    if coupon.maximum_discount is not None:
        discount = min(discount, _to_decimal(coupon.maximum_discount))
    new_total = max(Decimal("0"), total - discount)
    return {
        "valid": True,
        "discount_amount": float(discount),
        "new_total": float(new_total),
        "coupon": coupon,
    }


# ---------------------------------------------------------------------------
# Write operations
# ---------------------------------------------------------------------------

def create_coupon(db: Session, **fields) -> Coupon:
    """Create a coupon from keyword arguments (supports legacy field names)."""
    coupon = Coupon(**_normalize_fields(fields))
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def create_coupon_from_payload(db: Session, payload: dict) -> Coupon:
    """Create a coupon from a dict payload (e.g. API request body)."""
    payload = payload or {}
    code = str(payload.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail="Coupon code is required")
    if db.query(Coupon).filter(Coupon.code == code).first() is not None:
        raise HTTPException(status_code=409, detail="Coupon already exists")
    discount_type = _normalize_discount_type(payload.get("discount_type") or "percent")
    if discount_type is None:
        raise HTTPException(status_code=422, detail="discount_type must be one of: percent, fixed")
    discount_value = _to_decimal(payload.get("discount_value", payload.get("value")))
    minimum_order = _to_decimal(payload.get("minimum_order", payload.get("min_order", payload.get("min_order_amount", 0))))
    usage_limit_raw = payload.get("usage_limit", payload.get("max_uses"))
    usage_limit = None
    if usage_limit_raw not in (None, "", "none", "null", "nan"):
        usage_limit = _to_int(usage_limit_raw)
    coupon = Coupon(
        code=code,
        title=payload.get("title"),
        description=payload.get("description"),
        discount_type=discount_type,
        value=discount_value,
        discount_value=discount_value,
        maximum_discount=payload.get("maximum_discount"),
        min_order=minimum_order,
        minimum_order=minimum_order,
        max_uses=usage_limit,
        usage_limit=usage_limit,
        per_user_limit=payload.get("per_user_limit"),
        applicable_to=payload.get("applicable_to"),
        is_active=bool(payload.get("is_active", True)),
        starts_at=payload.get("starts_at"),
        expires_at=payload.get("expires_at"),
    )
    coupon.discount_type = _normalize_discount_type(coupon.discount_type) or "percent"
    db.add(coupon)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        normalized = _normalize_discount_type(coupon.discount_type)
        if normalized is None:
            raise exc
        coupon.discount_type = normalized
        db.add(coupon)
        db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    """Apply updates to an existing coupon."""
    for key, value in updates.items():
        if hasattr(coupon, key):
            setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    """Delete a coupon (no usage check — use delete_coupon_safe for that)."""
    db.delete(coupon)
    db.commit()


def delete_coupon_by_id(db: Session, coupon_id: str) -> dict:
    """Delete coupon by id or code, checking for usage history."""
    clause = Coupon.code == coupon_id
    if str(coupon_id).isdigit():
        clause = clause | (Coupon.id == int(coupon_id))
    coupon = db.query(Coupon).filter(clause).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).first() is not None:
        raise HTTPException(status_code=409, detail="Archive or disable it instead of deleting a coupon with usage history")
    db.delete(coupon)
    db.commit()
    return {"message": "Deleted"}


# ---------------------------------------------------------------------------
# Admin operations (require admin role)
# ---------------------------------------------------------------------------

def list_coupons_admin(current_user: dict, db: Session) -> List[Coupon]:
    """List all coupons (admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


def create_coupon_admin(
    code: str,
    discount_type: str,
    value: Decimal,
    min_order: Decimal,
    max_uses: Optional[int],
    is_active: bool,
    current_user: dict,
    db: Session,
) -> Coupon:
    """Create coupon (admin only, with audit log)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    code = code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    if discount_type not in ("percent", "fixed"):
        raise HTTPException(status_code=422, detail="discount_type must be 'percent' or 'fixed'")
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        value=round_money(value),
        min_order=round_money(min_order),
        max_uses=max_uses,
        is_active=True,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    audit_log(
        db,
        action=AuditAction.COUPON_CREATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="coupon",
        resource_id=coupon.id,
        details={"code": coupon.code, "discount_type": coupon.discount_type},
    )
    return coupon


def delete_coupon_admin(coupon_id: int, current_user: dict, db: Session) -> dict:
    """Delete coupon by ID (admin only, with usage check + audit log)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return _delete_coupon_record(coupon, current_user, db)


def delete_coupon_by_code_admin(code: str, current_user: dict, db: Session) -> dict:
    """Delete coupon by code (admin only, with usage check + audit log)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    coupon = db.query(Coupon).filter(Coupon.code == code.upper()).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return _delete_coupon_record(coupon, current_user, db)
