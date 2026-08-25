"""Audit domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# Canonical event type constants (shared contract)
EVENT_AUDIT_LOGGED = "audit.logged"
EVENT_ANOMALY_DETECTED = "audit.anomaly.detected"
EVENT_COMPLIANCE_VIOLATION = "audit.compliance.violation"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AuditEvent:
    """Base class for all audit-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.utcnow(), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# ── audit log events ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class AuditLogged(AuditEvent):
    audit_id: int = 0
    action: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    event_type: str = field(default=EVENT_AUDIT_LOGGED, init=False)

# ── anomaly events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class AnomalyDetected(AuditEvent):
    anomaly_type: str = ""
    severity: str = ""
    target_domain: str = ""
    target_id: Optional[int] = None
    description: str = ""
    event_type: str = field(default=EVENT_ANOMALY_DETECTED, init=False)

# ── compliance events ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class ComplianceViolation(AuditEvent):
    violation_type: str = ""
    regulation: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None
    severity: str = ""
    event_type: str = field(default=EVENT_COMPLIANCE_VIOLATION, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_audit_logged(audit_id: int, action: str, entity_type: str, entity_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """Publish an AuditLogged event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = AuditLogged(audit_id=audit_id, action=action, entity_type=entity_type, entity_id=entity_id, user_id=user_id)
        publish(EVENT_AUDIT_LOGGED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_anomaly_detected(anomaly_type: str, severity: str, target_domain: str, target_id: Optional[int] = None, description: str = "") -> None:
    """Publish an AnomalyDetected event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = AnomalyDetected(anomaly_type=anomaly_type, severity=severity, target_domain=target_domain, target_id=target_id, description=description)
        publish(EVENT_ANOMALY_DETECTED, event.serialize())
    except Exception:
        pass

def publish_compliance_violation(violation_type: str, regulation: str, entity_type: str, entity_id: Optional[int] = None, severity: str = "") -> None:
    """Publish a ComplianceViolation event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ComplianceViolation(violation_type=violation_type, regulation=regulation, entity_type=entity_type, entity_id=entity_id, severity=severity)
        publish(EVENT_COMPLIANCE_VIOLATION, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_AUDIT_LOGGED",
    "EVENT_ANOMALY_DETECTED",
    "EVENT_COMPLIANCE_VIOLATION",
    # Event classes
    "AuditEvent",
    "AuditLogged",
    "AnomalyDetected",
    "ComplianceViolation",
    # Publish helpers
    "publish_audit_logged",
    "publish_anomaly_detected",
    "publish_compliance_violation",
]
