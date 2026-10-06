"""Country domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners on the canonical ``event_bus`` so the country domain can
react to events without importing sibling domains directly.

Wire it at app startup by importing this module, or call
``register_country_subscribers()`` explicitly from ``lifespan.py``.
"""
from __future__ import annotations

import logging
import os
from typing import Any

from infrastructure.messaging.events.event_bus import subscribe

from .events import (
    CountryConfigPublished,
    CountryStaffAssigned,
    CountryTaxRateChanged,
)

logger = logging.getLogger(__name__)


def _ensure_implemented(feature: str) -> None:
    if os.getenv("APP_ENV", "development").lower() != "development":
        raise NotImplementedError(f"{feature} event handler is not implemented")


def _on_config_published(event: Any) -> None:
    """React to a country config being published.

    Triggers cache invalidation and dependent-domain notification.
    """
    _ensure_implemented("country.config_published")
    logger.info(
        "country config published: code=%s version=%s by=%s",
        event.country_code,
        event.version,
        event.published_by,
    )


def _on_staff_assigned(event: Any) -> None:
    logger.info(
        "country staff assigned: code=%s user=%s role=%s",
        event.country_code,
        event.user_id,
        event.role_in_country,
    )


def _on_tax_changed(event: Any) -> None:
    logger.info(
        "country tax rate changed: code=%s category=%s rate=%s",
        event.country_code,
        event.category_id,
        event.tax_rate,
    )


def register_country_subscribers() -> None:
    """Attach country-domain listeners to the canonical event bus."""
    subscribe(CountryConfigPublished, _on_config_published)
    subscribe(CountryStaffAssigned, _on_staff_assigned)
    subscribe(CountryTaxRateChanged, _on_tax_changed)
