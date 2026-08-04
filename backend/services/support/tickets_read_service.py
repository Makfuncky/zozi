"""Service methods for ticket read operations."""
from sqlalchemy.orm import Session
from data.models import Ticket, TicketReply


def get_user_tickets(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[Ticket]:
    """Get tickets for a user."""
    return (
        db.query(Ticket)
        .filter(Ticket.user_id == user_id)
        .order_by(Ticket.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_ticket_by_id(db: Session, ticket_id: int) -> Ticket | None:
    """Get a ticket by ID."""
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_ticket_messages(db: Session, ticket_id: int) -> list[TicketReply]:
    """Get messages/replies for a ticket."""
    return (
        db.query(TicketReply)
        .filter(TicketReply.ticket_id == ticket_id)
        .order_by(TicketReply.created_at)
        .all()
    )


def search_tickets(
    db: Session,
    status: str | None = None,
    priority: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Ticket]:
    """Search tickets with filters."""
    q = db.query(Ticket)
    if status:
        q = q.filter(Ticket.status == status)
    if priority:
        q = q.filter(Ticket.priority == priority)
    return q.order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()


def get_ticket_stats(db: Session, user_id: int) -> dict:
    """Get ticket statistics for a user."""
    from sqlalchemy import func as sqlfunc
    total = db.query(sqlfunc.count(Ticket.id)).filter(Ticket.user_id == user_id).scalar() or 0
    open_count = (
        db.query(sqlfunc.count(Ticket.id))
        .filter(Ticket.user_id == user_id, Ticket.status == "open")
        .scalar()
        or 0
    )
    resolved = (
        db.query(sqlfunc.count(Ticket.id))
        .filter(Ticket.user_id == user_id, Ticket.status == "resolved")
        .scalar()
        or 0
    )
    return {"total": total, "open": open_count, "resolved": resolved}
