"""Comms domain — typed cross-domain events (Law 3).

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
EVENT_MESSAGE_SENT = "comms.message.sent"
EVENT_TICKET_CREATED = "comms.ticket.created"
EVENT_NOTIFICATION_SENT = "comms.notification.sent"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class CommsServiceEvent:
    """Base class for all comms-domain service-level events."""

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

# ── messaging events ──────────────────────────────────────────────────────

@dataclass(frozen=True)
class MessageSent(CommsServiceEvent):
    message_id: int = 0
    sender_id: int = 0
    room_id: int = 0
    room_type: str = ""
    event_type: str = field(default=EVENT_MESSAGE_SENT, init=False)

# ── ticket events ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class TicketCreated(CommsServiceEvent):
    ticket_id: int = 0
    created_by: int = 0
    category: str = ""
    priority: str = "medium"
    event_type: str = field(default=EVENT_TICKET_CREATED, init=False)

# ── notification events ───────────────────────────────────────────────────

@dataclass(frozen=True)
class NotificationSent(CommsServiceEvent):
    notification_id: int = 0
    user_id: int = 0
    channel: str = "in_app"
    type: str = ""
    event_type: str = field(default=EVENT_NOTIFICATION_SENT, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_message_sent(message_id: int, sender_id: int, room_id: int, room_type: str) -> None:
    """Publish a MessageSent event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = MessageSent(message_id=message_id, sender_id=sender_id, room_id=room_id, room_type=room_type)
        publish(EVENT_MESSAGE_SENT, event.serialize())
    except Exception:
        pass  # Event publishing is best-effort

def publish_ticket_created(ticket_id: int, created_by: int, category: str, priority: str = "medium") -> None:
    """Publish a TicketCreated event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = TicketCreated(ticket_id=ticket_id, created_by=created_by, category=category, priority=priority)
        publish(EVENT_TICKET_CREATED, event.serialize())
    except Exception:
        pass

def publish_notification_sent(notification_id: int, user_id: int, channel: str, type_: str) -> None:
    """Publish a NotificationSent event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = NotificationSent(notification_id=notification_id, user_id=user_id, channel=channel, type=type_)
        publish(EVENT_NOTIFICATION_SENT, event.serialize())
    except Exception:
        pass

__all__ = [
    # Event type constants
    "EVENT_MESSAGE_SENT",
    "EVENT_TICKET_CREATED",
    "EVENT_NOTIFICATION_SENT",
    # Event classes
    "CommsServiceEvent",
    "MessageSent",
    "TicketCreated",
    "NotificationSent",
    # Publish helpers
    "publish_message_sent",
    "publish_ticket_created",
    "publish_notification_sent",
]
