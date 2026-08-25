"""
Conflict of Interest (COI) Detection & Nepotism Graph Engine.

Consolidates coi_engine.py (graph-based relationship detection + COI report CRUD)
and coi_service.py (COI detection, approval routing, audit logging) into a single
canonical service.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional, Set

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from domains.governance.models.core import AuditLog
from domains.hr.models.employee_models import COIReport
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeRelation
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


# ── Risk Levels ──────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ── Graph Engine ─────────────────────────────────────────────────────────────

class COIEngine:
    """Graph-based relationship detection and segregation-of-duties enforcement."""

    def __init__(self, db: Session):
        self.db = db

    def get_related_employees(self, employee_id: int) -> Set[int]:
        related_ids: Set[int] = set()
        stack = [employee_id]
        visited: Set[int] = set()

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
                other_id = (
                    rel.internal_employee_id
                    if rel.employee_id == current_id
                    else rel.employee_id
                )
                if other_id and other_id not in visited:
                    related_ids.add(other_id)
                    stack.append(other_id)

        return related_ids

    def check_approval_conflict(self, approver_id: int, target_employee_id: int) -> bool:
        if approver_id == target_employee_id:
            return True
        related = self.get_related_employees(target_employee_id)
        return approver_id in related

    def create_coi_report(
        self,
        employee_id: int,
        related_person_name: str,
        relation_type: str,
        is_internal: bool,
        internal_employee_id: Optional[int] = None,
    ) -> COIReport:
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
            is_approved=False,
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.warning("COI report created: employee=%s, risk=%s", employee_id, risk_level.value)
        return report

    def get_active_coi_reports(self, employee_id: int) -> List[COIReport]:
        return (
            self.db.query(COIReport)
            .filter(COIReport.employee_id == employee_id, COIReport.is_approved == False)
            .all()
        )

    def approve_coi_report(self, report_id: int, approver_id: int) -> bool:
        report = self.db.query(COIReport).filter(COIReport.id == report_id).first()
        if not report:
            return False

        report.is_approved = True
        report.approved_by = approver_id
        report.approved_at = datetime.now(timezone.utc)
        self.db.commit()
        return True

    def intercept_approval(
        self, approver_id: int, target_employee_id: int, transaction_type: str
    ) -> dict:
        has_conflict = self.check_approval_conflict(approver_id, target_employee_id)

        if has_conflict:
            return {
                "blocked": True,
                "reason": "Conflict of Interest detected",
                "requires_global_admin": True,
                "transaction_type": transaction_type,
            }

        return {"blocked": False}


# ── High-Level Service ───────────────────────────────────────────────────────

class COIService:
    """Conflict of Interest detection, approval routing, and audit logging."""

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

    def detect_coi(
        self, employee_id: int, related_entity_id: int, entity_type: str
    ) -> Optional[dict]:
        """Check for conflict of interest between employee and related entity."""
        employee = (
            self.db.query(Employee).filter(Employee.user_id == employee_id).first()
        )
        if not employee:
            return None

        if entity_type == "supplier":
            # TODO: Add supplier COI check when Supplier model is available
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


# ── Module-Level Helpers ─────────────────────────────────────────────────────

def get_coi_engine(db: Session) -> COIEngine:
    return COIEngine(db)


def check_approval_blocked(
    approver_user_id: int, employee_id: int, db: Session
) -> tuple[bool, str | None]:
    """Check if approval is blocked due to COI. Returns (blocked, reason)."""
    service = COIService(db)
    graph = service.build_relationship_graph()

    if employee_id in graph:
        if graph[employee_id].get("reports_to") == approver_user_id:
            return True, "Approver is direct manager of employee"
        if approver_user_id in graph.get(employee_id, {}).get("managed_employees", []):
            return True, "Approver manages the employee"

    return False, None
