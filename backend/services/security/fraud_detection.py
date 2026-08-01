from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import text

from models import AuditLog, Employee, User
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


from enum import Enum


class FraudRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


FRAUD_INDICATORS = {
    "multiple_failed_logins": 5.0,
    "high_value_transaction": 4.0,
    "new_device_login": 3.0,
    "unusual_time_access": 2.0,
}


class FraudDetectionService:
    """
    Ghost employee detection and anomaly detection engine.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_risk_score(
        self,
        user_id: int,
        action: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> Tuple[float, List[str]]:
        """Calculate fraud risk score based on indicators."""
        score = 0.0
        indicators = []
        
        if action == "LOGIN_FAILED":
            score += 5.0
            indicators.append("multiple_failed_logins")
        
        if details:
            if details.get("amount", 0) > 10000:
                score += 4.0
                indicators.append("high_value_transaction")
            if details.get("new_device", False):
                score += 3.0
                indicators.append("new_device_login")
            if details.get("outside_hours", False):
                score += 2.0
                indicators.append("unusual_time_access")
        
        return min(score, 100.0), indicators
    
    def is_blocked(self, user_id: int, risk_score: float) -> bool:
        return risk_score >= 50.0
    
    def should_challenge(self, user_id: int, risk_score: float) -> bool:
        return risk_score >= 15.0
    
    def detect_ghost_employees(self) -> List[int]:
        """Find employees with zero activity for 5+ working days."""
        five_days_ago = _utcnow() - timedelta(days=5)
        
        ghost_employees = []
        
        employees = self.db.query(Employee).all()
        for emp in employees:
            qr_scans = (
                self.db.query(AuditLog)
                .filter(
                    AuditLog.resource_type == "attendance",
                    AuditLog.resource_id == emp.id,
                    AuditLog.occurred_at > five_days_ago,
                )
                .count()
            )
            
            api_activity = (
                self.db.query(AuditLog)
                .filter(
                    AuditLog.actor_id == emp.user_id,
                    AuditLog.occurred_at > five_days_ago,
                )
                .count()
            )
            
            if qr_scans == 0 and api_activity == 0:
                ghost_employees.append(emp.user_id)
                self._flag_employee(emp.user_id, "SUSPENDED_PENDING_REVIEW")
        
        return ghost_employees
    
    def _flag_employee(self, user_id: int, status: str) -> None:
        """Flag an employee account."""
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = False
            
            audit = AuditLog(
                event_type="employee_flag",
                actor_id=None,
                action="suspend",
                resource_type="user",
                resource_id=user_id,
                details={"reason": "no_activity_detected", "status": status},
                severity="warning",
                occurred_at=_utcnow(),
            )
            self.db.add(audit)
            self.db.commit()
    
    def detect_anomalies(self) -> List[dict]:
        """Detect anomalous behavior patterns."""
        anomalies = []
        
        one_hour_ago = _utcnow() - timedelta(hours=1)
        recent_logins = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.event_type == "login",
                AuditLog.occurred_at > one_hour_ago,
            )
            .all()
        )
        
        login_counts = {}
        for login in recent_logins:
            user_id = login.actor_id
            login_counts[user_id] = login_counts.get(user_id, 0) + 1
        
        for user_id, count in login_counts.items():
            if count > 10:
                anomalies.append({
                    "type": "excessive_logins",
                    "user_id": user_id,
                    "count": count,
                    "severity": "medium",
                })
        
        return anomalies
    
    def freeze_payroll_for_ghost(self, user_id: int) -> None:
        """Freeze payroll disbursement for flagged employee."""
        audit = AuditLog(
            event_type="payroll_freeze",
            actor_id=None,
            action="freeze",
            resource_type="user",
            resource_id=user_id,
            details={"reason": "ghost_employee_flagged"},
            severity="critical",
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()

