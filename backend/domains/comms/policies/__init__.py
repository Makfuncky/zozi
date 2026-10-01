"""comms domain — authorization policies."""
from __future__ import annotations


# ── Chat Policy (from chat.py) ───

class ChatPolicy:
    """Authorization policies for chat operations."""

    @staticmethod
    def can_create_thread(actor: dict, entity_type: str, entity_id: int) -> bool:
        if actor.get("role") in ("admin", "super_admin"): return True
        if actor.get("role") == "employee": return True
        return False

    @staticmethod
    def can_send_message(actor: dict, thread_participants: list[int]) -> bool:
        if thread_participants is None: return False
        return actor.get("user_id") in thread_participants

    @staticmethod
    def can_moderate_chat(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin")


# ── Email Policy (from email.py) ───

class EmailPolicy:
    """Authorization policies for email operations."""

    @staticmethod
    def can_send_email(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin", "employee")

    @staticmethod
    def can_create_campaign(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_templates(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_view_email_stats(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin", "employee")


# ── Notification Policy (from notification.py) ───

class NotificationPolicy:
    """Authorization policies for notification operations."""

    @staticmethod
    def can_send_notification(actor: dict, recipient_id: int) -> bool:
        if actor.get("role") in ("admin", "super_admin"): return True
        return actor.get("user_id") == recipient_id

    @staticmethod
    def can_read_notifications(actor: dict, user_id: int) -> bool:
        if actor.get("role") in ("admin", "super_admin"): return True
        return actor.get("user_id") == user_id

    @staticmethod
    def can_register_push_token(actor: dict) -> bool:
        return True


# ── Ticket Policy (from ticket.py) ───

class TicketPolicy:
    """Authorization policies for ticket operations."""

    @staticmethod
    def can_create_ticket(actor: dict) -> bool:
        return True

    @staticmethod
    def can_view_ticket(actor: dict, ticket_user_id: int) -> bool:
        if actor.get("role") in ("admin", "super_admin"): return True
        return actor.get("user_id") == ticket_user_id

    @staticmethod
    def can_reply_to_ticket(actor: dict, ticket_user_id: int) -> bool:
        if actor.get("role") in ("admin", "super_admin"): return True
        return actor.get("user_id") == ticket_user_id

    @staticmethod
    def can_update_ticket_status(actor: dict) -> bool:
        return actor.get("role") in ("admin", "super_admin")


__all__ = ["ChatPolicy", "EmailPolicy", "NotificationPolicy", "TicketPolicy"]
