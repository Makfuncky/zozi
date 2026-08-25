"""Feature atoms for analytics domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the analytics domain. CI must fail on any
``require_feature("analytics.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "analytics.reports.read": {
        "label": "View Analytics Reports",
        "risk": "low",
        "actions": ["read"],
        "description": "View financial reports, executive news, and analytics dashboards.",
    },
    "analytics.reports.generate": {
        "label": "Generate Reports",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Generate new financial reports and analytics snapshots.",
    },
    "analytics.news.read": {
        "label": "View Executive News",
        "risk": "low",
        "actions": ["read"],
        "description": "Read published executive news and market intelligence.",
    },
    "analytics.news.publish": {
        "label": "Publish Executive News",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create, edit, and publish executive news items.",
    },
    "analytics.simulations.read": {
        "label": "View Simulations",
        "risk": "low",
        "actions": ["read"],
        "description": "View predictive simulations and forecasting results.",
    },
    "analytics.simulations.run": {
        "label": "Run Simulations",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Execute predictive simulations and forecasting models.",
    },
    "analytics.export": {
        "label": "Export Analytics Data",
        "risk": "medium",
        "actions": ["read"],
        "description": "Export analytics data and reports in various formats.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
