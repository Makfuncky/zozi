"""
Automatic service for export_read_service - DB read operations delegated from controllers.
"""

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from data.models import *
from data.services_write_helpers import add_and_flush, commit_only

def list_user(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.offset(skip).limit(limit).all()


def list_order(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.offset(skip).limit(limit).all()


def list_product(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.offset(skip).limit(limit).all()


def list_coupon(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.offset(skip).limit(limit).all()


def get_auditlog_first(db: Session, **filters) -> Optional[AuditLog]:
    query = db.query(AuditLog)
    for key, value in filters.items():
        query = query.filter(getattr(AuditLog, key) == value)
    return query.limit(1).first()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    """Generic scalar query factory for exported models."""
    model = Unknown  # registered at runtime via data.models
    query = db.query(getattr(model, column))
    for key, value in filters.items():
        query = query.filter(getattr(model, key) == value)
    return query.scalar()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def get_coupon_first(db: Session, **filters) -> Optional[Coupon]:
    query = db.query(Coupon)
    for key, value in filters.items():
        query = query.filter(getattr(Coupon, key) == value)
    return query.limit(1).first()

def count_user(db: Session) -> int:
    """Count total users — delegated from controller."""
    return db.query(func.count(User.id)).scalar() or 0


def count_order(db: Session) -> int:
    """Count total orders — delegated from controller."""
    return db.query(func.count(Order.id)).scalar() or 0


def count_product(db: Session) -> int:
    """Count total products — delegated from controller."""
    return db.query(func.count(Product.id)).scalar() or 0


def count_coupon(db: Session) -> int:
    """Count total coupons — delegated from controller."""
    return db.query(func.count(Coupon.id)).scalar() or 0


def count_auditlog_since(db: Session, since: Any) -> int:
    """Count audit logs since a given timestamp — delegated from controller."""
    return db.query(func.count(AuditLog.id)).filter(AuditLog.occurred_at >= since).scalar() or 0


def _db_user_all_0(db: Session) -> Optional[Any]:
    result = db.query(User).order_by(User.id).limit(MAX_EXPORT_ROWS).all()
    """Read-only query delegated from controller."""
    return result

def _db_order_all_1(db: Session) -> Optional[Any]:
    result = db.query(Order).order_by(Order.id).limit(MAX_EXPORT_ROWS).all()
    """Read-only query delegated from controller."""
    return result

def _db_product_all_2(db: Session) -> Optional[Any]:
    result = db.query(Product).order_by(Product.id).limit(MAX_EXPORT_ROWS).all()
    """Read-only query delegated from controller."""
    return result

def _db_coupon_all_3(db: Session) -> Optional[Any]:
    result = db.query(Coupon).order_by(Coupon.id).limit(MAX_EXPORT_ROWS).all()
    """Read-only query delegated from controller."""
    return result

def _db_auditlog_query_4(db: Session) -> Optional[Any]:
    """Read-only query delegated from controller."""
    return db.query(AuditLog)

def _db_user_query_5(db: Session) -> Optional[Any]:
    result = db.query(User).order_by(User.id)
    """Read-only query delegated from controller."""
    return result

def _db_order_query_6(db: Session) -> Optional[Any]:
    result = db.query(Order).order_by(Order.id)
    """Read-only query delegated from controller."""
    return result

def _db_product_query_7(db: Session) -> Optional[Any]:
    result = db.query(Product).order_by(Product.id)
    """Read-only query delegated from controller."""
    return result

def _db_coupon_query_8(db: Session) -> Optional[Any]:
    result = db.query(Coupon).order_by(Coupon.id)
    """Read-only query delegated from controller."""
    return result

def _db_auditlog_query_9(db: Session, occurred_at: Any, since: Any) -> Optional[Any]:
    result = db.query(AuditLog).filter(AuditLog.occurred_at >= since).order_by(AuditLog.id)
    """Read-only query delegated from controller."""
    return result
