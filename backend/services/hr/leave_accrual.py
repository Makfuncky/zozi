from __future__ import annotations

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from data.models import Employee, EmployeeLeaveLedger
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class LeaveAccrualEngine:
    """
    PTO accrual engine per GCC labor law.
    """
    
    DAILY_ACCRUAL_RATES = {
        "bronze": Decimal("0.022"),
        "silver": Decimal("0.033"),
        "gold": Decimal("0.045"),
        "platinum": Decimal("0.067"),
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_accrual(
        self,
        employee_id: int,
        period_days: int = 30,
    ) -> Decimal:
        """Calculate leave accrual for an employee."""
        employee = (
            self.db.query(Employee)
            .filter(Employee.user_id == employee_id)
            .first()
        )
        
        if not employee or not employee.hire_date:
            return Decimal("0")
        
        badge_level = employee.badge_level or "bronze"
        daily_rate = self.DAILY_ACCRUAL_RATES.get(badge_level, Decimal("0.022"))
        
        return daily_rate * period_days
    
    def accrue_for_all(self) -> dict:
        """Accrue leave for all active employees."""
        employees = (
            self.db.query(Employee)
            .filter(Employee.employment_status == "active")
            .all()
        )
        
        accrued_count = 0
        for emp in employees:
            accrual = self.calculate_accrual(emp.user_id)
            
            ledger = EmployeeLeaveLedger(
                employee_id=emp.id,
                leave_type="annual",
                accrued_days=float(accrual),
                used_days=0,
                carried_forward=0,
                financial_year=str(_utcnow().year),
            )
            self.db.add(ledger)
            accrued_count += 1
        
        self.db.commit()
        return {"accrued": accrued_count}
    
    def get_balance(self, employee_id: int) -> dict:
        """Get current leave balance."""
        ledgers = (
            self.db.query(EmployeeLeaveLedger)
            .filter(EmployeeLeaveLedger.employee_id == employee_id)
            .all()        )
        
        total_accrued = sum(l.accrued_days for l in ledgers)
        total_used = sum(l.used_days for l in ledgers)
        total_carried = sum(l.carried_forward for l in ledgers)
        
        return {
            "accrued": total_accrued,
            "used": total_used,
            "carried_forward": total_carried,
            "available": total_accrued - total_used + total_carried,
        }

