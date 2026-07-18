from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from models import Employee, EmployeeLeaveLedger, EmployeeExpense
from services.leave_accrual import LeaveAccrualEngine
from services.asset_tracking import AssetTrackingService
from services.expense_processing import ExpenseProcessingService
from middleware.country_rls import CountryAccessScope
from utils.country_rls import get_current_country_scope as get_country_scope

logger = logging.getLogger(__name__)

router = APIRouter()


class LeaveBalanceResponse(BaseModel):
    accrued: float
    used: float
    carried_forward: float
    available: float


class ExpenseSubmissionRequest(BaseModel):
    expense_type: str
    amount: float
    currency: str = "OMR"
    expense_date: Optional[datetime] = None
    receipt_url: Optional[str] = None


@router.get("/employees/{employee_id}/leave-balance", response_model=LeaveBalanceResponse)
def get_leave_balance(
    employee_id: int,
    current_user: dict,
    scope: CountryAccessScope = Depends(get_country_scope),
    db: Session = Depends(get_db),
):
    engine = LeaveAccrualEngine(db)
    return engine.get_balance(employee_id)


@router.post("/employees/{employee_id}/expenses")
def submit_expense(
    employee_id: int,
    request: ExpenseSubmissionRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = ExpenseProcessingService(db)
    expense_date = request.expense_date or datetime.utcnow()
    return service.submit_expense(
        employee_id=employee_id,
        expense_type=request.expense_type,
        amount=request.amount,
        currency=request.currency,
        expense_date=expense_date,
        receipt_url=request.receipt_url,
    )


@router.post("/employees/{employee_id}/assets")
def assign_asset(
    employee_id: int,
    asset_type: str,
    asset_tag: Optional[str] = None,
    current_user: dict = Depends(lambda: None),
    db: Session = Depends(get_db),
):
    service = AssetTrackingService(db)
    return service.assign_asset(
        employee_id=employee_id,
        asset_type=asset_type,
        asset_tag=asset_tag,
    )

