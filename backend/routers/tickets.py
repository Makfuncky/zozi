"""Support tickets router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.schemas import CursorPage
from data.models import User, SupportTicket, TicketMessage
from utils.dependencies import get_current_user
from utils.pagination import cursor_paginate_desc

from services.communication.tickets_write_service import (
    get_tickets_query,
    get_ticket_by_id,
    get_ticket_messages,
    create_ticket_with_message,
    create_ticket_reply,
)

router = APIRouter()


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


@router.get("", response_model=CursorPage)
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), cursor: str | None = Query(None, description="Cursor for next page"), limit: int = Query(20, ge=1, le=100)):
    user_id = current_user.id if current_user.role == "customer" else None
    q = get_tickets_query(db, user_id=user_id)
    page = cursor_paginate_desc(q, cursor=cursor, page_size=limit)
    page.items = [_ticket_payload(t) for t in page.items]
    return page


@router.post("", status_code=201)
def create_ticket(payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject, message, priority = _validate_ticket_input(payload)
    ticket, _initial = create_ticket_with_message(db, current_user.id, subject, priority, message)
    return _ticket_payload(ticket)


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    replies = get_ticket_messages(db, ticket_id, skip=skip, limit=limit)
    return _ticket_payload(ticket, replies)


@router.post("/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(db, ticket_id=ticket_id, sender_id=current_user.id, message=message, is_admin=False)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


@router.post("/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(db, ticket_id=ticket_id, sender_id=current_user.id, message=message, is_admin=False)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }
