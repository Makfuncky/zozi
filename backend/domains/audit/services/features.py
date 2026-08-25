"""Feature atoms for audit domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the audit domain. CI must fail on any
``require_feature("audit.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "audit.logs.read": {
        "label": "View Audit Logs",
        "risk": "low",
        "actions": ["read"],
        "description": "View audit trail logs and compliance records.",
    },
    "audit.logs.export": {
        "label": "Export Audit Logs",
        "risk": "medium",
        "actions": ["read"],
        "description": "Export audit log data for compliance reporting.",
    },
    "audit.anomalies.read": {
        "label": "View Anomalies",
        "risk": "low",
        "actions": ["read"],
        "description": "View detected anomalies and suspicious activity alerts.",
    },
    "audit.anomalies.manage": {
        "label": "Manage Anomalies",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Acknowledge, resolve, or escalate anomaly alerts.",
    },
    "audit.compliance.read": {
        "label": "View Compliance Status",
        "risk": "low",
        "actions": ["read"],
        "description": "View compliance violations and regulatory status.",
    },
    "audit.compliance.manage": {
        "label": "Manage Compliance",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage compliance rules, violations, and remediation.",
    },
    "audit.command_center.read": {
        "label": "View Command Center",
        "risk": "low",
        "actions": ["read"],
        "description": "Access command center dashboards and operational views.",
    },
    "audit.command_center.configure": {
        "label": "Configure Command Center",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Configure command center views and dashboard layouts.",
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
