"""Learning Management System Controller with Permission Locking.

Consolidates lms.py (LMS class with assign/unlock course),
lms_service.py (training module CRUD, assignment, completion verification),
and lms_permission_lock.py (certification-based access control).
"""
from __future__ import annotations
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeCertification
from infrastructure.database.database import get_service_session
from infrastructure.utils.datetime_utils import utcnow as _utcnow


# ── LMS Class (merged from lms.py) ───────────────────────────────────────────

class LMS:
    """Learning Management System with course assignment and permission locking."""

    def __init__(self, db: Session):
        self.db = db

    def assign_course(
        self, employee_id: int, course_id: str, locked: bool = False,
    ) -> dict:
        employee = (
            self.db.query(Employee).filter(Employee.id == employee_id).first()
        )
        if not employee:
            return {"success": False, "error": "Employee not found"}

        return {
            "success": True,
            "employee_id": employee_id,
            "course_id": course_id,
            "locked": locked,
            "assigned_at": datetime.now(timezone.utc).isoformat(),
        }

    def unlock_course(
        self, employee_id: int, course_id: str, admin_id: int,
    ) -> dict:
        admin = self.db.query(Employee).filter(Employee.id == admin_id).first()
        if not admin:
            return {"success": False, "error": "Admin not found"}

        return {
            "success": True,
            "employee_id": employee_id,
            "course_id": course_id,
            "unlocked_by": admin_id,
            "unlocked_at": datetime.now(timezone.utc).isoformat(),
        }


# ── Training Module Operations ───────────────────────────────────────────────


def create_training_module(module_data: dict, db: Session) -> dict:
    """Create a training module."""
    module_id = str(hash(module_data.get("title")))
    
    db.execute(text("""
        INSERT INTO training_modules (module_id, title, description, required_for_role, duration_minutes, is_active)
        VALUES (:mid, :title, :desc, :role, :dur, :active)
    """), {
        "mid": module_id,
        "title": module_data.get("title"),
        "desc": module_data.get("description"),
        "role": module_data.get("required_role"),
        "dur": module_data.get("duration_minutes", 30),
        "active": module_data.get("is_active", True),
    })
    db.commit()
    
    return {"module_id": module_id, "title": module_data.get("title")}


def assign_training(employee_id: int, module_id: str, db: Session) -> dict:
    """Assign a training module to an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    db.execute(text("""
        INSERT INTO employee_trainings (employee_id, module_id, assigned_at, status)
        VALUES (:eid, :mid, :now, 'assigned')
    """), {"eid": employee_id, "mid": module_id, "now": _utcnow()})
    db.commit()
    
    return {"employee_id": employee_id, "module_id": module_id, "status": "assigned"}


def verify_training_completion(employee_id: int, module_id: str, quiz_score: float, db: Session) -> dict:
    """Verify training completion and unlock permissions."""
    if quiz_score < 70:
        return {"status": "failed", "reason": "score_below_threshold", "score": quiz_score}
    
    db.execute(text("""
        UPDATE employee_trainings 
        SET status = 'completed', score = :score, completed_at = :now
        WHERE employee_id = :eid AND module_id = :mid
    """), {"score": quiz_score, "now": _utcnow(), "eid": employee_id, "mid": module_id})
    db.commit()
    
    return {"employee_id": employee_id, "module_id": module_id, "status": "completed", "unlocked": True}


def check_permission_lock(employee_id: int, permission: str, db: Session) -> dict:
    """Check if a permission is locked for an employee."""
    result = db.execute(text("""
        SELECT m.required_for_role, et.status
        FROM training_modules m
        JOIN employee_trainings et ON et.module_id = m.module_id
        WHERE m.permission_key = :perm AND et.employee_id = :eid
    """), {"perm": permission, "eid": employee_id}).fetchone()
    
    if not result:
        return {"locked": False, "reason": "no_requirement"}
    
    if result[1] != "completed":
        return {"locked": True, "reason": "training_incomplete", "required_role": result[0]}
    
    return {"locked": False, "reason": "training_completed"}


def get_training_progress(employee_id: int, db: Session) -> dict:
    """Get training progress for an employee."""
    progress = db.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            AVG(score) as avg_score
        FROM employee_trainings et
        JOIN training_modules m ON m.module_id = et.module_id
        WHERE et.employee_id = :eid
    """), {"eid": employee_id}).fetchone()

    return {
        "total_modules": progress[0] or 0,
        "completed": progress[1] or 0,
        "completion_rate": round((progress[1] or 0) / (progress[0] or 1) * 100, 2),
        "avg_score": progress[2] or 0,
    }


