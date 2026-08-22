"""Video-room read/write operations (admin media + country-scoped wrappers).

Owns the DB reads/writes for ``VideoRoom`` so the router stays free of
``db.query``/``db.commit``.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import func as sqlfunc
from sqlalchemy.orm import Session

from domains.accounts.ports import VideoRoom
import structlog
logger = structlog.get_logger(__name__)


def list_all_video_rooms(db: Session, limit: int = 200) -> list[VideoRoom]:
    """Return video rooms across all countries, newest first."""
    return db.query(VideoRoom).order_by(VideoRoom.created_at.desc()).limit(limit).all()


def list_video_rooms(db: Session, country: Optional[str], limit: int = 200) -> list[VideoRoom]:
    """Return video rooms, optionally filtered by country code."""
    q = db.query(VideoRoom)
    if country:
        q = q.filter(VideoRoom.country_code == country)
    return q.order_by(VideoRoom.created_at.desc()).limit(limit).all()


def list_video_rooms_for_country(db: Session, country_code: str, limit: int = 100) -> list[VideoRoom]:
    """Return video rooms for a single country code, newest first."""
    return (
        db.query(VideoRoom)
        .filter(VideoRoom.country_code == country_code.upper())
        .order_by(VideoRoom.created_at.desc())
        .limit(limit)
        .all()
    )


def video_room_metrics(db: Session) -> dict:
    """Aggregate counts across all video rooms."""
    total_rooms = db.query(sqlfunc.count(VideoRoom.id)).scalar() or 0
    active_rooms = db.query(sqlfunc.count(VideoRoom.id)).filter(VideoRoom.status == "active").scalar() or 0
    max_part_sum = db.query(sqlfunc.coalesce(sqlfunc.sum(VideoRoom.max_participants), 0)).scalar() or 0
    return {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "total_max_participants": max_part_sum,
    }


def serialize_video_room(r: VideoRoom) -> dict:
    """Convert a ``VideoRoom`` ORM row into the API representation."""
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


def ensure_video_room_country(db: Session, room_id, country_code: str) -> Optional[VideoRoom]:
    """Attach a country code to a created room if missing, returning the row."""
    db_room = db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()
    if db_room and not db_room.country_code:
        db_room.country_code = country_code.upper()
        db.commit()
        db.refresh(db_room)
    return db_room
