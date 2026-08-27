"""Canonical export read helpers — moved from infrastructure/utils/export_read.py.

This module provides capped query builders for domain export services.
Lives in governance domain because it imports governance, catalog, and orders models.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.governance.models.core import AuditLog
from domains.governance.models.user import User
from domains.catalog.models.products import Product
from domains.orders.models.orders import Order
from domains.catalog.models.promotions import Coupon

MAX_EXPORT_ROWS: int = 5000
DEFAULT_PAGE_SIZE: int = 50
MAX_PAGE_SIZE: int = 100


def _clamp_limit(limit: int | None) -> int:
    """Clamp limit to safe bounds (default 50, max 100 for list endpoints)."""
    if limit is None:
        return DEFAULT_PAGE_SIZE
    return min(max(1, limit), MAX_PAGE_SIZE)


def _clamp_export_limit(limit: int | None) -> int:
    """Clamp limit to safe bounds for exports (default 50000, max 5000)."""
    if limit is None:
        return MAX_EXPORT_ROWS
    return min(max(1, limit), MAX_EXPORT_ROWS)


def list_user(db: Session, limit: int | None = None) -> list[User]:
    """List users with cursor-safe limit clamping."""
    limit = _clamp_export_limit(limit)
    return db.query(User).order_by(User.id).limit(limit).all()


def list_order(db: Session, limit: int | None = None) -> list[Order]:
    """List orders with cursor-safe limit clamping."""
    limit = _clamp_export_limit(limit)
    return db.query(Order).order_by(Order.id).limit(limit).all()


def list_product(db: Session, limit: int | None = None) -> list[Product]:
    """List products with cursor-safe limit clamping."""
    limit = _clamp_export_limit(limit)
    return db.query(Product).order_by(Product.id).limit(limit).all()


def list_coupon(db: Session, limit: int | None = None) -> list[Coupon]:
    """List coupons with cursor-safe limit clamping."""
    limit = _clamp_export_limit(limit)
    return db.query(Coupon).order_by(Coupon.id).limit(limit).all()


def list_user_page(db: Session, limit: int | None = None) -> list[User]:
    """List users with keyset pagination (default 50, max 100)."""
    from infrastructure.utils.pagination import cursor_paginate_asc
    limit = _clamp_limit(limit)
    page = cursor_paginate_asc(db.query(User).order_by(User.id), page_size=limit)
    return page.items


def list_order_page(db: Session, limit: int | None = None) -> list[Order]:
    """List orders with keyset pagination (default 50, max 100)."""
    from infrastructure.utils.pagination import cursor_paginate_asc
    limit = _clamp_limit(limit)
    page = cursor_paginate_asc(db.query(Order).order_by(Order.id), page_size=limit)
    return page.items


def list_product_page(db: Session, limit: int | None = None) -> list[Product]:
    """List products with keyset pagination (default 50, max 100)."""
    from infrastructure.utils.pagination import cursor_paginate_asc
    limit = _clamp_limit(limit)
    page = cursor_paginate_asc(db.query(Product).order_by(Product.id), page_size=limit)
    return page.items


def list_coupon_page(db: Session, limit: int | None = None) -> list[Coupon]:
    """List coupons with keyset pagination (default 50, max 100)."""
    from infrastructure.utils.pagination import cursor_paginate_asc
    limit = _clamp_limit(limit)
    page = cursor_paginate_asc(db.query(Coupon).order_by(Coupon.id), page_size=limit)
    return page.items


def get_user_first(db: Session) -> User | None:
    return db.query(User).order_by(User.id).first()


def count_user(db: Session) -> int:
    return db.query(func.count(User.id)).scalar() or 0


def count_order(db: Session) -> int:
    return db.query(func.count(Order.id)).scalar() or 0


def count_product(db: Session) -> int:
    return db.query(func.count(Product.id)).scalar() or 0


def count_coupon(db: Session) -> int:
    return db.query(func.count(Coupon.id)).scalar() or 0


def db_user_all_0(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).limit(MAX_EXPORT_ROWS).all()


def db_order_all_1(db: Session) -> list[Order]:
    return db.query(Order).order_by(Order.id).limit(MAX_EXPORT_ROWS).all()


def db_product_all_2(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.id).limit(MAX_EXPORT_ROWS).all()


def db_coupon_all_3(db: Session) -> list[Coupon]:
    return db.query(Coupon).order_by(Coupon.id).limit(MAX_EXPORT_ROWS).all()


def db_auditlog_query_4(db: Session) -> Any:
    return db.query(AuditLog).order_by(AuditLog.id)


def db_user_query_5(db: Session) -> Any:
    return db.query(User)
