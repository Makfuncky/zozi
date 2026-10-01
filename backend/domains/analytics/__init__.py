"""Analytics domain — public facade.

Exports the public API for the analytics domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from domains.analytics.services.analytics_service import AnalyticsService

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "AnalyticsService": ("domains.analytics.services.analytics_service", "AnalyticsService"),
    "CommandCenterService": ("domains.analytics.services.aggregation.command_center_service", "CommandCenterService"),
    "CommandCenterQueryService": ("domains.analytics.services.aggregation.command_center_query_service", "CommandCenterQueryService"),
    # events
    "publish_analytics_executive_news_published": ("domains.analytics.events", "publish_analytics_executive_news_published"),
    "publish_analytics_simulation_completed": ("domains.analytics.events", "publish_analytics_simulation_completed"),
    "publish_analytics_kpi_snapshot_requested": ("domains.analytics.events", "publish_analytics_kpi_snapshot_requested"),
    # models
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.analytics' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
