"""Orders domain — typed cross-domain events (Law 3).

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
EVENT_ORDER_CREATED = "orders.order.created"
EVENT_ORDER_CONFIRMED = "orders.order.confirmed"
EVENT_ORDER_SHIPPED = "orders.order.shipped"
EVENT_ORDER_DELIVERED = "orders.order.delivered"
EVENT_ORDER_CANCELLED = "orders.order.cancelled"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class OrdersEvent:
    """Base class for all orders-domain events."""

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

# ── order lifecycle events ────────────────────────────────────────────────

@dataclass(frozen=True)
class OrderCreated(OrdersEvent):
    order_id: int = 0
    user_id: Optional[int] = None
    total_amount: str = ""
    currency: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_ORDER_CREATED, init=False)

@dataclass(frozen=True)
class OrderConfirmed(OrdersEvent):
    order_id: int = 0
    confirmed_by: Optional[int] = None
    event_type: str = field(default=EVENT_ORDER_CONFIRMED, init=False)

@dataclass(frozen=True)
class OrderShipped(OrdersEvent):
    order_id: int = 0
    shipment_id: Optional[int] = None
    carrier: str = ""
    tracking_number: str = ""
    event_type: str = field(default=EVENT_ORDER_SHIPPED, init=False)

@dataclass(frozen=True)
class OrderDelivered(OrdersEvent):
    order_id: int = 0
    delivered_at: str = ""
    event_type: str = field(default=EVENT_ORDER_DELIVERED, init=False)

@dataclass(frozen=True)
class OrderCancelled(OrdersEvent):
    order_id: int = 0
    reason: str = ""
    cancelled_by: Optional[int] = None
    event_type: str = field(default=EVENT_ORDER_CANCELLED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_order_created(order_id: int, total_amount: str, currency: str, country_code: str, user_id: Optional[int] = None) -> None:
    """Publish an OrderCreated event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = OrderCreated(order_id=order_id, user_id=user_id, total_amount=total_amount, currency=currency, country_code=country_code)
        publish(EVENT_ORDER_CREATED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish OrderCreated event: %s", exc)

def publish_order_confirmed(order_id: int, confirmed_by: Optional[int] = None) -> None:
    """Publish an OrderConfirmed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = OrderConfirmed(order_id=order_id, confirmed_by=confirmed_by)
        publish(EVENT_ORDER_CONFIRMED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish OrderConfirmed event: %s", exc)

def publish_order_shipped(order_id: int, carrier: str, tracking_number: str, shipment_id: Optional[int] = None) -> None:
    """Publish an OrderShipped event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = OrderShipped(order_id=order_id, shipment_id=shipment_id, carrier=carrier, tracking_number=tracking_number)
        publish(EVENT_ORDER_SHIPPED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish OrderShipped event: %s", exc)

def publish_order_delivered(order_id: int, delivered_at: str) -> None:
    """Publish an OrderDelivered event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = OrderDelivered(order_id=order_id, delivered_at=delivered_at)
        publish(EVENT_ORDER_DELIVERED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish OrderDelivered event: %s", exc)

def publish_order_cancelled(order_id: int, reason: str, cancelled_by: Optional[int] = None) -> None:
    """Publish an OrderCancelled event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = OrderCancelled(order_id=order_id, reason=reason, cancelled_by=cancelled_by)
        publish(EVENT_ORDER_CANCELLED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish OrderCancelled event: %s", exc)

__all__ = [
    # Event type constants
    "EVENT_ORDER_CREATED",
    "EVENT_ORDER_CONFIRMED",
    "EVENT_ORDER_SHIPPED",
    "EVENT_ORDER_DELIVERED",
    "EVENT_ORDER_CANCELLED",
    # Event classes
    "OrdersEvent",
    "OrderCreated",
    "OrderConfirmed",
    "OrderShipped",
    "OrderDelivered",
    "OrderCancelled",
    # Publish helpers
    "publish_order_created",
    "publish_order_confirmed",
    "publish_order_shipped",
    "publish_order_delivered",
    "publish_order_cancelled",
]
