"""Read/query helpers for admin data exports.

Cross-cutting export query infrastructure (infrastructure/utils/). Provides the
capped query builders that domain export services and ports rely on. Lives in
infrastructure because the export read surface spans multiple domains
(catalog products, orders, payments coupons, audit logs, users).
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


def list_user(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).all()


def list_order(db: Session) -> list[Order]:
    return db.query(Order).order_by(Order.id).all()


def list_product(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.id).all()


def list_coupon(db: Session) -> list[Coupon]:
    return db.query(Coupon).order_by(Coupon.id).all()


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
