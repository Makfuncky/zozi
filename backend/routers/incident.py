"""
Incident War Room API
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from data.models import IncidentWarRoom, User
from services.incident_service import get_incident_service, IncidentService
from data.db import get_db
from data.dependencies_auth import get_current_user

router = APIRouter()


@router.post("/incidents", response_model=dict)
async def create_incident(
    title: str,
    severity: str = "medium",
    context: Optional[Dict[str, Any]] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_incident_service(db)
    result = service.create_incident(title, severity, context)
    return result


@router.post("/incidents/{incident_id}/close", response_model=dict)
async def close_incident(
    incident_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_incident_service(db)
    return service.close_incident(incident_id)


@router.post("/war-rooms/{war_room_id}/actions", response_model=dict)
async def add_action_item(
    war_room_id: int,
    title: str,
    assignee_id: Optional[int] = None,
    priority: str = "medium",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_incident_service(db)
    item = service.generator.add_action_item(
        war_room_id=war_room_id,
        title=title,
        assignee_id=assignee_id,
        priority=priority
    )
    return {
        "action_item_id": item.id,
        "title": item.title,
        "status": item.status
    }


@router.get("/war-rooms/{war_room_id}", response_model=dict)
async def get_war_room(
    war_room_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
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
        "action_items": [{"id": a.id, "title": a.title, "status": a.status} for a in war_room.action_items]
    }
