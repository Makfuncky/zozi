"""Security domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The security domain owns verification and threat-detection entities. It
publishes events when security-relevant actions occur so downstream domains
may react.
"""

from infrastructure.messaging.events.event_bus import publish

EVENT_THREAT_DETECTED = "security.threat.detected"
EVENT_DOCUMENT_VERIFIED = "security.document.verified"
EVENT_KYC_COMPLETED = "security.kyc.completed"
EVENT_FRAUD_ALERT = "security.fraud.alert"


def publish_threat_detected(threat_type: str, severity: str, actor_id: int | None = None) -> None:
    publish(EVENT_THREAT_DETECTED, {
        "threat_type": threat_type, "severity": severity, "actor_id": actor_id,
    })


def publish_document_verified(verification_id: int, user_id: int, document_type: str) -> None:
    publish(EVENT_DOCUMENT_VERIFIED, {
        "verification_id": verification_id, "user_id": user_id, "document_type": document_type,
    })


def publish_kyc_completed(user_id: int, status: str) -> None:
    publish(EVENT_KYC_COMPLETED, {"user_id": user_id, "status": status})


def publish_fraud_alert(alert_id: int, order_id: int | None = None, risk_score: float = 0.0) -> None:
    publish(EVENT_FRAUD_ALERT, {"alert_id": alert_id, "order_id": order_id, "risk_score": risk_score})


__all__ = [
    "EVENT_THREAT_DETECTED",
    "EVENT_DOCUMENT_VERIFIED",
    "EVENT_KYC_COMPLETED",
    "EVENT_FRAUD_ALERT",
    "publish_threat_detected",
    "publish_document_verified",
    "publish_kyc_completed",
    "publish_fraud_alert",
]

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# constants merged from services/
EVENT_FRAUD_DETECTED = "security.fraud.detected"
EVENT_SECURITY_ALERT = "security.alert.triggered"
EVENT_THREAT_IDENTIFIED = "security.threat.identified"

# base classes merged from services/
class SecurityEvent:
    """Base class for all security-domain events."""

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
class FraudDetected(SecurityEvent):
    alert_id: int = 0
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    risk_score: float = 0.0
    reason: str = ""
    event_type: str = field(default=EVENT_FRAUD_DETECTED, init=False)
class SecurityAlert(SecurityEvent):
    alert_type: str = ""
    severity: str = ""
    message: str = ""
    target_domain: str = ""
    target_id: Optional[int] = None
    event_type: str = field(default=EVENT_SECURITY_ALERT, init=False)
class ThreatIdentified(SecurityEvent):
    threat_type: str = ""
    severity: str = ""
    source_ip: str = ""
    actor_id: Optional[int] = None
    event_type: str = field(default=EVENT_THREAT_IDENTIFIED, init=False)

# functions merged from services/
def publish_fraud_detected(alert_id: int, risk_score: float, reason: str, order_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """Publish a FraudDetected event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = FraudDetected(alert_id=alert_id, order_id=order_id, user_id=user_id, risk_score=risk_score, reason=reason)
        publish(EVENT_FRAUD_DETECTED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish FraudDetected event: %s", exc)
def publish_security_alert(alert_type: str, severity: str, message: str, target_domain: str = "", target_id: Optional[int] = None) -> None:
    """Publish a SecurityAlert event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SecurityAlert(alert_type=alert_type, severity=severity, message=message, target_domain=target_domain, target_id=target_id)
        publish(EVENT_SECURITY_ALERT, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish SecurityAlert event: %s", exc)
def publish_threat_identified(threat_type: str, severity: str, source_ip: str, actor_id: Optional[int] = None) -> None:
    """Publish a ThreatIdentified event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ThreatIdentified(threat_type=threat_type, severity=severity, source_ip=source_ip, actor_id=actor_id)
        publish(EVENT_THREAT_IDENTIFIED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish ThreatIdentified event: %s", exc)
