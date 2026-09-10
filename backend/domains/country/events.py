"""Country domain events.

Country is a *publishing* domain: when its config changes it emits events that
other domains may subscribe to (Law 3 — cross-domain writes only via events).
Events are plain dataclass-like objects; the bus is ``events.event_publisher.EventPublisher``
(which keys listeners by event *type*).
"""


import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CountryEvent:
    """Base class for all country domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class CountryConfigPublished(CountryEvent):
    country_code: str = ""
    version: int = 0
    published_by: int | None = None


@dataclass
class CountryStaffAssigned(CountryEvent):
    country_code: str = ""
    user_id: int = 0
    role_in_country: str = ""
    assigned_by: int | None = None


@dataclass
class CountryTaxRateChanged(CountryEvent):
    country_code: str = ""
    category_id: int | None = None
    tax_rate: float = 0.0

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# constants merged from services/
EVENT_COUNTRY_ADDED = "country.config.added"
EVENT_COUNTRY_UPDATED = "country.config.updated"
EVENT_CROSS_BORDER_DETECTED = "country.cross_border.detected"

# base classes merged from services/
class CountryAdded(CountryEvent):
    country_code: str = ""
    country_name: str = ""
    currency_code: str = ""
    added_by: Optional[int] = None
    event_type: str = field(default=EVENT_COUNTRY_ADDED, init=False)
class CountryUpdated(CountryEvent):
    country_code: str = ""
    changed_fields: str = ""
    updated_by: Optional[int] = None
    event_type: str = field(default=EVENT_COUNTRY_UPDATED, init=False)
class CrossBorderDetected(CountryEvent):
    user_id: int = 0
    from_country: str = ""
    to_country: str = ""
    session_id: str = ""
    event_type: str = field(default=EVENT_CROSS_BORDER_DETECTED, init=False)

# functions merged from services/
def publish_country_added(country_code: str, country_name: str, currency_code: str, added_by: Optional[int] = None) -> None:
    """Publish a CountryAdded event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CountryAdded(country_code=country_code, country_name=country_name, currency_code=currency_code, added_by=added_by)
        publish(EVENT_COUNTRY_ADDED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CountryAdded event: %s", exc)
def publish_country_updated(country_code: str, changed_fields: str, updated_by: Optional[int] = None) -> None:
    """Publish a CountryUpdated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CountryUpdated(country_code=country_code, changed_fields=changed_fields, updated_by=updated_by)
        publish(EVENT_COUNTRY_UPDATED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CountryUpdated event: %s", exc)
def publish_cross_border_detected(user_id: int, from_country: str, to_country: str, session_id: str) -> None:
    """Publish a CrossBorderDetected event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = CrossBorderDetected(user_id=user_id, from_country=from_country, to_country=to_country, session_id=session_id)
        publish(EVENT_CROSS_BORDER_DETECTED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish CrossBorderDetected event: %s", exc)
