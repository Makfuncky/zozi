"""Notification authorization policies."""
from __future__ import annotations


class NotificationPolicy:
    """Authorization policies for notification operations."""

    @staticmethod
    def can_send_notification(actor: dict, recipient_id: int) -> bool:
        """Check if actor can send a notification to recipient."""
        # Admin can send to anyone
        if actor.get("role") in ("admin", "super_admin"):
            return True
        # Users can send to themselves
        return actor.get("user_id") == recipient_id

    @staticmethod
    def can_read_notifications(actor: dict, user_id: int) -> bool:
        """Check if actor can read notifications for a user."""
        # Admin can read anyone's notifications
        if actor.get("role") in ("admin", "super_admin"):
            return True
        # Users can read their own notifications
        return actor.get("user_id") == user_id

    @staticmethod
    def can_register_push_token(actor: dict) -> bool:
        """Check if actor can register a push token."""
        return True  # Any authenticated user
