"""Coupon write service (SERVICES layer).

Owns all mutating database access for ``coupons``. Routers and controllers
must not call ``db.add`` / ``db.delete`` / ``db.commit`` directly for coupon
writes. Kept free of controller imports to avoid circular imports.

Field names match the live ``Coupon`` model (``models.payments.Coupon``):
``discount_value``, ``minimum_order``, ``usage_limit`` — there is no
``value`` / ``min_order`` / ``max_uses`` / ``title`` / ``description`` column.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from data.models import Coupon
import structlog
logger = structlog.get_logger(__name__)


def create_coupon(
    db: Session,
    *,
    code: str,
    discount_type: str,
    discount_value: Decimal,
    minimum_order: Decimal = Decimal("0"),
    usage_limit: Optional[int] = None,
    is_active: bool = True,
    maximum_discount: Optional[Decimal] = None,
    starts_at: Optional[object] = None,
    expires_at: Optional[object] = None,
) -> Coupon:
    coupon = Coupon(
        code=str(code).strip().upper(),
        discount_type=discount_type,
        discount_value=discount_value,
        minimum_order=minimum_order,
        maximum_discount=maximum_discount,
        usage_limit=usage_limit,
        is_active=is_active,
        starts_at=starts_at,
        expires_at=expires_at,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        if hasattr(coupon, key):
            setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon
