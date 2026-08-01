"""Tickets write service — DB write operations for ticket entities."""

from sqlalchemy.orm import Session

from models import Notification, SupportTicket, TicketMessage


def create_ticket_reply(
    db: Session,
    ticket_id: int,
    sender_id: int,
    message: str,
    is_admin: bool = True,
) -> TicketMessage:
    reply = TicketMessage(
        ticket_id=ticket_id,
        sender_id=sender_id,
        message=message,
        is_admin=is_admin,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def create_notification(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def update_ticket_status(db: Session, ticket: SupportTicket, status: str) -> SupportTicket:
    ticket.status = status
    db.commit()
    db.refresh(ticket)
    return ticket


def admin_reply_to_ticket(
    db: Session,
    ticket: SupportTicket,
    message: str,
    sender_id: int,
) -> SupportTicket:
    reply = TicketMessage(
        ticket_id=ticket.id,
        sender_id=sender_id,
        message=message,
        is_admin=True,
    )
    db.add(reply)

    if ticket.status in {"open", "pending", "resolved", "closed"}:
        ticket.status = "in_progress"

    notification = Notification(
        user_id=ticket.user_id,
        type="support",
        title="Support Reply Received",
        message=f'Admin replied to your ticket: "{ticket.subject}"',
        link=f"/tickets/{ticket.id}",
    )
    db.add(notification)

    db.commit()
    db.refresh(ticket)

    return ticket