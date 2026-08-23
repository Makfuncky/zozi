"""Ticket authorization policies."""
from __future__ import annotations


class TicketPolicy:
    """Authorization policies for ticket operations."""

    @staticmethod
    def can_create_ticket(actor: dict) -> bool:
        """Check if actor can create a support ticket."""
        return True  # Any authenticated user

    @staticmethod
    def can_view_ticket(actor: dict, ticket_user_id: int) -> bool:
        """Check if actor can view a ticket."""
        # Admin can view any ticket
        if actor.get("role") in ("admin", "super_admin"):
            return True
        # Users can view their own tickets
        return actor.get("user_id") == ticket_user_id

    @staticmethod
    def can_reply_to_ticket(actor: dict, ticket_user_id: int) -> bool:
        """Check if actor can reply to a ticket."""
        # Admin can reply to any ticket
        if actor.get("role") in ("admin", "super_admin"):
            return True
        # Users can reply to their own tickets
        return actor.get("user_id") == ticket_user_id

    @staticmethod
    def can_update_ticket_status(actor: dict) -> bool:
        """Check if actor can update ticket status."""
        return actor.get("role") in ("admin", "super_admin")
