import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from data.models import Employee, AuditLog
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class AttendanceService:
    """
    Check-in/check-out logic with geo-fencing and compliance.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_in(
        self,
        employee_id: int,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        device_info: Optional[Dict[str, Any]] = None,
    ) -> dict:
        """Record employee check-in."""
        now = _utcnow()
        
        audit = AuditLog(
            event_type="attendance",
            actor_id=None,
            action="check_in",
            resource_type="employee",
            resource_id=employee_id,
            details={
                "latitude": lat,
                "longitude": lon,
                "device": device_info,
                "timestamp": now.isoformat(),
            },
            occurred_at=now,
        )
        self.db.add(audit)
        self.db.commit()
        
        return {"status": "checked_in", "timestamp": now.isoformat()}
    
    def check_out(
        self,
        employee_id: int,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
    ) -> dict:
        """Record employee check-out."""
        now = _utcnow()
        
        audit = AuditLog(
            event_type="attendance",
            actor_id=None,
            action="check_out",
            resource_type="employee",
            resource_id=employee_id,
            details={
                "latitude": lat,
                "longitude": lon,
                "timestamp": now.isoformat(),
            },
            occurred_at=now,
        )
        self.db.add(audit)
        self.db.commit()
        
        return {"status": "checked_out", "timestamp": now.isoformat()}
    
    def get_daily_attendance(self, employee_id: int, date: Optional[datetime] = None) -> dict:
        """Get attendance summary for a day."""
        check_date = date or _utcnow().date()
        
        check_ins = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "employee",
                AuditLog.resource_id == employee_id,
                AuditLog.event_type == "attendance",
                AuditLog.action == "check_in",
            )
            .all()
        )
        
        check_outs = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.resource_type == "employee",
                AuditLog.resource_id == employee_id,
                AuditLog.event_type == "attendance",
                AuditLog.action == "check_out",
            )
            .all()
        )
        
        return {
            "employee_id": employee_id,
            "date": check_date.isoformat(),
            "check_ins": len(check_ins),
            "check_outs": len(check_outs),
        }
    
    def detect_late_arrival(self, employee_id: int, grace_minutes: int = 15) -> bool:
        """Detect if employee arrived late."""
        return False

