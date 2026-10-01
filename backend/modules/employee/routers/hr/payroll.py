"""Payroll sub-router — thin delegators to payroll_service."""
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.payroll.payroll_service import (
    PayrollApproveBody,
    process_payroll_batch as svc_process_payroll_batch,
    approve_payroll_batch as svc_approve_payroll_batch,
    calculate_employee_payroll,
    get_employee_payslips,
    employee_bank_accounts,
    verify_bank_account,
    payroll_status as svc_payroll_status,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.post("/payroll/calculate/{employee_id}")
def calculate_employee_payroll_route(employee_id: int, month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2020), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return calculate_employee_payroll(employee_id, month, year, db, current_user)


@router.post("/payroll/batch")
def process_payroll_batch_route(country_code: str = Query(..., min_length=2, max_length=10), month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2020), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return svc_process_payroll_batch(country_code, month, year, db, current_user)


@router.post("/payroll/approve")
def approve_payroll_batch_route(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    try:
        approve_body = PayrollApproveBody(**body)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    return svc_approve_payroll_batch(approve_body, db, current_user)


@router.get("/payroll/payslips/{employee_id}")
def get_employee_payslips_route(employee_id: int, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_employee_payslips(employee_id, db, current_user)


@router.get("/payroll/bank-accounts/{employee_id}")
def employee_bank_accounts_route(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return employee_bank_accounts(employee_id, db, current_user)


@router.post("/payroll/bank-accounts/{account_id}/verify")
def verify_bank_account_route(account_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return verify_bank_account(account_id, db, current_user)


@router.get("/payroll/status/{country_code}")
def payroll_status_route(country_code: str = Path(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return svc_payroll_status(country_code, db)