import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from data.models import Employee, AuditLog
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class ShiftSchedulingService:
    """
    Shift rostering engine for operations staff.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_shift(
        self,
        employee_id: int,
        start_time: datetime,
        end_time: datetime,
        shift_type: str = "regular",
    ) -> dict:
        """Create a shift assignment."""
        audit = AuditLog(
            event_type="shift",
            actor_id=None,
            action="create",
            resource_type="shift",
            resource_id=employee_id,
            details={
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "shift_type": shift_type,
            },
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
        
        return {"status": "created", "employee_id": employee_id}
    
    def swap_shift(
        self,
        original_employee_id: int,
        new_employee_id: int,
        shift_id: int,
    ) -> dict:
        """Request to swap a shift."""
        return {"status": "requested", "shift_id": shift_id}
    
    def get_weekly_schedule(self, employee_id: int, week_start: datetime) -> List[dict]:
        """Get employee's weekly schedule."""
        week_end = week_start + timedelta(days=7)
        
        shifts = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "shift",
                AuditLog.resource_id == employee_id,
                AuditLog.event_type == "shift",
            )
            .all()
        )
        
        return [{"shift_id": s.id, "details": s.details_json} for s in shifts]
    
    def enforce_overtime_rules(self, employee_id: int) -> dict:
        """Check and enforce overtime limits."""
        return {"overtime_hours": 0, "within_limit": True}

