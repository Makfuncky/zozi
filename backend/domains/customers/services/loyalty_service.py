"""Loyalty service — tier classification and rewards balance.

Tier is derived from the customer's lifetime order total (read via
``orders.ports`` per Law 3) and stored as a stable, deterministic label. The
rewards balance is computed from the sum of ``ReferralPointEvent`` rows for
the user (read from the customers domain's own model).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.customers.models import ReferralPointEvent
from domains.orders.ports import Order
import structlog

logger = structlog.get_logger(__name__)


_TIER_THRESHOLDS = (
    ("platinum", Decimal("5000")),
    ("gold", Decimal("2000")),
    ("silver", Decimal("500")),
    ("bronze", Decimal("0")),
)


def _classify_tier(lifetime_value: Decimal) -> str:
    for label, threshold in _TIER_THRESHOLDS:
        if lifetime_value >= threshold:
            return label
    return "bronze"


class LoyaltyService:
    """Service facade for loyalty tier + rewards balance."""

    def __init__(self, db: Session):
        self.db = db

    def get_loyalty_tier(self, user_id: int) -> Dict[str, Any]:
        """Return the loyalty tier and the spend that determined it."""
        orders = (
            self.db.query(Order)
            .filter(
                Order.user_id == int(user_id),
                Order.is_deleted.is_(False),
            )
            .all()
        )
        lifetime_value = sum(
            (o.total_amount for o in orders if o.total_amount is not None),
            Decimal("0.00"),
        )
        tier = _classify_tier(lifetime_value)
        next_tier: Dict[str, Any] | None = None
        for label, threshold in _TIER_THRESHOLDS:
            if threshold > lifetime_value:
                next_tier = {
                    "tier": label,
                    "threshold": threshold,
                    "remaining": threshold - lifetime_value,
                }
                break
        return {
            "user_id": int(user_id),
            "tier": tier,
            "lifetime_value": lifetime_value,
            "order_count": len(orders),
            "next_tier": next_tier,
        }

    def get_rewards_balance(self, user_id: int) -> Dict[str, Any]:
        """Return the customer's current points balance from referral events."""
        try:
            events = (
                self.db.query(ReferralPointEvent)
                .filter(
                    ReferralPointEvent.user_id == int(user_id),
                    ReferralPointEvent.is_deleted.is_(False),
                )
                .all()
            )
        except Exception as exc:
            logger.warning(
                "loyalty.rewards_query_failed",
                user_id=user_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load rewards balance.",
            ) from exc
        earned = sum(int(e.points) for e in events if int(e.points) > 0)
        redeemed = -sum(int(e.points) for e in events if int(e.points) < 0)
        return {
            "user_id": int(user_id),
            "balance": earned - redeemed,
            "earned": earned,
            "redeemed": redeemed,
            "event_count": len(events),
        }
