"""
LMS & Permission Locking Middleware
Features: Certification-based access control, permission revocation on expiry
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeCertification
from db.database import get_service_session

logger = logging.getLogger("zozi.lms")


class LMSPermissionLock:
    """Locks system permissions until LMS certification is passed."""
    
    PERMISSION_COURSE_MAP = {
        "approve_invoices": "ZATCA_E_Invoicing",
        "approve_payouts": "Payment_Gateway_Compliance",
        "access_finance": "Financial_Data_Protection",
        "manage_suppliers": "Supplier_Onboarding_Compliance",
        "dispatch_treasury": "Treasury_Operations_Certification"
    }
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
    
    def check_permission(self, employee_id: int, permission: str) -> Dict[str, Any]:
        """Check if employee has valid certification for a permission."""
        required_course = self.PERMISSION_COURSE_MAP.get(permission)
        if not required_course:
            return {"allowed": True, "reason": "No certification required"}
        
        certification = self.db.query(EmployeeCertification).filter(
            EmployeeCertification.employee_id == employee_id,
            EmployeeCertification.cert_name == required_course,
            EmployeeCertification.is_valid == True
        ).first()
        
        if not certification:
            return {
                "allowed": False,
                "reason": f"Missing certification: {required_course}",
                "locked": True,
                "course": required_course
            }
        
        if certification.expiry_date and certification.expiry_date < datetime.now().date():
            return {
                "allowed": False,
                "reason": f"Certification expired: {required_course}",
                "locked": True,
                "course": required_course,
                "expired_at": certification.expiry_date.isoformat()
            }
        
        return {"allowed": True, "certification": required_course}
    
    def grant_permission(self, employee_id: int, permission: str, course_name: str) -> dict:
        """Grant permission by recording certification completion."""
        cert = EmployeeCertification(
            employee_id=employee_id,
            cert_type="lms_permission",
            cert_name=course_name,
            expiry_date=datetime.now(timezone.utc).date() + timedelta(days=365),
            is_valid=True
        )
        self.db.add(cert)
        self.db.commit()
        self.db.refresh(cert)
        
        return {
            "status": "granted",
            "employee_id": employee_id,
            "permission": permission,
            "course": course_name,
            "cert_id": cert.id
        }
    
    def revoke_expired_permissions(self) -> int:
        """Revoke permissions for expired certifications."""
        expired = self.db.query(EmployeeCertification).filter(
            EmployeeCertification.is_valid == True,
            EmployeeCertification.cert_type == "lms_permission",
            EmployeeCertification.expiry_date < datetime.now().date()
        ).all()
        
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
                    "reason": result.get("reason")
                })
        return locked


def get_lms_permission_lock(db: Session = None) -> LMSPermissionLock:
    return LMSPermissionLock(db or get_service_session())
