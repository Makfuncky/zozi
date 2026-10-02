"""Logistics domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the logistics domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module, or call
``register_logistics_subscribers()`` explicitly from ``lifespan.py``.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from infrastructure.messaging.events.event_bus import subscribe

from domains.logistics.events import (
    EVENT_SHIPMENT_CREATED,
    EVENT_SHIPMENT_DELIVERED,
    EVENT_SHIPMENT_IN_TRANSIT,
)
from domains.orders.events import (
    EVENT_ORDER_CANCELLED,
    EVENT_ORDER_CREATED,
)

logger = logging.getLogger(__name__)


def _on_shipment_created(payload: Dict[str, Any]) -> None:
    """React to a shipment being created.

    Triggers tracking initialization and customer notification.
    """
    logger.info(
        "shipment created: shipment_id=%s order_id=%s carrier=%s — init tracking",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("carrier", "?"),
    )
    # Future: init tracking record, notify customer of shipment creation.


def _on_shipment_in_transit(payload: Dict[str, Any]) -> None:
    """React to a shipment entering transit.

    Triggers status update and ETA recalculation.
    """
    logger.info(
        "shipment in transit: shipment_id=%s order_id=%s location=%s — update status",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("current_location", "?"),
    )
    # Future: update tracking status, recalculate ETA, notify customer.


def _on_shipment_delivered(payload: Dict[str, Any]) -> None:
    """React to a shipment being delivered.

    Triggers delivery confirmation and order completion check.
    """
    logger.info(
        "shipment delivered: shipment_id=%s order_id=%s — confirm delivery",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
    )
    # Future: confirm delivery, trigger order completion flow.


def _on_order_created(payload: Dict[str, Any]) -> None:
    """React to an order being created in the orders domain.

    Triggers shipment pre-allocation for the order's country.
    """
    logger.info(
        "order created: order_id=%s country=%s — pre-allocate shipment",
        payload.get("order_id", "?"),
        payload.get("country_code", "?"),
    )
    # Future: pre-allocate shipment slot, assign default carrier by country.


def _on_order_cancelled(payload: Dict[str, Any]) -> None:
    """React to an order being cancelled.

    Triggers shipment cancellation and carrier release.
    """
    logger.info(
        "order cancelled: order_id=%s reason=%s — cancel shipment",
        payload.get("order_id", "?"),
        payload.get("reason", "?"),
    )
    # Future: cancel pending shipments, release carrier allocation.


def register_logistics_subscribers() -> None:
    """Register all logistics-domain event listeners on the canonical event bus."""
    subscribe(EVENT_SHIPMENT_CREATED, _on_shipment_created)
    subscribe(EVENT_SHIPMENT_IN_TRANSIT, _on_shipment_in_transit)
    subscribe(EVENT_SHIPMENT_DELIVERED, _on_shipment_delivered)
    subscribe(EVENT_ORDER_CREATED, _on_order_created)
    subscribe(EVENT_ORDER_CANCELLED, _on_order_cancelled)
    logger.info("Logistics domain event subscribers registered")
