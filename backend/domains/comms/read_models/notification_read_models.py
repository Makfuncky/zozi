"""CQRS-lite read-model projections for the ``comms`` domain.

These are thin, read-optimised views built from the write-side ORM models.
They are the sanctioned surface that cross-domain consumers project from
(ARCHITECTURE_DIAGRAM.md §3 / RESOLVER §11.3 COMMS-STRUCT) instead of
traversing write-model relationships. Kept dependency-free (no service or
port imports) so they remain safe to construct anywhere.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from domains.comms.models.communication import Notification, InternalMessage


@dataclass
class NotificationProjection:
    """Flattened, read-optimised view of a :class:`Notification`."""

    id: int
    user_id: int
    type: Optional[str]
    title: str
    message: str
    channel: str
    priority: str
    is_read: bool
    status: str
    link: Optional[str]
    created_at: Optional[str]

    @classmethod
    def from_orm(cls, n: "Notification") -> "NotificationProjection":
        return cls(
            id=n.id,
            user_id=n.user_id,
            type=n.type,
            title=n.title,
            message=n.message,
            channel=n.channel or "in_app",
            priority=n.priority or "medium",
            is_read=bool(n.is_read),
            status=n.status or "delivered",
            link=n.link,
            created_at=n.created_at.isoformat() if n.created_at else None,
        )


@dataclass
class InboxItemProjection:
    """A unified inbox row spanning chat / internal-channel messages."""

    id: int
    transport: str
    title: str
    preview: str
    unread: bool
    updated_at: Optional[str]
    channel_type: str = "group"

    @classmethod
    def from_internal_message(cls, m: "InternalMessage") -> "InboxItemProjection":
        return cls(
            id=m.id,
            transport="internal",
            title=getattr(m.channel, "name", "channel") if m.channel else "channel",
            preview=(m.message or "")[:120],
            unread=bool(m.read_at is None),
            updated_at=m.created_at.isoformat() if m.created_at else None,
            channel_type="group",
        )


@dataclass
class CommandCenterNotificationProjection:
    """Aggregated notification counters for the command-center read view."""

    total: int = 0
    unread: int = 0
    by_priority: dict = field(default_factory=dict)

    @classmethod
    def aggregate(cls, notifications: List["Notification"]) -> "CommandCenterNotificationProjection":
        total = len(notifications)
        unread = sum(1 for n in notifications if not n.is_read)
        by_priority: dict = {}
        for n in notifications:
            prio = n.priority or "medium"
            by_priority[prio] = by_priority.get(prio, 0) + 1
        return cls(total=total, unread=unread, by_priority=by_priority)