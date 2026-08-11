"""controllers.admin.tickets controller.

Business logic is delegated to services.admin.tickets_service (routers -> controllers -> services)."""

from services.admin.tickets_service import (
    _serialize_support_ticket, _serialize_ticket_attachment, _serialize_ticket_message, get_ticket_detail, list_tickets, reply_to_ticket,
    update_ticket_status
)

__all__ = [
    "_serialize_support_ticket", "_serialize_ticket_attachment", "_serialize_ticket_message", "get_ticket_detail", "list_tickets", "reply_to_ticket",
    "update_ticket_status"
]
