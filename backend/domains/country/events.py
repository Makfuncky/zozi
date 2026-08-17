"""Country domain events.

Country is a *publishing* domain: when its config changes it emits events that
other domains may subscribe to (Law 3 — cross-domain writes only via events).
Events are plain dataclass-like objects; the bus is ``events.event_publisher.EventPublisher``
(which keys listeners by event *type*).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class CountryEvent:
    """Base class for all country domain events."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CountryConfigPublished(CountryEvent):
    country_code: str = ""
    version: int = 0
    published_by: int | None = None


@dataclass
class CountryConfigDraftCreated(CountryEvent):
    country_code: str = ""
    config_type: str = ""
    draft_by: int | None = None


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
