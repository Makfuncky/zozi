
"""analytics domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The analytics domain owns the ``analytics``/``ai`` intelligence schemas. It
publishes notifications when intelligence artifacts change (so downstream
domains can react) and exposes intent constants other domains publish to ask
analytics to (re)compute snapshots.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""

from __future__ import annotations

from infrastructure.messaging.events.event_bus import publish

# --- notifications analytics emits after a write (downstream reacts) ---
EVENT_ANALYTICS_EXECUTIVE_NEWS_PUBLISHED = "analytics.executive_news_published"
EVENT_ANALYTICS_SIMULATION_COMPLETED = "analytics.simulation_completed"

# --- intents other domains publish for analytics to execute (Law 3 writes) ---
EVENT_ANALYTICS_KPI_SNAPSHOT_REQUESTED = "analytics.kpi_snapshot_requested"


def publish_analytics_executive_news_published(news_id: int, country_code: str) -> None:
    publish(EVENT_ANALYTICS_EXECUTIVE_NEWS_PUBLISHED, {"news_id": news_id, "country_code": country_code})


def publish_analytics_simulation_completed(simulation_id: int, country_code: str) -> None:
    publish(EVENT_ANALYTICS_SIMULATION_COMPLETED, {"simulation_id": simulation_id, "country_code": country_code})


def publish_analytics_kpi_snapshot_requested(country_code: str, kpi: str | None = None) -> None:
    publish(EVENT_ANALYTICS_KPI_SNAPSHOT_REQUESTED, {"country_code": country_code, "kpi": kpi})


__all__ = [
    "EVENT_ANALYTICS_EXECUTIVE_NEWS_PUBLISHED",
    "EVENT_ANALYTICS_SIMULATION_COMPLETED",
    "EVENT_ANALYTICS_KPI_SNAPSHOT_REQUESTED",
    "publish_analytics_executive_news_published",
    "publish_analytics_simulation_completed",
    "publish_analytics_kpi_snapshot_requested",
]
