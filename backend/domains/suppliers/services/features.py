"""Feature atoms for suppliers domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the suppliers domain. CI must fail on any
``require_feature("suppliers.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "suppliers.profiles.read": {
        "label": "View Supplier Profiles",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier profiles, company information, and verification status.",
    },
    "suppliers.profiles.manage": {
        "label": "Manage Supplier Profiles",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Manage supplier profiles, documentation, and verification processes.",
    },
    "suppliers.verification": {
        "label": "Verify Suppliers",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Approve, reject, or suspend supplier verification and onboarding.",
    },
    "suppliers.catalog.read": {
        "label": "View Supplier Catalog",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier product catalogs and inventory.",
    },
    "suppliers.catalog.manage": {
        "label": "Manage Supplier Catalog",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Manage supplier product listings, pricing, and inventory allocation.",
    },
    "suppliers.orders.read": {
        "label": "View Supplier Orders",
        "risk": "low",
        "actions": ["read"],
        "description": "View orders containing supplier products and fulfillment status.",
    },
    "suppliers.orders.manage": {
        "label": "Manage Supplier Orders",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Manage order fulfillment, shipping, and delivery for supplier items.",
    },
    "suppliers.analytics": {
        "label": "Supplier Analytics",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier performance analytics, sales reports, and metrics.",
    },
    "suppliers.badges.manage": {
        "label": "Manage Supplier Badges",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Manage supplier badges, tiers, and achievement recognition.",
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
