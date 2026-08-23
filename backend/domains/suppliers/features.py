"""suppliers domain - AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the suppliers domain. CI must fail on any
``require_feature("suppliers.*")`` literal that is not present in this map.

Seeded from the supplier-facing service surface: registration, verification,
profile, products, orders, documents, badges, analytics, payouts, health,
legal contracts, and bulk operations.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "suppliers.registration.manage": {
        "label": "Manage Supplier Registration",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Register new suppliers and manage onboarding pipeline state.",
    },
    "suppliers.verification.manage": {
        "label": "Manage Supplier Verification",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Verify, reject, suspend, and reactivate supplier accounts (admin).",
    },
    "suppliers.profile.manage": {
        "label": "Manage Supplier Profile",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Create and update supplier business profiles and storefront settings.",
    },
    "suppliers.products.manage": {
        "label": "Manage Supplier Products",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, delete, and bulk-upload supplier product listings.",
    },
    "suppliers.orders.manage": {
        "label": "Manage Supplier Orders",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "View and update status of orders containing supplier products.",
    },
    "suppliers.documents.manage": {
        "label": "Manage Supplier Documents",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Upload, list, and review supplier verification documents.",
    },
    "suppliers.badges.manage": {
        "label": "Manage Supplier Badges",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Assign, update, and revoke supplier badge tiers and billing.",
    },
    "suppliers.analytics.view": {
        "label": "View Supplier Analytics",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier sales, revenue, and performance analytics.",
    },
    "suppliers.payouts.manage": {
        "label": "Manage Supplier Payouts",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Request, approve, and process supplier payouts and settlements.",
    },
    "suppliers.health.view": {
        "label": "View Supplier Health",
        "risk": "low",
        "actions": ["read"],
        "description": "View supplier health scores and trust indicators.",
    },
    "suppliers.contracts.manage": {
        "label": "Manage Supplier Legal Contracts",
        "risk": "high",
        "actions": ["read", "create"],
        "description": "Generate and manage supplier legal contracts and terms.",
    },
    "suppliers.bulk.operations": {
        "label": "Execute Bulk Supplier Operations",
        "risk": "high",
        "actions": ["create", "update", "delete"],
        "description": "Execute bulk verify, reject, badge, and lifecycle operations on suppliers.",
    },
}


def all_features() -> list[str]:
    """Return all supplier feature atom identifiers, sorted."""
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    """Return True if ``feature`` is a known supplier feature atom (supports wildcard)."""
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
