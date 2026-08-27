"""Promotions domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Canonical event type constants (shared contract)
EVENT_COUPON_APPLIED = "promotions.coupon.applied"
EVENT_PROMOTION_ACTIVATED = "promotions.promotion.activated"
EVENT_PROMOTION_EXPIRED = "promotions.promotion.expired"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
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

# ── coupon events ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CouponApplied(PromotionsEvent):
    coupon_id: int = 0
    code: str = ""
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    discount_amount: str = ""
    event_type: str = field(default=EVENT_COUPON_APPLIED, init=False)

# ── promotion lifecycle events ────────────────────────────────────────────

@dataclass(frozen=True)
class PromotionActivated(PromotionsEvent):
    promotion_id: int = 0
    name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_PROMOTION_ACTIVATED, init=False)

@dataclass(frozen=True)
class PromotionExpired(PromotionsEvent):
    promotion_id: int = 0
    name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_PROMOTION_EXPIRED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_coupon_applied(coupon_id: int, code: str, discount_amount: str, order_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """Publish a CouponApplied event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CouponApplied(coupon_id=coupon_id, code=code, order_id=order_id, user_id=user_id, discount_amount=discount_amount)
        publish(EVENT_COUPON_APPLIED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CouponApplied event: %s", exc)

def publish_promotion_activated(promotion_id: int, name: str, country_code: str) -> None:
    """Publish a PromotionActivated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PromotionActivated(promotion_id=promotion_id, name=name, country_code=country_code)
        publish(EVENT_PROMOTION_ACTIVATED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish PromotionActivated event: %s", exc)

def publish_promotion_expired(promotion_id: int, name: str, country_code: str) -> None:
    """Publish a PromotionExpired event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PromotionExpired(promotion_id=promotion_id, name=name, country_code=country_code)
        publish(EVENT_PROMOTION_EXPIRED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish PromotionExpired event: %s", exc)

__all__ = [
    # Event type constants
    "EVENT_COUPON_APPLIED",
    "EVENT_PROMOTION_ACTIVATED",
    "EVENT_PROMOTION_EXPIRED",
    # Event classes
    "PromotionsEvent",
    "CouponApplied",
    "PromotionActivated",
    "PromotionExpired",
    # Publish helpers
    "publish_coupon_applied",
    "publish_promotion_activated",
    "publish_promotion_expired",
]
