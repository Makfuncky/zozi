"""Incident war-room read service (W1).

Owns the read behind ``incident_admin_controller.get_war_room`` so the
controller stays free of direct ORM queries.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import IncidentWarRoom
import structlog

logger = structlog.get_logger(__name__)


def get_war_room(db: Session, war_room_id: int) -> dict:
    war_room = db.query(IncidentWarRoom).filter_by(id=war_room_id).first()
    if not war_room:
        return {"exists": False}
    return {
        "id": war_room.id,
        "incident_id": war_room.incident_id,
        "title": war_room.title,
        "severity": war_room.severity,
        "status": war_room.status,
        "started_at": war_room.started_at.isoformat(),
        "action_items": [
            {"id": a.id, "title": a.title, "status": a.status}
            for a in war_room.action_items
        ],
    }
