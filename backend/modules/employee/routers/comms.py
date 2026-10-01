"""Employee comms router — canonical (consolidated from 24 source files)."""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, status, WebSocket, Request, Form, File, UploadFile
from sqlalchemy.orm import Session
from typing import Annotated, Any, Dict, List, Optional
import logging

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user, require_admin
from rbac.dependencies import require_feature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employee/comms", tags=["employee", "comms"])


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH / LIVENESS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/push_notifications/health")
def push_notifications_health():
    return {"status": "ok", "router": "push_notifications", "prefix": "/api/v1/push-notifications"}


@router.get("/ws_chat/health")
def ws_chat_health():
    return {"status": "ok", "router": "ws_chat", "prefix": "/api/v1/ws-chat"}


@router.get("/email_controller/health")
def email_controller_health():
    return {"status": "ok", "router": "email_controller", "prefix": "/api/v1/email-gateway"}


# ══════════════════════════════════════════════════════════════════════════════
# CHAT SYSTEM (from comms_chat.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.messaging.chat_service import get_chat_system, create_notification_service


@router.post("/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/group")
def create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.create_group_chat(name, participants, is_encrypted)


@router.post("/message")
def send_chat_message(
    chat_id: str = Body(..., embed=True),
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.send_message(chat_id, sender_id, content, message_type)


@router.get("/history/{chat_id}")
def get_history(chat_id: str, limit: int = 100, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.read"))
):
    chat = get_chat_system(db)
    return chat.get_chat_history(chat_id, limit)


@router.get("/threads")
def list_threads(db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.read"))
):
    chat = get_chat_system(db)
    return chat.list_threads()


@router.post("/threads")
def create_thread(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.create_thread(title, entity_type, entity_id)


@router.get("/threads/{thread_id}/messages")
def get_thread_messages(
    thread_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Message ID to fetch messages before (cursor-based pagination)"),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.read")),
):
    """Get messages for a thread with cursor-based pagination."""
    chat = get_chat_system(db)
    data = chat.get_thread_messages(thread_id, limit, cursor)
    return data


