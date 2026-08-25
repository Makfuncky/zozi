"""Feature atoms for promotions domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the promotions domain. CI must fail on any
``require_feature("promotions.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "promotions.coupons.read": {
        "label": "View Coupons",
        "risk": "low",
        "actions": ["read"],
        "description": "View coupon configurations and usage history.",
    },
    "promotions.coupons.manage": {
        "label": "Manage Coupons",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and manage discount coupons and promo codes.",
    },
    "promotions.campaigns.read": {
        "label": "View Campaigns",
        "risk": "low",
        "actions": ["read"],
        "description": "View promotion campaigns and their performance.",
    },
    "promotions.campaigns.manage": {
        "label": "Manage Campaigns",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create and manage promotion campaigns and marketing automation.",
    },
    "promotions.engine.configure": {
        "label": "Configure Promotion Engine",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Configure promotion engine rules, eligibility, and discount stacking.",
    },
    "promotions.discounts.read": {
        "label": "View Discounts",
        "risk": "low",
        "actions": ["read"],
        "description": "View active discounts and pricing rules.",
    },
    "promotions.discounts.manage": {
        "label": "Manage Discounts",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create and manage discount rules and automatic price adjustments.",
    },
    "promotions.analytics": {
        "label": "Promotion Analytics",
        "risk": "low",
        "actions": ["read"],
        "description": "View promotion performance analytics and conversion metrics.",
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
