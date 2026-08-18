"""controllers.comms.notification_controller (CONTROLLERS layer).

Wraps ``services.comms.notification_engine`` and exposes the notification
endpoints. The HTTP contract is declared with ``infrastructure.routing.route_contract`` decorators
so ``routers/generated/auto_router.py`` can auto-generate the thin router — the
previous hand-written ``routers/notifications.py`` instantiated the engine,
parsed channel/priority enums inline, and read ``current_user["id"]``; that
orchestration now lives here.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get, post

from domains.comms.services.notification_engine import (
    NotificationChannel,
    NotificationPriority,
    get_notification_engine,
)

def _parse_channel(value: str) -> NotificationChannel:
    try:
        return NotificationChannel(value)
    except ValueError:
        return NotificationChannel.IN_APP

def _parse_priority(value: str) -> NotificationPriority:
    try:
        return NotificationPriority(value)
    except ValueError:
        return NotificationPriority.MEDIUM

@post(
    "/api/v1/notifications/send",
    deps=["user", "db"],
    query=["user_id", "title", "message", "channel", "priority"],
)
def send_notification(
    user_id: int,
    title: str,
    message: str,
    channel: str = "in_app",
    priority: str = "medium",
    current_user: dict = None,
    db: Session = None,
):
    """Send a notification to a user."""
    engine = get_notification_engine(db)
    return engine.send(
        user_id, title, message, _parse_channel(channel), _parse_priority(priority)
    )

@post(
    "/api/v1/notifications/bulk",
    deps=["user", "db"],
    query=["user_ids", "title", "message", "channel", "priority"],
)
def send_bulk_notifications(
    user_ids: list,
    title: str,
    message: str,
    channel: str = "email",
    priority: str = "medium",
    current_user: dict = None,
    db: Session = None,
):
    """Send a bulk notification to many users."""
    engine = get_notification_engine(db)
    return engine.send_bulk(
        user_ids, title, message, _parse_channel(channel), _parse_priority(priority)
    )

@get("/api/v1/notifications", deps=["user", "db"], query=["unread_only"])
def get_notifications(
    unread_only: bool = False,
    current_user: dict = None,
    db: Session = None,
):
    """Return the current user's notifications."""
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.get_user_notifications(user_id, unread_only)

@post("/api/v1/notifications/{notification_id}/read", deps=["user", "db"])
def mark_notification_read(notification_id: int, current_user: dict = None, db: Session = None):
    """Mark a notification as read for the current user."""
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.mark_read(notification_id, user_id)

__all__ = [
    "send_notification",
    "send_bulk_notifications",
    "get_notifications",
    "mark_notification_read",
]
