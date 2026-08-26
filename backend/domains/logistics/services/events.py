"""Logistics domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# Canonical event type constants (shared contract)
EVENT_SHIPMENT_CREATED = "logistics.shipment.created"
EVENT_SHIPMENT_IN_TRANSIT = "logistics.shipment.in_transit"
EVENT_SHIPMENT_DELIVERED = "logistics.shipment.delivered"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LogisticsEvent:
    """Base class for all logistics-domain events."""

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

# ── shipment events ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class ShipmentCreated(LogisticsEvent):
    shipment_id: int = 0
    order_id: int = 0
    carrier: str = ""
    tracking_number: str = ""
    origin_country: str = ""
    destination_country: str = ""
    event_type: str = field(default=EVENT_SHIPMENT_CREATED, init=False)

@dataclass(frozen=True)
class ShipmentInTransit(LogisticsEvent):
    shipment_id: int = 0
    order_id: int = 0
    current_location: str = ""
    status: str = ""
    estimated_delivery: Optional[str] = None
    event_type: str = field(default=EVENT_SHIPMENT_IN_TRANSIT, init=False)

@dataclass(frozen=True)
class ShipmentDelivered(LogisticsEvent):
    shipment_id: int = 0
    order_id: int = 0
    delivered_at: str = ""
    signed_by: str = ""
    event_type: str = field(default=EVENT_SHIPMENT_DELIVERED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_shipment_created(shipment_id: int, order_id: int, carrier: str, tracking_number: str, origin_country: str, destination_country: str) -> None:
    """Publish a ShipmentCreated event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ShipmentCreated(shipment_id=shipment_id, order_id=order_id, carrier=carrier, tracking_number=tracking_number, origin_country=origin_country, destination_country=destination_country)
        publish(EVENT_SHIPMENT_CREATED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_shipment_in_transit(shipment_id: int, order_id: int, current_location: str, status: str, estimated_delivery: Optional[str] = None) -> None:
    """Publish a ShipmentInTransit event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ShipmentInTransit(shipment_id=shipment_id, order_id=order_id, current_location=current_location, status=status, estimated_delivery=estimated_delivery)
        publish(EVENT_SHIPMENT_IN_TRANSIT, event.serialize())
    except Exception:
        pass

def publish_shipment_delivered(shipment_id: int, order_id: int, delivered_at: str, signed_by: str = "") -> None:
    """Publish a ShipmentDelivered event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ShipmentDelivered(shipment_id=shipment_id, order_id=order_id, delivered_at=delivered_at, signed_by=signed_by)
        publish(EVENT_SHIPMENT_DELIVERED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_SHIPMENT_CREATED",
    "EVENT_SHIPMENT_IN_TRANSIT",
    "EVENT_SHIPMENT_DELIVERED",
    # Event classes
    "LogisticsEvent",
    "ShipmentCreated",
    "ShipmentInTransit",
    "ShipmentDelivered",
    # Publish helpers
    "publish_shipment_created",
    "publish_shipment_in_transit",
    "publish_shipment_delivered",
]
