"""Payroll Router â€” batch processing, maker-checker approval, disbursement, payslips."""
from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from services.finance.payroll_read_service import get_payroll_records, get_payroll_record_by_id, get_payroll_summary
from data.db import get_db
from data.models import Employee, EmployeeDocument
from services.payroll_engine import PayrollEngine
from services.hr.employee_write_service import list_employee_documents
from services.effective_permissions import check_permission
from utils.country_rls import enforce_country_access

logger = logging.getLogger(__name__)

router = APIRouter(tags=["payroll"])

# In-memory approval state (production would use DB)
PENDING_PAYROLL_APPROVALS: dict = {}


class PayrollApproveBody(BaseModel):
    batch_id: str
    approved: bool = True
    notes: Optional[str] = None


@router.post("/payroll/calculate/{employee_id}")
def calculate_employee_payroll(
    employee_id: int = Path(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    engine = PayrollEngine(db)
    period = date(year, month, 1)
    result = engine.calculate_monthly_payroll(employee_id, period)
    return result


@router.post("/payroll/batch")
def process_payroll_batch(
    country_code: str = Query(..., min_length=2, max_length=10),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate payroll batch (Maker step)."""
    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.release", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.release permission")

    engine = PayrollEngine(db)
    period = date(year, month, 1)

    # Check if already approved
    batch_key = f"{country_code}:{year}:{month:02d}"
    existing = PENDING_PAYROLL_APPROVALS.get(batch_key)
    if existing and existing.get("status") == "disbursed":
        raise HTTPException(status_code=400, detail="This period has already been disbursed")

    payroll = engine.process_payroll_batch(period, country_code.upper())
    payroll["country_code"] = country_code.upper()
    payroll["status"] = "pending_approval"
    PENDING_PAYROLL_APPROVALS[batch_key] = payroll
    return payroll


@router.post("/payroll/approve")
def approve_payroll_batch(
    body: PayrollApproveBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve payroll for disbursement (Checker step - cannot be same user as Maker)."""
    parts = body.batch_id.split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid batch_id format")
    country_code = parts[1]
    year = parts[2]
    month = parts[3] if len(parts) > 3 else "01"
    batch_key = f"{country_code}:{year}:{month}"

    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.approve", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.approve permission")

    pending = PENDING_PAYROLL_APPROVALS.get(batch_key)
    if not pending or pending.get("status") != "pending_approval":
        raise HTTPException(status_code=400, detail="No pending payroll batch found for this period")

    maker_user_id = pending.get("maker_user_id")
    if maker_user_id and maker_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot approve your own payroll batch")

    if not body.approved:
        PENDING_PAYROLL_APPROVALS[batch_key]["status"] = "rejected"
        return {"status": "rejected", "batch_id": body.batch_id}

    # Execute auto-disbursement
    engine = PayrollEngine(db)
    period = date(int(year), int(month), 1)
    disbursement = engine.auto_disburse(period, approved_by=user_id)
    disbursement["batch_id"] = body.batch_id
    disbursement["status"] = "disbursed"
    disbursement["approved_by"] = user_id
    disbursement["approved_at"] = datetime.utcnow().isoformat()

    PENDING_PAYROLL_APPROVALS[batch_key] = disbursement
    return disbursement


@router.get("/payroll/payslips/{employee_id}")
def get_employee_payslips(
    employee_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    docs = list_employee_documents(db, employee_id, skip, limit)
    return {
        "payslips": [
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "file_url": d.file_url,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    }


@router.get("/payroll/bank-accounts/{employee_id}")
def employee_bank_accounts(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    engine = PayrollEngine(db)
    return {"bank_accounts": engine.get_employee_bank_accounts(employee_id)}


@router.post("/payroll/bank-accounts/{account_id}/verify")
def verify_bank_account(
    account_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user.get("id", 0))
    engine = PayrollEngine(db)
    return engine.validate_bank_account(account_id, verified_by=user_id)


@router.get("/payroll/status/{country_code}")
def payroll_status(
    country_code: str = Path(..., min_length=2, max_length=10),
    db: Session = Depends(get_current_user),
):
    """Get current payroll batch status for a country."""
    results = {}
    for key, value in PENDING_PAYROLL_APPROVALS.items():
        if key.startswith(country_code.upper()):
            results[key] = {
                "status": value.get("status"),
                "processed": value.get("processed"),
                "total_net": value.get("total_net"),
            }
    return {"payroll_batches": results}
