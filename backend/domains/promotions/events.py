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
