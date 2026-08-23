"""
Catalog — Pricing sub-domain: Product Discount Service.

Handles product-level discount pricing rules, including:
- Time-limited price overrides (discount_starts_at / discount_ends_at)
- Percentage and fixed-amount discount types
- Bulk discount application across product catalogs
- Discount scheduling and expiry
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from kernel.money import round_money, to_decimal

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_discount_active(product: Product) -> bool:
    """Check if a product currently has an active discount."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    starts_at = getattr(product, "discount_starts_at", None)
    ends_at = getattr(product, "discount_ends_at", None)
    if starts_at and starts_at > now:
        return False
    if ends_at and ends_at < now:
        return False
    return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_effective_price(product: Product) -> Decimal:
    """Return the effective price of a product, applying any active discount."""
    base_price = to_decimal(getattr(product, "price", 0))
    if not _is_discount_active(product):
        return base_price
    discount_pct = getattr(product, "discount_pct", None)
    discount_value = getattr(product, "discount_value", None)
    if discount_pct is not None and discount_pct > 0:
        discount = round_money(base_price * to_decimal(discount_pct) / Decimal("100"))
        return round_money(base_price - discount)
    if discount_value is not None and discount_value > 0:
        return round_money(base_price - to_decimal(discount_value))
    return base_price


def set_product_discount(
    db: Session,
    product_id: int,
    discount_pct: Optional[float] = None,
    discount_value: Optional[float] = None,
    starts_at: Optional[datetime] = None,
    ends_at: Optional[datetime] = None,
) -> Product:
    """Set a discount on a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if discount_pct is not None:
        if discount_pct < 0 or discount_pct > 100:
            raise HTTPException(status_code=422, detail="discount_pct must be between 0 and 100")
        setattr(product, "discount_pct", discount_pct)
    if discount_value is not None:
        if discount_value < 0:
            raise HTTPException(status_code=422, detail="discount_value must be positive")
        setattr(product, "discount_value", discount_value)
    if starts_at is not None:
        setattr(product, "discount_starts_at", starts_at)
    if ends_at is not None:
        setattr(product, "discount_ends_at", ends_at)
    db.commit()
    db.refresh(product)
    return product


def remove_product_discount(db: Session, product_id: int) -> Product:
    """Remove discount from a product."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    setattr(product, "discount_pct", None)
    setattr(product, "discount_value", None)
    setattr(product, "discount_starts_at", None)
    setattr(product, "discount_ends_at", None)
    db.commit()
    db.refresh(product)
    return product


def is_product_discounted(product: Product) -> bool:
    """Check if product has an active discount."""
    if not _is_discount_active(product):
        return False
    discount_pct = getattr(product, "discount_pct", None)
    discount_value = getattr(product, "discount_value", None)
    return (discount_pct is not None and discount_pct > 0) or (discount_value is not None and discount_value > 0)
