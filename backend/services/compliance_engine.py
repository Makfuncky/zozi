"""
GCC Labor Law Compliance Engine
Enforces labor law requirements for Gulf Cooperation Council countries
"""
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeAttendance, EmployeeWorkLog
from models import User

logger = logging.getLogger("zozi.compliance")


class GCCComplianceEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def validate_work_hours(self, employee_id: int, date: datetime) -> dict:
        attendance = self.db.query(EmployeeAttendance).filter(
            EmployeeAttendance.employee_id == employee_id,
            EmployeeAttendance.date == date.date()
        ).first()
        
        if not attendance or not attendance.scan_in_time or not attendance.scan_out_time:
            return {"valid": False, "reason": "Missing attendance record"}
        
        work_duration = (attendance.scan_out_time - attendance.scan_in_time).total_seconds() / 3600
        max_daily_hours = 8
        
        violations = []
        if work_duration > max_daily_hours:
            violations.append({
                "type": "overtime_exceeded",
                "allowed": max_daily_hours,
                "actual": work_duration
            })
        
        return {"valid": len(violations) == 0, "violations": violations}
    
    def calculate_overtime(self, employee_id: int, week_start: datetime) -> Decimal:
        week_end = week_start + timedelta(days=7)
        
        work_logs = self.db.query(EmployeeWorkLog).filter(
            EmployeeWorkLog.employee_id == employee_id,
            EmployeeWorkLog.date >= week_start.date(),
            EmployeeWorkLog.date < week_end.date()
        ).all()
        
        total_hours = sum([log.hours_worked or Decimal("0") for log in work_logs])
        regular_hours = min(total_hours, Decimal("40"))
        overtime_hours = max(total_hours - Decimal("40"), Decimal("0"))
        
        return overtime_hours
    
    def validate_hajj_leave(self, employee_id: int, start_date: datetime, 
                            end_date: datetime) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"valid": False, "reason": "Employee not found"}
        
        if employee.country_code not in ["SA", "AE", "QA", "KW", "BH", "OM"]:
            return {"valid": True, "note": "Not applicable to non-GCC country"}
        
        leave_days = (end_date.date() - start_date.date()).days
        max_hajj_days = 60
        
        return {
            "valid": leave_days <= max_hajj_days,
            "requested_days": leave_days,
            "max_allowed": max_hajj_days
        }
    
    def validate_weekly_rest(self, employee_id: int, week_start: datetime) -> dict:
        week_end = week_start + timedelta(days=7)
        
        attendance = self.db.query(EmployeeAttendance).filter(
            EmployeeAttendance.employee_id == employee_id,
            EmployeeAttendance.date >= week_start.date(),
            EmployeeAttendance.date < week_end.date()
        ).all()
        
        consecutive_days = 0
        max_consecutive = 6
        
        for day in attendance:
            if day.status == "present":
                consecutive_days += 1
            else:
                consecutive_days = 0
        
        return {
            "valid": consecutive_days <= max_consecutive,
            "consecutive_work_days": consecutive_days
        }
    
    def get_compliance_report(self, employee_id: int, month: datetime) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found"}
        
        month_start = month.replace(day=1)
        if month.month == 12:
            month_end = month_start.replace(year=month.year + 1, month=1, day=1)
        else:
            month_end = month_start.replace(month=month.month + 1, day=1)
        
        total_work_days = self.db.query(EmployeeAttendance).filter(
            EmployeeAttendance.employee_id == employee_id,
            EmployeeAttendance.date >= month_start.date(),
            EmployeeAttendance.date < month_end.date(),
            EmployeeAttendance.status == "present"
        ).count()
        
        total_work_hours = self.db.query(EmployeeWorkLog).filter(
            EmployeeWorkLog.employee_id == employee_id,
            EmployeeWorkLog.date >= month_start.date(),
            EmployeeWorkLog.date < month_end.date()
        ).sum(EmployeeWorkLog.hours_worked) or Decimal("0")
        
        return {
            "employee_id": employee_id,
            "month": month.strftime("%Y-%m"),
            "total_work_days": total_work_days,
            "total_work_hours": str(total_work_hours),
            "country_code": employee.country_code,
            "compliance_status": "pending_review"
        }


def get_compliance_engine(db: Session) -> GCCComplianceEngine:
    return GCCComplianceEngine(db)

