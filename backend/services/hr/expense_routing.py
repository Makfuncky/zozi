"""
Expense Claims Routing System
Routes expense claims based on amount, department, and approval hierarchy
"""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict

from sqlalchemy import and_
from sqlalchemy.orm import Session

from models.employee_models import Employee
from models import User

logger = logging.getLogger("zozi.expense")


class ExpenseRoutingEngine:
    def __init__(self, db: Session):
        self.db = db
    
    def get_approval_chain(self, employee_id: int, amount: Decimal) -> List[Dict]:
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return []
        
        chain = []
        current_level = 1
        
        reporting_manager_id = employee.reporting_manager_id
        if reporting_manager_id:
            manager = self.db.query(Employee).filter(Employee.id == reporting_manager_id).first()
            if manager:
                chain.append({
                    "level": current_level,
                    "employee_id": manager.id,
                    "approver_id": manager.user_id,
                    "max_amount": Decimal("5000.00"),
                    "required": amount > Decimal("1000.00")
                })
                current_level += 1
        
        if employee.department in ["finance", "operations", "admin"]:
            department_head = self.db.query(Employee).filter(
                Employee.department == employee.department,
                Employee.position.ilike("%head%")
            ).first()
            if department_head and department_head.id != reporting_manager_id:
                chain.append({
                    "level": current_level,
                    "employee_id": department_head.id,
                    "approver_id": department_head.user_id,
                    "max_amount": Decimal("50000.00"),
                    "required": amount > Decimal("10000.00")
                })
                current_level += 1
        
        if amount > Decimal("50000.00"):
            cfo = self.db.query(Employee).filter(
                Employee.position.ilike("%cfo%")
            ).first()
            if cfo:
                chain.append({
                    "level": current_level,
                    "employee_id": cfo.id,
                    "approver_id": cfo.user_id,
                    "max_amount": Decimal("1000000.00"),
                    "required": True
                })
        
        return chain
    
    def route_expense_claim(self, employee_id: int, amount: Decimal, 
                            category: str, description: str) -> dict:
        chain = self.get_approval_chain(employee_id, amount)
        
        if not chain:
            return {
                "routed": False,
                "error": "No approval chain found",
                "employee_id": employee_id
            }
        
        first_approver = next((a for a in chain if a["required"]), chain[0])
        
        return {
            "routed": True,
            "employee_id": employee_id,
            "amount": str(amount),
            "category": category,
            "approval_chain": chain,
            "first_approver": first_approver,
            "routing_timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def calculate_reimbursement_deadline(self, submission_date: datetime, 
                                         priority: str = "normal") -> datetime:
        from datetime import timedelta
        
        if priority == "urgent":
            return submission_date + timedelta(days=3)
        elif priority == "high":
            return submission_date + timedelta(days=7)
        else:
            return submission_date + timedelta(days=14)


def get_expense_router(db: Session) -> ExpenseRoutingEngine:
    return ExpenseRoutingEngine(db)

