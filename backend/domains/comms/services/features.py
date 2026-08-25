"""Feature atoms for comms domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the comms domain. CI must fail on any
``require_feature("comms.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "comms.messages.read": {
        "label": "Read Messages",
        "risk": "low",
        "actions": ["read"],
        "description": "View messages in rooms the user has access to.",
    },
    "comms.messages.send": {
        "label": "Send Messages",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Send messages in chat rooms and conversations.",
    },
    "comms.tickets.read": {
        "label": "View Support Tickets",
        "risk": "low",
        "actions": ["read"],
        "description": "View support tickets and their status.",
    },
    "comms.tickets.create": {
        "label": "Create Support Tickets",
        "risk": "low",
        "actions": ["read", "create"],
        "description": "Create new support tickets and inquiries.",
    },
    "comms.tickets.manage": {
        "label": "Manage Support Tickets",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Full management of support tickets including assignment and resolution.",
    },
    "comms.notifications.read": {
        "label": "View Notifications",
        "risk": "low",
        "actions": ["read"],
        "description": "View personal notifications and alerts.",
    },
    "comms.notifications.send": {
        "label": "Send Notifications",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Send notifications to users via in-app, email, or SMS channels.",
    },
    "comms.broadcast": {
        "label": "Send Broadcasts",
        "risk": "high",
        "actions": ["read", "create"],
        "description": "Send broadcast messages and notifications to user segments.",
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
