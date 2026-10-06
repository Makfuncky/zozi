"""Logistics domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the logistics domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module, or call
``register_logistics_subscribers()`` explicitly from ``lifespan.py``.
"""
from __future__ import annotations

import logging
import os
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


def _ensure_implemented(feature: str) -> None:
    if os.getenv("APP_ENV", "development").lower() != "development":
        raise NotImplementedError(f"{feature} event handler is not implemented")


def _on_shipment_created(payload: Dict[str, Any]) -> None:
    """React to a shipment being created.

    Triggers tracking initialization and customer notification.
    """
    _ensure_implemented("shipment.created")
    logger.info(
        "shipment created: shipment_id=%s order_id=%s carrier=%s — init tracking",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("carrier", "?"),
    )


def _on_shipment_in_transit(payload: Dict[str, Any]) -> None:
    """React to a shipment entering transit.

    Triggers status update and ETA recalculation.
    """
    _ensure_implemented("shipment.in_transit")
    logger.info(
        "shipment in transit: shipment_id=%s order_id=%s location=%s — update status",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
        payload.get("current_location", "?"),
    )


def _on_shipment_delivered(payload: Dict[str, Any]) -> None:
    """React to a shipment being delivered.

    Triggers delivery confirmation and order completion check.
    """
    _ensure_implemented("shipment.delivered")
    logger.info(
        "shipment delivered: shipment_id=%s order_id=%s — confirm delivery",
        payload.get("shipment_id", "?"),
        payload.get("order_id", "?"),
    )


def _on_order_created(payload: Dict[str, Any]) -> None:
    """React to an order being created in the orders domain.

    Triggers shipment pre-allocation for the order's country.
    """
    _ensure_implemented("orders.created")
    logger.info(
        "order created: order_id=%s country=%s — pre-allocate shipment",
        payload.get("order_id", "?"),
        payload.get("country_code", "?"),
    )


def _on_order_cancelled(payload: Dict[str, Any]) -> None:
    """React to an order being cancelled.

    Triggers shipment cancellation and carrier release.
    """
    _ensure_implemented("orders.cancelled")
    logger.info(
        "order cancelled: order_id=%s reason=%s — cancel shipment",
        payload.get("order_id", "?"),
        payload.get("reason", "?"),
    )


def register_logistics_subscribers() -> None:
    """Register all logistics-domain event listeners on the canonical event bus."""
    subscribe(EVENT_SHIPMENT_CREATED, _on_shipment_created)
    subscribe(EVENT_SHIPMENT_IN_TRANSIT, _on_shipment_in_transit)
    subscribe(EVENT_SHIPMENT_DELIVERED, _on_shipment_delivered)
    subscribe(EVENT_ORDER_CREATED, _on_order_created)
    subscribe(EVENT_ORDER_CANCELLED, _on_order_cancelled)
    logger.info("Logistics domain event subscribers registered")