@router.post("/threads/{thread_id}/messages")
def send_thread_message(
    thread_id: int,
    sender_id: int = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    result = chat.send_message(str(thread_id), sender_id, message)
    return result


@router.post("/threads/{thread_id}/messages/upload")
async def send_thread_message_with_attachments(
    thread_id: int,
    sender_id: int = Form(...),
    message: str = Form(""),
    files: list[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    """Send a thread message with optional file attachments via multipart/form-data."""
    chat = get_chat_system(db)
    file_list = files or []
    return await chat.send_message_with_files(
        str(thread_id), sender_id, message, file_list
    )


@router.post("/read")
def mark_read(
    chat_id: str = Body(..., embed=True),
    user_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("comms.chat.send")),
):
    chat = get_chat_system(db)
    return chat.mark_read(chat_id, user_id)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL (from email.py — full email router)
# ══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel
from rbac.dependencies import require_roles
from domains.comms.services.email.email_gateway import EmailGateway
from domains.comms.services.email.transactional import (
    enqueue_invoice_email,
    enqueue_low_stock_alert_email,
    enqueue_order_created_email,
)
from domains.comms.services.email.email_management import (
    EmailManagementService,
    get_email_management_service,
)


AdminUser = Annotated[dict, Depends(require_roles("admin"))]
AdminOrSuperAdminUser = Annotated[dict, Depends(require_roles("admin", "superadmin"))]

_TRANSPARENT_GIF = (
    b"GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01"
    b"\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
)


class SendEmailPayload(BaseModel):
    to: str
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    is_html: bool = True


class SendTransactionalPayload(BaseModel):
    to: str
    template: str
    variables: Dict[str, Any] = {}


class InternalEmailPayload(BaseModel):
    to: List[int]
    subject: str
    body: str
    cc: Optional[List[int]] = None
    attachment_ids: Optional[List[int]] = None


class ExternalEmailPayload(BaseModel):
    to: str
    subject: str
    body: str
    template_id: Optional[str] = None


@router.post("/send")
def send_email(
    current_user: AdminUser,
    payload: SendEmailPayload,
    db: Session = Depends(get_db),
):
    """Send an email via the configured email provider."""
    gateway = EmailGateway()
    result = gateway.send_external_email(
        to_email=payload.to,
        subject=payload.subject,
        body=payload.body,
        cc=payload.cc or [],
        bcc=payload.bcc or [],
        is_html=payload.is_html,
    )
    return {"status": result.get("status", "sent"), "email_id": result.get("email_id")}


@router.post("/send/transactional")
def send_transactional(
    current_user: AdminUser,
    payload: SendTransactionalPayload,
):
    """Send a transactional email using a predefined template."""
    templates = {
        "order_created": lambda: enqueue_order_created_email(payload.to, payload.variables),
        "invoice": lambda: enqueue_invoice_email(payload.to, payload.variables),
        "low_stock": lambda: enqueue_low_stock_alert_email(payload.to, payload.variables),
    }
    handler = templates.get(payload.template)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown template: {payload.template}")
    handler()
    return {"status": "queued", "template": payload.template}


@router.post("/send/alias")
def send_from_alias(
    current_user: AdminUser,
    alias_key: str = Body(...),
    to: str = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
):
    """Send email from a role-based alias (e.g., kyc.ksa@zozi.com)."""
    gateway = EmailGateway()
    result = gateway.send_from_alias(alias_key, to, subject, body)
    return {"status": result.get("status", "sent")}


@router.post("/send/bulk")
def send_bulk(
    to_emails: List[str] = Body(...),
    subject: str = Body(...),
    body: str = Body(...),
    current_user: AdminOrSuperAdminUser = None,
):
    """Send bulk email with DLP protection."""
    gateway = EmailGateway()
    results = gateway.send_bulk_email(to_emails, subject, body)
    return {
        "total": len(to_emails),
        "sent": sum(1 for r in results if r.get("status") == "sent"),
        "failed": sum(1 for r in results if r.get("status") != "sent"),
        "results": results,
    }


@router.get("/templates")
def list_templates(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    return svc.list_templates(skip=(page - 1) * limit, limit=limit)


@router.post("/templates")
def create_template(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    user_id = current_user.get("id") if isinstance(current_user, dict) else None
    return svc.create_template(payload, user_id=user_id)


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    try:
        return svc.update_template(template_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    try:
        return svc.delete_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/campaigns")
def list_campaigns(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    return svc.list_campaigns(skip=(page - 1) * limit, limit=limit)


@router.post("/campaigns")
def create_campaign(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    user_id = current_user.get("id") if isinstance(current_user, dict) else None
    return svc.create_campaign(payload, user_id=user_id)


@router.get("/suppressions")
def list_suppressions(
    status: Optional[str] = Query(None),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    return svc.list_suppressions(status=status)


@router.patch("/suppressions/{suppression_id}")
def update_suppression(
    suppression_id: int,
    body: Dict[str, Any] = Body(default={}),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    try:
        return svc.update_suppression(suppression_id, body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/config/runtime")
def get_email_runtime_config(current_user: AdminUser = None, db: Session = Depends(get_db)):
    svc = get_email_management_service(db)
    return svc.get_email_runtime_config()


@router.put("/config/runtime")
def update_email_runtime_config(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    svc = get_email_management_service(db)
    return svc.update_email_runtime_config(payload)


@router.post("/config/test-send")
def test_send_email(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    to_email = payload.get("to_email") or (payload.get("to") if isinstance(payload.get("to"), str) else None)
    if not to_email:
        raise HTTPException(status_code=422, detail="to_email is required")
    purpose = payload.get("purpose", "transactional")
    subject = payload.get("subject") or f"ZOZI test email ({purpose})"
    gateway = EmailGateway(db)
    sender_id = current_user.get("id") if isinstance(current_user, dict) else None
    result = gateway.send_external_email(
        to_email=to_email,
        subject=subject,
        body=f"<p>This is a test email from ZOZI (purpose: {purpose}).</p>",
        sender_id=sender_id,
    )
    return {
        "provider": result.get("provider", "unknown"),
        "from_address": result.get("from_address"),
        "preview_only": result.get("preview_only", False),
        "status": result.get("status", "sent"),
    }


@router.post("/internal", response_model=dict)
def send_internal_email(
    payload: InternalEmailPayload,
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    """Send an internal email and store it in the employee inbox."""
    gateway = EmailGateway(db)
    sender_id = current_user.get("id") if isinstance(current_user, dict) else None
    return gateway.send_internal_email(
        to_user_ids=payload.to,
        subject=payload.subject,
        body=payload.body,
        sender_id=sender_id or 0,
    )


@router.get("/inbox")
def get_my_inbox(
    folder: str = Query("inbox"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    """Get internal emails for the current admin/staff user."""
    from domains.comms.services.comms_service import get_employee_inbox
    employee_id = current_user.get("id") if isinstance(current_user, dict) else 0
    return get_employee_inbox(db, employee_id=employee_id, folder=folder, limit=limit, offset=offset)


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED INBOX (from comms_unified.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.email.email_management import get_unified_inbox_service


@router.get("/unified-inbox")
def unified_inbox(
    lens: str = Query("all"),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    transport: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return a cursor-paginated, server-sorted merge of all conversation types."""
    svc = get_unified_inbox_service(db)
    user_id = int(current_user["id"]) if isinstance(current_user, dict) else 0
    return svc.get_unified_inbox(
        user_id=user_id,
        lens=lens,
        cursor=cursor,
        limit=limit,
        transport=transport,
    )


# ══════════════════════════════════════════════════════════════════════════════
# NOTIFICATIONS (from notifications.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.comms_service import NotificationChannel, NotificationPriority
from rbac import get_current_user as rbac_get_current_user


def _parse_channel(value: str) -> NotificationChannel:
    try:
        return NotificationChannel(value)
    except ValueError:
        return NotificationChannel.IN_APP


def _parse_priority(value: str) -> NotificationPriority:
    try:
        return NotificationPriority(value)
    except ValueError:
        return NotificationPriority.MEDIUM


@router.post("/notifications/send")
def send_notification(
    user_id: int,
    title: str,
    message: str,
    channel: str = "in_app",
    priority: str = "medium",
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    engine = create_notification_service(db)
    return engine.send_notification(user_id, title, message, _parse_channel(channel), _parse_priority(priority))


@router.post("/notifications/bulk")
def send_bulk_notifications(
    user_ids: list,
    title: str,
    message: str,
    channel: str = "email",
    priority: str = "medium",
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    engine = create_notification_service(db)
    return engine.send_alert(alert_type="bulk", data={"user_ids": user_ids, "title": title, "message": message}, priority=_parse_priority(priority))


@router.get("/notifications")
def get_notifications(
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = False,
):
    user_id = current_user.get("id")
    engine = create_notification_service(db)
    return engine.send_alert(alert_type="get", data={"user_id": user_id, "unread_only": unread_only})


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id")
    engine = create_notification_service(db)
    return engine.send_alert(alert_type="mark_read", data={"notification_id": notification_id, "user_id": user_id})


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKETS (from tickets.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.tickets.tickets_service import get_tickets_query
from domains.comms.services.tickets.tickets_service import get_ticket_by_id
from domains.comms.services.tickets.tickets_service import get_ticket_messages
from domains.comms.services.tickets.tickets_service import create_ticket_with_message
from domains.comms.services.tickets.tickets_service import create_ticket_reply
from domains.comms.services.tickets.tickets_service import list_tickets_paginated


def _ticket_payload(ticket, replies: list | None = None) -> dict:
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


@router.get("/tickets")
def list_tickets(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    user_id = current_user["id"] if isinstance(current_user, dict) and current_user.get("role") == "customer" else None
    tickets, total = list_tickets_paginated(db=db, page=page, page_size=page_size, user_id=user_id)
    return {"data": [_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


@router.post("/tickets", status_code=201)
def create_ticket(payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    subject, message, priority = _validate_ticket_input(payload)
    ticket, _ = create_ticket_with_message(
        db=db,
        user_id=current_user["id"] if isinstance(current_user, dict) else 0,
        subject=subject,
        priority=priority,
        message=message,
    )
    return _ticket_payload(ticket)


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if isinstance(current_user, dict) and current_user.get("role") == "customer" and ticket.user_id != current_user["id"]:
        raise HTTPException(404)
    replies = get_ticket_messages(db, ticket_id)
    return _ticket_payload(ticket, replies)


@router.post("/tickets/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if isinstance(current_user, dict) and current_user.get("role") == "customer" and ticket.user_id != current_user["id"]:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user["id"] if isinstance(current_user, dict) else 0,
        message=message,
    )
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


@router.post("/tickets/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: int, payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user["id"] if isinstance(current_user, dict) else 0,
        message=message,
    )
    return {
        "id": msg.id,
        "ticket_id": msg.ticket_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PROXY COMMUNICATION (from proxy_communication.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.proxy_communication import get_proxy_service


@router.post("/proxy/channels", response_model=dict)
async def create_proxy_channel(
    entity_type: str,
    entity_id: int,
    participant_ids: List[int],
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    channel = proxy_service.create_proxy_channel(
        entity_type=entity_type,
        entity_id=entity_id,
        participant_ids=participant_ids
    )
    return {
        "id": channel.id,
        "proxy_phone": proxy_service.mask_phone_number(channel.proxy_phone) if channel.proxy_phone else None,
        "proxy_email": channel.proxy_email,
        "is_active": channel.is_active
    }


@router.get("/proxy/channels/{channel_id}", response_model=dict)
async def get_proxy_channel(
    channel_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    channel = proxy_service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Proxy channel not found")
    return {
        "id": channel.id,
        "entity_type": channel.entity_type,
        "entity_id": channel.entity_id,
        "proxy_phone": proxy_service.mask_phone_number(channel.proxy_phone) if channel.proxy_phone else None,
        "proxy_email": channel.proxy_email,
        "is_active": channel.is_active,
        "participants": channel.participants
    }


@router.post("/proxy/sessions", response_model=dict)
async def start_proxy_session(
    channel_id: int,
    participant_one_id: int,
    participant_two_id: int,
    metadata: Optional[dict] = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    try:
        session = proxy_service.start_proxy_session(
            channel_id=channel_id,
            participant_one_id=participant_one_id,
            participant_two_id=participant_two_id,
            metadata=metadata
        )
        return {
            "id": session.id,
            "channel_id": session.channel_id,
            "started_at": session.started_at.isoformat(),
            "is_encrypted": session.is_encrypted
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/proxy/messages", response_model=dict)
async def send_proxy_message(
    session_id: int,
    sender_id: int,
    recipient_id: int,
    content: str,
    message_type: str = "text",
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    message = proxy_service.send_proxy_message(
        session_id=session_id,
        sender_id=sender_id,
        recipient_id=recipient_id,
        content=content,
        message_type=message_type
    )
    return {
        "id": message.id,
        "session_id": message.session_id,
        "sender_id": message.sender_id,
        "created_at": message.created_at.isoformat()
    }


@router.post("/proxy/calls/initiate", response_model=dict)
async def initiate_call(
    channel_id: int,
    caller_id: int,
    callee_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    call_log = proxy_service.initiate_call(
        channel_id=channel_id,
        caller_id=caller_id,
        callee_id=callee_id
    )
    return {
        "call_id": call_log.id,
        "channel_id": call_log.channel_id,
        "direction": call_log.direction,
        "started_at": call_log.started_at.isoformat()
    }


@router.post("/proxy/calls/{call_id}/end", response_model=dict)
async def end_call(
    call_id: int,
    duration_seconds: int,
    recording_url: Optional[str] = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    proxy_service.end_call(call_id, duration_seconds, recording_url)
    return {"status": "ended"}


@router.get("/proxy/users/{user_id}/channels", response_model=List[dict])
async def get_user_channels(
    user_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    channels = proxy_service.list_user_channels(
        user_id,
        skip=(page - 1) * limit,
        limit=limit,
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


@router.get("/proxy/admin/channels", response_model=List[dict])
async def admin_list_channels(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    return proxy_service.list_channels(skip=(page - 1) * limit, limit=limit)


# ══════════════════════════════════════════════════════════════════════════════
# ENTITY CHAT (from entity_chat.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.accounts.ports import get_user_by_id


@router.post("/entity/threads", response_model=dict)
async def create_entity_thread(
    entity_type: str,
    entity_id: int,
    title: Optional[str] = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_system(db)
    thread = service.create_entity_chat(entity_type, entity_id, participants=[], name=title)
    return thread


@router.post("/entity/threads/{thread_id}/messages", response_model=dict)
async def send_entity_chat_message(
    thread_id: int,
    message: str,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, int(current_user["sub"])) if isinstance(current_user, dict) else None
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    service = get_chat_system(db)
    msg = service.send_message(str(thread_id), user.id, message)
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_id": msg.sender_id,
        "created_at": msg.created_at.isoformat()
    }


@router.get("/entity/threads/{thread_id}/messages", response_model=dict)
async def get_entity_chat_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_system(db)
    messages = service.get_thread_messages(thread_id, limit, offset)
    return {"messages": messages}


@router.get("/entity/entities/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_system(db)
    thread = service.get_entity_thread(entity_type, entity_id)
    return thread or {"exists": False}
