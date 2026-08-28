"""Logistics domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners against the shared ``EventPublisher``. Wire it at boot by calling
``register_logistics_subscribers(publisher)`` from ``lifespan.py`` (kept optional so the
domain stays importable without side effects).
"""

from __future__ import annotations

import logging
from typing import Any

from infrastructure.messaging.events.event_publisher import EventPublisher

logger = logging.getLogger(__name__)


def _on_shipment_created(event: Any) -> None:
    """React to a shipment being created.

    Triggers tracking initialization and customer notification.
    """
    logger.info(
        "shipment created: shipment_id=%s order_id=%s carrier=%s — init tracking",
        getattr(event, "shipment_id", "?"),
        getattr(event, "order_id", "?"),
        getattr(event, "carrier", "?"),
    )
    # Future: init tracking record, notify customer of shipment creation.


def _on_shipment_in_transit(event: Any) -> None:
    """React to a shipment entering transit.

    Triggers status update and ETA recalculation.
    """
    logger.info(
        "shipment in transit: shipment_id=%s order_id=%s location=%s — update status",
        getattr(event, "shipment_id", "?"),
        getattr(event, "order_id", "?"),
        getattr(event, "current_location", "?"),
    )
    # Future: update tracking status, recalculate ETA, notify customer.


def _on_shipment_delivered(event: Any) -> None:
    """React to a shipment being delivered.

    Triggers delivery confirmation and order completion check.
    """
    logger.info(
        "shipment delivered: shipment_id=%s order_id=%s — confirm delivery",
        getattr(event, "shipment_id", "?"),
        getattr(event, "order_id", "?"),
    )
    # Future: confirm delivery, trigger order completion flow.


def _on_order_created(event: Any) -> None:
    """React to an order being created in the orders domain.

    Triggers shipment pre-allocation for the order's country.
    """
    logger.info(
        "order created: order_id=%s country=%s — pre-allocate shipment",
        getattr(event, "order_id", "?"),
        getattr(event, "country_code", "?"),
    )
    # Future: pre-allocate shipment slot, assign default carrier by country.


def _on_order_cancelled(event: Any) -> None:
    """React to an order being cancelled.

    Triggers shipment cancellation and carrier release.
    """
    logger.info(
        "order cancelled: order_id=%s reason=%s — cancel shipment",
        getattr(event, "order_id", "?"),
        getattr(event, "reason", "?"),
    )
    # Future: cancel pending shipments, release carrier allocation.


def register_logistics_subscribers(publisher: EventPublisher) -> None:
    """Register all logistics-domain event listeners.

    Called once at app startup from ``lifespan.py``. Importing the event
    classes lazily avoids hard dependencies on publishing domains that may
    not be wired in every deployment.
    """
    # Logistics-domain events we publish and react to.
    try:
        from domains.logistics.events import (
            EVENT_SHIPMENT_CREATED,
            EVENT_SHIPMENT_IN_TRANSIT,
            EVENT_SHIPMENT_DELIVERED,
        )

        publisher.register_listener(EVENT_SHIPMENT_CREATED, _on_shipment_created)
        publisher.register_listener(EVENT_SHIPMENT_IN_TRANSIT, _on_shipment_in_transit)
        publisher.register_listener(EVENT_SHIPMENT_DELIVERED, _on_shipment_delivered)
    except ImportError:
        logger.debug("Logistics events not available — skipping logistics listeners")

    # Orders-domain events we react to (resolved lazily to avoid import cycle).
    try:
        from domains.orders.events import (
            EVENT_ORDER_CREATED,
            EVENT_ORDER_CANCELLED,
        )

        publisher.register_listener(EVENT_ORDER_CREATED, _on_order_created)
        publisher.register_listener(EVENT_ORDER_CANCELLED, _on_order_cancelled)
    except ImportError:
        logger.debug("Orders events not available — skipping logistics order listeners")

    logger.info("Logistics domain event subscribers registered")
