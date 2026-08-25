"""Feature atoms for country domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the country domain. CI must fail on any
``require_feature("country.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "country.read": {
        "label": "View Countries",
        "risk": "low",
        "actions": ["read"],
        "description": "View country configurations, settings, and metadata.",
    },
    "country.manage": {
        "label": "Manage Countries",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Add, configure, and deactivate countries in the marketplace.",
    },
    "country.currency.configure": {
        "label": "Configure Currency",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Configure currency settings, exchange rates, and display formats.",
    },
    "country.tax.configure": {
        "label": "Configure Tax Rules",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Configure tax rules, rates, and exemptions per country.",
    },
    "country.cross_border.read": {
        "label": "View Cross-Border Activity",
        "risk": "low",
        "actions": ["read"],
        "description": "View cross-border detection logs and compliance data.",
    },
    "country.cross_border.manage": {
        "label": "Manage Cross-Border Rules",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Configure cross-border detection rules and compliance policies.",
    },
    "country.rls.configure": {
        "label": "Configure RLS Policies",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Configure row-level security policies and tenant isolation rules.",
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
