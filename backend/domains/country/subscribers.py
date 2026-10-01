"""Country domain event subscribers.

Per Law 3, cross-domain *writes* happen only by consuming events here. This module
registers listeners against the shared ``EventPublisher``. Wire it at boot by calling
``register_country_subscribers(publisher)`` from ``lifespan.py`` (kept optional so the
domain stays importable without side effects).
"""

from __future__ import annotations

import logging
from typing import Any

from .events import (
    CountryConfigPublished,
    CountryStaffAssigned,
    CountryTaxRateChanged,
)

logger = logging.getLogger(__name__)


def _on_config_published(event: CountryConfigPublished) -> None:
    logger.info(
        "country config published: code=%s version=%s by=%s",
        event.country_code,
        event.version,
        event.published_by,
    )
    # Future: invalidate country-scoped caches, notify dependent domains.


def _on_staff_assigned(event: CountryStaffAssigned) -> None:
    logger.info(
        "country staff assigned: code=%s user=%s role=%s",
        event.country_code,
        event.user_id,
        event.role_in_country,
    )


def _on_tax_changed(event: CountryTaxRateChanged) -> None:
    logger.info(
        "country tax rate changed: code=%s category=%s rate=%s",
        event.country_code,
        event.category_id,
        event.tax_rate,
    )


def register_country_subscribers(publisher: Any) -> None:
    """Attach country-domain listeners to the shared event publisher."""
    publisher.register_listener(CountryConfigPublished, _on_config_published)
    publisher.register_listener(CountryStaffAssigned, _on_staff_assigned)
    publisher.register_listener(CountryTaxRateChanged, _on_tax_changed)
