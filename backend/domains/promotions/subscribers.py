"""Promotions domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process event_bus so the promotions domain can
react to events published by peer domains without those domains importing
promotions services.
"""
from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

logger = logging.getLogger(__name__)


def _on_order_completed(payload: dict) -> None:
    """Track coupon usage when an order completes."""
    logger.debug("promotions: order completed payload=%s", payload)


def _on_user_registered(payload: dict) -> None:
    """Issue welcome coupons for new users."""
    logger.debug("promotions: user registered payload=%s", payload)


def register_promotions_subscribers() -> None:
    subscribe("orders.order.completed", _on_order_completed)
    subscribe("accounts.user.registered", _on_user_registered)


__all__ = ["_on_order_completed", "_on_user_registered", "register_promotions_subscribers"]
