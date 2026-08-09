"""
BOGO Promotion Service
======================
Handles Buy-One-Get-One (and Buy-X-Get-Y-Free) promotion types.

Supported types from PROMOTION.md:
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

logger = logging.getLogger(__name__)


# ── Types ────────────────────────────────────────────────────────────────

BOGOConfig = dict[str, any]
"""Structure:
{
    "id": int,
    "title": str,
    "description": str,
    "buy_quantity": int,       # X — how many to buy
    "free_quantity": int,      # Y — how many get free
    "free_discount_pct": int,  # 100 = completely free, 50 = half off
    "apply_to": str,           # "product" | "category" | "all"
    "target_id": Optional[int],  # product_id or category_id
    "max_uses_per_customer": Optional[int],
    "stacking_allowed": bool,
    "is_active": bool,
    "starts_at": Optional[str],
    "ends_at": Optional[str],
}
"""

CartItem = dict[str, any]
"""Structure:
{
    "product_id": int,
    "product_name": str,
    "category_id": Optional[int],
    "quantity": int,
    "unit_price": Decimal,
    "line_total": Decimal,
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════


def find_eligible_bogo_promotions(
    cart_items: list[CartItem],
    db: Session,
) -> list[BOGOConfig]:
    """Find all active BOGO promotions that apply to the given cart items.

    In a full implementation, this would query a ``bogo_promotions`` table.
    For now, returns an empty list as a placeholder since the BOGO table
    has not been created yet.
    """
    # TODO: Query from bogo_promotions table once created
    # active_promos = (
    #     db.query(BOGOPromotion)
    #     .filter(BOGOPromotion.is_active == True)
    #     .all()
    # )
    return []


def calculate_bogo_discount(
    cart_items: list[CartItem],
    promo: BOGOConfig,
) -> dict:
    """Calculate the BOGO discount for the given cart items and promotion.

    Returns the discount details including which item gets the free
    discount and the amount saved.

    Algorithm:
    1. Filter cart items matching the promotion's target (product/category/all)
    2. Count qualifying items (sum of quantities)
    3. If qualifying count < buy_quantity, no discount applies
    4. Determine how many free items can be claimed:
       free_claims = (qualifying_count // buy_quantity) * free_quantity
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

    # Filter matching items
    matching_items = []
    for item in cart_items:
        if apply_to == "product" and item.get("product_id") != target_id:
            continue
        if apply_to == "category" and item.get("category_id") != target_id:
            continue
        matching_items.append(item)

    if not matching_items:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}

    # Total qualifying quantity
    total_qty = sum(item.get("quantity", 0) for item in matching_items)
    if total_qty < buy_qty:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}

    # How many free claims
    free_claims = (total_qty // buy_qty) * free_qty
    if free_claims <= 0:
        return {"discount": Decimal("0.00"), "free_items": 0, "applied": False}

    # Cheapest qualifying item's unit price
    cheapest_price = min(
        Decimal(str(item.get("unit_price", 0)))
        for item in matching_items
    )

    discount = cheapest_price * Decimal(str(free_pct)) / Decimal("100") * Decimal(str(free_claims))

    return {
        "discount": discount.quantize(Decimal("0.01")),
        "free_items": free_claims,
        "cheapest_unit_price": float(cheapest_price),
        "free_discount_pct": free_pct,
        "applied": True,
        "total_qualifying_qty": total_qty,
    }


def validate_bogo_eligibility(
    cart_items: list[CartItem],
    promo: BOGOConfig,
) -> dict:
    """Check if the cart qualifies for the BOGO promotion and return details.

    Returns a dict with ``eligible`` (bool), ``reason`` (str), and
    qualifying item details.
    """
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
        "eligible": True,
        "reason": "",
        "free_items_available": (total_qty // buy_qty) * promo.get("free_quantity", 1),
    }
