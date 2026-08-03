"""
Automated Incident War Room Generation
Features: Auto-provisioning, Context capture, Action items
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from data.models import IncidentWarRoom, IncidentThread, IncidentActionItem, User
from data.db import get_service_session

logger = logging.getLogger("zozi.incident")


class WarRoomGenerator:
    """Generates incident war rooms automatically."""
    
    TEMPLATES = {
        "security": {
            "channels": ["security", "engineering", "legal"],
            "actions": ["Containment", "Investigation", "Notification"],
            "escalation": ["CISO", "Legal Team"]
        },
        "outage": {
            "channels": ["engineering", "ops", "customer_success"],
            "actions": ["Root Cause Analysis", "Fix Deployment", "Status Update"],
            "escalation": ["CTO", "CEO"]
        },
        "data_breach": {
            "channels": ["security", "legal", "compliance", "communications"],
            "actions": ["Containment", "Forensics", "Regulatory Notification"],
            "escalation": ["CISO", "General Counsel", "CEO"]
        }
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_war_room(
        self,
        incident_id: str,
        title: str,
        severity: str,
        context: Dict[str, Any],
        auto_assign: bool = True
    ) -> IncidentWarRoom:
        """Generate a war room for an incident."""
        war_room = IncidentWarRoom(
            incident_id=incident_id,
            title=title,
            severity=severity,
            status="active",
            created_by=1,
            context_data=context
        )
        self.db.add(war_room)
        self.db.commit()
        self.db.refresh(war_room)
        
        if auto_assign:
            self._assign_default_participants(war_room, severity)
            self._create_default_action_items(war_room, severity)
        
        return war_room
    
    def _assign_default_participants(self, war_room: IncidentWarRoom, severity: str):
        """Assign default participants based on severity."""
        participant_ids = [1]
        
        if severity in ("high", "critical"):
            participant_ids.extend([2, 3])
        
        for pid in participant_ids:
            thread = IncidentThread(
                war_room_id=war_room.id,
                participant_id=pid,
                message=f"Auto-assigned to participant {pid}"
            )
            self.db.add(thread)
        
        self.db.commit()
    
    def _create_default_action_items(self, war_room: IncidentWarRoom, severity: str):
        """Create default action items based on severity."""
        actions = ["Initial Assessment"]
        
        if severity == "critical":
            actions.extend(["Containment", "Root Cause Analysis", "Post-mortem"])
        elif severity == "high":
            actions.extend(["Investigation", "Resolution"])
        else:
            actions.append("Documentation")
        
        for action in actions:
            item = IncidentActionItem(
                war_room_id=war_room.id,
                title=action,
                status="pending"
            )
            self.db.add(item)
        
        self.db.commit()
    
    def add_action_item(
        self,
        war_room_id: int,
        title: str,
        assignee_id: Optional[int] = None,
        priority: str = "medium",
        due_date: Optional[datetime] = None
    ) -> IncidentActionItem:
        """Add an action item to a war room."""
        item = IncidentActionItem(
            war_room_id=war_room_id,
            assignee_id=assignee_id,
            title=title,
            status="pending",
            priority=priority,
            due_date=due_date
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item


class IncidentService:
    """Service for incident management."""
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.generator = WarRoomGenerator(self.db)
    
    def create_incident(
        self,
        title: str,
        severity: str = "medium",
        context: Optional[Dict[str, Any]] = None,
        auto_create_war_room: bool = True
    ) -> Dict[str, Any]:
        """Create a new incident."""
        incident_id = f"INC-{uuid.uuid4().hex[:10].upper()}"
        
        if auto_create_war_room:
            war_room = self.generator.generate_war_room(
                incident_id=incident_id,
                title=title,
                severity=severity,
                context=context or {}
            )
            return {
                "incident_id": incident_id,
                "war_room_id": war_room.id,
                "status": "created"
            }
        
        return {"incident_id": incident_id, "status": "created"}
    
    def close_incident(self, incident_id: str) -> Dict[str, Any]:
        """Close an incident."""
        war_room = self.db.query(IncidentWarRoom).filter(
            IncidentWarRoom.incident_id == incident_id
        ).first()
        
        if war_room:
            war_room.status = "closed"
            war_room.closed_at = datetime.now(timezone.utc)
            self.db.commit()
            return {"status": "closed", "incident_id": incident_id}
        
        return {"status": "not_found", "incident_id": incident_id}


def get_incident_service(db: Session = None) -> IncidentService:
    return IncidentService(db or get_service_session())
