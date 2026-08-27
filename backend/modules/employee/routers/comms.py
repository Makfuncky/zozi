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

from domains.comms.services.messaging.chat_service import get_chat_system


@router.post("/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    require_feature("comms.chat.send")
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/group")
def create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    db: Session = Depends(get_db)
):
    require_feature("comms.chat.send")
    chat = get_chat_system(db)
    return chat.create_group_chat(name, participants, is_encrypted)


@router.post("/message")
def send_chat_message(
    chat_id: str = Body(..., embed=True),
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db)
):
    require_feature("comms.chat.send")
    chat = get_chat_system(db)
    return chat.send_message(chat_id, sender_id, content, message_type)


@router.get("/history/{chat_id}")
def get_history(chat_id: str, limit: int = 100, db: Session = Depends(get_db)):
    require_feature("comms.chat.read")
    chat = get_chat_system(db)
    return chat.get_chat_history(chat_id, limit)


@router.get("/threads")
def list_threads(db: Session = Depends(get_db)):
    require_feature("comms.chat.read")
    chat = get_chat_system(db)
    return chat.list_threads()


@router.post("/threads")
def create_thread(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    require_feature("comms.chat.send")
    chat = get_chat_system(db)
    return chat.create_thread(title, entity_type, entity_id)


@router.get("/threads/{thread_id}/messages")
def get_thread_messages(
    thread_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Message ID to fetch messages before (cursor-based pagination)"),
    db: Session = Depends(get_db),
):
    """Get messages for a thread with cursor-based pagination."""
    require_feature("comms.chat.read")
    chat = get_chat_system(db)
    data = chat.get_thread_messages(thread_id, limit, cursor)
    return data


@router.post("/threads/{thread_id}/messages")
def send_thread_message(
    thread_id: int,
    sender_id: int = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db),
):
    require_feature("comms.chat.send")
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
):
    """Send a thread message with optional file attachments via multipart/form-data."""
    require_feature("comms.chat.send")
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
):
    require_feature("comms.chat.send")
    chat = get_chat_system(db)
    return chat.mark_read(chat_id, user_id)


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO CONFERENCING (from video_controller.py — admin-enhanced version)
# ══════════════════════════════════════════════════════════════════════════════


@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    employee_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code, employee_id)


@router.get("/rooms")
def list_rooms(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.list_rooms()


@router.get("/rooms/{room_id}")
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)


@router.post("/rooms/{room_id}/token")
def generate_token(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    ip_address: Optional[str] = Body(None, embed=True),
    device_fingerprint: Optional[str] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address, device_fingerprint, country_code)


@router.post("/rooms/{room_id}/recording/start")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/recording/end")
def end_recording(
    room_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}/transcript")
