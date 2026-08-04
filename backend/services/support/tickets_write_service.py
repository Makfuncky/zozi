"""Service methods for ticket write operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import Ticket, TicketReply


def create_ticket(db: Session, user_id: int, subject: str, message: str, priority: str = "medium") -> Ticket:
    """Create a new support ticket."""
    ticket = Ticket(user_id=user_id, subject=subject, message=message, priority=priority, status="open")
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    reply = TicketReply(ticket_id=ticket.id, sender_id=user_id, message=message)
    db.add(reply)
    db.commit()
    return ticket


def reply_to_ticket(db: Session, ticket_id: int, sender_id: int, message: str) -> TicketReply:
    """Reply to a ticket."""
    reply = TicketReply(ticket_id=ticket_id, sender_id=sender_id, message=message)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def update_ticket_status(db: Session, ticket_id: int, status: str) -> Ticket | None:
    """Update ticket status."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None
    ticket.status = status
    db.commit()
    db.refresh(ticket)
    return ticket


def assign_ticket(db: Session, ticket_id: int, assignee_id: int) -> Ticket | None:
    """Assign a ticket to a staff member."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        return None
    ticket.assigned_to = assignee_id
    db.commit()
    db.refresh(ticket)
    return ticket
