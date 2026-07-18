"""
Ghost Employee Watchdog
Detects employees with no activity but still active in payroll
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeWorkLog, EmployeeAttendance
from models import User, TreasuryAccount

logger = logging.getLogger("zozi.ghost_watchdog")


class GhostEmployeeWatchdog:
    def __init__(self, db: Session):
        self.db = db
    
    def find_ghost_employees(self, days_threshold: int = 90) -> List[dict]:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_threshold)
        
        recent_attendance = self.db.query(EmployeeAttendance.employee_id).filter(
            EmployeeAttendance.scan_in_time >= cutoff_date
        ).distinct().subquery()
        
        recent_work_logs = self.db.query(EmployeeWorkLog.employee_id).filter(
            EmployeeWorkLog.work_date >= cutoff_date
        ).distinct().subquery()
        
        ghosts = self.db.query(Employee).filter(
            Employee.employment_status == "active",
            and_(
                ~Employee.id.in_(recent_attendance),
                ~Employee.id.in_(recent_work_logs)
            )
        ).all()
        
        results = []
        for emp in ghosts:
            treasury = self.db.query(TreasuryAccount).filter(
                TreasuryAccount.employee_id == emp.id
            ).first()
            
            results.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "last_active": self._get_last_activity(emp.id),
                "payroll_active": treasury is not None,
                "risk_level": "high" if treasury else "medium"
            })
        
        return results
    
    def _get_last_activity(self, employee_id: int) -> Optional[datetime]:
        last_attendance = self.db.query(EmployeeAttendance.scan_in_time).filter(
            EmployeeAttendance.employee_id == employee_id
        ).order_by(EmployeeAttendance.scan_in_time.desc()).first()
        
        last_worklog = self.db.query(EmployeeWorkLog.work_date).filter(
            EmployeeWorkLog.employee_id == employee_id
        ).order_by(EmployeeWorkLog.work_date.desc()).first()
        
        activities = [a[0] for a in [last_attendance, last_worklog] if a]
        return max(activities) if activities else None
    
    def flag_for_review(self, employee_id: int, reason: str) -> dict:
        return {
            "employee_id": employee_id,
            "flagged": True,
            "reason": reason,
            "requires_review": True
        }
    
    def generate_ghost_report(self, days_threshold: int = 90) -> dict:
        ghosts = self.find_ghost_employees(days_threshold)
        return {
            "report_generated_at": datetime.now(timezone.utc).isoformat(),
            "threshold_days": days_threshold,
            "ghost_count": len(ghosts),
            "ghosts": ghosts
        }


def get_ghost_watchdog(db: Session) -> GhostEmployeeWatchdog:
    return GhostEmployeeWatchdog(db)

