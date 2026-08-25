"""Employee suppliers router — consolidated from 7 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/employee/suppliers", tags=["employee", "suppliers"])


# === From travel.py ===
"""
Corporate Travel Router
"""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.travel.travel_service import get_travel_service


@router.post("/requests", response_model=dict)
async def create_travel_request(
    employee_id: int,
    destination_country: str,
    start_date: str,
    end_date: str,
    purpose: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.create_travel_request(
        employee_id=employee_id,
        destination_country=destination_country,
        start_date=start_date,
        end_date=end_date,
        purpose=purpose
    )


@router.post("/expenses/validate", response_model=dict)
async def validate_expense(
    employee_id: int,
    amount: float,
    currency: str,
    description: str,
    receipt_image_hash: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.validate_expense(
        employee_id=employee_id,
        amount=amount,
        currency=currency,
        description=description,
        receipt_image_hash=receipt_image_hash
    )


@router.post("/requests/{request_id}/approve", response_model=dict)
async def approve_travel_request(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.approve_travel_request(request_id, int(current_user["sub"]))


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


# === From messaging.py ===
"""Email Gateway Router"""
from modules.employee.routers.email_controller import router as email_router

router = email_router


