"""Audit service for financial operations and compliance."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

from models import AuditLog


class AuditService:
    """Service for comprehensive audit logging of financial operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[str],
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
    ) -> AuditLog:
        log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else None,
            details=details and str(details) or None,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def log_financial_operation(
        self,
        user_id: int,
        operation: str,
        amount: float,
        currency: str,
        country_code: str,
        reference_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        return self.log_action(
            user_id=user_id,
            action=f"FINANCIAL_{operation}",
            resource_type="financial_transaction",
            resource_id=reference_id,
            details={
                "amount": amount,
                "currency": currency,
                "country_code": country_code,
                **(details or {}),
            },
            status="success",
        )
    
    def log_payroll_freeze(
        self,
        employee_id: int,
        reason: str,
        frozen_by: int,
    ) -> AuditLog:
        return self.log_action(
            user_id=frozen_by,
            action="PAYROLL_FREEZE",
            resource_type="employee",
            resource_id=str(employee_id),
            details={"reason": reason},
            status="success",
        )
    
    def log_coi_violation(
        self,
        employee_id: int,
        related_employee_id: int,
        entity_type: str,
        entity_id: int,
        blocked: bool = True,
    ) -> AuditLog:
        return self.log_action(
            user_id=None,
            action="COI_DETECTED",
            resource_type="conflict_of_interest",
            resource_id=str(employee_id),
            details={
                "related_employee_id": related_employee_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "blocked": blocked,
            },
            status="blocked" if blocked else "warning",
        )


def create_audit_service(db: Session) -> AuditService:
    return AuditService(db)

