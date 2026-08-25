"""Security domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the security domain. CI must fail on any
``require_feature("security.*")`` literal that is not present in this map.

Service-level features for fraud detection and threat monitoring subsystems.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "fraud.detection.view": {
        "label": "View Fraud Detection",
        "risk": "medium",
        "actions": ["read"],
        "description": "View fraud detection alerts, risk scores, and investigation queues.",
    },
    "fraud.detection.manage": {
        "label": "Manage Fraud Detection",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Configure fraud rules, manage detection models, and override risk decisions.",
    },
    "fraud.investigation": {
        "label": "Fraud Investigation",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Investigate fraud cases, add case notes, and resolve investigations.",
    },
    "threat.monitoring.view": {
        "label": "View Threat Monitoring",
        "risk": "medium",
        "actions": ["read"],
        "description": "View threat intelligence feeds, active threats, and security dashboards.",
    },
    "threat.monitoring.manage": {
        "label": "Manage Threat Monitoring",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Configure threat detection rules, manage threat feeds, and respond to incidents.",
    },
    "threat.response": {
        "label": "Threat Response",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Execute threat response actions: block, quarantine, or escalate threats.",
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
