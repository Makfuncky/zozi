"""Video room write service.

Owns the trivial DB write in `backend/routers/admin_video.py`: stamping a
country code onto a freshly-created VideoRoom. Keeps the router free of
`db.commit` (W1). The session is passed in (db-param contract).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.accounts.models.core import VideoRoom
import structlog
logger = structlog.get_logger(__name__)


def ensure_video_room_country(db_room: VideoRoom, country_code: str, db: Session) -> VideoRoom:
    """Set the room's country code once and persist it. No-op if already set."""
    if db_room is None:
        return db_room
    normalized = country_code.upper() if country_code else country_code
    if not getattr(db_room, "country_code", None):
        db_room.country_code = normalized
        db.commit()
        db.refresh(db_room)
    return db_room
