"""Tickets write service — DB write operations for ticket entities."""

from typing import Optional

from sqlalchemy.orm import Session, selectinload

from data.models import Notification, SupportTicket, TicketMessage, TicketAttachment


def get_tickets_query(db: Session, user_id: int | None = None):
    q = db.query(SupportTicket).options(selectinload(SupportTicket.messages))
    if user_id is not None:
        q = q.filter(SupportTicket.user_id == user_id)
    return q


def get_ticket_by_id(db: Session, ticket_id: int) -> SupportTicket | None:
    return (
        db.query(SupportTicket)
        .options(selectinload(SupportTicket.messages))
        .filter(SupportTicket.id == ticket_id)
        .first()
    )


def get_ticket_with_details(db: Session, ticket_id: int) -> SupportTicket | None:
    """Return a ticket with user, messages, and attachments preloaded."""
    return (
        db.query(SupportTicket)
        .options(
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.messages).selectinload(TicketMessage.sender),
            selectinload(SupportTicket.attachments),
        )
        .filter(SupportTicket.id == ticket_id)
        .first()
    )


def list_tickets(
    db: Session,
    status: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> list[SupportTicket]:
    """List support tickets with optional status filter, preload user + attachments + messages."""
    from utils.constants import _ADMIN_MAX_PAGE_SIZE
    resolved_limit = 200 if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    return (
        q.options(
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.attachments),
            selectinload(SupportTicket.messages),
        )
        .order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
        .offset(max(0, offset))
        .limit(resolved_limit)
        .all()
    )


def count_tickets(db: Session, status: Optional[str] = None) -> int:
    """Count support tickets with optional status filter."""
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    return q.count()


def get_ticket_messages(db: Session, ticket_id: int, skip: int = 0, limit: int = 20):
    return (
        db.query(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket_id)
        .order_by(TicketMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_ticket_with_message(
    db: Session,
    user_id: int,
    subject: str,
    priority: str,
    message: str,
) -> tuple[SupportTicket, TicketMessage]:
    ticket = SupportTicket(user_id=user_id, subject=subject, priority=priority)
    db.add(ticket)
    db.flush()
    initial = TicketMessage(ticket_id=ticket.id, sender_id=user_id, message=message)
    db.add(initial)
    db.commit()
    db.refresh(ticket)
    return ticket, initial


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
def get_invoice_first(db: Session, **filters) -> Optional[Invoice]:
    query = db.query(Invoice)
    for key, value in filters.items():
        query = query.filter(getattr(Invoice, key) == value)
    return query.limit(1).first()


def get_order_by_id(db: Session, record_id: int) -> Optional[Order]:
    return db.query(Order).filter(Order.id == record_id).first()


def get_order_first(db: Session, **filters) -> Optional[Order]:
    query = db.query(Order)
    for key, value in filters.items():
        query = query.filter(getattr(Order, key) == value)
    return query.limit(1).first()


def get_invoice_by_id(db: Session, record_id: int) -> Optional[Invoice]:
    return db.query(Invoice).filter(Invoice.id == record_id).first()


def count_invoice(db: Session, **filters) -> int:
    query = db.query(Invoice)
    for key, value in filters.items():
        query = query.filter(getattr(Invoice, key) == value)
    return query.count()


def list_unknown(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.offset(skip).limit(limit).all()


def list_invoice(db: Session, skip: int = 0, limit: int = 100, **filters) -> list[Invoice]:
    query = db.query(Invoice)
    for key, value in filters.items():
        query = query.filter(getattr(Invoice, key) == value)
    return query.offset(skip).limit(limit).all()

def _db_invoice_query_0(db: Session) -> Optional[Any]:
    result = db.query(Invoice)
    return result
    """Read-only query delegated from controller."""

def _db_invoice_query_1(db: Session) -> Optional[Any]:
    return db.query(Invoice)
    """Read-only query delegated from controller."""

def _db_order_first_2(db: Session, id: Any, inv: Any, order_id: Any, uid: Any, user_id: Any) -> Optional[Any]:
    result = db.query(Order).filter(Order.id == inv.order_id, Order.user_id == uid).first()
    return result
    """Read-only query delegated from controller."""

def _db_order_query_3(db: Session) -> Optional[Any]:
    return db.query(Order)
    """Read-only query delegated from controller."""

def _db_invoice_first_4(db: Session, invoice_type: Any, order_id: Any, sale: Any, supplier_id: Any) -> Optional[Any]:
    result = db.query(Invoice).filter( Invoice.order_id == order_id, Invoice.supplier_id == supplier_id, Invoice.invoice_type == "sale", ).first()
    return result
    """Read-only query delegated from controller."""

def _db_invoice_count_5(db: Session) -> Optional[Any]:
    result = db.query(Invoice).count()
    return result
    """Read-only query delegated from controller."""

def _db_invoice_all_6(db: Session) -> Optional[Any]:
    result = db.query(Invoice).order_by(desc(Invoice.created_at)).limit(10).all()
    return result
    """Read-only query delegated from controller."""
