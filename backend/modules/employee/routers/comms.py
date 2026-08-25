"""Employee comms router — consolidated from 23 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from domains.comms.services._auto_stubs import get_internal_communication_service
from infrastructure.database.database import get_db
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

router = APIRouter(prefix="/api/v1/employee/comms", tags=["employee", "comms"])


# === From chat.py ===
"""Chat Router"""
from modules.employee.routers.chat_api import router as chat_router

router = chat_router




# === From chat_api.py ===
"""Chat API sub-router.

PLACEHOLDER: the original ``routers.chat_api`` module is missing. This stub exposes an
empty ``APIRouter`` so ``routers.chat`` can mount it. Implement the real chat endpoints
and replace this file.
"""
from fastapi import APIRouter



# === From chat_enrichment.py ===
"""Chat Enrichment Router — emoji reactions, message edit/delete, legal hold, voice notes."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.comms.services._auto_stubs import add_reaction
from domains.comms.services._auto_stubs import apply_legal_hold
from domains.comms.services._auto_stubs import create_voice_note_attachment
from domains.comms.services._auto_stubs import delete_message
from domains.comms.services._auto_stubs import edit_message
from domains.comms.services._auto_stubs import get_reactions
from domains.comms.services._auto_stubs import is_legal_hold_active
from domains.comms.services._auto_stubs import release_legal_hold
from domains.comms.services._auto_stubs import remove_reaction
from domains.comms.services._auto_stubs import upload_attachment

logger = logging.getLogger(__name__)

# ── Reactions ────────────────────────────────────────────────────


@router.post("/reactions")
def api_add_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_reaction(db, message_id, message_type, current_user.id, emoji)


