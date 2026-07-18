"""
Learning Management System with Permission Locking
"""
import logging
from datetime import datetime, timezone

from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from models.employee_models import Employee

logger = logging.getLogger("zozi.lms")


class LMS:
    def __init__(self, db: Session):
        self.db = db
    
    def assign_course(self, employee_id: int, course_id: str, 
                      locked: bool = False) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "course_id": course_id,
            "locked": locked,
            "assigned_at": datetime.now(timezone.utc).isoformat()
        }
    
    def unlock_course(self, employee_id: int, course_id: str, 
                      admin_id: int) -> dict:
        admin = self.db.query(Employee).filter(Employee.id == admin_id).first()
        if not admin:
            return {"success": False, "error": "Admin not found"}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "course_id": course_id,
            "unlocked_by": admin_id,
            "unlocked_at": datetime.now(timezone.utc).isoformat()
        }
    
    def get_progress(self, employee_id: int) -> Dict:
        return {
            "employee_id": employee_id,
            "courses": [],
            "completion_rate": 0,
            "locked_courses": []
        }


def get_lms(db: Session) -> LMS:
    return LMS(db)

