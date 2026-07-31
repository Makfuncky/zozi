"""Coupons write service — DB write operations for coupons."""

from sqlalchemy.orm import Session

from models import Coupon, CouponUsage


def create_coupon(db: Session, **coupon_data) -> Coupon:
    coupon = Coupon(**coupon_data)
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


def update_coupon(db: Session, coupon: Coupon, updates: dict) -> Coupon:
    for key, value in updates.items():
        setattr(coupon, key, value)
    db.commit()
    db.refresh(coupon)
    return coupon


def delete_coupon(db: Session, coupon: Coupon) -> None:
    db.delete(coupon)
    db.commit()


def get_coupon_usage_count(db: Session, coupon_id: int) -> int:
    return db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon_id).count()