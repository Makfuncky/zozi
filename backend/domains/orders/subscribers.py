"""orders domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners against the shared ``EventPublisher``. Wire it at boot by calling
``register_orders_subscribers(publisher)`` from ``lifespan.py`` (kept optional so the
domain stays importable without side effects).
"""

from __future__ import annotations

import logging
from typing import Any

from infrastructure.messaging.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


def _on_order_created(event: Any) -> None:
    """React to an order being created.

    Triggers notification dispatch, fraud evaluation, and inventory reservation.
    """
    logger.info(
        "order created: order_id=%s user_id=%s — dispatch notifications, evaluate fraud",
        getattr(event, "order_id", "?"),
        getattr(event, "user_id", "?"),
    )
    # Future: reserve inventory, enqueue fraud check, send confirmation notification.


def _on_order_confirmed(event: Any) -> None:
    """React to an order being confirmed.

    Triggers supplier notification and payout hold creation.
    """
    logger.info(
        "order confirmed: order_id=%s — notify suppliers, create payout hold",
        getattr(event, "order_id", "?"),
    )
    # Future: notify suppliers, create payout hold, start SLA timer.


def _on_order_shipped(event: Any) -> None:
    """React to an order being shipped.

    Triggers shipment tracking initialization and customer notification.
    """
    logger.info(
        "order shipped: order_id=%s tracking=%s — init tracking, notify customer",
        getattr(event, "order_id", "?"),
        getattr(event, "tracking_number", "?"),
    )
    # Future: init shipment tracking, send shipping notification.


def _on_order_delivered(event: Any) -> None:
    """React to an order being delivered.

    Triggers payout release and review request.
    """
    logger.info(
        "order delivered: order_id=%s — release payout, request review",
        getattr(event, "order_id", "?"),
    )
    # Future: release supplier payout, request customer review.


def _on_order_cancelled(event: Any) -> None:
    """React to an order being cancelled.

    Triggers inventory release, refund initiation, and supplier notification.
    """
    logger.info(
        "order cancelled: order_id=%s reason=%s — release inventory, initiate refund",
        getattr(event, "order_id", "?"),
        getattr(event, "reason", "?"),
    )
    # Future: release reserved inventory, initiate refund, notify suppliers.


def register_orders_subscribers(publisher: EventPublisher) -> None:
    """Register all orders-domain event listeners.

    Called once at app startup from ``lifespan.py``. Importing the event
    classes lazily avoids hard dependencies on publishing domains that may
    not be wired in every deployment.
    """
    # Orders-domain events we publish and react to.
    try:
        from domains.orders.events import (
            EVENT_ORDER_CREATED,
            EVENT_ORDER_CONFIRMED,
            EVENT_ORDER_SHIPPED,
            EVENT_ORDER_DELIVERED,
            EVENT_ORDER_CANCELLED,
        )

        publisher.register_listener(EVENT_ORDER_CREATED, _on_order_created)
        publisher.register_listener(EVENT_ORDER_CONFIRMED, _on_order_confirmed)
        publisher.register_listener(EVENT_ORDER_SHIPPED, _on_order_shipped)
        publisher.register_listener(EVENT_ORDER_DELIVERED, _on_order_delivered)
        publisher.register_listener(EVENT_ORDER_CANCELLED, _on_order_cancelled)
    except ImportError:
        logger.debug("Orders events not available — skipping orders listeners")

    logger.info("Orders domain event subscribers registered")
