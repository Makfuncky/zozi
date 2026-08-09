"""Admin support ticket management controller."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from data.models import SupportTicket, TicketAttachment, TicketMessage, User
from utils.constants import _ADMIN_MAX_PAGE_SIZE
from services.db_read import all_rows, count, first
from services.comms.tickets_write_service import (
    admin_reply_to_ticket,
    update_ticket_status as update_status_in_service,
)
import structlog
logger = structlog.get_logger(__name__)


def _build_list_page_payload(items: list[Any], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict[str, Any]:
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": page_size or len(items),
    }


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
    filters: list = []
    if status:
        filters.append(SupportTicket.status == status)
    total = count(db, SupportTicket, filters)
    tickets = all_rows(
        db,
        SupportTicket,
        filters,
        order_by=[SupportTicket.created_at.desc(), SupportTicket.id.desc()],
        offset=max(0, offset),
        limit=resolved_limit,
        options=[
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.attachments),
            selectinload(SupportTicket.messages),
        ],
    )
    serialized = [_serialize_support_ticket(ticket) for ticket in tickets]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=resolved_limit)


def get_ticket_detail(ticket_id: int, db: Session) -> dict:
    ticket = first(
        db,
        SupportTicket,
        [SupportTicket.id == ticket_id],
        options=[
            selectinload(SupportTicket.user),
            selectinload(SupportTicket.messages).selectinload(TicketMessage.sender),
            selectinload(SupportTicket.attachments),
        ],
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def reply_to_ticket(ticket_id: int, message: str, acting_user: dict, db: Session) -> dict:
    ticket = first(db, SupportTicket, [SupportTicket.id == ticket_id])
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if not message or not message.strip():
        raise HTTPException(status_code=400, detail="Reply message cannot be empty")
    ticket = admin_reply_to_ticket(db=db, ticket=ticket, message=message.strip(), sender_id=acting_user["id"])
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)


def update_ticket_status(ticket_id: int, status: str, acting_user: dict, db: Session) -> dict:
    allowed = {"open", "pending", "in_progress", "resolved", "closed"}
    if status not in allowed:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(allowed)}")
    ticket = first(db, SupportTicket, [SupportTicket.id == ticket_id])
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    ticket = update_status_in_service(db=db, ticket=ticket, status=status)
    return _serialize_support_ticket(ticket, include_message=True, include_replies=True)