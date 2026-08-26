"""Security domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# Canonical event type constants (shared contract)
EVENT_FRAUD_DETECTED = "security.fraud.detected"
EVENT_THREAT_IDENTIFIED = "security.threat.identified"
EVENT_SECURITY_ALERT = "security.alert.triggered"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
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

# ── fraud events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FraudDetected(SecurityEvent):
    alert_id: int = 0
    order_id: Optional[int] = None
    user_id: Optional[int] = None
    risk_score: float = 0.0
    reason: str = ""
    event_type: str = field(default=EVENT_FRAUD_DETECTED, init=False)

# ── threat events ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ThreatIdentified(SecurityEvent):
    threat_type: str = ""
    severity: str = ""
    source_ip: str = ""
    actor_id: Optional[int] = None
    event_type: str = field(default=EVENT_THREAT_IDENTIFIED, init=False)

# ── alert events ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SecurityAlert(SecurityEvent):
    alert_type: str = ""
    severity: str = ""
    message: str = ""
    target_domain: str = ""
    target_id: Optional[int] = None
    event_type: str = field(default=EVENT_SECURITY_ALERT, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_fraud_detected(alert_id: int, risk_score: float, reason: str, order_id: Optional[int] = None, user_id: Optional[int] = None) -> None:
    """Publish a FraudDetected event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = FraudDetected(alert_id=alert_id, order_id=order_id, user_id=user_id, risk_score=risk_score, reason=reason)
        publish(EVENT_FRAUD_DETECTED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_threat_identified(threat_type: str, severity: str, source_ip: str, actor_id: Optional[int] = None) -> None:
    """Publish a ThreatIdentified event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = ThreatIdentified(threat_type=threat_type, severity=severity, source_ip=source_ip, actor_id=actor_id)
        publish(EVENT_THREAT_IDENTIFIED, event.serialize())
    except Exception:
        pass

def publish_security_alert(alert_type: str, severity: str, message: str, target_domain: str = "", target_id: Optional[int] = None) -> None:
    """Publish a SecurityAlert event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = SecurityAlert(alert_type=alert_type, severity=severity, message=message, target_domain=target_domain, target_id=target_id)
        publish(EVENT_SECURITY_ALERT, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_FRAUD_DETECTED",
    "EVENT_THREAT_IDENTIFIED",
    "EVENT_SECURITY_ALERT",
    # Event classes
    "SecurityEvent",
    "FraudDetected",
    "ThreatIdentified",
    "SecurityAlert",
    # Publish helpers
    "publish_fraud_detected",
    "publish_threat_identified",
    "publish_security_alert",
]
