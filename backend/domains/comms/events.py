"""comms domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus (``infrastructure.messaging.event_bus``) can emit
them to subscribers in the same process or, later, over Redis pub/sub.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CommsEvent:
    """Base class for all comms-domain events."""

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

# ── notification events ───────────────────────────────────────────────────

@dataclass(frozen=True)
class NotificationCreated(CommsEvent):
    notification_id: int = 0
    user_id: int = 0
    type: Optional[str] = None
    title: str = ""
    channel: str = "in_app"
    event_type: str = field(default="comms.notification.created", init=False)

@dataclass(frozen=True)
class TicketReplied(CommsEvent):
    ticket_id: int = 0
    message_id: int = 0
    sender_id: int = 0
    is_admin: bool = False
    event_type: str = field(default="comms.ticket.replied", init=False)

@dataclass(frozen=True)
class TicketStatusChanged(CommsEvent):
    ticket_id: int = 0
    old_status: str = ""
    new_status: str = ""
    changed_by: int = 0
    event_type: str = field(default="comms.ticket.status_changed", init=False)

# ── chat / messaging events ───────────────────────────────────────────────

@dataclass(frozen=True)
class EmailCampaignCreated(CommsEvent):
    campaign_id: int = 0
    name: str = ""
    created_by: int = 0
    event_type: str = field(default="comms.campaign.created", init=False)

@dataclass(frozen=True)
class EmailCampaignSent(CommsEvent):
    campaign_id: int = 0
    recipient_count: int = 0
    event_type: str = field(default="comms.campaign.sent", init=False)

@dataclass(frozen=True)
class EscalationTriggered(CommsEvent):
    sla_log_id: int = 0
    message_type: str = ""
    escalated_to_role: str = ""
    priority: str = ""
    event_type: str = field(default="comms.escalation.triggered", init=False)

__all__ = [
    "CommsEvent",
    "NotificationCreated",
    "TicketReplied",
    "TicketStatusChanged",
    "EmailCampaignCreated",
    "EmailCampaignSent",
    "EscalationTriggered",
]
