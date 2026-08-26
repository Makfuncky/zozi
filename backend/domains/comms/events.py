"""comms domain — typed cross-domain events (Law 3).

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
EVENT_NOTIFICATION_CREATED = "comms.notification.created"
EVENT_TICKET_REPLIED = "comms.ticket.replied"
EVENT_TICKET_STATUS_CHANGED = "comms.ticket.status_changed"
EVENT_EMAIL_CAMPAIGN_CREATED = "comms.campaign.created"
EVENT_EMAIL_CAMPAIGN_SENT = "comms.campaign.sent"
EVENT_ESCALATION_TRIGGERED = "comms.escalation.triggered"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CommsEvent:
    """Base class for all comms-domain events."""

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

# ── notification events ───────────────────────────────────────────────────

@dataclass(frozen=True)
class NotificationCreated(CommsEvent):
    notification_id: int = 0
    user_id: int = 0
    type: Optional[str] = None
    title: str = ""
    channel: str = "in_app"
    event_type: str = field(default=EVENT_NOTIFICATION_CREATED, init=False)

@dataclass(frozen=True)
class TicketReplied(CommsEvent):
    ticket_id: int = 0
    message_id: int = 0
    sender_id: int = 0
    is_admin: bool = False
    event_type: str = field(default=EVENT_TICKET_REPLIED, init=False)

@dataclass(frozen=True)
class TicketStatusChanged(CommsEvent):
    ticket_id: int = 0
    old_status: str = ""
    new_status: str = ""
    changed_by: int = 0
    event_type: str = field(default=EVENT_TICKET_STATUS_CHANGED, init=False)

# ── chat / messaging events ───────────────────────────────────────────────

@dataclass(frozen=True)
class EmailCampaignCreated(CommsEvent):
    campaign_id: int = 0
    name: str = ""
    created_by: int = 0
    event_type: str = field(default=EVENT_EMAIL_CAMPAIGN_CREATED, init=False)

@dataclass(frozen=True)
class EmailCampaignSent(CommsEvent):
    campaign_id: int = 0
    recipient_count: int = 0
    event_type: str = field(default=EVENT_EMAIL_CAMPAIGN_SENT, init=False)

@dataclass(frozen=True)
class EscalationTriggered(CommsEvent):
    sla_log_id: int = 0
    message_type: str = ""
    escalated_to_role: str = ""
    priority: str = ""
    event_type: str = field(default=EVENT_ESCALATION_TRIGGERED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_notification_created(notification_id: int, user_id: int, type_: str, title: str, channel: str = "in_app") -> None:
    """Publish a NotificationCreated event to the canonical event bus."""
    try:
        from infrastructure.utils.event_bus import publish
        event = NotificationCreated(notification_id=notification_id, user_id=user_id, type=type_, title=title, channel=channel)
        publish(EVENT_NOTIFICATION_CREATED, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_ticket_replied(ticket_id: int, message_id: int, sender_id: int, is_admin: bool) -> None:
    """Publish a TicketReplied event."""
    try:
        from infrastructure.utils.event_bus import publish
        event = TicketReplied(ticket_id=ticket_id, message_id=message_id, sender_id=sender_id, is_admin=is_admin)
        publish(EVENT_TICKET_REPLIED, event.serialize())
    except Exception:
        pass

def publish_ticket_status_changed(ticket_id: int, old_status: str, new_status: str, changed_by: int) -> None:
    """Publish a TicketStatusChanged event."""
    try:
        from infrastructure.utils.event_bus import publish
        event = TicketStatusChanged(ticket_id=ticket_id, old_status=old_status, new_status=new_status, changed_by=changed_by)
        publish(EVENT_TICKET_STATUS_CHANGED, event.serialize())
    except Exception:
        pass

def publish_email_campaign_created(campaign_id: int, name: str, created_by: int) -> None:
    """Publish an EmailCampaignCreated event."""
    try:
        from infrastructure.utils.event_bus import publish
        event = EmailCampaignCreated(campaign_id=campaign_id, name=name, created_by=created_by)
        publish(EVENT_EMAIL_CAMPAIGN_CREATED, event.serialize())
    except Exception:
        pass

def publish_email_campaign_sent(campaign_id: int, recipient_count: int) -> None:
    """Publish an EmailCampaignSent event."""
    try:
        from infrastructure.utils.event_bus import publish
        event = EmailCampaignSent(campaign_id=campaign_id, recipient_count=recipient_count)
        publish(EVENT_EMAIL_CAMPAIGN_SENT, event.serialize())
    except Exception:
        pass

def publish_escalation_triggered(sla_log_id: int, message_type: str, escalated_to_role: str, priority: str) -> None:
    """Publish an EscalationTriggered event."""
    try:
        from infrastructure.utils.event_bus import publish
        event = EscalationTriggered(sla_log_id=sla_log_id, message_type=message_type, escalated_to_role=escalated_to_role, priority=priority)
        publish(EVENT_ESCALATION_TRIGGERED, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_NOTIFICATION_CREATED",
    "EVENT_TICKET_REPLIED",
    "EVENT_TICKET_STATUS_CHANGED",
    "EVENT_EMAIL_CAMPAIGN_CREATED",
    "EVENT_EMAIL_CAMPAIGN_SENT",
    "EVENT_ESCALATION_TRIGGERED",
    # Event classes
    "CommsEvent",
    "NotificationCreated",
    "TicketReplied",
    "TicketStatusChanged",
    "EmailCampaignCreated",
    "EmailCampaignSent",
    "EscalationTriggered",
    # Publish helpers
    "publish_notification_created",
    "publish_ticket_replied",
    "publish_ticket_status_changed",
    "publish_email_campaign_created",
    "publish_email_campaign_sent",
    "publish_escalation_triggered",
]