# ── LMS Permission Lock (merged from lms_permission_lock.py) ───────────────────

class LMSPermissionLock:
    """Locks system permissions until LMS certification is passed."""

    PERMISSION_COURSE_MAP = {
        "approve_invoices": "ZATCA_E_Invoicing",
        "approve_payouts": "Payment_Gateway_Compliance",
        "access_finance": "Financial_Data_Protection",
        "manage_suppliers": "Supplier_Onboarding_Compliance",
        "dispatch_treasury": "Treasury_Operations_Certification",
    }

    def __init__(self, db: Session = None):
        self.db = db or get_service_session()

    def check_permission(self, employee_id: int, permission: str) -> Dict[str, Any]:
        """Check if employee has valid certification for a permission."""
        required_course = self.PERMISSION_COURSE_MAP.get(permission)
        if not required_course:
            return {"allowed": True, "reason": "No certification required"}

        certification = (
            self.db.query(EmployeeCertification)
            .filter(
                EmployeeCertification.employee_id == employee_id,
                EmployeeCertification.cert_name == required_course,
                EmployeeCertification.is_valid == True,
            )
            .first()
        )

        if not certification:
            return {
                "allowed": False,
                "reason": f"Missing certification: {required_course}",
                "locked": True,
                "course": required_course,
            }

        if certification.expiry_date and certification.expiry_date < datetime.now().date():
            return {
                "allowed": False,
                "reason": f"Certification expired: {required_course}",
                "locked": True,
                "course": required_course,
                "expired_at": certification.expiry_date.isoformat(),
            }

        return {"allowed": True, "certification": required_course}

    def grant_permission(self, employee_id: int, permission: str, course_name: str) -> dict:
        """Grant permission by recording certification completion."""
        cert = EmployeeCertification(
            employee_id=employee_id,
            cert_type="lms_permission",
            cert_name=course_name,
            expiry_date=datetime.now(timezone.utc).date() + timedelta(days=365),
            is_valid=True,
        )
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)

        return {
            "status": "granted",
            "employee_id": employee_id,
            "permission": permission,
            "course": course_name,
            "cert_id": cert.id,
        }

    def revoke_expired_permissions(self) -> int:
        """Revoke permissions for expired certifications."""
        expired = (
            self.db.query(EmployeeCertification)
            .filter(
                EmployeeCertification.is_valid == True,
                EmployeeCertification.cert_type == "lms_permission",
                EmployeeCertification.expiry_date < datetime.now().date(),
            )
            .all()
        )

        count = 0
        for cert in expired:
            cert.is_valid = False
            count += 1

        self.db.commit()
        return count

    def get_locked_permissions(self, employee_id: int) -> List[Dict[str, Any]]:
        """Get all locked permissions for an employee."""
        locked = []
        for permission, course in self.PERMISSION_COURSE_MAP.items():
            result = self.check_permission(employee_id, permission)
            if not result.get("allowed", True):
                locked.append({
                    "permission": permission,
                    "required_course": course,
                    "reason": result.get("reason"),
                })
        return locked


def get_lms_permission_lock(db: Session = None) -> LMSPermissionLock:
    return LMSPermissionLock(db or get_service_session())