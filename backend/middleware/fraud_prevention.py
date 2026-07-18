from __future__ import annotations

import json
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db
from models import User, Employee, AuditLog

logger = logging.getLogger(__name__)


class FraudDetectionMiddleware:
    """Real-time fraud detection for financial operations."""
    
    FRAUD_RULES = {
        "max_login_attempts_per_hour": 5,
        "max_transactions_per_hour": 10,
        "max_transaction_amount": 10000,
        "suspicious_country_change_days": 30,
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_impossible_travel(self, user_id: int, country_code: str, ip_address: str) -> bool:
        """Check if login location is physically impossible."""
        recent_logins = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.actor_id == user_id,
                AuditLog.event_type == "login",
                AuditLog.occurred_at > datetime.utcnow() - timedelta(hours=1),
            )
            .all()
        )
        
        for login in recent_logins:
            if login.details_json:
                details = json.loads(login.details_json)
                prev_country = details.get("country_code")
                if prev_country and prev_country != country_code:
                    return True
        return False
    
    def check_ghost_employee(self, employee_id: int) -> bool:
        """Check if employee has zero activity for 5+ working days."""
        five_days_ago = datetime.utcnow() - timedelta(days=5)
        
        recent_qr_scans = self.db.query(AuditLog).filter(
            AuditLog.resource_type == "attendance",
            AuditLog.resource_id == employee_id,
            AuditLog.occurred_at > five_days_ago,
        ).count()
        
        recent_api_activity = self.db.query(AuditLog).filter(
            AuditLog.actor_id == employee_id,
            AuditLog.occurred_at > five_days_ago,
        ).count()
        
        return recent_qr_scans == 0 and recent_api_activity == 0
    
    def check_coi(self, user_id: int, related_entity_id: int, entity_type: str) -> bool:
        """Check for conflict of interest."""
        employee = self.db.query(Employee).filter(Employee.user_id == user_id).first()
        if not employee:
            return False
        
        related_user = self.db.query(User).filter(User.id == related_entity_id).first()
        if not related_user:
            return False
        
        if employee.country_code and related_user.staff_country_codes:
            related_countries = set(str(c).strip().upper() for c in related_user.staff_country_codes)
            if employee.country_code.upper() in related_countries:
                return True
        
        return False


def fraud_prevention_dependency(request: Request, db: Session = None):
    """FastAPI dependency for fraud prevention checks."""
    if db is None:
        with get_db() as db_session:
            return _fraud_check_internal(request, db_session)
    return _fraud_check_internal(request, db)


def _fraud_check_internal(request: Request, db: Session):
    """Internal fraud check implementation."""
    user = getattr(request.state, "user", None)
    if not user:
        return None
    
    fraud_checker = FraudDetectionMiddleware(db)
    
    if fraud_checker.check_ghost_employee(user.get("id")):
        raise HTTPException(
            status_code=403,
            detail="Account flagged for review - no activity detected"
        )
    return None
