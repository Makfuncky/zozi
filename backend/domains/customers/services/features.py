"""Customers domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the customers domain. CI must fail on any
``require_feature("customers.*")`` literal that is not present in this map.

Service-level features for reviews, referrals, wishlist, and coins subsystems.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "customers.reviews.write": {
        "label": "Write Reviews",
        "risk": "low",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and soft-delete product reviews; read product review listings.",
    },
    "customers.reviews.moderate": {
        "label": "Moderate Reviews",
        "risk": "medium",
        "actions": ["read", "update", "delete"],
        "description": "Approve, reject, or remove product reviews (staff).",
    },
    "customers.referrals.manage": {
        "label": "Manage Referrals",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "View referral config and get/create the authenticated customer's referral code.",
    },
    "customers.referrals.view": {
        "label": "View Referrals",
        "risk": "low",
        "actions": ["read"],
        "description": "View own referral history, earnings, and referred users.",
    },
    "customers.wishlist.manage": {
        "label": "Manage Wishlist",
        "risk": "low",
        "actions": ["read", "create", "delete"],
        "description": "Add and remove wishlist items; clear the wishlist.",
    },
    "customers.wishlist.view": {
        "label": "View Wishlist",
        "risk": "low",
        "actions": ["read"],
        "description": "View own wishlist items and share settings.",
    },
    "coins.earn": {
        "label": "Earn Coins",
        "risk": "low",
        "actions": ["read"],
        "description": "View coin balance, earn history, and earning opportunities.",
    },
    "coins.redeem": {
        "label": "Redeem Coins",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Redeem Zozi coins for discounts, rewards, or order credits.",
    },
    "coins.manage": {
        "label": "Manage Coins (Admin)",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Administer coin programs, adjust balances, and configure earning rules.",
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
