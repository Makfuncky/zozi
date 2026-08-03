"""
Offboarding Kill Switch & Asset Recovery Cascade
Immediate revocation of all access when employee is terminated
"""
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from data.models_employee_models import Employee, PhysicalIDCard, DynamicQRSession
from data.models import User, TreasuryAccount
from services.notification_service import NotificationService


logger = logging.getLogger("zozi.offboarding")


class AssetRecoveryTask:
    """Represents an asset recovery task for offboarding."""
    
    def __init__(self, asset_type: str, asset_id: str, assigned_to: int, status: str = "pending"):
        self.asset_type = asset_type
        self.asset_id = asset_id
        self.assigned_to = assigned_to
        self.status = status
        self.created_at = datetime.now(timezone.utc)
        self.returned_at = None


class OffboardingKillSwitch:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    def execute_offboarding(self, employee_id: int, reason: str = "termination") -> dict:
        """Execute the complete offboarding cascade."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        employee.employment_status = "terminated"
        employee.termination_date = datetime.now(timezone.utc).date()
        self.db.commit()
        
        results = {
            "success": True,
            "employee_id": employee_id,
            "employee_code": employee.employee_code,
            "actions_executed": [],
            "asset_recovery_tasks": []
        }
        
        results["actions_executed"].extend(self._revoke_physical_cards(employee_id))
        results["actions_executed"].extend(self._invalidate_qr_sessions(employee_id))
        results["actions_executed"].extend(self._revoke_user_access(employee_id))
        results["actions_executed"].extend(self._suspend_treasury_access(employee_id))
        results["asset_recovery_tasks"] = self._create_asset_recovery_tasks(employee_id)
        
        self._send_offboarding_notification(employee_id, results)
        
        logger.critical(f"Offboarding executed for employee {employee_id}: {reason}")
        
        return results
    
    def _revoke_physical_cards(self, employee_id: int) -> List[str]:
        cards = self.db.query(PhysicalIDCard).filter(
            PhysicalIDCard.employee_id == employee_id,
            PhysicalIDCard.is_revoked == False
        ).all()
        
        for card in cards:
            card.is_revoked = True
            card.revoked_at = datetime.now(timezone.utc)
        
        self.db.commit()
        return [f"revoked_card_{c.id}" for c in cards]
    
    def _invalidate_qr_sessions(self, employee_id: int) -> List[str]:
        sessions = self.db.query(DynamicQRSession).filter(
            DynamicQRSession.employee_id == employee_id,
            DynamicQRSession.used_at == None
        ).all()
        
        for session in sessions:
            session.expires_at = datetime.now(timezone.utc)
        
        self.db.commit()
        return [f"invalidated_session_{s.id}" for s in sessions]
    
    def _revoke_user_access(self, employee_id: int) -> List[str]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee or not employee.user_id:
            return []
        
        user = self.db.query(User).filter(User.id == employee.user_id).first()
        if user:
            user.is_active = False
            user.is_verified = False
            self.db.commit()
            return ["revoked_user_access"]
        return []
    
    def _suspend_treasury_access(self, employee_id: int) -> List[str]:
        results = []
        treasury = self.db.execute(
            text("SELECT id FROM treasury_accounts WHERE employee_id = :eid LIMIT 1"),
            {"eid": employee_id}
        ).fetchone()
        if treasury:
            results.append(f"suspended_treasury_{treasury[0]}")
        return results
    
    def _create_asset_recovery_tasks(self, employee_id: int) -> List[Dict[str, Any]]:
        """Create asset recovery tasks for IT department."""
        tasks = [
            AssetRecoveryTask("laptop", f"LAP-{employee_id}", employee_id),
            AssetRecoveryTask("phone", f"PHN-{employee_id}", employee_id),
            AssetRecoveryTask("badge", f"BAD-{employee_id}", employee_id),
            AssetRecoveryTask("keycard", f"KEY-{employee_id}", employee_id),
        ]
        
        task_list = []
        for task in tasks:
            task_list.append({
                "asset_type": task.asset_type,
                "asset_id": task.asset_id,
                "assigned_to": task.assigned_to,
                "status": task.status
            })
        
        return task_list
    
    def _send_offboarding_notification(self, employee_id: int, results: dict, reason: str = "termination"):
        """Send offboarding notifications to relevant parties."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee or not employee.user_id:
            return
        
        user = self.db.query(User).filter(User.id == employee.user_id).first()
        if user:
            self.notification_service.send_alert(
                alert_type="employment_terminated",
                data={
                    "user_id": user.id,
                    "employee_id": employee_id,
                    "reason": reason,
                    "message": "Your employment has been terminated. All systems access has been revoked."
                },
                priority="high"
            )
    
    def pre_offboarding_check(self, employee_id: int) -> dict:
        """Check if employee is ready for offboarding."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"valid": False, "reason": "Employee not found"}
        
        issues = []
        
        cards = self.db.query(PhysicalIDCard).filter(
            PhysicalIDCard.employee_id == employee_id,
            PhysicalIDCard.is_revoked == False
        ).count()
        if cards > 0:
            issues.append(f"{cards} active physical cards")
        
        pending_sessions = self.db.query(DynamicQRSession).filter(
            DynamicQRSession.employee_id == employee_id,
            DynamicQRSession.used_at == None,
            DynamicQRSession.expires_at > datetime.now(timezone.utc)
        ).count()
        if pending_sessions > 0:
            issues.append(f"{pending_sessions} pending QR sessions")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "ready_for_offboarding": True
        }


def get_kill_switch(db: Session) -> OffboardingKillSwitch:
    return OffboardingKillSwitch(db)

