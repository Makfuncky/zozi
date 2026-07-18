"""
Shift Handover Service
Auto-generates handover sessions for shift transitions with task tracking.
"""
import logging
from datetime import datetime, timezone, date
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from models.core import ShiftHandoverSession, ShiftHandoverTask
from models.employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger("zozi.shift_handover")


class ShiftHandoverService:
    def __init__(self, db: Session):
        self.db = db

    def create_handover(
        self,
        outgoing_employee_id: int,
        country_code: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> dict:
        session = ShiftHandoverSession(
            country_code=country_code,
            outgoing_employee_id=outgoing_employee_id,
            shift_date=datetime.now(timezone.utc),
            notes=notes,
            status="pending",
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return {
            "id": session.id,
            "outgoing_employee_id": outgoing_employee_id,
            "shift_date": session.shift_date.isoformat(),
            "status": session.status,
            "notes": session.notes,
        }

    def assign_incoming(
        self,
        session_id: int,
        incoming_employee_id: int,
    ) -> dict:
        session = self.db.query(ShiftHandoverSession).filter(
            ShiftHandoverSession.id == session_id
        ).first()
        if not session:
            raise ValueError(f"Handover session {session_id} not found")
        session.incoming_employee_id = incoming_employee_id
        self.db.commit()
        return {"id": session.id, "incoming_employee_id": incoming_employee_id}

    def add_task(
        self,
        session_id: int,
        description: str,
        priority: str = "normal",
        assigned_to: Optional[int] = None,
    ) -> dict:
        session = self.db.query(ShiftHandoverSession).filter(
            ShiftHandoverSession.id == session_id
        ).first()
        if not session:
            raise ValueError(f"Handover session {session_id} not found")
        task = ShiftHandoverTask(
            session_id=session_id,
            description=description,
            priority=priority,
            assigned_to=assigned_to,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return {
            "id": task.id,
            "session_id": session_id,
            "description": description,
            "priority": priority,
            "status": task.status,
        }

    def acknowledge_handover(self, session_id: int) -> dict:
        session = self.db.query(ShiftHandoverSession).filter(
            ShiftHandoverSession.id == session_id
        ).first()
        if not session:
            raise ValueError(f"Handover session {session_id} not found")
        session.status = "acknowledged"
        session.acknowledged_at = _utcnow()
        self.db.commit()
        return {
            "id": session.id,
            "status": "acknowledged",
            "acknowledged_at": session.acknowledged_at.isoformat(),
        }

    def get_pending_handovers(self, employee_id: int) -> List[dict]:
        sessions = self.db.query(ShiftHandoverSession).filter(
            ShiftHandoverSession.incoming_employee_id == employee_id,
            ShiftHandoverSession.status == "pending",
        ).order_by(ShiftHandoverSession.shift_date.desc()).all()
        result = []
        for s in sessions:
            tasks = self.db.query(ShiftHandoverTask).filter(
                ShiftHandoverTask.session_id == s.id,
                ShiftHandoverTask.status == "open",
            ).all()
            result.append({
                "id": s.id,
                "outgoing_employee_id": s.outgoing_employee_id,
                "shift_date": s.shift_date.isoformat(),
                "notes": s.notes,
                "status": s.status,
                "open_tasks": len(tasks),
                "tasks": [
                    {"id": t.id, "description": t.description, "priority": t.priority, "status": t.status}
                    for t in tasks
                ],
            })
        return result


def get_shift_handover_service(db: Session) -> ShiftHandoverService:
    return ShiftHandoverService(db)
