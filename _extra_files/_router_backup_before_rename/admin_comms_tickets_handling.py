"""Support tickets router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from db.database import get_db
from data.models import SupportTicket, TicketMessage, User
from services.db_read import all_rows, count, first, scalars
from utils.dependencies import get_current_user
from services.comms.tickets_write_service import create_ticket_with_message, create_ticket_reply
import structlog
logger = structlog.get_logger(__name__)

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


@router.get("", response_model=dict)
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    filters = []
    if current_user.role == "customer":
        filters.append(SupportTicket.user_id == current_user.id)
    total = count(db, SupportTicket, filters)
    stmt = (
        select(SupportTicket)
        .where(*filters)
        .order_by(SupportTicket.created_at.desc())
        .options(selectinload(SupportTicket.messages))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tickets = scalars(db, stmt)
    return {"data": [_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201, response_model=dict)
def create_ticket(payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject, message, priority = _validate_ticket_input(payload)
    ticket, _initial = create_ticket_with_message(db, current_user.id, subject, priority, message)
    return _ticket_payload(ticket)


@router.get("/{ticket_id}", response_model=dict)
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    matches = scalars(db, (
        select(SupportTicket)
        .options(selectinload(SupportTicket.messages))
        .where(SupportTicket.id == ticket_id)
        .limit(1)
    ))
    ticket = matches[0] if matches else None
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    replies = all_rows(db, TicketMessage, [TicketMessage.ticket_id == ticket_id], order_by=TicketMessage.created_at.asc())
    return _ticket_payload(ticket, replies)


@router.post("/{ticket_id}/reply", response_model=dict)
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = first(db, SupportTicket, [SupportTicket.id == ticket_id])
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(db, ticket_id, current_user.id, message, is_admin=False)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


@router.post("/{ticket_id}/messages", status_code=201, response_model=dict)
def add_message(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = first(db, SupportTicket, [SupportTicket.id == ticket_id])
    if not ticket:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(db, ticket_id, current_user.id, message, is_admin=False)
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }

