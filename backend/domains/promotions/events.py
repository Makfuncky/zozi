"""Promotions domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The promotions domain owns coupon and promotion entities. It publishes events
when promotions are applied or redeemed so downstream domains may react.
"""
from __future__ import annotations

from infrastructure.messaging.events.event_bus import publish

EVENT_COUPON_APPLIED = "promotions.coupon.applied"
EVENT_COUPON_REDEEMED = "promotions.coupon.redeemed"
EVENT_PROMOTION_ACTIVATED = "promotions.promotion.activated"
EVENT_PROMOTION_EXPIRED = "promotions.promotion.expired"


def publish_coupon_applied(coupon_id: int, order_id: int, user_id: int, discount_amount: float) -> None:
    publish(EVENT_COUPON_APPLIED, {
        "coupon_id": coupon_id, "order_id": order_id,
        "user_id": user_id, "discount_amount": discount_amount,
    })


def publish_coupon_redeemed(coupon_id: int, user_id: int, order_id: int) -> None:
    publish(EVENT_COUPON_REDEEMED, {"coupon_id": coupon_id, "user_id": user_id, "order_id": order_id})


def publish_promotion_activated(promotion_id: int, country_code: str | None = None) -> None:
    publish(EVENT_PROMOTION_ACTIVATED, {"promotion_id": promotion_id, "country_code": country_code})


def publish_promotion_expired(promotion_id: int) -> None:
    publish(EVENT_PROMOTION_EXPIRED, {"promotion_id": promotion_id})


__all__ = [
    "EVENT_COUPON_APPLIED",
    "EVENT_COUPON_REDEEMED",
    "EVENT_PROMOTION_ACTIVATED",
    "EVENT_PROMOTION_EXPIRED",
    "publish_coupon_applied",
    "publish_coupon_redeemed",
    "publish_promotion_activated",
    "publish_promotion_expired",
]

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# base classes merged from services/
class PromotionsEvent:
    """Base class for all promotions-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# derived classes merged from services/
class CouponApplied(PromotionsEvent):
    coupon_id: int = 0
    code: str = ""
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    discount_amount: str = ""
    event_type: str = field(default=EVENT_COUPON_APPLIED, init=False)
class PromotionActivated(PromotionsEvent):
    promotion_id: int = 0
    name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_PROMOTION_ACTIVATED, init=False)
class PromotionExpired(PromotionsEvent):
    promotion_id: int = 0
    name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_PROMOTION_EXPIRED, init=False)
