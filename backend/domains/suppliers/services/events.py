"""Suppliers domain — typed cross-domain events (Law 3).

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
EVENT_SUPPLIER_REGISTERED = "suppliers.supplier.registered"
EVENT_SUPPLIER_VERIFIED = "suppliers.supplier.verified"
EVENT_SUPPLIER_SUSPENDED = "suppliers.supplier.suspended"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SuppliersEvent:
    """Base class for all suppliers-domain events."""

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

# ── supplier lifecycle events ─────────────────────────────────────────────

@dataclass(frozen=True)
class SupplierRegistered(SuppliersEvent):
    supplier_id: int = 0
    user_id: Optional[int] = None
    company_name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_SUPPLIER_REGISTERED, init=False)

@dataclass(frozen=True)
class SupplierVerified(SuppliersEvent):
    supplier_id: int = 0
    verified_by: Optional[int] = None
    event_type: str = field(default=EVENT_SUPPLIER_VERIFIED, init=False)

@dataclass(frozen=True)
class SupplierSuspended(SuppliersEvent):
    supplier_id: int = 0
    reason: str = ""
    suspended_by: Optional[int] = None
    event_type: str = field(default=EVENT_SUPPLIER_SUSPENDED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_supplier_registered(supplier_id: int, company_name: str, country_code: str, user_id: Optional[int] = None) -> None:
    """Publish a SupplierRegistered event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SupplierRegistered(supplier_id=supplier_id, user_id=user_id, company_name=company_name, country_code=country_code)
        publish(EVENT_SUPPLIER_REGISTERED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish SupplierRegistered event: %s", exc)

def publish_supplier_verified(supplier_id: int, verified_by: Optional[int] = None) -> None:
    """Publish a SupplierVerified event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SupplierVerified(supplier_id=supplier_id, verified_by=verified_by)
        publish(EVENT_SUPPLIER_VERIFIED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish SupplierVerified event: %s", exc)

def publish_supplier_suspended(supplier_id: int, reason: str, suspended_by: Optional[int] = None) -> None:
    """Publish a SupplierSuspended event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SupplierSuspended(supplier_id=supplier_id, reason=reason, suspended_by=suspended_by)
        publish(EVENT_SUPPLIER_SUSPENDED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish SupplierSuspended event: %s", exc)

__all__ = [
    # Event type constants
    "EVENT_SUPPLIER_REGISTERED",
    "EVENT_SUPPLIER_VERIFIED",
    "EVENT_SUPPLIER_SUSPENDED",
    # Event classes
    "SuppliersEvent",
    "SupplierRegistered",
    "SupplierVerified",
    "SupplierSuspended",
    # Publish helpers
    "publish_supplier_registered",
    "publish_supplier_verified",
    "publish_supplier_suspended",
]
