"""
Coupon Service — coupon validation and quote logic (shared across controllers).

Extracted from controllers/coupons_controller.py to break the
services -> controllers / controller -> controller forbidden dependency
edges (W4). Consumers should import from this module instead of importing
coupon helpers from another controller.
"""
import logging
from decimal import Decimal
from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import Coupon, Product
from db.schemas import OrderItemBase
from utils.datetime_utils import utcnow
from utils.money import round_money, to_decimal

logger = logging.getLogger(__name__)


def normalize_coupon_code(code: str) -> str:
    return code.strip().upper()


def get_coupon_by_code(code: str, db: Session) -> Coupon:
    coupon = db.query(Coupon).filter(
        Coupon.code == normalize_coupon_code(code),
        Coupon.is_active.is_(True),
    ).first()
    if not coupon:
        logger.info("Coupon code %s not found or inactive", code)
        raise HTTPException(status_code=404, detail="Invalid coupon code")
    return coupon


def validate_coupon_for_total(coupon: Coupon, order_total: Decimal) -> None:
    if coupon.expires_at and coupon.expires_at < utcnow():
        raise HTTPException(status_code=410, detail="Coupon has expired")
    if coupon.max_uses and coupon.uses_count >= coupon.max_uses:
        raise HTTPException(status_code=410, detail="Coupon has reached max uses")
    if order_total < to_decimal(coupon.min_order):
        raise HTTPException(
            status_code=422,
            detail=f"Minimum order for this coupon is {coupon.min_order} AED",
        )


def calculate_discount(coupon: Coupon, order_total: Decimal) -> Decimal:
    if coupon.discount_type == "percent":
        return round_money(order_total * to_decimal(coupon.value) / Decimal("100"))
    return round_money(min(to_decimal(coupon.value), order_total))


def calculate_total_from_items(items: List[OrderItemBase], db: Session) -> Decimal:
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
    coupon = get_coupon_by_code(code, db)
    validate_coupon_for_total(coupon, normalized_total)
    discount = calculate_discount(coupon, normalized_total)
    return {
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.value,
        "discount_amount": discount,
        "new_total": round_money(normalized_total - discount),
    }
