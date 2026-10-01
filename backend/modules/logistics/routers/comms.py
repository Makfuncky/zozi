"""Logistics comms router — logistics partner communications endpoints.

Logistics partners can:
- read their own notifications
- create/manage support tickets
- use proxy communication channels (when transacting with customers)
- view their own chat threads
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import (
    require_logistics,
)
from rbac.dependencies import require_feature

from domains.comms.services.comms_service import (
    create_support_ticket,
    get_support_ticket,
    list_support_tickets,
    reply_to_support_ticket,
)
from domains.comms.services.messaging.chat_service import get_chat_system
from domains.comms.services.proxy_communication import get_proxy_service


router = APIRouter(prefix="/api/v1/logistics/comms", tags=["logistics", "comms"])


# ── Notifications ───────────────────────────────────────────────────────────


@router.get("/notifications")
def list_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.notification.read")),
):
    from domains.comms.services.messaging.chat_service import get_user_notifications
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    items = get_user_notifications(user_id, limit=1000)
    if unread_only:
        items = [n for n in items if not n.get("read_at")]
    total = len(items)
    start = (page - 1) * page_size
    return {
        "data": items[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.notification.read")),
):
    from domains.comms.services.messaging.chat_service import mark_notification_read
    return mark_notification_read(notification_id)


# ── Support tickets ─────────────────────────────────────────────────────────


@router.get("/tickets")
def list_my_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.ticket.read")),
):
    return list_support_tickets(db, current_user, page=page, page_size=page_size)


@router.post("/tickets", status_code=201)
def create_ticket(
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.ticket.create")),
):
    return create_support_ticket(db, payload, current_user)


@router.get("/tickets/{ticket_id}")
def get_ticket(
    ticket_id: int,
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.ticket.read")),
):
    return get_support_ticket(db, ticket_id, current_user)


@router.post("/tickets/{ticket_id}/reply")
def reply_to_ticket(
    ticket_id: int,
    payload: Dict[str, Any] = Body(...),
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.ticket.create")),
):
    return reply_to_support_ticket(db, ticket_id, payload, current_user)


# ── Chat (direct/threads) ───────────────────────────────────────────────────


@router.post("/chat/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_logistics),
    _feature: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/chat/message")
def send_chat_message(
    chat_id: str = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_logistics),
    _feature: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    sender_id = current_user.get("id")
    return chat.send_message(chat_id, sender_id, content, message_type)


@router.get("/chat/history/{chat_id}")
def get_chat_history(
    chat_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_logistics),
    _feature: None = Depends(require_feature("comms.chat.read")),
):
    chat = get_chat_system(db)
    return chat.get_chat_history(chat_id, limit)


@router.get("/chat/threads")
def list_threads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_logistics),
    _feature: None = Depends(require_feature("comms.chat.read")),
):
    chat = get_chat_system(db)
    threads = chat.list_threads()
    start = (page - 1) * page_size
    return {
        "data": threads[start : start + page_size],
        "total": len(threads),
        "page": page,
        "page_size": page_size,
    }


# ── Proxy communication ─────────────────────────────────────────────────────


@router.get("/proxy/channels")
def list_my_proxy_channels(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_logistics),
    db: Session = Depends(get_db),
    _feature: None = Depends(require_feature("comms.proxy.use")),
):
    proxy_service = get_proxy_service(db)
    user_id = current_user.get("id")
    channels = proxy_service.list_user_channels(
        user_id,
        skip=(page - 1) * page_size,
        limit=page_size,
    )
    return [
        {
            "id": c.id,
            "proxy_phone": proxy_service.mask_phone_number(c.proxy_phone) if c.proxy_phone else None,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active,
        }
        for c in channels
    ]
