"""Logistics domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the logistics domain. CI must fail on any
``require_feature("logistics.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "logistics.shipping.tracking": {
        "label": "Track Shipments",
        "risk": "low",
        "actions": ["read"],
        "description": "View shipment tracking information and delivery status updates.",
    },
    "logistics.delivery.estimates": {
        "label": "View Delivery Estimates",
        "risk": "low",
        "actions": ["read"],
        "description": "View estimated delivery dates and transit time calculations.",
    },
    "logistics.shipping.manage": {
        "label": "Manage Shipping",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create and update shipments, manage carriers and shipping methods.",
    },
    "logistics.fulfillment.manage": {
        "label": "Manage Fulfillment",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Manage fulfillment centers, inventory allocation, and order processing.",
    },
    "logistics.partners.manage": {
        "label": "Manage Logistics Partners",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Manage third-party logistics partners, contracts, and service agreements.",
    },
    "logistics.sla.manage": {
        "label": "Manage Logistics SLA",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Configure service-level agreements for shipping and delivery.",
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
