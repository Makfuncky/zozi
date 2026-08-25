"""Security domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The security domain owns verification and threat-detection entities. It
publishes events when security-relevant actions occur so downstream domains
may react.
"""
from __future__ import annotations

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
