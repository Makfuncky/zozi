"""Auto-migrated service logic from routers/admin_media_geography.py."""
from __future__ import annotations

import logging

from typing import List, Optional

from fastapi import Body, Depends, Path, Request

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from domains.governance.models.user import User

from domains.governance.models.core import VideoRoom

from domains.comms.services.messaging.video.video_conferencing import get_video_conference

from domains.comms.services.messaging.video.video_room_service import ensure_video_room_country
from domains.comms.services.messaging.video.video_room_service import list_all_video_rooms
from domains.comms.services.messaging.video.video_room_service import list_video_rooms
from domains.comms.services.messaging.video.video_room_service import list_video_rooms_for_country
from domains.comms.services.messaging.video.video_room_service import video_room_metrics

from infrastructure.utils.dependencies import require_admin

from domains.country.utils.country_rls import get_country_or_404

from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context
from domains.governance.services.comms.flat_admin_comms_messaging_service import _resolve_country

logger = logging.getLogger("zozi.api.admin_video")

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


def admin_list_all_rooms(_: User, db: Session):
    """List all video rooms across all countries (consolidated view)."""
    rooms = list_all_video_rooms(db)
    return [_serialize_room(r) for r in rooms]

def admin_list_video_rooms(request: Request, _: User, db: Session):
    """List video rooms, filtered by the X-Country-Code header when present."""
    country = _resolve_country(request, "")
    rooms = list_video_rooms(db, country)
    return [_serialize_room(r) for r in rooms]

def admin_create_video_room(request: Request, name: str, purpose: str, max_participants: int, created_by: Optional[int], participants: Optional[List[int]], is_boardroom: Optional[bool], _: User, db: Session):
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

def admin_video_metrics(_: User, db: Session):
    """Video room metrics across all countries."""
    return video_room_metrics(db)

def admin_list_rooms(country_code: str, _: User, db: Session):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        rooms = list_video_rooms_for_country(db, country_code)
        return [_serialize_room(r) for r in rooms]
    finally:
        clear_rls_context()

def admin_create_room(country_code: str, name: str, purpose: str, max_participants: int, created_by: Optional[int], _: User, db: Session):
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


