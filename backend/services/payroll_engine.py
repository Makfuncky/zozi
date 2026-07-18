from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict

from sqlalchemy.orm import Session

from models import Employee, EmployeeLeaveLedger, User, AuditLog
from services.leave_accrual import LeaveAccrualEngine
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class PayrollEngine:
    """
    Salary calculation engine with tax and deduction calculations per country.
    """
    
    TAX_RATES = {
        "OMR": Decimal("0.00"),
        "AED": Decimal("0.00"),
        "SAR": Decimal("0.00"),
        "QAR": Decimal("0.00"),
        "KWD": Decimal("0.00"),
        "BHD": Decimal("0.00"),
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_gross_pay(self, employee_id: int, period_days: int = 30) -> Decimal:
        """Calculate gross pay for an employee."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == employee_id)
            .first()
        )
        
        if not employee or not employee.base_salary:
            return Decimal("0")
        
        daily_salary = employee.base_salary / Decimal("30")
        return daily_salary * period_days
    
    def calculate_deductions(self, employee_id: int) -> Dict[str, Decimal]:
        """Calculate tax and other deductions."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == employee_id)
            .first()
        )
        
        if not employee:
            return {"tax": Decimal("0"), "other": Decimal("0")}
        
        tax_rate = self.TAX_RATES.get(employee.currency, Decimal("0"))
        gross = self.calculate_gross_pay(employee_id)
        tax = gross * tax_rate
        
        return {"tax": tax, "other": Decimal("0")}
    
    def process_payroll_batch(self, month: Optional[datetime] = None) -> dict:
        """Process payroll for all active employees."""
        month = month or _utcnow()
        active_employees = (
            self.db.query(Employee)
            .filter(Employee.employment_status == "active")
            .all()
        )
        
        processed = 0
        total_gross = Decimal("0")
        total_net = Decimal("0")
        
        for emp in active_employees:
            gross = self.calculate_gross_pay(emp.user_id)
            deductions = self.calculate_deductions(emp.user_id)
            net = gross - deductions["tax"] - deductions["other"]
            
            audit = AuditLog(
                event_type="payroll",
                actor_id=None,
                action="process",
                resource_type="employee",
                resource_id=emp.user_id,
                details={
                    "gross": float(gross),
                    "tax": float(deductions["tax"]),
                    "net": float(net),
                    "currency": emp.currency,
                },
                occurred_at=_utcnow(),
            )
            self.db.add(audit)
            
            total_gross += gross
            total_net += net
            processed += 1
        
        self.db.commit()
        return {
            "processed": processed,
            "total_gross": float(total_gross),
            "total_net": float(total_net),
        }
    
    def calculate_eosb(self, employee_id: int) -> Decimal:
        """Calculate End-of-Service Gratuity per GCC labor law."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == employee_id)
            .first()
        )
        
        if not employee or not employee.hire_date:
            return Decimal("0")
        
        years_of_service = (datetime.utcnow().date() - employee.hire_date).days / 365
        if years_of_service < 1:
            return Decimal("0")
        
        daily_salary = employee.base_salary / Decimal("30")
        if years_of_service < 5:
            return daily_salary * years_of_service * 21
        else:
            return daily_salary * 21 * 5 + daily_salary * (years_of_service - 5) * 30

