from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from models import Employee
from services.mobile_auth_service import MobileAuthService
from services.attendance_service import AttendanceService
from services.leave_accrual import LeaveAccrualEngine
from services.expense_processing import ExpenseProcessingService
from middleware.country_rls import CountryAccessScope
from utils.country_rls import get_current_country_scope as get_country_scope

logger = logging.getLogger(__name__)

router = APIRouter()


class BiometricLoginRequest(BaseModel):
    biometric_token: str
    platform: str


class CheckInRequest(BaseModel):
    lat: float
    lon: float
    office_id: Optional[int] = None


class LeaveRequest(BaseModel):
    leave_type: str
    days: float
    start_date: datetime
    end_date: datetime


class ExpenseSubmitRequest(BaseModel):
    expense_type: str
    amount: float
    currency: str = "OMR"
    expense_date: datetime
    receipt_url: Optional[str] = None


@router.post("/mobile/biometric-login")
def biometric_login(
    request: BiometricLoginRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = MobileAuthService(db)
    return service.validate_biometric(
        current_user.get("id"),
        request.biometric_token,
        request.platform,
    )


@router.post("/mobile/check-in")
def mobile_check_in(
    request: CheckInRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = MobileAuthService(db)
    return service.geo_fenced_check_in(
        current_user.get("id"),
        request.lat,
        request.lon,
        request.office_id,
    )


@router.get("/mobile/leave-balance")
def get_leave_balance(
    current_user: dict,
    db: Session = Depends(get_db),
):
    engine = LeaveAccrualEngine(db)
    employee = db.query(Employee).filter(Employee.user_id == current_user.get("id")).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return engine.get_balance(employee.id)


@router.post("/mobile/expenses")
def submit_expense(
    request: ExpenseSubmitRequest,
    current_user: dict,
    db: Session = Depends(get_db),
):
    service = ExpenseProcessingService(db)
    employee = db.query(Employee).filter(Employee.user_id == current_user.get("id")).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return service.submit_expense(
        employee_id=employee.id,
        expense_type=request.expense_type,
        amount=request.amount,
        currency=request.currency,
        expense_date=request.expense_date,
        receipt_url=request.receipt_url,
    )

