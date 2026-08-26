"""Admin comms router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .chat import router as chat_router
from .email import router as email_router
from .notifications import router as notifications_router
from .tickets import router as tickets_router
from __future__ import annotations
from domains.accounts.models.user import User
from infrastructure.database.database import get_db
from domains.accounts.ports import list_video_rooms
from domains.accounts.services._auto_stubs import list_video_rooms_for_country
from domains.comms.models.chat import EntityChatMessage
from domains.comms.models.chat import EntityChatThread
from domains.comms.models.chat import VideoRoom
from domains.comms.models.marketing import (
from domains.comms.models.marketing import CampaignRecipient
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import NewsletterSubscriber
from domains.comms.services._auto_stubs import EntityChatService
from domains.comms.services._auto_stubs import ensure_video_room_country
from domains.comms.services._auto_stubs import get_chat_service
from domains.comms.services._auto_stubs import get_escalation_sla_service
from domains.comms.services._auto_stubs import get_video_conference
from domains.comms.services._auto_stubs import handle_message
from domains.comms.services._auto_stubs import list_all_video_rooms
from domains.comms.services._auto_stubs import record_product_click
from domains.comms.services._auto_stubs import video_room_metrics
from domains.comms.services.email.email_gateway import EmailGateway
from domains.comms.services.email.email_management import _serialize_template
from domains.comms.services.email.transactional import enqueue_invoice_email
from domains.comms.services.email.transactional import enqueue_low_stock_alert_email
from domains.comms.services.email.transactional import enqueue_order_created_email
from domains.comms.services.messaging.chat_service import ChatSystem
from domains.comms.services.messaging.chat_service import get_chat_system
from domains.country.utils.country_rls import get_country_or_404
from domains.governance.models.user import User
from domains.hr.services._auto_stubs import get_inbox
from infrastructure.database.database import get_db
from infrastructure.database.schemas import EmailCampaignCreate, EmailCampaignOut
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from infrastructure.utils.dependencies import get_current_user_optional
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.email_service import record_email_delivery_event
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from modules.admin.routers.auth import require_roles
from rbac import get_current_user
from seed_comms import seed as _seed_comms
from domains.comms.services.chat_system import ChatSystem, get_chat_system
from domains.comms.services.video_conferencing import VideoConferenceRoom, get_video_conference
from sqlalchemy import case as sql_case
from sqlalchemy import desc
from sqlalchemy import func as sqlfunc
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Annotated, Any, Dict, List, Optional
from typing import List, Optional
from typing import Optional
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.utils.dependencies import get_current_user, require_admin
from infrastructure.utils.ip_utils import get_ip_for_logging
import base64
import logging
import logging as _l; _l.getLogger(__name__).warning("skip chat_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip email_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip notifications_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip tickets_router: %s", _e)
import structlog

router = APIRouter(prefix="/api/v1/admin/comms", tags=["admin", "comms"])

@router.get("/chat")
def admin_list_all_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads")
def admin_list_chat_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{thread_id}/messages")
def admin_get_chat_thread_messages(
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{thread_id}/messages")
def admin_send_chat_thread_message(
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/direct")
def admin_create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/group")
def admin_create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/metrics")
def admin_chat_metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{country_code}")
def admin_list_threads(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{country_code}")
def admin_create_thread(
    country_code: str = Path(..., description="ISO country code"),
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads")
def admin_create_thread_global(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{country_code}/{thread_id}/messages")
def admin_get_thread_messages(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{country_code}/{thread_id}/messages")
def admin_send_thread_message(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat")
def admin_list_all_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads")
def admin_list_chat_threads(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{thread_id}/messages")
def admin_get_chat_thread_messages(
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{thread_id}/messages")
def admin_send_chat_thread_message(
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/direct")
def admin_create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/group")
def admin_create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/metrics")
def admin_chat_metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{country_code}")
def admin_list_threads(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{country_code}")
def admin_create_thread(
    country_code: str = Path(..., description="ISO country code"),
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads")
def admin_create_thread_global(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/chat/threads/{country_code}/{thread_id}/messages")
def admin_get_thread_messages(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    limit: int = Query(100, ge=1, le=500),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/chat/threads/{country_code}/{thread_id}/messages")
def admin_send_thread_message(
    country_code: str = Path(..., description="ISO country code"),
    thread_id: int = Path(...),
    sender_id: int = Body(...),
    message: str = Body(...),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/campaigns", response_model=list[EmailCampaignOut])
def list_all_campaigns(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """List all email campaigns across all countries (consolidated view)."""
    return db.query(EmailCampaign).order_by(EmailCampaign.created_at.desc()).limit(200).all()




@router.get("/metrics")
def admin_email_metrics(_: User = Depends(require_admin), db: Session = Depends(get_db)):
    """Consolidated email metrics across all countries."""
    total_subscribers = db.query(sqlfunc.count(NewsletterSubscriber.id)).filter(NewsletterSubscriber.is_active == True).scalar() or 0
    campaign_stats = db.query(
        sqlfunc.count(EmailCampaign.id).label("total"),
        sqlfunc.sum(sql_case((EmailCampaign.status == "sending", 1), else_=0)).label("active"),
        sqlfunc.count(CampaignRecipient.id).label("total_sent"),
    ).first()
    total_sent = int(campaign_stats.total_sent or 0)
    return {
        "total_subscribers": total_subscribers,
        "active_campaigns": int(campaign_stats.active or 0),
        "total_campaigns": int(campaign_stats.total or 0),
        "total_sent": total_sent,
    }




@router.get("/campaigns/{country_code}")
def list_campaigns(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        q = db.query(EmailCampaign).filter(EmailCampaign.country_code == country_code.upper())
        total = q.count()
        rows = q.order_by(EmailCampaign.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"data": rows, "total": total, "page": page, "page_size": page_size}
    finally:
        clear_rls_context()




@router.post("/campaigns/{country_code}", response_model=EmailCampaignOut, status_code=201)
def create_campaign(country_code: str = Path(..., description="ISO country code"), payload: EmailCampaignCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        allowed = {"name", "subject", "status", "send_at", "created_by", "country_code"}
        data = {k: v for k, v in payload.model_dump().items() if k in allowed and v is not None}
        data["country_code"] = country_code.upper()
        c = EmailCampaign(**data)
        db.add(c); db.commit(); db.refresh(c)
        return c
    finally:
        clear_rls_context()




@router.delete("/campaigns/{country_code}/{campaign_id}")
def delete_campaign(country_code: str = Path(..., description="ISO country code"), campaign_id: int = Path(...), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        c = db.query(EmailCampaign).filter(EmailCampaign.id == campaign_id, EmailCampaign.country_code == country_code.upper()).first()
        if not c: raise HTTPException(404)
        db.delete(c); db.commit()
        return {"message": "Deleted"}
    finally:
        clear_rls_context()




@router.get("/video")
def admin_list_all_rooms(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/video/rooms")
def admin_list_video_rooms(
    request: Request,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/video/rooms")
def admin_create_video_room(
    request: Request,
    name: str = Body(...),
    purpose: str = Body("meeting"),
    max_participants: int = Body(10),
    created_by: Optional[int] = Body(None),
    participants: Optional[List[int]] = Body(None),
    is_boardroom: Optional[bool] = Body(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/video/metrics")
def admin_video_metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/video/rooms/{country_code}")
def admin_list_rooms(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/video/rooms/{country_code}")
def admin_create_room(
    country_code: str = Path(..., description="ISO country code"),
    name: str = Body(...),
    purpose: str = Body("meeting"),
    max_participants: int = Body(10),
    created_by: Optional[int] = Body(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.post("/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)


@router.post("/group")
def create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    db: Session = Depends(get_db)


@router.post("/message")
def send_message(
    chat_id: str = Body(..., embed=True),
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db)


@router.get("/history/{chat_id}")
def get_history(chat_id: str, limit: int = 100, db: Session = Depends(get_db)):
    chat = get_chat_system(db)
    return chat.get_chat_history(chat_id, limit)




@router.get("/threads")
def list_threads(db: Session = Depends(get_db)):
    chat = get_chat_system(db)
    return chat.list_threads()




@router.post("/threads")
def create_thread(
    title: str = Query(...),
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),


@router.get("/threads/{thread_id}/messages")
def get_thread_messages(
    thread_id: int,
    limit: int = Query(50, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Message ID to fetch messages before (cursor-based pagination)"),
    db: Session = Depends(get_db),


@router.post("/threads/{thread_id}/messages")
def send_thread_message(
    thread_id: int,
    sender_id: int = Body(..., embed=True),
    message: str = Body(..., embed=True),
    db: Session = Depends(get_db),


@router.post("/threads/{thread_id}/messages/upload")
async def send_thread_message_with_attachments(
    thread_id: int,
    sender_id: int = Form(...),
    message: str = Form(""),
    files: list[UploadFile] = File(None),
    db: Session = Depends(get_db),
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


@router.get("/unified-inbox/reset")
def reset_unified_inbox(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),


@router.get("/unified-inbox")
def unified_inbox(
    lens: str = Query("all"),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    transport: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),


@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)


@router.get("/rooms")
def list_rooms(db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.list_rooms()




@router.post("/rooms/{room_id}/tokens")
def generate_token(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    ip_address: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)


@router.post("/rooms/{room_id}/recording")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)


@router.post("/rooms/{room_id}/end")
def end_room(
    room_id: str,
    db: Session = Depends(get_db)


@router.get("/rooms/{room_id}")
def get_room_details(room_id: str, db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)



@router.post("/track")
def track_message(
    message_id: int,
    message_type: str,
    recipient_id: int,
    priority: str = "normal",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/check")
def check_escalations(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/{tracking_id}/acknowledge")
def acknowledge_escalation(
    tracking_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),


@router.post("/message")
def chat_message(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),


@router.post("")
def chat_message_root(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),


@router.post("/record-click/{product_id}")
def chat_record_click(
    product_id: int,
    payload: ProductClickRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),

