"""Audit domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The audit domain owns audit-log and compliance entities. It publishes events
when audit records are created so downstream domains may react.
"""
from __future__ import annotations

from infrastructure.messaging.events.event_bus import publish

EVENT_AUDIT_TRAIL_CREATED = "audit.trail.created"
EVENT_AUDIT_TRAIL_EXPORTED = "audit.trail.exported"
EVENT_COMPLIANCE_CHECK_RUN = "audit.compliance.check_run"
EVENT_DATA_RESIDENCY_VIOLATION = "audit.data_residency.violation"


def publish_audit_trail_created(trail_id: int, actor_id: int, action: str, country_code: str | None = None) -> None:
    publish(EVENT_AUDIT_TRAIL_CREATED, {
        "trail_id": trail_id, "actor_id": actor_id, "action": action, "country_code": country_code,
    })


def publish_audit_trail_exported(trail_id: int, exported_by: int) -> None:
    publish(EVENT_AUDIT_TRAIL_EXPORTED, {"trail_id": trail_id, "exported_by": exported_by})


def publish_compliance_check_run(check_id: int, domain: str, passed: bool) -> None:
    publish(EVENT_COMPLIANCE_CHECK_RUN, {"check_id": check_id, "domain": domain, "passed": passed})


def publish_data_residency_violation(resource_type: str, resource_id: int, country_code: str) -> None:
    publish(EVENT_DATA_RESIDENCY_VIOLATION, {
        "resource_type": resource_type, "resource_id": resource_id, "country_code": country_code,
    })


__all__ = [
    "EVENT_AUDIT_TRAIL_CREATED",
    "EVENT_AUDIT_TRAIL_EXPORTED",
    "EVENT_COMPLIANCE_CHECK_RUN",
    "EVENT_DATA_RESIDENCY_VIOLATION",
    "publish_audit_trail_created",
    "publish_audit_trail_exported",
    "publish_compliance_check_run",
    "publish_data_residency_violation",
]

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# constants merged from services/
EVENT_ANOMALY_DETECTED = "audit.anomaly.detected"
EVENT_AUDIT_LOGGED = "audit.logged"
EVENT_COMPLIANCE_VIOLATION = "audit.compliance.violation"

# base classes merged from services/
class AuditEvent:
    """Base class for all audit-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# derived classes merged from services/
class AnomalyDetected(AuditEvent):
    anomaly_type: str = ""
    severity: str = ""
    target_domain: str = ""
    target_id: Optional[int] = None
    description: str = ""
    event_type: str = field(default=EVENT_ANOMALY_DETECTED, init=False)
class AuditLogged(AuditEvent):
    audit_id: int = 0
    action: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    event_type: str = field(default=EVENT_AUDIT_LOGGED, init=False)
class ComplianceViolation(AuditEvent):
    violation_type: str = ""
    regulation: str = ""
    entity_type: str = ""
    entity_id: Optional[int] = None
    severity: str = ""
    event_type: str = field(default=EVENT_COMPLIANCE_VIOLATION, init=False)

# functions merged from services/
def publish_anomaly_detected(anomaly_type: str, severity: str, target_domain: str, target_id: Optional[int] = None, description: str = "") -> None:
    """Publish an AnomalyDetected event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = AnomalyDetected(anomaly_type=anomaly_type, severity=severity, target_domain=target_domain, target_id=target_id, description=description)
        publish(EVENT_ANOMALY_DETECTED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish AnomalyDetected event: %s", exc)
def publish_audit_logged(audit_id: int, action: str, entity_type: str, entity_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """Publish an AuditLogged event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = AuditLogged(audit_id=audit_id, action=action, entity_type=entity_type, entity_id=entity_id, user_id=user_id)
        publish(EVENT_AUDIT_LOGGED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish AuditLogged event: %s", exc)
def publish_compliance_violation(violation_type: str, regulation: str, entity_type: str, entity_id: Optional[int] = None, severity: str = "") -> None:
    """Publish a ComplianceViolation event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ComplianceViolation(violation_type=violation_type, regulation=regulation, entity_type=entity_type, entity_id=entity_id, severity=severity)
        publish(EVENT_COMPLIANCE_VIOLATION, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish ComplianceViolation event: %s", exc)
