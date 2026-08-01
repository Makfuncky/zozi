"""Admin support ticket management controller."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from models import SupportTicket, TicketMessage, TicketAttachment, Notification
from utils.audit import audit_log, AuditAction
from utils.constants import _ADMIN_MAX_PAGE_SIZE

from services.write_helpers import add_and_flush, commit_and_refresh

def _serialize_ticket_attachment(attachment: TicketAttachment) -> dict[str, Any]:
    return {
        "id": cast(int, getattr(attachment, "id")),
        "original_name": cast(str, getattr(attachment, "original_name")),
        "mime_type": cast(str | None, getattr(attachment, "mime_type", None)),
        "file_size_bytes": cast(int | None, getattr(attachment, "file_size_bytes", None)),
        "file_path": cast(str, getattr(attachment, "file_path")),
        "created_at": cast(datetime, getattr(attachment, "created_at")),
    }


def _serialize_ticket_message(reply: TicketMessage) -> dict[str, Any]:
    user = cast(User | None, getattr(reply, "sender", None))
    return {
        "id": cast(int, getattr(reply, "id")),
        "user_id": cast(int | None, getattr(reply, "sender_id", None)),
        "username": cast(str | None, getattr(user, "username", None)) if user else ("Admin" if getattr(reply, "is_admin", False) else "User"),
        "message": cast(str, getattr(reply, "message")),
        "is_admin": bool(cast(Any, getattr(reply, "is_admin", False))),
        "created_at": cast(datetime, getattr(reply, "created_at")),
        "attachments": [],
    }


def _serialize_support_ticket(ticket: SupportTicket, *, include_message: bool = False, include_replies: bool = False) -> dict[str, Any]:
    user = cast(User | None, getattr(ticket, "user", None))
    payload: dict[str, Any] = {
        "id": cast(int, getattr(ticket, "id")),
        "user_id": cast(int | None, getattr(ticket, "user_id", None)),
        "username": cast(str | None, getattr(user, "username", None)) if user else "Unknown",
        "subject": cast(str, getattr(ticket, "subject")),
        "status": cast(str, getattr(ticket, "status")),
        "priority": cast(str | None, getattr(ticket, "priority", None)) or "normal",
        "ticket_category": cast(str | None, getattr(ticket, "ticket_category", None)) or "customer",
        "raised_by_role": cast(str | None, getattr(ticket, "raised_by_role", None)),
        "related_entity_type": cast(str | None, getattr(ticket, "related_entity_type", None)),
        "related_entity_id": cast(int | None, getattr(ticket, "related_entity_id", None)),
        "created_at": cast(datetime, getattr(ticket, "created_at")),
        "updated_at": cast(datetime, getattr(ticket, "updated_at")),
        "reply_count": len(list(getattr(ticket, "messages", []) or [])),
        "attachments": [_serialize_ticket_attachment(attachment) for attachment in list(getattr(ticket, "attachments", []) or [])],
    }
    if include_message:
        msgs = list(getattr(ticket, "messages", []) or [])
        payload["message"] = cast(str, msgs[0].message) if msgs else ""
    if include_replies:
        payload["replies"] = [_serialize_ticket_message(reply) for reply in list(getattr(ticket, "messages", []) or [])]
    return payload

def list_tickets(db: Session, status: Optional[str] = None, limit: Optional[int] = None, offset: int = 0) -> dict[str, Any]:
    resolved_limit = 200 if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    q = db.query(SupportTicket)
    if status:
        q = q.filter(SupportTicket.status == status)
    total = q.count()
    tickets = (
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
    serialized = [_serialize_support_ticket(ticket) for ticket in tickets]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=resolved_limit)


def get_ticket_detail(ticket_id: int, db: Session) -> dict:
    ticket = (
        db.query(SupportTicket)
        .options(
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.messages).selectinload(TicketMessage.sender),
            selectinload(SupportTicket.attachments),
        )
        .filter(SupportTicket.id == ticket_id)
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def reply_to_ticket(ticket_id: int, message: str, acting_user: dict, db: Session) -> dict:
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Reply message cannot be empty")
    reply = TicketMessage(
        ticket_id=ticket_id,
        sender_id=acting_user["id"],
        message=message.strip(),
        is_admin=True,
    )
    add_and_flush(db, reply)
    if cast(str, getattr(ticket, "status")) in {"open", "pending", "resolved", "closed"}:
        setattr(ticket, "status", "in_progress")
    add_and_flush(db, 
   Notification(
            user_id=ticket.user_id,
            type="support",
            title="Support Reply Received",
            message=f'Admin replied to your ticket: "{ticket.subject}"',
            link=f"/tickets/{ticket.id}",
        )
    )
    commit_and_refresh(db, ticket)
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def update_ticket_status(ticket_id: int, status: str, acting_user: dict, db: Session) -> dict:
    allowed = {"open", "pending", "in_progress", "resolved", "closed"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed)}")
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    setattr(ticket, "status", status)
    commit_and_refresh(db, ticket)
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


