"""
Incident War Room API
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from services.security.security_router_service import get_war_room_db
from services.incident_service import get_incident_service

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
    return get_war_room_db(db, war_room_id=war_room_id)
