"""Analytics domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the analytics domain. CI must fail on any
``require_feature("analytics.*")`` literal not present in this map.

Seeded from the analytics-facing service surface: dashboards, reports, exports,
and cross-domain analytics reads.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "analytics.read": {
        "label": "View Analytics",
        "risk": "low",
        "actions": ["read"],
        "description": "View analytics dashboards, metrics, and performance data.",
    },
    "analytics.reports.read": {
        "label": "View Analytics Reports",
        "risk": "low",
        "actions": ["read"],
        "description": "View generated analytics reports and summaries.",
    },
    "analytics.reports.export": {
        "label": "Export Analytics Reports",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Export analytics data and reports in various formats.",
    },
    "analytics.dashboard.view": {
        "label": "View Analytics Dashboard",
        "risk": "low",
        "actions": ["read"],
        "description": "Access analytics dashboards and real-time metrics.",
    },
}


def all_features() -> list[str]:
    """Return all analytics feature atom identifiers, sorted."""
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    """Return True if ``feature`` is a known analytics feature atom (supports wildcard)."""
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
