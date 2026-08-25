"""Country domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# Canonical event type constants (shared contract)
EVENT_COUNTRY_ADDED = "country.added"
EVENT_COUNTRY_UPDATED = "country.updated"
EVENT_CROSS_BORDER_DETECTED = "country.cross_border.detected"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CountryEvent:
    """Base class for all country-domain service-level events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.utcnow(), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# ── country lifecycle events ──────────────────────────────────────────────

@dataclass(frozen=True)
class CountryAdded(CountryEvent):
    country_code: str = ""
    country_name: str = ""
    currency_code: str = ""
    added_by: Optional[int] = None
    event_type: str = field(default=EVENT_COUNTRY_ADDED, init=False)

@dataclass(frozen=True)
class CountryUpdated(CountryEvent):
    country_code: str = ""
    changed_fields: str = ""
    updated_by: Optional[int] = None
    event_type: str = field(default=EVENT_COUNTRY_UPDATED, init=False)

# ── cross-border events ───────────────────────────────────────────────────

@dataclass(frozen=True)
class CrossBorderDetected(CountryEvent):
    user_id: int = 0
    from_country: str = ""
    to_country: str = ""
    session_id: str = ""
    event_type: str = field(default=EVENT_CROSS_BORDER_DETECTED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_country_added(country_code: str, country_name: str, currency_code: str, added_by: Optional[int] = None) -> None:
    """Publish a CountryAdded event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CountryAdded(country_code=country_code, country_name=country_name, currency_code=currency_code, added_by=added_by)
        publish(EVENT_COUNTRY_ADDED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_country_updated(country_code: str, changed_fields: str, updated_by: Optional[int] = None) -> None:
    """Publish a CountryUpdated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CountryUpdated(country_code=country_code, changed_fields=changed_fields, updated_by=updated_by)
        publish(EVENT_COUNTRY_UPDATED, event.serialize())
    except Exception:
        pass

def publish_cross_border_detected(user_id: int, from_country: str, to_country: str, session_id: str) -> None:
    """Publish a CrossBorderDetected event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CrossBorderDetected(user_id=user_id, from_country=from_country, to_country=to_country, session_id=session_id)
        publish(EVENT_CROSS_BORDER_DETECTED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_COUNTRY_ADDED",
    "EVENT_COUNTRY_UPDATED",
    "EVENT_CROSS_BORDER_DETECTED",
    # Event classes
    "CountryEvent",
    "CountryAdded",
    "CountryUpdated",
    "CrossBorderDetected",
    # Publish helpers
    "publish_country_added",
    "publish_country_updated",
    "publish_cross_border_detected",
]
