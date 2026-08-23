"""
Incident War Room API
"""
from typing import Optional, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session
from domains.governance.models.user import User
from domains.governance.models.incident import IncidentWarRoom
from domains.governance.services.incident_service import get_incident_service
from domains.governance.services.incident_service import IncidentService
from infrastructure.database.database import get_db
from rbac import get_current_user

async def get_war_room(war_room_id: int, current_user: dict=Depends(get_current_user), db: Session=Depends(get_db)):
    war_room = db.query(IncidentWarRoom).filter_by(id=war_room_id).first()
    if not war_room:
        return {'exists': False}
    return {'id': war_room.id, 'incident_id': war_room.incident_id, 'title': war_room.title, 'severity': war_room.severity, 'status': war_room.status, 'started_at': war_room.started_at.isoformat(), 'action_items': [{'id': a.id, 'title': a.title, 'status': a.status} for a in war_room.action_items]}
