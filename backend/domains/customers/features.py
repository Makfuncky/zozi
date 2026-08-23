"""customers domain - AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the customers domain. CI must fail on any
``require_feature("customers.*")`` literal that is not present in this map.

Seeded from the customer-facing service surface: addresses, cart, wishlist,
referrals, reviews, returns, customer profile and customer health.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "customers.address.manage": {
        "label": "Manage Customer Addresses",
        "risk": "low",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, delete, and set default shipping addresses for the authenticated customer.",
    },
    "customers.cart.manage": {
        "label": "Manage Cart",
        "risk": "low",
        "actions": ["read", "create", "update", "delete"],
        "description": "Add, update, remove, clear, and sync server-side cart items.",
    },
    "customers.wishlist.manage": {
        "label": "Manage Wishlist",
        "risk": "low",
        "actions": ["read", "create", "delete"],
        "description": "Add and remove wishlist items; clear the wishlist.",
    },
    "customers.referral.manage": {
        "label": "Manage Referrals",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "View referral config and get/create the authenticated customer's referral code.",
    },
    "customers.reviews.write": {
        "label": "Write Reviews",
        "risk": "low",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and soft-delete product reviews; read product review listings.",
    },
    "customers.returns.request": {
        "label": "Request Returns",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "List return requests and create a new return request for an order.",
    },
    "customers.profile.manage": {
        "label": "Manage Customer Profile",
        "risk": "low",
        "actions": ["read", "update"],
        "description": "Read and update the authenticated customer's profile.",
    },
    "customers.health.view": {
        "label": "View Customer Health",
        "risk": "medium",
        "actions": ["read"],
        "description": "View customer health scores and the ranked health list (admin).",
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
