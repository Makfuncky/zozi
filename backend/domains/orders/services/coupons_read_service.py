"""Coupon read service (SERVICES layer).

Owns all read access for ``coupons``. Routers and controllers must not query
the ORM directly for coupon reads. Pagination uses keyset (cursor) semantics
over a stable ``id DESC`` sort so concurrent inserts never cause the drift
that skip-based pagination suffers from.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.governance.models.admin import CouponUsage
from domains.payments.models.payments import Coupon
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation):
        return Decimal("0")


def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def get_coupon_by_code_active(db: Session, code: str) -> Optional[Coupon]:
    """Return the active coupon for ``code`` (case-insensitive, trimmed)."""
    normalized = (code or "").strip().upper()
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
    """Keyset (cursor) pagination over active, non-deleted coupons.

    ``cursor`` is the ``id`` of the last coupon the caller saw; the next page
    returns coupons with a strictly smaller ``id`` under a stable ``id DESC``
    sort. This avoids position-based scanning and the drift it causes when rows
    are inserted concurrently.
    """
    query = db.query(Coupon).filter(Coupon.is_deleted.is_(False))
    if cursor is not None:
        query = query.filter(Coupon.id < int(cursor))
    return query.order_by(Coupon.id.desc()).limit(min(max(1, limit), SAFE_QUERY_LIMIT)).all()


def list_coupons_paginated(db: Session, page: int = 1, page_size: int = 20) -> dict:
    """Page-based list of coupons (router contract: {data, total, page, page_size})."""
    total = db.query(Coupon).count()
    coupons = (
        db.query(Coupon)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {"data": coupons, "total": total, "page": page, "page_size": page_size}


def validate_coupon_code(db: Session, code: str, order_total) -> dict:
    """Validate a coupon code against an order total and return the discount breakdown.

    Behaviour-preserving extraction of the inline ``.post("/validate")`` handler in
    ``routers.public_commerce_validation`` (also fixes a latent bug where ``Decimal``/
    ``_to_decimal``/``_to_int`` were referenced but never imported/defined).
    """
    coupon = (
        db.query(Coupon)
        .filter(Coupon.code == (code or "").strip(), Coupon.is_active == True)
        .first()
    )
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")

    now = utcnow()
    total = _to_decimal(order_total)
    minimum_order_raw = getattr(coupon, "minimum_order", None)
    if minimum_order_raw is None:
        minimum_order_raw = getattr(coupon, "min_order", 0)
    minimum_order = _to_decimal(minimum_order_raw)
    usage_limit = getattr(coupon, "usage_limit", None)
    if usage_limit is None:
        usage_limit = getattr(coupon, "max_uses", None)
    usage_count = getattr(coupon, "usage_count", None)
    if usage_count is None:
        usage_count = getattr(coupon, "uses_count", 0)
    discount_value_raw = getattr(coupon, "discount_value", None)
    if discount_value_raw is None:
        discount_value_raw = getattr(coupon, "value", 0)
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
