"""Role-Based Access Control service with delegation workflows."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from data.models import User, Employee, CountryStaffAssignment


from utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP


class RBACService:
    """Service for role-based access control and delegation workflows."""

    DEFAULT_ROLES = {
        role: {"permissions": sorted(permissions)}
        for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_role(self, user_id: int) -> str:
        """Get user's role."""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.role if user else "customer"
    
    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user's permissions based on role."""
        role = self.get_user_role(user_id)
        role_def = self.DEFAULT_ROLES.get(role, {"permissions": []})
        return list(role_def.get("permissions", []))
    
    def get_user_country_scope(self, user_id: int) -> List[str]:
        """Get countries user has access to."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        role = str(user.role or "").lower()
        if role == "admin":
            return ["ALL"]
        
        staff_codes = user.staff_country_codes or []
        return [str(c).strip().upper() for c in staff_codes]
    
    def check_permission(self, user_id: int, permission: str, country_code: str = None) -> bool:
        """Check if user has a specific permission for a country."""
        permissions = self.get_user_permissions(user_id)
        if permission not in permissions:
            return False
        
        if country_code:
            scope = self.get_user_country_scope(user_id)
            if "ALL" not in scope and country_code.upper() not in scope:
                return False
        
        return True
    
    def delegate_permission(
        self,
        delegator_id: int,
        delegatee_id: int,
        permission: str,
        country_code: str,
        valid_until: datetime,
        notes: str = None,
    ) -> bool:
        """Delegate a permission to another user (e.g., manager approval)."""
        if not self.check_permission(delegator_id, "approve"):
            return False
        
        if not self.check_permission(delegator_id, "write", country_code):
            return False
        
        return True
    
    def request_leave_approval(
        self,
        employee_id: int,
        leave_request_id: int,
        approver_id: int,
    ) -> bool:
        """Request leave approval through delegation workflow."""
        if not self.check_permission(approver_id, "approve"):
            return False
        
        employee = (
            self.db.query(Employee)
            .filter(Employee.id == employee_id)
            .first()
        )
        if not employee:
            return False
        
        if employee.user_id != approver_id:
            if not self.check_permission(approver_id, "manage_operations", employee.country_code):
                return False
        
        return True
    
    def get_delegation_chain(self, user_id: int) -> List[Dict[str, Any]]:
        """Get the delegation chain for a user."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return []

        role = str(user.role or "").lower()
        if role == "admin":
            return [{"type": "admin", "id": user.id}]

        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == user_id)
            .first()
        )
        if not employee:
            return []

        chain = []
        if employee.hiring_manager_id:
            chain.append({"type": "hiring_manager", "id": employee.hiring_manager_id})
        if employee.reporting_manager_id:
            chain.append({"type": "reports_to", "id": employee.reporting_manager_id})

        return chain

    def can_approve_resource(
        self,
        user_id: int,
        resource_type: str,
        amount: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Check if user can approve a resource using the approval matrix."""
        from services.approval_matrix_service import can_approve as _can_approve
        return _can_approve(self.db, user_id, resource_type, amount=amount)

    def resolve_resource_approvers(
        self,
        resource_type: str,
        org_unit_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Find all users who can approve a given resource type."""
        from services.approval_matrix_service import resolve_approvers as _resolve
        return _resolve(self.db, resource_type, org_unit_id=org_unit_id)

    def get_resource_approval_chain(
        self,
        user_id: int,
        resource_type: str,
    ) -> List[Dict[str, Any]]:
        """Get the user's chain of approvers for a resource type."""
        from services.approval_matrix_service import get_approval_chain as _chain
        return _chain(self.db, user_id, resource_type)


def create_rbac_service(db: Session) -> RBACService:
    return RBACService(db)

