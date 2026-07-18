"""
Conflict of Interest (COI) & Nepotism Graph Engine
Detects relationships between employees and enforces segregation of duties
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Set
from enum import Enum

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeRelation, COIReport
from models import User

logger = logging.getLogger("zozi.coi")


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class COIEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_related_employees(self, employee_id: int) -> Set[int]:
        related_ids = set()
        stack = [employee_id]
        visited = set()
        
        while stack:
            current_id = stack.pop()
            if current_id in visited:
                continue
            visited.add(current_id)
            
            relations = self.db.query(EmployeeRelation).filter(
                or_(
                    EmployeeRelation.employee_id == current_id,
                    EmployeeRelation.internal_employee_id == current_id
                )
            ).all()
            
            for rel in relations:
                other_id = rel.internal_employee_id if rel.employee_id == current_id else rel.employee_id
                if other_id and other_id not in visited:
                    related_ids.add(other_id)
                    stack.append(other_id)
        
        return related_ids
    
    def check_approval_conflict(self, approver_id: int, target_employee_id: int) -> bool:
        if approver_id == target_employee_id:
            return True
        
        related = self.get_related_employees(target_employee_id)
        return approver_id in related
    
    def create_coi_report(self, employee_id: int, related_person_name: str, 
                          relation_type: str, is_internal: bool, 
                          internal_employee_id: Optional[int] = None) -> COIReport:
        related_ids = self.get_related_employees(employee_id)
        risk_level = RiskLevel.LOW
        
        if internal_employee_id and internal_employee_id in related_ids:
            risk_level = RiskLevel.CRITICAL
        
        report = COIReport(
            employee_id=employee_id,
            related_person_name=related_person_name,
            relation_type=relation_type,
            is_internal=is_internal,
            internal_employee_id=internal_employee_id,
            risk_level=risk_level.value,
            is_approved=False
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        
        logger.warning(f"COI report created: employee={employee_id}, risk={risk_level.value}")
        return report
    
    def get_active_coi_reports(self, employee_id: int) -> List[COIReport]:
        return self.db.query(COIReport).filter(
            COIReport.employee_id == employee_id,
            COIReport.is_approved == False
        ).all()
    
    def approve_coi_report(self, report_id: int, approver_id: int) -> bool:
        report = self.db.query(COIReport).filter(COIReport.id == report_id).first()
        if not report:
            return False
        
        report.is_approved = True
        report.approved_by = approver_id
        report.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        return True
    
    def intercept_approval(self, approver_id: int, target_employee_id: int, 
                           transaction_type: str) -> dict:
        has_conflict = self.check_approval_conflict(approver_id, target_employee_id)
        
        if has_conflict:
            return {
                "blocked": True,
                "reason": "Conflict of Interest detected",
                "requires_global_admin": True,
                "transaction_type": transaction_type
            }
        
        return {"blocked": False}


def get_coi_engine(db: Session) -> COIEngine:
    return COIEngine(db)

