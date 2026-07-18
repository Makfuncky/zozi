"""Admin Video Router — consolidated + country-scoped wrapper around VideoConferenceRoom endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Request
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from db.database import get_db
from models import User
from models.core import VideoRoom
from services.video_conferencing import get_video_conference
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger("zozi.api.admin_video")
router = APIRouter()


def _serialize_room(r: VideoRoom) -> dict:
    return {
        "id": r.id,
        "room_uuid": r.room_uuid,
        "name": r.name,
        "purpose": "boardroom" if r.is_boardroom else "meeting",
        "status": r.status,
        "max_participants": r.max_participants,
        "country_code": r.country_code,
        "created_at": r.created_at.isoformat() if r.created_at else None,
        "invite_link": f"/meet/{r.room_uuid}" if r.room_uuid else None,
    }


def _resolve_country(request: Request, default: str = "AE") -> str:
    raw = (request.headers.get("X-Country-Code") or "").strip().upper()
    return raw or default


@router.get("/")
def admin_list_all_rooms(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all video rooms across all countries (consolidated view)."""
    rooms = db.query(VideoRoom).order_by(VideoRoom.created_at.desc()).limit(200).all()
    return [_serialize_room(r) for r in rooms]


@router.get("/video/rooms")
def admin_list_video_rooms(
    request: Request,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List video rooms, filtered by the X-Country-Code header when present."""
    country = _resolve_country(request, "")
    q = db.query(VideoRoom)
    if country:
        q = q.filter(VideoRoom.country_code == country)
    rooms = q.order_by(VideoRoom.created_at.desc()).limit(200).all()
    return [_serialize_room(r) for r in rooms]


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
):
    """Create a video room (used by the unified Communication hub and employee comms)."""
    country = _resolve_country(request)
    boardroom = is_boardroom if is_boardroom is not None else (purpose == "boardroom")
    creator = created_by or (participants[0] if participants else None)
    part_list = participants or ([creator] if creator is not None else [])
    vc = get_video_conference(db)
    result = vc.create_room(name, part_list, boardroom, country_code=country, employee_id=creator)
    db_room = db.query(VideoRoom).filter(VideoRoom.room_id == result["room_id"]).first()
    if db_room and not db_room.country_code:
        db_room.country_code = country
        db.commit()
    return {
        "id": db_room.id if db_room else None,
        "room_uuid": result.get("room_uuid"),
        "name": name,
        "purpose": purpose,
        "status": result.get("status", "created"),
        "max_participants": max_participants,
        "country_code": country,
        "created_at": db_room.created_at.isoformat() if db_room and db_room.created_at else None,
        "invite_link": f"/meet/{result.get('room_uuid')}",
    }


@router.get("/video/metrics")
def admin_video_metrics(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Video room metrics across all countries."""
    total_rooms = db.query(sqlfunc.count(VideoRoom.id)).scalar() or 0
    active_rooms = db.query(sqlfunc.count(VideoRoom.id)).filter(VideoRoom.status == "active").scalar() or 0
    max_part_sum = db.query(sqlfunc.coalesce(sqlfunc.sum(VideoRoom.max_participants), 0)).scalar() or 0
    return {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "total_max_participants": max_part_sum,
    }


@router.get("/video/rooms/{country_code}")
def admin_list_rooms(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        rooms = db.query(VideoRoom).filter(VideoRoom.country_code == country_code.upper()).order_by(VideoRoom.created_at.desc()).limit(100).all()
        return [
            {
                "id": r.id,
                "room_uuid": r.room_uuid,
                "name": r.name,
                "purpose": "boardroom" if r.is_boardroom else "meeting",
                "status": r.status,
                "max_participants": r.max_participants,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "invite_link": f"/meet/{r.room_uuid}" if r.room_uuid else None,
            }
            for r in rooms
        ]
    finally:
        clear_rls_context()


@router.post("/video/rooms/{country_code}")
def admin_create_room(
    country_code: str = Path(..., description="ISO country code"),
    name: str = Body(...),
    purpose: str = Body("meeting"),
    max_participants: int = Body(10),
    created_by: Optional[int] = Body(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        vc = get_video_conference(db)
        participants = [created_by] if created_by else []
        is_boardroom = purpose == "boardroom"
        result = vc.create_room(name, participants, is_boardroom, employee_id=created_by)

        db_room = db.query(VideoRoom).filter(VideoRoom.room_id == result["room_id"]).first()
        if db_room and not db_room.country_code:
            db_room.country_code = country_code.upper()
            db.commit()
            db.refresh(db_room)
        return {
            "id": db_room.id if db_room else None,
            "room_uuid": result.get("room_uuid"),
            "name": name,
            "purpose": purpose,
            "status": result.get("status", "created"),
            "max_participants": max_participants,
            "created_at": db_room.created_at.isoformat() if db_room and db_room.created_at else None,
            "invite_link": f"/meet/{result.get('room_uuid')}",
        }
    finally:
        clear_rls_context()

