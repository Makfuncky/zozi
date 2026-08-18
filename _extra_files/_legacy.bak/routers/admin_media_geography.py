"""Admin Video Router — consolidated + country-scoped wrapper around VideoConferenceRoom endpoints."""
import logging
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Path, Request
from sqlalchemy.orm import Session

from db.database import get_db
from _legacy.models import User
from _legacy.models.core import VideoRoom
from services.comms.video_conferencing import get_video_conference
from services.comms.video_room_service import (
    ensure_video_room_country,
    list_all_video_rooms,
    list_video_rooms,
    list_video_rooms_for_country,
    video_room_metrics,
)
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger("zozi.api.admin_video")
router = APIRouter(prefix="/api/v1/admin")


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


@router.get("/video")
def admin_list_all_rooms(
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all video rooms across all countries (consolidated view)."""
    rooms = list_all_video_rooms(db)
    return [_serialize_room(r) for r in rooms]


@router.get("/video/rooms")
def admin_list_video_rooms(
    request: Request,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List video rooms, filtered by the X-Country-Code header when present."""
    country = _resolve_country(request, "")
    rooms = list_video_rooms(db, country)
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
    db_room = ensure_video_room_country(db, result["room_id"], country)
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
    return video_room_metrics(db)


@router.get("/video/rooms/{country_code}")
def admin_list_rooms(
    country_code: str = Path(..., description="ISO country code"),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        rooms = list_video_rooms_for_country(db, country_code)
        return [_serialize_room(r) for r in rooms]
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

        db_room = ensure_video_room_country(db, result["room_id"], country_code)
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
