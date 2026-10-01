"""Audit domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the audit domain. CI must fail on any
``require_feature("audit.*")`` literal not present in this map.

Seeded from the audit-facing service surface: audit logs, compliance reports,
activity trails, and audit configuration.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "audit.read": {
        "label": "View Audit Logs",
        "risk": "medium",
        "actions": ["read"],
        "description": "View audit logs, activity trails, and change history.",
    },
    "audit.logs.read": {
        "label": "View Audit Logs",
        "risk": "medium",
        "actions": ["read"],
        "description": "View detailed audit log entries and filtered audit trails.",
    },
    "audit.logs.export": {
        "label": "Export Audit Logs",
        "risk": "medium",
        "actions": ["read", "create"],
        "description": "Export audit logs and activity trails for compliance.",
    },
    "audit.compliance.read": {
        "label": "View Compliance Reports",
        "risk": "medium",
        "actions": ["read"],
        "description": "View compliance reports and regulatory audit findings.",
    },
    "audit.compliance.manage": {
        "label": "Manage Compliance",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage compliance policies, reports, and audit schedules.",
    },
    "audit.config.read": {
        "label": "View Audit Configuration",
        "risk": "low",
        "actions": ["read"],
        "description": "View audit logging configuration and retention policies.",
    },
    "audit.config.manage": {
        "label": "Manage Audit Configuration",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage audit logging configuration, retention, and rules.",
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
    """Return all audit feature atom identifiers, sorted."""
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    """Return True if ``feature`` is a known audit feature atom (supports wildcard)."""
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
