"""Support tickets controller (customer surface).

Thin orchestration layer for ticket writes. Satisfies the CIR2 circuit rule
(routers call controllers, not services directly); all DB writes live in
``services.comms.tickets_write_service``.
"""
from __future__ import annotations

from services.comms.tickets_write_service import (
    create_ticket_reply as _create_ticket_reply,
    create_ticket_with_message as _create_ticket_with_message,
)
import structlog
logger = structlog.get_logger(__name__)


def create_ticket_with_message(db, user_id: int, subject: str, priority: str, message: str):
    """Persist a new ticket with its first message (delegates to the service)."""
    return _create_ticket_with_message(db, user_id, subject, priority, message)


def create_ticket_reply(
    db,
    ticket_id: int,
    sender_id: int,
    message: str,
    is_admin: bool = False,
):
    """Append a reply to a ticket (delegates to the service)."""
    return _create_ticket_reply(db, ticket_id, sender_id, message, is_admin=is_admin)
