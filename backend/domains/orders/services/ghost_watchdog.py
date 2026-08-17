"""
Ghost Employee Watchdog
Detects employees with no activity but still active in payroll
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from _legacy.models.employee_models import Employee, EmployeeWorkLog, EmployeeAttendance
from _legacy.models import User, TreasuryAccount

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

        ghost_ids = [emp.id for emp in ghosts]

        treasury_map: dict[int, "TreasuryAccount"] = {}
        if ghost_ids:
            treasury_map = {
                t.employee_id: t for t in self.db.query(TreasuryAccount).filter(
                    TreasuryAccount.employee_id.in_(ghost_ids)
                ).all()
            }

        last_attendance_map: dict[int, datetime] = {}
        last_worklog_map: dict[int, datetime] = {}
        if ghost_ids:
            att_rows = (
                self.db.query(
                    EmployeeAttendance.employee_id,
                    func.max(EmployeeAttendance.scan_in_time).label("max_scan"),
                )
                .filter(
                    EmployeeAttendance.employee_id.in_(ghost_ids)
                )
                .group_by(EmployeeAttendance.employee_id)
                .all()
            )
            last_attendance_map = {row.employee_id: row.max_scan for row in att_rows}

            wl_rows = (
                self.db.query(
                    EmployeeWorkLog.employee_id,
                    func.max(EmployeeWorkLog.work_date).label("max_date"),
                )
                .filter(
                    EmployeeWorkLog.employee_id.in_(ghost_ids)
                )
                .group_by(EmployeeWorkLog.employee_id)
                .all()
            )
            last_worklog_map = {row.employee_id: row.max_date for row in wl_rows}

        results = []
        for emp in ghosts:
            treasury = treasury_map.get(emp.id)
            last_attendance = last_attendance_map.get(emp.id)
            last_worklog = last_worklog_map.get(emp.id)
            activities = [a for a in [last_attendance, last_worklog] if a]
            last_active = max(activities) if activities else None

            results.append({
                "employee_id": emp.id,
                "employee_code": emp.employee_code,
                "name": f"{emp.first_name} {emp.last_name}",
                "last_active": last_active,
                "payroll_active": treasury is not None,
                "risk_level": "high" if treasury else "medium"
            })

        return results

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

