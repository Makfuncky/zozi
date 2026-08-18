"""Read/query helpers for admin data exports.

Extracted from ``controllers/core/export_controller.py`` so the read side of
the export feature lives in the services layer (HL502 fix). Previously this
module relied on a wildcard model import and an undefined ``MAX_EXPORT_ROWS``;
imports are now explicit and the dead unknown-scalar helper is gone.

The matching write/stream side remains in the controller; this module only
exposes the query builders the controller (and the regression tests) rely on.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.accounts.models.core import AuditLog
from domains.accounts.models.user import User
from domains.catalog.models.products import Product
from domains.orders.models.orders import Order
from domains.payments.models.payments import Coupon

MAX_EXPORT_ROWS: int = 5000


# ── List helpers ──────────────────────────────────────────────────────────────

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


# ── Count helpers ─────────────────────────────────────────────────────────────

def count_user(db: Session) -> int:
    return db.query(func.count(User.id)).scalar() or 0


def count_order(db: Session) -> int:
    return db.query(func.count(Order.id)).scalar() or 0


def count_product(db: Session) -> int:
    return db.query(func.count(Product.id)).scalar() or 0


def count_coupon(db: Session) -> int:
    return db.query(func.count(Coupon.id)).scalar() or 0


# ── Capped "all" query helpers (materialised, limited to MAX_EXPORT_ROWS) ──────

def db_user_all_0(db: Session) -> list[User]:
    return db.query(User).order_by(User.id).limit(MAX_EXPORT_ROWS).all()


def db_order_all_1(db: Session) -> list[Order]:
    return db.query(Order).order_by(Order.id).limit(MAX_EXPORT_ROWS).all()


def db_product_all_2(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.id).limit(MAX_EXPORT_ROWS).all()


def db_coupon_all_3(db: Session) -> list[Coupon]:
    return db.query(Coupon).order_by(Coupon.id).limit(MAX_EXPORT_ROWS).all()


# ── Raw query builders (return a SQLAlchemy Query, not materialised rows) ─────

def db_auditlog_query_4(db: Session) -> Any:
    return db.query(AuditLog).order_by(AuditLog.id)


def db_user_query_5(db: Session) -> Any:
    return db.query(User)
