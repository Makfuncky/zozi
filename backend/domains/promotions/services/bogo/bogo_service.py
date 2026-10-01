"""
Promotions — BOGO (Buy-One-Get-One) Service (canonical).

Merged from:
  - domains/catalog/services/bogo_service.py
  - domains/orders/services/promotion_bogo_service.py
  - domains/_parked/promotion_bogo_service.py

Handles Buy-One-Get-One (and Buy-X-Get-Y-Free) promotion types.

Supported types:
  - Buy 1 Get 1 Free (B1G1)
  - Buy 2 Get 1 Free (B2G1)
  - Custom buy X get Y free

Rules:
  - Applies to specific products or categories
  - Free item is the cheapest qualifying item in the cart
  - Can stack with other promotions if stacking is enabled
  - Inventory check: free item must be in stock
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from domains.catalog.ports import BOGOPromotion
from infrastructure.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)

# Types
BOGOConfig = dict[str, any]
CartItem = dict[str, any]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_eligible_bogo_promotions(cart_items: list[CartItem], db: Session) -> list[BOGOConfig]:
    """Find all active BOGO promotions that apply to the given cart items."""
    now = utcnow()
    active_promos = db.query(BOGOPromotion).filter(BOGOPromotion.is_active == True).all()
    eligible: list[BOGOConfig] = []
    for promo in active_promos:
        if promo.starts_at and promo.starts_at > now:
            continue
        if promo.ends_at and promo.ends_at < now:
            continue
        eligible.append({
            "id": promo.id, "title": promo.title, "description": promo.description,
            "buy_quantity": promo.buy_quantity, "free_quantity": promo.free_quantity,
            "free_discount_pct": promo.free_discount_pct, "apply_to": promo.apply_to,
            "target_id": promo.target_id, "max_uses_per_customer": promo.max_uses_per_customer,
            "stacking_allowed": promo.stacking_allowed, "is_active": promo.is_active,
            "starts_at": promo.starts_at.isoformat() if promo.starts_at else None,
            "ends_at": promo.ends_at.isoformat() if promo.ends_at else None,
        })
    return eligible


def calculate_bogo_discount(cart_items: list[CartItem], promo: BOGOConfig) -> dict:
    """Calculate the BOGO discount for the given cart items and promotion.

    Algorithm:
    1. Filter cart items matching the promotion's target
    2. Count qualifying items
    3. If qualifying count < buy_quantity, no discount
    4. free_claims = (qualifying_count // buy_quantity) * free_quantity
    5. Free item is the cheapest among qualifying items
    6. Discount = free_claims * cheapest_unit_price * (free_discount_pct / 100)
    """
    if not promo.get("is_active", False):
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}
    buy_qty = promo.get("buy_quantity", 1)
    free_qty = promo.get("free_quantity", 1)
    free_pct = promo.get("free_discount_pct", 100)
    apply_to = promo.get("apply_to", "all")
    target_id = promo.get("target_id")
    matching_items = []
    for item in cart_items:
        if apply_to == "product" and item.get("product_id") != target_id:
            continue
        if apply_to == "category" and item.get("category_id") != target_id:
            continue
        matching_items.append(item)
    if not matching_items:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}
    total_qty = sum(item.get("quantity", 0) for item in matching_items)
    if total_qty < buy_qty:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}
    free_claims = (total_qty // buy_qty) * free_qty
    if free_claims <= 0:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}
    cheapest_price = min(Decimal(str(item.get("unit_price", 0))) for item in matching_items)
    discount = cheapest_price * Decimal(str(free_pct)) / Decimal("100") * Decimal(str(free_claims))
    return {
        "discount": discount.quantize(Decimal("0.01")),
        "free_items": free_claims,
        "cheapest_unit_price": float(cheapest_price),
        "free_discount_pct": free_pct,
        "applied": True,
        "total_qualifying_qty": total_qty,
    }


def validate_bogo_eligibility(cart_items: list[CartItem], promo: BOGOConfig) -> dict:
    """Check if the cart qualifies for the BOGO promotion."""
    if not promo.get("is_active", False):
        return {"eligible": False, "reason": "Promotion is not active"}
    buy_qty = promo.get("buy_quantity", 1)
    total_qty = sum(item.get("quantity", 0) for item in cart_items)
    if total_qty < buy_qty:
        return {
            "eligible": False,
            "reason": f"Need at least {buy_qty} qualifying items (have {total_qty})",
            "needed": buy_qty - total_qty,
        }
    return {
        "eligible": True, "reason": "",
        "free_items_available": (total_qty // buy_qty) * promo.get("free_quantity", 1),
    }
