"""Supplier tier / badge system service."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile, SupplierBadge

logger = logging.getLogger(__name__)

# Tier thresholds — suppliers are evaluated against these to determine tier.
TIER_THRESHOLDS = {
    "platinum": {"min_orders": 500, "min_credibility": 90, "min_fulfillment_rate": 95},
    "gold": {"min_orders": 200, "min_credibility": 75, "min_fulfillment_rate": 90},
    "silver": {"min_orders": 50, "min_credibility": 50, "min_fulfillment_rate": 80},
    "bronze": {"min_orders": 0, "min_credibility": 0, "min_fulfillment_rate": 0},
}

TIER_ORDER = ["platinum", "gold", "silver", "bronze"]


def get_tier(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return the current tier for a supplier based on active badges."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    active_badges = db.query(SupplierBadge).filter(
        SupplierBadge.supplier_id == supplier_id,
        SupplierBadge.status == "active",
    ).all()

    current_tier = "bronze"
    for badge in active_badges:
        badge_level = (badge.badge_level or "bronze").lower()
        if badge_level in TIER_ORDER:
            tier_idx = TIER_ORDER.index(badge_level)
            current_idx = TIER_ORDER.index(current_tier)
            if tier_idx < current_idx:
                current_tier = badge_level

    return {
        "supplier_id": supplier_id,
        "tier": current_tier,
        "active_badges": len(active_badges),
        "credibility_score": float(supplier.credibility_score or 0),
        "checked_at": now.isoformat(),
    }


def evaluate_tier(supplier_id: int, db: Session) -> dict[str, Any]:
    """Evaluate and return the appropriate tier for a supplier based on metrics.

    Compares supplier performance against tier thresholds and returns
    the highest tier the supplier qualifies for.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    from domains.orders.ports import Order, OrderItem

    total_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier_id,
        Order.status.in_(["completed", "delivered"]),
    ).scalar() or 0

    credibility = float(supplier.credibility_score or 0)

    all_orders = db.query(func.count(func.distinct(Order.id))).join(OrderItem).filter(
        OrderItem.supplier_id == supplier_id,
    ).scalar() or 0

    fulfillment_rate = (total_orders / all_orders * 100) if all_orders > 0 else 0.0

    evaluated_tier = "bronze"
    for tier_name in TIER_ORDER:
        thresholds = TIER_THRESHOLDS[tier_name]
        if (
            total_orders >= thresholds["min_orders"]
            and credibility >= thresholds["min_credibility"]
            and fulfillment_rate >= thresholds["min_fulfillment_rate"]
        ):
            evaluated_tier = tier_name
            break

    return {
        "supplier_id": supplier_id,
        "tier": evaluated_tier,
        "metrics": {
            "total_orders": total_orders,
            "credibility_score": credibility,
            "fulfillment_rate": round(fulfillment_rate, 2),
        },
        "thresholds_met": {
            tier: (
                total_orders >= TIER_THRESHOLDS[tier]["min_orders"]
                and credibility >= TIER_THRESHOLDS[tier]["min_credibility"]
                and fulfillment_rate >= TIER_THRESHOLDS[tier]["min_fulfillment_rate"]
            )
            for tier in TIER_ORDER
        },
        "evaluated_at": now.isoformat(),
    }
