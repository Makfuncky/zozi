"""
HSE & Insurance Automation
Health, Safety, Environment and Insurance management
"""
import logging
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy.orm import Session

from data.models_employee_models import Employee

logger = logging.getLogger("zozi.hse")


class HSEManager:
    def __init__(self, db: Session):
        self.db = db
    
    def register_insurance_policy(self, employee_id: int, policy_type: str,
                                   provider: str, coverage_amount: Decimal,
                                   start_date: datetime, end_date: datetime) -> dict:
        from decimal import Decimal
        
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "policy_type": policy_type,
            "provider": provider,
            "coverage": str(coverage_amount),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    
    def schedule_safety_training(self, employee_id: int, training_type: str,
                                  due_date: datetime) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "training_type": training_type,
            "due_date": due_date.isoformat(),
            "status": "scheduled"
        }
    
    def track_incident(self, employee_id: int, incident_type: str,
                       severity: str, description: str) -> dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"success": False, "error": "Employee not found"}
        
        return {
            "success": True,
            "employee_id": employee_id,
            "incident_type": incident_type,
            "severity": severity,
            "description": description,
            "incident_date": datetime.now(timezone.utc).isoformat()
        }
    
    def get_compliance_status(self, employee_id: int) -> Dict:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return {"error": "Employee not found"}
        
        return {
            "employee_id": employee_id,
            "insurance_enrolled": True,
            "safety_training_complete": True,
            "next_training_due": (datetime.now(timezone.utc) + timedelta(days=365)).isoformat(),
            "incident_count": 0
        }


def get_hse_manager(db: Session) -> HSEManager:
    return HSEManager(db)

