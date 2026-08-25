"""Feature atoms for governance domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the governance domain. CI must fail on any
``require_feature("governance.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "governance.roles.read": {
        "label": "View Roles",
        "risk": "low",
        "actions": ["read"],
        "description": "View governance roles and their permission assignments.",
    },
    "governance.roles.manage": {
        "label": "Manage Roles",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and delete governance roles and assign permissions.",
    },
    "governance.permissions.read": {
        "label": "View Permissions",
        "risk": "low",
        "actions": ["read"],
        "description": "View the permission catalog and feature registry.",
    },
    "governance.permissions.assign": {
        "label": "Assign Permissions",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Assign and revoke permissions to roles and users.",
    },
    "governance.policies.read": {
        "label": "View Policies",
        "risk": "low",
        "actions": ["read"],
        "description": "View governance policies, terms, and acceptable use agreements.",
    },
    "governance.policies.manage": {
        "label": "Manage Policies",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create and manage governance policies and compliance frameworks.",
    },
    "governance.user.ban": {
        "label": "Ban/Suspend Users",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Ban or suspend user accounts for policy violations.",
    },
    "governance.moderation": {
        "label": "Content Moderation",
        "risk": "medium",
        "actions": ["read", "update", "delete"],
        "description": "Moderate user-generated content and enforce community guidelines.",
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
