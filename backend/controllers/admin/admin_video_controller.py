"""Controller for the admin video router.

Thin orchestration between `routers.admin_video_governance` and
`services.comms.video_room_write_service` so the router issues no `db.commit`
(W1).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models_core import VideoRoom
from services.comms.video_room_write_service import ensure_video_room_country
import structlog
logger = structlog.get_logger(__name__)


def ensure_room_country(db_room: VideoRoom, country_code: str, db: Session) -> VideoRoom:
    return ensure_video_room_country(db_room, country_code, db)
