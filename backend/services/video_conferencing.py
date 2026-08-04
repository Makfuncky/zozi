"""Service methods for video conferencing data access."""
from __future__ import annotations
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc
from data.models_core import VideoRoom

from services.communication.video_conferencing import (
    VideoConferenceRoom,
    get_video_conference,
    list_all_video_rooms,
)


__all__ = [
    "list_video_rooms_by_country",
    "get_video_room_by_room_id",
    "update_video_room_country",
    "get_video_room_metrics",
    "VideoConferenceRoom",
    "get_video_conference",
    "list_all_video_rooms",
]


def list_video_rooms_by_country(db: Session, country_code: str | None = None, limit: int = 200) -> list[VideoRoom]:
    """List video rooms, optionally filtered by country."""
    q = db.query(VideoRoom)
    if country_code:
        q = q.filter(VideoRoom.country_code == country_code)
    return q.order_by(VideoRoom.created_at.desc()).limit(limit).all()


def get_video_room_by_room_id(db: Session, room_id: str) -> VideoRoom | None:
    """Get a video room by its room_id."""
    return db.query(VideoRoom).filter(VideoRoom.room_id == room_id).first()


def update_video_room_country(db: Session, room: VideoRoom, country_code: str) -> VideoRoom:
    """Update a video room's country code."""
    room.country_code = country_code
    db.commit()
    db.refresh(room)
    return room


def get_video_room_metrics(db: Session) -> dict:
    """Get video room metrics."""
    total_rooms = db.query(sqlfunc.count(VideoRoom.id)).scalar() or 0
    active_rooms = (
        db.query(sqlfunc.count(VideoRoom.id))
        .filter(VideoRoom.status == "active")
        .scalar()
        or 0
    )
    max_part_sum = (
        db.query(sqlfunc.coalesce(sqlfunc.sum(VideoRoom.max_participants), 0))
        .scalar()
        or 0
    )
    return {
        "total_rooms": total_rooms,
        "active_rooms": active_rooms,
        "max_participants_sum": max_part_sum,
    }
