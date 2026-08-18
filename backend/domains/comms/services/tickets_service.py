"""Auto-migrated service logic from routers/tickets.py."""
from __future__ import annotations

from fastapi import Body, Depends, HTTPException, Query

from sqlalchemy.orm import Session, selectinload

from infrastructure.database.database import get_db

from domains.accounts.models.core import SupportTicket
from domains.accounts.models.user import User
from domains.comms.models.communication import TicketMessage

from infrastructure.utils.dependencies import get_current_user

def _ticket_payload(ticket: SupportTicket, replies: list[TicketMessage] | None = None) -> dict:
    msgs = replies if replies is not None else list(getattr(ticket, "messages", []) or [])
    first_message = msgs[0].message if msgs else ""
    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "subject": ticket.subject,
        "message": first_message,
        "priority": ticket.priority,
        "status": ticket.status,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "replies": [
            {
                "id": r.id,
                "ticket_id": r.ticket_id,
                "sender_id": r.sender_id,
                "message": r.message,
                "is_admin": bool(getattr(r, "is_admin", False)),
                "created_at": r.created_at,
            }
            for r in msgs
        ],
    }

def _validate_ticket_input(payload: dict) -> tuple[str, str, str]:
    subject = str(payload.get("subject") or "").strip()
    message = str(payload.get("message") or payload.get("body") or "").strip()
    priority = str(payload.get("priority") or "normal").strip().lower()

    if not subject:
        raise HTTPException(status_code=422, detail="subject is required")
    if len(message) < 10:
        raise HTTPException(status_code=422, detail="message must be at least 10 characters")
    if priority not in {"low", "normal", "high"}:
        raise HTTPException(status_code=422, detail="priority must be one of: low, normal, high")

    return subject, message, priority

def list_tickets(current_user: User, db: Session, page: int, page_size: int):
    q = db.query(SupportTicket)
    if current_user.role == "customer":
        q = q.filter(SupportTicket.user_id == current_user.id)
    total = q.count()
    tickets = q.order_by(SupportTicket.created_at.desc()).options(selectinload(SupportTicket.messages)).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}

def create_ticket(payload: dict, current_user: User, db: Session):
    subject, message, priority = _validate_ticket_input(payload)
    ticket = SupportTicket(
        user_id=current_user.id,
        subject=subject,
        priority=priority,
    )
    db.add(ticket)
    db.flush()
    initial = TicketMessage(ticket_id=ticket.id, sender_id=current_user.id, message=message)
    db.add(initial)
    db.commit()
    db.refresh(ticket)
    return _ticket_payload(ticket)

def get_ticket(ticket_id: int, current_user: User, db: Session):
    ticket = db.query(SupportTicket).options(selectinload(SupportTicket.messages)).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    replies = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at.asc()).all()
    return _ticket_payload(ticket, replies)

def reply_to_ticket(ticket_id: int, payload: dict, current_user: User, db: Session):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = TicketMessage(ticket_id=ticket_id, sender_id=current_user.id, message=message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }

def add_message(ticket_id: int, payload: dict, current_user: User, db: Session):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = TicketMessage(ticket_id=ticket_id, sender_id=current_user.id, message=message)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


