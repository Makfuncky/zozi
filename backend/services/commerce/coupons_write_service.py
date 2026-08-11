"""Coupon write operations.

Centralizes coupon persistence so routers/controllers never touch the ORM
session directly. Kept free of controller imports to avoid circular imports.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.payments import Coupon
from models.admin import CouponUsage
import structlog
logger = structlog.get_logger(__name__)


_FIELD_ALIASES = {
    "value": "discount_value",
    "min_order": "minimum_order",
    "max_uses": "usage_limit",
    "min_order_amount": "minimum_order",
}


def _normalize_fields(fields: dict) -> dict:
    data: dict[str, Any] = {}
    for key, value in fields.items():
        mapped = _FIELD_ALIASES.get(key, key)
        if hasattr(Coupon, mapped):
            data[mapped] = value
    return data


def create_coupon(db: Session, **fields) -> Coupon:
    coupon = Coupon(**_normalize_fields(fields))
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        if hasattr(coupon, key):
            setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def get_coupon_usage_count(db: Session, coupon_id: int) -> int:
    return int(db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0)
