from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import List, Optional, Set

from sqlalchemy.orm import Session

from models import User, AuditLog, Employee
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class COIService:
    """
    Conflict of Interest detection and prevention engine.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def build_relationship_graph(self) -> dict:
        """Build graph of all employee relationships."""
        employees = self.db.query(Employee).all()
        graph = {}
        
        for emp in employees:
            graph[emp.user_id] = {
                "reports_to": emp.reports_to_id,
                "hiring_manager": emp.hiring_manager_id,
                "managed_employees": [],
            }
        
        for user_id, data in graph.items():
            if data["reports_to"]:
                if data["reports_to"] in graph:
                    graph[data["reports_to"]]["managed_employees"].append(user_id)
        
        return graph
    
    def detect_coi(self, employee_id: int, related_entity_id: int, entity_type: str) -> Optional[dict]:
        """Check for conflict of interest between employee and related entity."""
        employee = self.db.query(Employee).filter(Employee.user_id == employee_id).first()
        if not employee:
            return None
        
        if entity_type == "supplier":
            supplier = self.db.query(User).filter(User.id == related_entity_id).first()
            if not supplier:
                return None
            
            if employee.country_code and supplier.staff_country_codes:
                supplier_countries = set(str(c).strip().upper() for c in supplier.staff_country_codes)
                if employee.country_code.upper() in supplier_countries:
                    return {
                        "type": "supplier_relationship",
                        "employee_id": employee_id,
                        "related_id": related_entity_id,
                        "risk_level": "high",
                        "requires_approval": True,
                    }
        
        return None
    
    def auto_route_approval(self, operation: dict) -> str:
        """Route operations with COI to appropriate approvers."""
        coi = operation.get("coi_risk")
        if not coi:
            return "direct_approve"
        
        if coi.get("risk_level") == "high":
            return "senior_management"
        elif coi.get("risk_level") == "medium":
            return "department_head"
        
        return "peer_review"
    
    def log_coi_detection(self, coi_result: dict) -> None:
        """Log COI detection to audit trail."""
        audit = AuditLog(
            event_type="coi_detection",
            actor_id=None,
            action="flag",
            resource_type="financial_operation",
            resource_id=coi_result.get("related_id"),
            details=json.dumps(coi_result),
            severity="warning",
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()


def check_approval_blocked(approver_user_id: int, employee_id: int, db: Session) -> tuple[bool, str | None]:
    """Check if approval is blocked due to COI. Returns (blocked, reason)."""
    service = COIService(db)
    graph = service.build_relationship_graph()
    
    if employee_id in graph:
        if graph[employee_id].get("reports_to") == approver_user_id:
            return True, "Approver is direct manager of employee"
        if approver_user_id in graph.get(employee_id, {}).get("managed_employees", []):
            return True, "Approver manages the employee"
    
    return False, None

