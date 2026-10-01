"""Orders domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the orders domain. CI must fail on any
``require_feature("orders.*")`` literal that is not present in this map.
"""
from __future__ import annotations

FEATURES: dict[str, dict] = {
    "orders.list": {
        "label": "List Orders",
        "risk": "low",
        "actions": ["read"],
        "description": "List and browse orders with filtering and pagination.",
    },
    "orders.read": {
        "label": "View Orders",
        "risk": "low",
        "actions": ["read"],
        "description": "View order details and order history.",
    },
    "orders.write": {
        "label": "Write Orders",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create orders, update order status, and modify order fields.",
    },
    "orders.create": {
        "label": "Create Orders",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Create new orders and initiate checkout.",
    },
    "orders.manage": {
        "label": "Manage Orders",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Update order status, modify orders, and manage fulfillment.",
    },
    "orders.cancel": {
        "label": "Cancel Orders",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Cancel orders and process order cancellations.",
    },
    "orders.fulfill": {
        "label": "Fulfill Orders",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Manage order fulfillment, shipping status, and delivery tracking.",
    },
    "orders.returns.read": {
        "label": "View Returns",
        "risk": "low",
        "actions": ["read"],
        "description": "View return requests and return history.",
    },
    "orders.returns.manage": {
        "label": "Manage Returns",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Approve, reject, and process return requests and refunds.",
    },
    "orders.export": {
        "label": "Export Orders",
        "risk": "low",
        "actions": ["read"],
        "description": "Export order data and reports for analytics.",
    },
    "orders.update": {
        "label": "Update Orders",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Update order fields, status, and metadata.",
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
