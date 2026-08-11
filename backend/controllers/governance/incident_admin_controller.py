"""Thin orchestration controller for incident war-room admin operations.

The ``routers.admin_security_operations`` router delegates to this controller so
it stays within the allowed circuit (routers -> controllers/schemas/auth-deps only).
All ``db`` reads and the incident service wiring live here.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from services.security.incident_service import get_incident_service
from services.governance.incident_admin_read_service import get_war_room as _get_war_room


def create_incident(db: Session, title: str, severity: str = "medium", context: Optional[Dict[str, Any]] = None, current_user: dict = None) -> dict:
    service = get_incident_service(db)
    return service.create_incident(title, severity, context)


def close_incident(db: Session, incident_id: str, current_user: dict = None) -> dict:
    service = get_incident_service(db)
    return service.close_incident(incident_id)


def add_action_item(db: Session, war_room_id: int, title: str, assignee_id: Optional[int] = None, priority: str = "medium", current_user: dict = None) -> dict:
    service = get_incident_service(db)
    item = service.generator.add_action_item(war_room_id=war_room_id, title=title, assignee_id=assignee_id, priority=priority)
    return {"action_item_id": item.id, "title": item.title, "status": item.status}


def get_war_room(db: Session, war_room_id: int) -> dict:
    return _get_war_room(db, war_room_id)
