"""orders domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the orders domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module (its ``register_*`` calls
run at import time), or call ``register_orders_subscribers()`` explicitly.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from infrastructure.messaging.events.event_bus import subscribe

from domains.orders.events import (
    EVENT_ORDER_CANCELLED,
    EVENT_ORDER_CONFIRMED,
    EVENT_ORDER_CREATED,
    EVENT_ORDER_DELIVERED,
    EVENT_ORDER_SHIPPED,
)

logger = logging.getLogger(__name__)


def _ensure_implemented(feature: str) -> None:
    if os.getenv("APP_ENV", "development").lower() != "development":
        raise NotImplementedError(f"{feature} event handler is not implemented")


def _on_order_created(event: Any) -> None:
    """React to an order being created.

    Triggers notification dispatch, fraud evaluation, and inventory reservation.
    """
    _ensure_implemented("orders.created")
    logger.info(
        "order created: order_id=%s user_id=%s — dispatch notifications, evaluate fraud",
        getattr(event, "order_id", "?"),
        getattr(event, "user_id", "?"),
    )


def _on_order_confirmed(event: Any) -> None:
    """React to an order being confirmed.

    Triggers supplier notification and payout hold creation.
    """
    _ensure_implemented("orders.confirmed")
    logger.info(
        "order confirmed: order_id=%s — notify suppliers, create payout hold",
        getattr(event, "order_id", "?"),
    )


def _on_order_shipped(event: Any) -> None:
    """React to an order being shipped.

    Triggers shipment tracking initialization and customer notification.
    """
    _ensure_implemented("orders.shipped")
    logger.info(
        "order shipped: order_id=%s tracking=%s — init tracking, notify customer",
        getattr(event, "order_id", "?"),
        getattr(event, "tracking_number", "?"),
    )


def _on_order_delivered(event: Any) -> None:
    """React to an order being delivered.

    Triggers payout release and review request.
    """
    _ensure_implemented("orders.delivered")
    logger.info(
        "order delivered: order_id=%s — release payout, request review",
        getattr(event, "order_id", "?"),
    )


def _on_order_cancelled(event: Any) -> None:
    """React to an order being cancelled.

    Triggers inventory release, refund initiation, and supplier notification.
    """
    _ensure_implemented("orders.cancelled")
    logger.info(
        "order cancelled: order_id=%s reason=%s — release inventory, initiate refund",
        getattr(event, "order_id", "?"),
        getattr(event, "reason", "?"),
    )


def register_orders_subscribers() -> None:
    """Register all orders-domain event listeners on the canonical event bus.

    Called once at app startup from ``lifespan.py``.
    """
    subscribe(EVENT_ORDER_CREATED, _on_order_created)
    subscribe(EVENT_ORDER_CONFIRMED, _on_order_confirmed)
    subscribe(EVENT_ORDER_SHIPPED, _on_order_shipped)
    subscribe(EVENT_ORDER_DELIVERED, _on_order_delivered)
    subscribe(EVENT_ORDER_CANCELLED, _on_order_cancelled)
    logger.info("Orders domain event subscribers registered")
