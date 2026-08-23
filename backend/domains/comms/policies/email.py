"""Email authorization policies."""
from __future__ import annotations


class EmailPolicy:
    """Authorization policies for email operations."""

    @staticmethod
    def can_send_email(actor: dict) -> bool:
        """Check if actor can send emails."""
        return actor.get("role") in ("admin", "super_admin", "employee")

    @staticmethod
    def can_create_campaign(actor: dict) -> bool:
        """Check if actor can create email campaigns."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_manage_templates(actor: dict) -> bool:
        """Check if actor can manage email templates."""
        return actor.get("role") in ("admin", "super_admin")

    @staticmethod
    def can_view_email_stats(actor: dict) -> bool:
        """Check if actor can view email statistics."""
        return actor.get("role") in ("admin", "super_admin", "employee")
