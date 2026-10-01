"""Security domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the security domain. CI must fail on any
``require_feature("security.*")`` literal not present in this map.

Seeded from the security-facing service surface: sessions, MFA, API keys,
security policies, threat detection, and incident response.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "security.read": {
        "label": "View Security",
        "risk": "medium",
        "actions": ["read"],
        "description": "View security events, alerts, and security dashboard.",
    },
    "security.events.read": {
        "label": "View Security Events",
        "risk": "medium",
        "actions": ["read"],
        "description": "View security events, alerts, and anomaly detections.",
    },
    "security.events.manage": {
        "label": "Manage Security Events",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage security events, triage alerts, and assign incidents.",
    },
    "security.sessions.read": {
        "label": "View Sessions",
        "risk": "medium",
        "actions": ["read"],
        "description": "View active user sessions and session history.",
    },
    "security.sessions.manage": {
        "label": "Manage Sessions",
        "risk": "high",
        "actions": ["read", "update", "delete"],
        "description": "Revoke and manage active user sessions.",
    },
    "security.mfa.manage": {
        "label": "Manage MFA",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage multi-factor authentication policies and user MFA.",
    },
    "security.api_keys.read": {
        "label": "View API Keys",
        "risk": "medium",
        "actions": ["read"],
        "description": "View API keys and their permissions.",
    },
    "security.api_keys.manage": {
        "label": "Manage API Keys",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and revoke API keys and tokens.",
    },
    "security.policies.read": {
        "label": "View Security Policies",
        "risk": "medium",
        "actions": ["read"],
        "description": "View security policies and access control rules.",
    },
    "security.policies.manage": {
        "label": "Manage Security Policies",
        "risk": "critical",
        "actions": ["read", "create", "update", "delete"],
        "description": "Manage security policies, password rules, and access controls.",
    },
    "security.incident.read": {
        "label": "View Security Incidents",
        "risk": "high",
        "actions": ["read"],
        "description": "View security incidents and investigation details.",
    },
    "security.incident.manage": {
        "label": "Manage Security Incidents",
        "risk": "critical",
        "actions": ["read", "create", "update", "approve"],
        "description": "Manage security incidents, response actions, and resolution.",
    },
    # ── Fraud detection atoms (from services/features.py) ─────────────────────
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
    # ── Threat monitoring atoms (from services/features.py) ────────────────────
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
    """Return all security feature atom identifiers, sorted."""
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    """Return True if ``feature`` is a known security feature atom (supports wildcard)."""
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
