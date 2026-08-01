from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy.orm import Session

from models import EmployeeExpense, AuditLog
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


class ExpenseProcessingService:
    """
    Expense validation and reimbursement processing.
    """
    
    PER_DIEM_LIMITS = {
        "OMR": Decimal("50.000"),
        "AED": Decimal("50.000"),
        "SAR": Decimal("50.000"),
        "QAR": Decimal("50.000"),
        "KWD": Decimal("15.000"),
        "BHD": Decimal("50.000"),
        "OMR": Decimal("50.000"),
    }
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_expense(self, expense: EmployeeExpense) -> tuple:
        """Validate expense against policy."""
        errors = []
        
        if expense.amount <= 0:
            errors.append("Amount must be positive")
        
        per_diem = self.PER_DIEM_LIMITS.get(expense.currency, Decimal("50.000"))
        if expense.amount > per_diem:
            errors.append(f"Exceeds per-diems limit of {per_diem} {expense.currency}")
        
        return len(errors) == 0, errors
    
    def submit_expense(
        self,
        employee_id: int,
        expense_type: str,
        amount: float,
        currency: str,
        expense_date: datetime,
        receipt_url: Optional[str] = None,
    ) -> EmployeeExpense:
        """Submit an expense for approval."""
        expense = EmployeeExpense(
            employee_id=employee_id,
            expense_type=expense_type,
            amount=amount,
            currency=currency,
            expense_date=expense_date,
            receipt_url=receipt_url,
            submitted_at=_utcnow(),
            status="submitted",
        )
        
        is_valid, errors = self.validate_expense(expense)
        if not is_valid:
            expense.status = "rejected"
            expense.approval_notes = "; ".join(errors)
        
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def approve_expense(self, expense_id: int, approver_id: int, approved: bool) -> bool:
        """Approve or reject an expense."""
        expense = (
            self.db.query(EmployeeExpense)
            .filter(EmployeeExpense.id == expense_id)
            .first()
        )
        if not expense:
            return False
        
        expense.status = "approved" if approved else "rejected"
        expense.approved_by = approver_id
        expense.approved_at = _utcnow()
        
        audit = AuditLog(
            event_type="expense_approval",
            actor_id=approver_id,
            action="approve" if approved else "reject",
            resource_type="expense",
            resource_id=expense_id,
            occurred_at=_utcnow(),
        )
        self.db.add(audit)
        self.db.commit()
        return True
    
    def process_reimbursement(self, expense_id: int) -> dict:
        """Process reimbursement payment."""
        expense = (
            self.db.query(EmployeeExpense)
            .filter(EmployeeExpense.id == expense_id)
            .first()
        )
        if not expense:
            return {"status": "not_found"}
        
        expense.status = "paid"
        self.db.commit()
        
        return {"status": "processed", "amount": expense.amount}

