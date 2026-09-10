
"""analytics domain - AXIS 2 event subscribers (Law 3: react to cross-domain intents).

Registers handlers on the in-process ``event_bus`` so the analytics domain can
react to its own intents (e.g. a requested KPI snapshot recompute) without other
domains importing analytics services.

Importing this module registers the handlers. Wire it from the domain package
(or the central subscriber registry) once the recompute logic exists.
"""

from __future__ import annotations

import logging

from infrastructure.messaging.events.event_bus import subscribe

from .events import EVENT_ANALYTICS_KPI_SNAPSHOT_REQUESTED

logger = logging.getLogger(__name__)


def _on_kpi_snapshot_requested(payload: dict) -> None:
    country_code = payload.get("country_code")
    kpi = payload.get("kpi")
    logger.info("analytics: KPI snapshot requested country=%s kpi=%s", country_code, kpi)
    # TODO(PART 1.12): dispatch the actual snapshot recompute once the
    # consolidated analytics service lives in this domain.


def register_analytics_subscribers() -> None:
    subscribe(EVENT_ANALYTICS_KPI_SNAPSHOT_REQUESTED, _on_kpi_snapshot_requested)


__all__ = ["_on_kpi_snapshot_requested", "register_analytics_subscribers"]