def get_transcript(
    room_id: str,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.get_transcript(room_id)


@router.post("/rooms/{room_id}/action-items")
def extract_action_items(
    room_id: str,
    entity_type: str = Body(..., embed=True),
    entity_id: int = Body(..., embed=True),
    action: str = Body(..., embed=True),
    metadata: Optional[dict] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.extract_action_items(room_id, entity_type, entity_id, action, metadata)


@router.post("/rooms/{room_id}/transcript/segment")
async def add_transcript_segment(
    room_id: str,
    speaker_id: int = Body(..., embed=True),
    content: Optional[str] = Body(None, embed=True),
    timestamp: str = Body(..., embed=True),
    language: str = Body("en", embed=True),
    audio_bytes: Optional[bytes] = Body(None, embed=True),
    target_language: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    vc = get_video_conference(db)
    from datetime import datetime
    return await vc.add_transcript_segment(
        room_id, speaker_id, content,
        datetime.fromisoformat(timestamp) if timestamp else None,
        language, audio_bytes, target_language
    )


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

from domains.audit.ports import AuditAction, audit_log
from infrastructure.utils.ip_utils import get_ip_for_logging
from domains.comms.services.email.email_management import get_unified_inbox_service


@router.get("/unified-inbox/reset")
def reset_unified_inbox(
    request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset the unified inbox demo data. Admin-only."""
    ip_address = get_ip_for_logging(request)
    try:
        from seed_comms import seed as _seed_comms
        _seed_comms()
        audit_log(
            db=db,
            action=AuditAction.INBOX_RESET,
            user_id=current_user.id,
            username=current_user.username or current_user.email,
            user_role=current_user.role,
            ip_address=ip_address,
            resource_type="comms",
            resource_id="unified_inbox",
            status="success",
            details={"action": "reset_unified_inbox", "endpoint": "/comms/unified-inbox/reset"},
        )
        return {"status": "ok", "message": "Communication data reset and re-seeded successfully"}
    except Exception as exc:
        logger.exception("Failed to reset unified inbox")
        audit_log(
            db=db,
            action=AuditAction.INBOX_RESET,
            user_id=current_user.id,
            username=current_user.username or current_user.email,
            user_role=current_user.role,
            ip_address=ip_address,
            resource_type="comms",
            resource_id="unified_inbox",
            status="failure",
            details={"action": "reset_unified_inbox", "endpoint": "/comms/unified-inbox/reset", "error": str(exc)},
        )
        raise HTTPException(status_code=500, detail=f"Failed to reset inbox: {str(exc)}")


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
    user_id = int(current_user.id)
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
    engine = get_notification_engine(db)
    return engine.send(user_id, title, message, _parse_channel(channel), _parse_priority(priority))


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
    engine = get_notification_engine(db)
    return engine.send_bulk(user_ids, title, message, _parse_channel(channel), _parse_priority(priority))


@router.get("/notifications")
def get_notifications(
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = False,
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.get_user_notifications(user_id, unread_only)


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.mark_read(notification_id, user_id)


# ══════════════════════════════════════════════════════════════════════════════
# SUPPORT TICKETS (from tickets.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.tickets.tickets_service import get_tickets_query
from domains.comms.services.tickets.tickets_service import get_ticket_by_id
from domains.comms.services.tickets.tickets_service import get_ticket_messages
from domains.comms.services.tickets.tickets_service import create_ticket_with_message
from domains.comms.services.tickets.tickets_service import create_ticket_reply


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
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    from domains.comms.models.communication_schema_models import SupportTicket
    from sqlalchemy.orm import selectinload
    from sqlalchemy import desc
    q = get_tickets_query(db, user_id=current_user["id"] if current_user.get("role") == "customer" else None)
    total = q.count()
    tickets = q.order_by(desc(SupportTicket.created_at)).options(selectinload(SupportTicket.messages)).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


@router.post("/tickets", status_code=201)
def create_ticket(payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subject, message, priority = _validate_ticket_input(payload)
    ticket, _ = create_ticket_with_message(
        db=db,
        user_id=current_user.id,
        subject=subject,
        priority=priority,
        message=message,
    )
    return _ticket_payload(ticket)


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    replies = get_ticket_messages(db, ticket_id)
    return _ticket_payload(ticket, replies)


@router.post("/tickets/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user.id,
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
def add_message(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = get_ticket_by_id(db, ticket_id)
    if not ticket:
        raise HTTPException(404)
    message = str(payload.get("message") or payload.get("body") or "").strip()
    if len(message) < 1:
        raise HTTPException(status_code=422, detail="message is required")
    msg = create_ticket_reply(
        db=db,
        ticket_id=ticket_id,
        sender_id=current_user.id,
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
# CHAT ENRICHMENT — reactions, edit/delete, legal hold, attachments (from chat_enrichment.py)
# ══════════════════════════════════════════════════════════════════════════════




@router.post("/reactions")
def api_add_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_reaction(db, message_id, message_type, current_user.id, emoji)


@router.delete("/reactions")
def api_remove_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return remove_reaction(db, message_id, message_type, current_user.id, emoji)


@router.get("/reactions/{message_type}/{message_id}")
def api_get_reactions(
    message_type: str,
    message_id: int,
    db: Session = Depends(get_db),
):
    return get_reactions(db, message_id, message_type)


@router.put("/messages/{message_type}/{message_id}")
def api_edit_message(
    message_type: str,
    message_id: int,
    body: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return edit_message(db, message_id, message_type, body, current_user.id)


@router.delete("/messages/{message_type}/{message_id}")
def api_delete_message(
    message_type: str,
    message_id: int,
    hard_delete: bool = False,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_message(db, message_id, message_type, current_user.id, hard_delete)


@router.post("/legal-hold")
def api_apply_legal_hold(
    room_id: int,
    room_type: str,
    reason: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return apply_legal_hold(db, room_id, room_type, current_user.id, reason)


@router.delete("/legal-hold/{room_type}/{room_id}")
def api_release_legal_hold(
    room_type: str,
    room_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return release_legal_hold(db, room_id, room_type)


@router.get("/legal-hold/{room_type}/{room_id}")
def api_check_legal_hold(
    room_type: str,
    room_id: int,
    db: Session = Depends(get_db),
):
    active = is_legal_hold_active(db, room_id, room_type)
    return {"room_id": room_id, "room_type": room_type, "legal_hold_active": active}


@router.post("/attachments/voice")
def api_upload_voice_note(
    message_id: int,
    message_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    duration_seconds: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return create_voice_note_attachment(
        db, message_id, message_type, file_url, file_name,
        file_size_bytes, duration_seconds,
    )


@router.post("/attachments")
def api_upload_attachment(
    message_id: int,
    message_type: str,
    attachment_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    mime_type: str,
    duration_seconds: Optional[int] = None,
    thumbnail_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_attachment(
        db, message_id, message_type, attachment_type, file_url, file_name,
        file_size_bytes, mime_type, duration_seconds, thumbnail_url,
    )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL ENRICHMENT — DLP, address resolution, notifications (from email_enrichment.py)
# ══════════════════════════════════════════════════════════════════════════════




@router.post("/address/resolve")
def api_resolve_address(
    address: str,
    db: Session = Depends(get_db),
):
    delivery_type, email, emp_id = resolve_address(db, address)
    return {
        "address": address,
        "delivery_type": delivery_type,
        "email": email,
        "employee_id": emp_id,
    }


@router.post("/address/resolve-bulk")
def api_resolve_recipients(
    addresses: List[str],
    db: Session = Depends(get_db),
):
    internal, external = resolve_recipients(db, addresses)
    return {
        "internal_recipients": internal,
        "external_addresses": external,
        "total_internal": len(internal),
        "total_external": len(external),
    }


@router.post("/dlp/scan")
def api_dlp_scan(
    subject: str,
    body_html: str,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    sender_role = current_user.get("role", "")
    return scan_content_for_dlp(subject, body_html, sender_role)


@router.post("/notify")
def api_send_notification(
    recipient_employee_id: int,
    email_id: int,
    subject: str,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db),
):
    send_email_notification(db, recipient_employee_id, email_id, subject)
    return {"notified": True, "employee_id": recipient_employee_id}


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
    service = get_chat_service(db)
    thread = service.create_or_get_thread(entity_type, entity_id, title)
    return {
        "id": thread.id,
        "entity_type": thread.entity_type,
        "entity_id": thread.entity_id,
        "title": thread.title
    }


@router.post("/entity/threads/{thread_id}/messages", response_model=dict)
async def send_entity_chat_message(
    thread_id: int,
    message: str,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_id(db, int(current_user["sub"]))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    service = get_chat_service(db)
    msg = service.send_message(thread_id, user.id, message)
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
    service = get_chat_service(db)
    messages = service.get_thread_messages(thread_id, limit, offset)
    return {"messages": messages}


@router.get("/entity/entities/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    thread = service.get_entity_thread(entity_type, entity_id)
    return thread or {"exists": False}


# ══════════════════════════════════════════════════════════════════════════════
# ENTITY COMMUNICATION (from entity_communication.py)
# ══════════════════════════════════════════════════════════════════════════════

from domains.comms.services.email.email_gateway import get_email_gateway


@router.get("/entity/comm/threads/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_comm_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    thread = chat_service.get_entity_thread(entity_type, entity_id)
    if not thread:
        thread = chat_service.create_or_get_thread(entity_type, entity_id)
    return thread


@router.post("/entity/comm/threads/{thread_id}/messages", response_model=dict)
async def send_entity_comm_message(
    thread_id: int,
    message: str,
    sender_id: int,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    msg = chat_service.send_message(thread_id, sender_id, message)
    return {
        "id": msg.id,
        "thread_id": msg.thread_id,
        "sender_id": msg.sender_id,
        "message": msg.message,
        "created_at": msg.created_at.isoformat()
    }


@router.get("/entity/comm/threads/{thread_id}/messages", response_model=List[dict])
async def get_entity_comm_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    return chat_service.get_thread_messages(thread_id, limit, offset)


@router.post("/entity/comm/email/send", response_model=dict)
async def send_entity_email(
    entity_type: str,
    entity_id: int,
    to_email: str,
    subject: str,
    body: str,
    sender_id: int,
    template_id: Optional[str] = None,
    current_user: dict = Depends(rbac_get_current_user),
    db: Session = Depends(get_db)
):
    email_gateway = get_email_gateway(db)
    result = email_gateway.send_external_email(
        to_email=to_email,
        subject=subject,
        body=body,
        sender_id=sender_id,
        template_id=template_id
    )
    return result


# ══════════════════════════════════════════════════════════════════════════════
# INTERNAL CHANNELS (from internal_channels.py)
# ══════════════════════════════════════════════════════════════════════════════




@router.post("/channels")
def create_channel(
    name: str = Body(..., embed=True),
    description: Optional[str] = Body(None, embed=True),
    is_public: bool = Body(False, embed=True),
    created_by: Optional[int] = Body(None, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    allowed_roles: Optional[List[str]] = Body(None, embed=True),
    entity_type: Optional[str] = Body(None, embed=True),
    entity_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.create_channel(
        name=name,
        description=description,
        is_public=is_public,
        created_by=created_by,
        country_code=country_code,
        allowed_roles=allowed_roles,
        entity_type=entity_type,
        entity_id=entity_id,
    )


@router.get("/channels")
def list_channels(
    user_id: int = Query(...),
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.list_channels(user_id, country_code)


@router.get("/channels/{channel_id}")
def get_channel(channel_id: str, db: Session = Depends(get_db)):
    service = get_internal_communication_service(db)
    result = service.get_channel(channel_id)
    if not result:
        raise HTTPException(status_code=404, detail="Channel not found")
    return result


@router.post("/channels/{channel_id}/members")
def add_member(
    channel_id: str,
    user_id: int = Body(..., embed=True),
    role: str = Body("member", embed=True),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.add_member(channel_id, user_id, role)


@router.delete("/channels/{channel_id}/members/{user_id}")
def remove_member(channel_id: str, user_id: int, db: Session = Depends(get_db)):
    service = get_internal_communication_service(db)
    return service.remove_member(channel_id, user_id)


@router.post("/channels/{channel_id}/messages")
def send_channel_message(
    channel_id: str,
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    is_masked: bool = Body(True, embed=True),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.send_message(channel_id, sender_id, content, message_type, is_masked)


@router.get("/channels/{channel_id}/messages")
def get_channel_messages(
    channel_id: str,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)


# ══════════════════════════════════════════════════════════════════════════════
# CHATBOT (from chatbot.py)
# ══════════════════════════════════════════════════════════════════════════════

from pydantic import BaseModel, Field
from infrastructure.security.dependencies import get_current_user_optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    lang: Optional[str] = "en"


class ProductClickRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


@router.post("/chatbot/message")
def chatbot_message(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) if current_user else None
    return handle_message(
        db=db,
        message=payload.message,
        user_id=user_id,
        session_id=payload.session_id,
        supplier_id=supplier_id,
        lang=payload.lang or "en",
    )


@router.post("/chatbot")
def chatbot_message_root(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return chatbot_message(payload, supplier_id, current_user, db)


@router.post("/chatbot/record-click/{product_id}")
def chatbot_record_click(
    product_id: int,
    payload: ProductClickRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    user_id = int(current_user.id) if current_user else None
    record_product_click(
        db=db,
        session_id=payload.session_id,
        product_id=product_id,
        user_id=user_id,
    )
    return {"status": "recorded"}


# ══════════════════════════════════════════════════════════════════════════════
# ENTERPRISE COMMUNICATION — WebSocket, incidents, masked messages (from comm.py)
# ══════════════════════════════════════════════════════════════════════════════

from infrastructure.messaging.ws_manager import manager


@router.post("/enterprise/video")
def create_enterprise_room(room_data: dict, db: Session = Depends(get_db)):
    return create_video_room(room_data, db)


@router.post("/enterprise/chat")
def create_enterprise_thread(thread_data: dict, db: Session = Depends(get_db)):
    return create_chat_thread(thread_data, db)


@router.post("/enterprise/message")
def send_enterprise_message(sender_id: int = Query(...), recipient_ref: str = Query(...), message: str = Query(...), db: Session = Depends(get_db)):
    return send_masked_message(sender_id, recipient_ref, message, db)


@router.post("/enterprise/incident")
def create_incident(alert_data: dict, db: Session = Depends(get_db)):
    return create_incident_room(alert_data, db)


@router.get("/enterprise/metrics")
def comm_metrics(db: Session = Depends(get_db)):
    return get_command_center_metrics(db)


@router.websocket("/ws/{room}")
async def websocket_endpoint(websocket: WebSocket, room: str):
    await manager.connect(websocket, room)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast_to_room(room, {"data": data})
    except Exception:
        manager.disconnect(websocket, room)
