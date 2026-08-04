"""Service methods for coupon read operations."""
from sqlalchemy.orm import Session
from data.models import Coupon, CouponUsage


def get_available_coupons(db: Session, country_code: str) -> list[Coupon]:
    """Get active coupons available for a country."""
    return (
        db.query(Coupon)
        .filter(Coupon.is_active == True, Coupon.country_code == country_code)
        .all()
    )


def get_coupon_by_code(db: Session, code: str) -> Coupon | None:
    """Get a coupon by its code."""
    return db.query(Coupon).filter(Coupon.code == code, Coupon.is_active == True).first()


def get_user_coupon_usage(db: Session, coupon_id: int, user_id: int) -> CouponUsage | None:
    """Check if a user has used a coupon."""
    return (
        db.query(CouponUsage)
        .filter(CouponUsage.coupon_id == coupon_id, CouponUsage.user_id == user_id)
        .first()
    )


def apply_coupon_to_order(db: Session, coupon_id: int, user_id: int, order_id: int) -> CouponUsage:
    """Record coupon usage for an order."""
    usage = CouponUsage(coupon_id=coupon_id, user_id=user_id, order_id=order_id)
    db.add(usage)
    db.commit()
    db.refresh(usage)
    return usage



def count_coupon_usage(db: Session, coupon_id: int) -> int:
    """Count how many times a coupon has been used — delegated from controller."""
    return db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0
