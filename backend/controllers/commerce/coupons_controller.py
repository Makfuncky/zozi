"""
Coupons Controller â€” coupon validation and admin CRUD logic.
"""
import logging
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from utils.audit_log import audit_log, AuditAction
from models import Coupon, CouponUsage, Product
from db.schemas import CouponValidate, OrderItemBase
from utils.datetime_utils import utcnow
from utils.money import round_money, to_decimal
from services.write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
    rollback_only,
)



def _normalize_coupon_code(code: str) -> str:
    return code.strip().upper()


def _get_coupon_by_code(code: str, db: Session) -> Coupon:
    coupon = db.query(Coupon).filter(
        Coupon.code == _normalize_coupon_code(code),
        Coupon.is_active.is_(True),
    ).first()
    if not coupon:
        logger.info("Coupon code %s not found or inactive", code)
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    return coupon


def _validate_coupon_for_total(coupon: Coupon, order_total: Decimal) -> None:
    if coupon.expires_at and coupon.expires_at < utcnow():
        raise HTTPException(status_code=410, detail="Coupon has expired")
    if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
        raise HTTPException(status_code=410, detail="Coupon has reached max uses")
    if order_total < to_decimal(coupon.min_order):
        raise HTTPException(
            status_code=422,
            detail=f"Minimum order for this coupon is {coupon.min_order} AED",
        )


def _calculate_discount(coupon: Coupon, order_total: Decimal) -> Decimal:
    if coupon.discount_type == "percent":
        return round_money(order_total * to_decimal(coupon.value) / Decimal("100"))
    return round_money(min(to_decimal(coupon.value), order_total))


def _calculate_total_from_items(items: List[OrderItemBase], db: Session) -> Decimal:
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
        subtotal += to_decimal(product.price) * item.quantity

    return round_money(subtotal)


def build_coupon_quote(code: str, order_total: Decimal, db: Session) -> dict:
    normalized_total = round_money(order_total)
    coupon = _get_coupon_by_code(code, db)
    _validate_coupon_for_total(coupon, normalized_total)
    discount = _calculate_discount(coupon, normalized_total)
    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.value,
        "discount_amount": discount,
        "new_total": round_money(normalized_total - discount),
    }


def validate_coupon(body: CouponValidate, current_user: dict, db: Session) -> dict:
    order_total = (
        _calculate_total_from_items(body.items, db)
        if body.items
        else body.order_total
    )
    if order_total is None:
        raise HTTPException(status_code=422, detail="order_total or items is required")
    return build_coupon_quote(body.code, order_total, db)


def list_coupons(current_user: dict, db: Session) -> List[Coupon]:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return db.query(Coupon).order_by(Coupon.created_at.desc()).all()


def create_coupon(
    code: str,
    discount_type: str,
    value: Decimal,
    min_order: Decimal,
    max_uses: Optional[int],
    is_active: bool,
    current_user: dict,
    db: Session,
) -> Coupon:
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
    add_and_flush(db, coupon)
    commit_and_refresh(db, coupon)
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


def _delete_coupon_record(coupon: Coupon, current_user: dict, db: Session) -> dict:
    usage_count = db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).count()
    if usage_count:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} usage record(s). Archive or disable it instead of deleting.",
        )

    coupon_id = coupon.id
    coupon_code = coupon.code
    try:
        delete_only(db, coupon)
        commit_only(db)
    except IntegrityError:
        rollback_only(db)
        raise HTTPException(
            status_code=409,
            detail="Coupon is still referenced by other records. Archive or disable it instead of deleting.",
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


def delete_coupon(coupon_id: int, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return _delete_coupon_record(coupon, current_user, db)


def delete_coupon_by_code(code: str, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    coupon = db.query(Coupon).filter(Coupon.code == code.upper()).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return _delete_coupon_record(coupon, current_user, db)