@router.delete("/reactions")
def api_remove_reaction(
    message_id: int,
    message_type: str,
    emoji: str,
    current_user: User = Depends(get_current_user),
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


# ── Message Edit / Delete ────────────────────────────────────────


@router.put("/messages/{message_type}/{message_id}")
def api_edit_message(
    message_type: str,
    message_id: int,
    body: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return edit_message(db, message_id, message_type, body, current_user.id)


@router.delete("/messages/{message_type}/{message_id}")
def api_delete_message(
    message_type: str,
    message_id: int,
    hard_delete: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return delete_message(db, message_id, message_type, current_user.id, hard_delete)


# ── Legal Hold ───────────────────────────────────────────────────


@router.post("/legal-hold")
def api_apply_legal_hold(
    room_id: int,
    room_type: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return apply_legal_hold(db, room_id, room_type, current_user.id, reason)


@router.delete("/legal-hold/{room_type}/{room_id}")
def api_release_legal_hold(
    room_type: str,
    room_id: int,
    current_user: User = Depends(get_current_user),
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


# ── Voice Note / Attachment Upload ───────────────────────────────


@router.post("/attachments/voice")
def api_upload_voice_note(
    message_id: int,
    message_type: str,
    file_url: str,
    file_name: str,
    file_size_bytes: int,
    duration_seconds: int,
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return upload_attachment(
        db, message_id, message_type, attachment_type, file_url, file_name,
        file_size_bytes, mime_type, duration_seconds, thumbnail_url,
    )



# === From chatbot.py ===
"""Chatbot router — AI product assistant."""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from domains.comms.services._auto_stubs import handle_message
from domains.comms.services._auto_stubs import record_product_click
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.dependencies import get_current_user_optional

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    lang: Optional[str] = "en"


class ProductClickRequest(BaseModel):
    session_id: str = Field(..., min_length=1)


@router.post("/message")
def chat_message(
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


@router.post("")
def chat_message_root(
    payload: ChatRequest,
    supplier_id: Optional[int] = Query(default=None, ge=1),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    return chat_message(payload, supplier_id, current_user, db)


@router.post("/record-click/{product_id}")
def chat_record_click(
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




# === From comm.py ===
"""Enterprise Communication Router."""

from fastapi import APIRouter, Depends, Query, WebSocket
from sqlalchemy.orm import Session

from domains.comms.services._auto_stubs import create_chat_thread
from domains.comms.services._auto_stubs import create_incident_room
from domains.comms.services._auto_stubs import create_video_room
from domains.comms.services._auto_stubs import get_command_center_metrics
from domains.comms.services._auto_stubs import send_masked_message
from infrastructure.database.database import get_db
from infrastructure.utils.websocket_manager import manager

@router.post("/video")
def create_room(room_data: dict, db: Session = Depends(get_db)):
    return create_video_room(room_data, db)


@router.post("/chat")
def create_thread(thread_data: dict, db: Session = Depends(get_db)):
    return create_chat_thread(thread_data, db)


@router.post("/message")
def send_message(sender_id: int = Query(...), recipient_ref: str = Query(...), message: str = Query(...), db: Session = Depends(get_db)):
    return send_masked_message(sender_id, recipient_ref, message, db)


@router.post("/incident")
def create_incident(alert_data: dict, db: Session = Depends(get_db)):
    return create_incident_room(alert_data, db)


@router.get("/metrics")
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




# === From comms_chat.py ===
"""
Chat System router (legacy hand-written).

Thin HTTP layer; all logic lives in services.comms.chat_system. Previously this
lived in controllers/comms/chat_controller.py, which violated the rule that a
controller must not declare FastAPI routes.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.comms.services.messaging.chat_service import ChatSystem
from domains.comms.services.messaging.chat_service import get_chat_system

logger = logging.getLogger("zozi.api.chat")

@router.post("/direct")
def create_direct_chat(
    participants: List[int] = Body(..., embed=True),
    name: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.create_direct_chat(participants, name)


@router.post("/group")
def create_group_chat(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_encrypted: bool = Body(False, embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.create_group_chat(name, participants, is_encrypted)


@router.post("/message")
def send_message(
    chat_id: str = Body(..., embed=True),
    sender_id: int = Body(..., embed=True),
    content: str = Body(..., embed=True),
    message_type: str = Body("text", embed=True),
    db: Session = Depends(get_db)
):
    chat = get_chat_system(db)
    return chat.send_message(chat_id, sender_id, content, message_type)


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
):
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
    chat = get_chat_system(db)
    return chat.mark_read(chat_id, user_id)



# === From comms_unified.py ===
"""Unified Inbox — cursor-paginated merge of all communication channels."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.utils.dependencies import get_current_user, require_admin
from infrastructure.utils.ip_utils import get_ip_for_logging

logger = logging.getLogger("zozi.api.comms")

@router.get("/unified-inbox/reset")
def reset_unified_inbox(
    request: Request,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Reset the unified inbox demo data.

    Admin-only endpoint that clears all communication seed data
    (entity threads, DMs, group chats, internal emails) and
    re-seeds it with realistic demo conversations.

    Useful for resetting the Communication workspace from the UI
    without requiring SSH or terminal access.

    Every reset is recorded in the audit log with the admin user's
    ID, timestamp, and IP address for traceability.
    """
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
            details={
                "action": "reset_unified_inbox",
                "endpoint": "/comms/unified-inbox/reset",
            },
        )

        return {
            "status": "ok",
            "message": "Communication data reset and re-seeded successfully",
        }
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
            details={
                "action": "reset_unified_inbox",
                "endpoint": "/comms/unified-inbox/reset",
                "error": str(exc),
            },
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset inbox: {str(exc)}",
        )


@router.get("/unified-inbox")
def unified_inbox(
    lens: str = Query("all"),
    cursor: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    transport: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Return a cursor-paginated, server-sorted merge of all conversation
    types — DMs, group mentions, channel posts, internal emails — each as
    a normalized row.

    The unified inbox is powered by a UNION of all message sources ordered
    by `updated_at DESC`. `cursor` is a base64-encoded `<updated_at>::<id>`
    pair from the last visible row so the client requests the next page.
    """
    import base64

    where = "1=1"
    params: dict = {"limit": limit + 1}  # fetch +1 for has_more

    if transport:
        where += " AND transport = :transport"
        params["transport"] = transport

    if lens == "unread":
        where += " AND unread > 0"
    elif lens == "mentions":
        where += " AND channel_type = 'mention'"

    if cursor:
        try:
            decoded = base64.urlsafe_b64decode(cursor).decode()
            ts, cid = decoded.split("::", 1)
            where += " AND (updated_at, id) < (:cursor_ts, :cursor_id)"
            params["cursor_ts"] = ts
            params["cursor_id"] = int(cid) if cid.isdigit() else cid
        except Exception:
            pass

    sql = f"""
        SELECT * FROM (
            -- Direct messages
            SELECT
                'dm_' || dcr.id AS id,
                dcr.id AS local_id,
                'chat' AS transport,
                u.full_name AS title,
                SUBSTR(dcm.message, 1, 120) AS preview,
                CASE WHEN dcm.read_at IS NULL AND dcm.sender_id != :user_id THEN 1 ELSE 0 END AS unread,
                dcm.created_at AS updated_at,
                'direct' AS channel_type,
                0 AS participants,
                NULL AS peer_avatar,
                NULL AS folder
            FROM direct_chat_messages dcm
            JOIN direct_chat_rooms dcr ON dcr.id = dcm.room_id
            JOIN users u ON u.id = CASE WHEN dcr.participant_one = :user_id THEN dcr.participant_two ELSE dcr.participant_one END
            WHERE :user_id IN (dcr.participant_one, dcr.participant_two)

            UNION ALL

            -- Group messages
            SELECT
                'grp_' || gcm.id,
                gcm.id,
                'group',
                gcr.name,
                SUBSTR(gcm.message, 1, 120),
                CASE WHEN gcm.read_at IS NULL AND gcm.sender_id != :user_id THEN 1 ELSE 0 END,
                gcm.created_at,
                'group',
                (SELECT COUNT(*) FROM group_chat_members WHERE room_id = gcr.id),
                NULL,
                NULL AS folder
            FROM group_chat_messages gcm
            JOIN group_chat_rooms gcr ON gcr.id = gcm.room_id
            JOIN group_chat_members gcmem ON gcmem.room_id = gcr.id AND gcmem.user_id = :user_id

            UNION ALL

            -- Internal channels
            SELECT
                'ch_' || im.id,
                im.id,
                'group',
                ic.name,
                SUBSTR(im.message, 1, 120),
                CASE WHEN im.read_at IS NULL AND im.user_id != :user_id THEN 1 ELSE 0 END,
                im.created_at,
                'channel',
                (SELECT COUNT(*) FROM internal_channel_members WHERE channel_id = ic.id),
                NULL,
                NULL AS folder
            FROM internal_messages im
            JOIN internal_channels ic ON ic.id = im.channel_id
            JOIN internal_channel_members icm ON icm.channel_id = ic.id AND icm.user_id = :user_id

            UNION ALL

            -- Internal emails
            SELECT
                'eml_' || ie.id,
                ie.id,
                'email',
                ie.subject,
                SUBSTR(ie.body_text, 1, 120),
                CASE WHEN ef.name = 'inbox' THEN 1 ELSE 0 END,
                ie.created_at,
                'email',
                0,
                NULL,
                ef.name
            FROM internal_emails ie
            JOIN email_folders ef ON ef.id = ie.folder_id
            JOIN employees e ON e.id = ef.employee_id AND e.user_id = :user_id

        ) AS inbox
        WHERE {where}
        ORDER BY updated_at DESC, id DESC
        LIMIT :limit
    """

    user_id = int(current_user.id)
    params["user_id"] = user_id

    rows = db.execute(text(sql), params).mappings().all()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    items = []
    next_cursor = None
    for r in rows:
        ts = r["updated_at"]
        if hasattr(ts, "isoformat"):
            ts = ts.isoformat()
        items.append({
            "id": str(r["id"]),
            "transport": r["transport"],
            "title": r["title"],
            "preview": r["preview"],
            "unread": r["unread"],
            "updatedAt": ts,
            "channelType": r["channel_type"],
            "participants": r["participants"] or 0,
            "peerAvatar": r["peer_avatar"],
            "folder": r["folder"],
        })

    if has_more and rows:
        last = rows[-1]
        ts = last["updated_at"]
        if hasattr(ts, "isoformat"):
            ts = ts.isoformat()
        raw = f"{ts}::{last['local_id']}"
        next_cursor = base64.urlsafe_b64encode(raw.encode()).decode()

    return {"items": items, "nextCursor": next_cursor, "hasMore": has_more}




# === From comms_video.py ===
"""
Video Conferencing router (legacy hand-written).

Thin HTTP layer; all logic lives in services.comms.video_conferencing. Previously
this lived in controllers/comms/video_controller.py, which violated the rule that
a controller must not declare FastAPI routes.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.comms.services._auto_stubs import VideoConferenceRoom
from domains.comms.services._auto_stubs import get_video_conference

logger = logging.getLogger("zozi.api.video")

@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code)


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
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address)


@router.post("/rooms/{room_id}/recording")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/end")
def end_room(
    room_id: str,
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}")
def get_room_details(room_id: str, db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)



# === From email.py ===
"""
Email Router — send, manage templates, and handle delivery webhooks.
"""

import logging
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from domains.security.services.iam.security_dependencies import require_roles
from infrastructure.database.database import get_db
from domains.comms.models.marketing import EmailCampaign
from domains.comms.models.marketing import EmailRuntimeConfig
from domains.comms.models.marketing import EmailSuppression
from domains.comms.models.marketing import EmailTemplate
from domains.comms.services.email.email_gateway import EmailGateway
from domains.comms.services.email.transactional import enqueue_invoice_email
from domains.comms.services.email.transactional import enqueue_low_stock_alert_email
from domains.comms.services.email.transactional import enqueue_order_created_email
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

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


@public_router.post("/webhooks/resend")
async def resend_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive delivery event webhooks from Resend."""
    try:
        payload = await request.json()
        event_type = payload.get("type", "")
        email_id = payload.get("data", {}).get("email_id", "")
        logger.info("Email webhook: type=%s email_id=%s", event_type, email_id)
    except Exception as exc:
        logger.debug("Webhook parse error: %s", exc)
    return {"status": "received"}


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
def list_templates(current_user: AdminUser, db: Session = Depends(get_db)):
    templates = db.query(EmailTemplate).order_by(desc(EmailTemplate.created_at)).all()
    return [_serialize_template(t) for t in templates]


@router.get("/campaigns")
def list_campaigns(current_user: AdminUser, db: Session = Depends(get_db)):
    from domains.comms.models.marketing import EmailCampaign
    campaigns = db.query(EmailCampaign).order_by(desc(EmailCampaign.created_at)).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "subject": c.subject,
            "status": c.status,
            "sent_count": c.sent_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ]


@router.get("/suppressions")
def list_suppressions(
    status: Optional[str] = Query(None),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
    q = db.query(EmailSuppression)
    if status:
        q = q.filter(EmailSuppression.status == status)
    suppressions = q.all()
    return [
        {
            "id": s.id,
            "email": s.email,
            "reason": s.reason,
            "source": s.source,
            "provider": s.provider,
            "status": s.status,
            "notes": s.notes,
            "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
            "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in suppressions
    ]


@router.patch("/suppressions/{suppression_id}")
def update_suppression(
    suppression_id: int,
    body: Dict[str, Any] = Body(default={}),
    current_user: AdminOrSuperAdminUser = None,
    db: Session = Depends(get_db),
):
    s = db.query(EmailSuppression).filter(EmailSuppression.id == suppression_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Suppression not found")
    if "status" in body:
        s.status = body["status"]
        if body["status"] == "active" and not s.suppressed_at:
            s.suppressed_at = _utcnow()
        s.last_event_at = _utcnow()
    if "reason" in body:
        s.reason = body["reason"]
    if "notes" in body:
        s.notes = body["notes"]
    db.commit()
    db.refresh(s)
    return {
        "id": s.id,
        "email": s.email,
        "reason": s.reason,
        "source": s.source,
        "provider": s.provider,
        "status": s.status,
        "notes": s.notes,
        "suppressed_at": s.suppressed_at.isoformat() if s.suppressed_at else None,
        "last_event_at": s.last_event_at.isoformat() if s.last_event_at else None,
    }


@router.post("/campaigns")
def create_campaign(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    campaign = EmailCampaign(
        name=payload.get("name", "Untitled Campaign"),
        subject=payload.get("subject", ""),
        status=payload.get("status", "draft"),
        target_audience=payload.get("target_audience"),
        country_code=payload.get("country_code"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return {
        "id": campaign.id,
        "name": campaign.name,
        "subject": campaign.subject,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat() if campaign.created_at else None,
    }


@router.post("/templates")
def create_template(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    template = EmailTemplate(
        name=payload.get("name", ""),
        subject=payload.get("subject", ""),
        content=payload.get("content"),
        template_type=payload.get("template_type", "marketing"),
        created_by=current_user.get("id") if isinstance(current_user, dict) else None,
    )
    db.add(template)
    db.commit()
    db.refresh(template)
    return _serialize_template(template)


@router.put("/templates/{template_id}")
def update_template(
    template_id: int,
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    if "name" in payload:
        template.name = payload["name"]
    if "subject" in payload:
        template.subject = payload["subject"]
    if "content" in payload:
        template.content = payload["content"]
    if "template_type" in payload:
        template.template_type = payload["template_type"]
    db.commit()
    db.refresh(template)
    return _serialize_template(template)


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"message": "Template deleted", "id": template_id}


def _serialize_template(t: EmailTemplate) -> dict:
    return {
        "id": t.id,
        "name": t.name,
        "subject": t.subject,
        "content": t.content,
        "template_type": t.template_type,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _email_runtime_to_dict(cfg: EmailRuntimeConfig) -> dict:
    resend_key = bool(cfg.resend_api_key)
    resend_secret = bool(cfg.resend_webhook_secret)
    return {
        "id": cfg.id,
        "provider": cfg.provider,
        "active_provider": cfg.provider,
        "source": "db",
        "available": True,
        "live": cfg.provider not in ("disabled", None),
        "preview_only": cfg.provider == "environment",
        "supports_webhooks": True,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port or 587,
        "smtp_username": cfg.smtp_username,
        "smtp_use_tls": cfg.smtp_use_tls,
        "smtp_use_ssl": cfg.smtp_use_ssl,
        "smtp_timeout_seconds": cfg.smtp_timeout_seconds or 15,
        "email_from_default": cfg.email_from_default,
        "email_from_promotional": cfg.email_from_promotional,
        "email_from_transactional": cfg.email_from_transactional,
        "email_from_notification": cfg.email_from_notification,
        "email_from_alert": cfg.email_from_alert,
        "email_from_verification": cfg.email_from_verification,
        "email_from_login_verification": cfg.email_from_login_verification,
        "email_from_password_reset": cfg.email_from_password_reset,
        "resend_api_key_configured": resend_key,
        "resend_webhook_secret_configured": resend_secret,
        "smtp_password_configured": bool(cfg.smtp_password),
    }


@router.get("/config/runtime")
def get_email_runtime_config(current_user: AdminUser = None, db: Session = Depends(get_db)):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig(provider="environment", smtp_port=587)
        db.add(cfg)
        db.commit()
        db.refresh(cfg)
    return _email_runtime_to_dict(cfg)


@router.put("/config/runtime")
def update_email_runtime_config(
    payload: Dict[str, Any] = Body(default={}),
    current_user: AdminUser = None,
    db: Session = Depends(get_db),
):
    cfg = db.query(EmailRuntimeConfig).order_by(EmailRuntimeConfig.id.asc()).first()
    if not cfg:
        cfg = EmailRuntimeConfig()
        db.add(cfg)
    simple_fields = [
        "provider", "smtp_host", "smtp_port", "smtp_username",
        "smtp_use_tls", "smtp_use_ssl", "smtp_timeout_seconds",
        "email_from_default", "email_from_promotional", "email_from_transactional",
        "email_from_notification", "email_from_alert", "email_from_verification",
        "email_from_login_verification", "email_from_password_reset",
    ]
    for field in simple_fields:
        if field in payload:
            setattr(cfg, field, payload[field])
    # Only overwrite secrets when a non-empty value is supplied.
    if payload.get("resend_api_key"):
        cfg.resend_api_key = payload["resend_api_key"]
    if payload.get("resend_webhook_secret"):
        cfg.resend_webhook_secret = payload["resend_webhook_secret"]
    if payload.get("smtp_password"):
        cfg.smtp_password = payload["smtp_password"]
    db.commit()
    db.refresh(cfg)
    return _email_runtime_to_dict(cfg)


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


@public_router.get("/track/open")
async def track_open(email_id: str = Query(...), user_id: int = Query(None)):
    """Tracking pixel for email open detection."""
    try:
        from infrastructure.utils.email_service import record_email_delivery_event
        record_email_delivery_event(email_id=email_id, user_id=user_id, event_type="open")
    except Exception:
        pass
    return Response(content=_TRANSPARENT_GIF, media_type="image/gif")


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
    from domains.hr.services._auto_stubs import get_inbox
    employee_id = current_user.get("id") if isinstance(current_user, dict) else 0
    return get_inbox(db, employee_id=employee_id, folder=folder, limit=limit, offset=offset)




# === From email_controller.py ===
"""email controller router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

@router.get("/email_controller/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "email_controller", "prefix": "/api/v1/email-gateway"}



# === From email_enrichment.py ===
"""Email Enrichment Router — smart addressing, DLP scanning, notifications."""

import logging
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.comms.services._auto_stubs import resolve_address
from domains.comms.services._auto_stubs import resolve_recipients
from domains.comms.services._auto_stubs import scan_content_for_dlp
from domains.comms.services._auto_stubs import send_email_notification

logger = logging.getLogger(__name__)

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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sender_role = current_user.get("role", "")
    return scan_content_for_dlp(subject, body_html, sender_role)


@router.post("/notify")
def api_send_notification(
    recipient_employee_id: int,
    email_id: int,
    subject: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    send_email_notification(db, recipient_employee_id, email_id, subject)
    return {"notified": True, "employee_id": recipient_employee_id}



# === From entity_chat.py ===
"""
Entity Chat API
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.comms.services._auto_stubs import get_chat_service

@router.post("/threads", response_model=dict)
async def create_thread(
    entity_type: str,
    entity_id: int,
    title: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
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


@router.post("/threads/{thread_id}/messages", response_model=dict)
async def send_message(
    thread_id: int,
    message: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == int(current_user["sub"])).first()
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


@router.get("/threads/{thread_id}/messages", response_model=dict)
async def get_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    messages = service.get_thread_messages(thread_id, limit, offset)
    return {"messages": messages}


@router.get("/entities/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_chat_service(db)
    thread = service.get_entity_thread(entity_type, entity_id)
    return thread or {"exists": False}



# === From entity_communication.py ===
"""
Entity Communication Router
Links emails, chats, and calls to business entities
"""
from typing import List, Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.comms.services.email.email_gateway import get_email_gateway
from domains.comms.services._auto_stubs import get_chat_service

@router.get("/threads/{entity_type}/{entity_id}", response_model=dict)
async def get_entity_thread(
    entity_type: str,
    entity_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    thread = chat_service.get_entity_thread(entity_type, entity_id)
    if not thread:
        thread = chat_service.create_or_get_thread(entity_type, entity_id)
    return thread


@router.post("/threads/{thread_id}/messages", response_model=dict)
async def send_thread_message(
    thread_id: int,
    message: str,
    sender_id: int,
    current_user: dict = Depends(get_current_user),
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


@router.get("/threads/{thread_id}/messages", response_model=List[dict])
async def get_thread_messages(
    thread_id: int,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_service = get_chat_service(db)
    return chat_service.get_thread_messages(thread_id, limit, offset)


@router.post("/email/send", response_model=dict)
async def send_entity_email(
    entity_type: str,
    entity_id: int,
    to_email: str,
    subject: str,
    body: str,
    sender_id: int,
    template_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
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



# === From internal_channels.py ===



logger = logging.getLogger("zozi.api.internal")

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
def send_message(
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
def get_messages(
    channel_id: str,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)



# === From internal_comms_channels.py ===



logger = logging.getLogger("zozi.api.internal")

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
def send_message(
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
def get_messages(
    channel_id: str,
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    service = get_internal_communication_service(db)
    return service.get_messages(channel_id, limit, offset)



# === From messaging.py ===
"""Email Gateway Router"""
from modules.employee.routers.email_controller import router as email_router

router = email_router




# === From notifications.py ===
"""
Notification Engine API Endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.comms.services._auto_stubs import NotificationChannel
from domains.comms.services._auto_stubs import NotificationPriority
from domains.comms.services._auto_stubs import get_notification_engine

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


@router.post("/send")
def send_notification(
    user_id: int,
    title: str,
    message: str,
    channel: str = "in_app",
    priority: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_notification_engine(db)
    return engine.send(user_id, title, message, _parse_channel(channel), _parse_priority(priority))


@router.post("/bulk")
def send_bulk_notifications(
    user_ids: list,
    title: str,
    message: str,
    channel: str = "email",
    priority: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = get_notification_engine(db)
    return engine.send_bulk(user_ids, title, message, _parse_channel(channel), _parse_priority(priority))


@router.get("")
def get_notifications(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    unread_only: bool = False,
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.get_user_notifications(user_id, unread_only)


@router.post("/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.get("id")
    engine = get_notification_engine(db)
    return engine.mark_read(notification_id, user_id)



# === From proxy_communication.py ===
"""
Proxy Communication Channels API
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.utils.dependencies import require_admin
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.comms.models.communication import ProxyChannel
from domains.comms.services.proxy_communication import get_proxy_service

@router.post("/channels", response_model=dict)
async def create_proxy_channel(
    entity_type: str,
    entity_id: int,
    participant_ids: List[int],
    current_user: dict = Depends(get_current_user),
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


@router.get("/channels/{channel_id}", response_model=dict)
async def get_proxy_channel(
    channel_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channel = db.query(ProxyChannel).filter_by(id=channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Proxy channel not found")
    proxy_service = get_proxy_service(db)
    return {
        "id": channel.id,
        "entity_type": channel.entity_type,
        "entity_id": channel.entity_id,
        "proxy_phone": proxy_service.mask_phone_number(channel.proxy_phone) if channel.proxy_phone else None,
        "proxy_email": channel.proxy_email,
        "is_active": channel.is_active,
        "participants": channel.participants
    }


@router.post("/sessions", response_model=dict)
async def start_proxy_session(
    channel_id: int,
    participant_one_id: int,
    participant_two_id: int,
    metadata: Optional[dict] = None,
    current_user: dict = Depends(get_current_user),
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


@router.post("/messages", response_model=dict)
async def send_proxy_message(
    session_id: int,
    sender_id: int,
    recipient_id: int,
    content: str,
    message_type: str = "text",
    current_user: dict = Depends(get_current_user),
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


@router.post("/calls/initiate", response_model=dict)
async def initiate_call(
    channel_id: int,
    caller_id: int,
    callee_id: int,
    current_user: dict = Depends(get_current_user),
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


@router.post("/calls/{call_id}/end", response_model=dict)
async def end_call(
    call_id: int,
    duration_seconds: int,
    recording_url: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    proxy_service = get_proxy_service(db)
    proxy_service.end_call(call_id, duration_seconds, recording_url)
    return {"status": "ended"}


@router.get("/users/{user_id}/channels", response_model=List[dict])
async def get_user_channels(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    channels = db.query(ProxyChannel).filter(
        ProxyChannel.participants.contains({"user_ids": [user_id]})
    ).all()
    proxy_service = get_proxy_service(db)
    return [
        {
            "id": c.id,
            "proxy_phone": proxy_service.mask_phone_number(c.proxy_phone) if c.proxy_phone else None,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active
        }
        for c in channels
    ]


@router.get("/admin/channels", response_model=List[dict])
async def admin_list_channels(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    channels = db.query(ProxyChannel).all()
    proxy_service = get_proxy_service(db)
    return [
        {
            "id": c.id,
            "entity_type": c.entity_type,
            "entity_id": c.entity_id,
            "proxy_phone": c.proxy_phone,
            "proxy_email": c.proxy_email,
            "is_active": c.is_active
        }
        for c in channels
    ]



# === From push_notifications.py ===
"""push notifications router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

@router.get("/push_notifications/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "push_notifications", "prefix": "/api/v1/push-notifications"}



# === From tickets.py ===
"""Support tickets router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from infrastructure.database.database import get_db
from domains.comms.models.communication_schema_models import SupportTicket
from domains.governance.models.user import User
from domains.comms.models.communication import TicketMessage
from infrastructure.utils.dependencies import get_current_user

__router_prefix__ = "/tickets"


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


@router.get("")
def list_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    q = db.query(SupportTicket)
    if current_user.role == "customer":
        q = q.filter(SupportTicket.user_id == current_user.id)
    total = q.count()
    tickets = q.order_by(SupportTicket.created_at.desc()).options(selectinload(SupportTicket.messages)).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": [_ticket_payload(t) for t in tickets], "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=201)
def create_ticket(payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).options(selectinload(SupportTicket.messages)).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(404)
    if current_user.role == "customer" and ticket.user_id != current_user.id:
        raise HTTPException(404)
    replies = db.query(TicketMessage).filter(TicketMessage.ticket_id == ticket_id).order_by(TicketMessage.created_at.asc()).all()
    return _ticket_payload(ticket, replies)


@router.post("/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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


@router.post("/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: int, payload: dict = Body(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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




# === From video.py ===
"""
Video Conferencing Router
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from domains.comms.services._auto_stubs import get_video_conference
from infrastructure.utils.dependencies import get_db

logger = logging.getLogger("zozi.api.video")

@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code)


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
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address)


@router.post("/rooms/{room_id}/recording")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/end")
def end_room(
    room_id: str,
    db: Session = Depends(get_db)
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}")
def get_room_details(room_id: str, db: Session = Depends(get_db)):
    vc = get_video_conference(db)
    return vc.get_room_details(room_id)



# === From video_controller.py ===
"""Video Conference Controller for admin and employee meetings."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.comms.services._auto_stubs import get_video_conference
from infrastructure.utils.dependencies import require_admin

logger = logging.getLogger("zozi.api.video")

@router.post("/rooms")
def create_room(
    name: str = Body(..., embed=True),
    participants: List[int] = Body(..., embed=True),
    is_boardroom: bool = Body(False, embed=True),
    country_code: Optional[str] = Body(None, embed=True),
    employee_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.create_room(name, participants, is_boardroom, country_code, employee_id)


@router.get("/rooms")
def list_rooms(
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.list_rooms()


@router.get("/rooms/{room_id}")
def get_room(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.generate_token(room_id, employee_id, ip_address, device_fingerprint, country_code)


@router.post("/rooms/{room_id}/recording/start")
def start_recording(
    room_id: str,
    employee_id: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.start_recording(room_id, employee_id)


@router.post("/rooms/{room_id}/recording/end")
def end_recording(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    return vc.end_room(room_id)


@router.get("/rooms/{room_id}/transcript")
def get_transcript(
    room_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
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
    _: User = Depends(require_admin),
):
    vc = get_video_conference(db)
    from datetime import datetime
    return await vc.add_transcript_segment(
        room_id, speaker_id, content, 
        datetime.fromisoformat(timestamp) if timestamp else None,
        language, audio_bytes, target_language
    )



# === From ws_chat.py ===
"""ws chat router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter

@router.get("/ws_chat/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "ws_chat", "prefix": "/api/v1/ws-chat"}

