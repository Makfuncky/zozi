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
