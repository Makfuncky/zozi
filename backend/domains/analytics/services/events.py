"""Analytics domain — typed cross-domain events (Law 3).

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
EVENT_REPORT_GENERATED = "analytics.report.generated"
EVENT_NEWS_PUBLISHED = "analytics.news.published"
EVENT_SIMULATION_COMPLETED = "analytics.simulation.completed"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AnalyticsEvent:
    """Base class for all analytics-domain events."""

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

# ── report events ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReportGenerated(AnalyticsEvent):
    report_id: int = 0
    report_type: str = ""
    country_code: str = ""
    period_start: str = ""
    period_end: str = ""
    event_type: str = field(default=EVENT_REPORT_GENERATED, init=False)

# ── news events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class NewsPublished(AnalyticsEvent):
    news_id: int = 0
    title: str = ""
    category: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_NEWS_PUBLISHED, init=False)

# ── simulation events ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class SimulationCompleted(AnalyticsEvent):
    simulation_id: int = 0
    simulation_type: str = ""
    country_code: str = ""
    result_summary: str = ""
    event_type: str = field(default=EVENT_SIMULATION_COMPLETED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_report_generated(report_id: int, report_type: str, country_code: str, period_start: str, period_end: str) -> None:
    """Publish a ReportGenerated event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ReportGenerated(report_id=report_id, report_type=report_type, country_code=country_code, period_start=period_start, period_end=period_end)
        publish(EVENT_REPORT_GENERATED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_news_published(news_id: int, title: str, category: str, country_code: str) -> None:
    """Publish a NewsPublished event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = NewsPublished(news_id=news_id, title=title, category=category, country_code=country_code)
        publish(EVENT_NEWS_PUBLISHED, event.serialize())
    except Exception:
        pass

def publish_simulation_completed(simulation_id: int, simulation_type: str, country_code: str, result_summary: str) -> None:
    """Publish a SimulationCompleted event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SimulationCompleted(simulation_id=simulation_id, simulation_type=simulation_type, country_code=country_code, result_summary=result_summary)
        publish(EVENT_SIMULATION_COMPLETED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_REPORT_GENERATED",
    "EVENT_NEWS_PUBLISHED",
    "EVENT_SIMULATION_COMPLETED",
    # Event classes
    "AnalyticsEvent",
    "ReportGenerated",
    "NewsPublished",
    "SimulationCompleted",
    # Publish helpers
    "publish_report_generated",
    "publish_news_published",
    "publish_simulation_completed",
]
