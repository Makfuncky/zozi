"""
Finance Domain — payroll, treasury, expense routing, contractor milestones.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.audit_log import AuditAction, audit_log
from dependencies.auth import get_current_user
from db.database import get_db
from services.expense_routing import ExpenseRoutingEngine, get_expense_router
from services.financial_reporting import FinancialReportingService
from services.payroll_engine import PayrollEngine
from services.treasury_adapter import TreasuryAdapter

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Pydantic Models ──────────────────────────────────────────────────────────


class PayrollProcessRequest(BaseModel):
    month: Optional[datetime] = None


class TreasuryEntryRequest(BaseModel):
    entry_type: str
    amount: float
    currency: str = "OMR"
    debit_account_id: int
    credit_account_id: int
    description: str
    reference_id: Optional[int] = None


# ── Payroll / Treasury ──────────────────────────────────────────────────────


@router.post("/payroll/process")
def process_payroll(
    request: PayrollProcessRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = PayrollEngine(db)
    result = engine.process_payroll_batch(request.month)
    audit_log(
        db=db,
        action=AuditAction.PAYROLL_PROCESSED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="payroll_batch",
        details={"month": str(request.month) if request.month else None, "result": result},
    )
    return result


@router.post("/treasury/journal-entry")
def create_journal_entry(
    request: TreasuryEntryRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    adapter = TreasuryAdapter(db)
    entry = adapter.post_journal_entry(
        entry_type=request.entry_type,
        amount=Decimal(str(request.amount)),
        currency=request.currency,
        debit_account_id=request.debit_account_id,
        credit_account_id=request.credit_account_id,
        description=request.description,
        reference_id=request.reference_id,
    )
    audit_log(
        db=db,
        action=AuditAction.JOURNAL_ENTRY_CREATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="journal_entry",
        resource_id=entry.id,
        details={
            "entry_type": request.entry_type,
            "amount": request.amount,
            "currency": request.currency,
            "debit_account_id": request.debit_account_id,
            "credit_account_id": request.credit_account_id,
            "description": request.description,
        },
    )
    return {"id": entry.id, "status": "created"}


@router.get("/financial/cash-flow")
def get_cash_flow(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FinancialReportingService(db)
    result = service.get_cash_flow_forecast(days)
    audit_log(
        db=db,
        action=AuditAction.CASH_FORECAST_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="cash_flow_forecast",
        details={"days": days},
    )
    return result


@router.get("/financial/profitability")
def get_profitability(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = FinancialReportingService(db)
    result = service.get_profitability_by_country()
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="profitability_report",
        details={"countries": list(result.keys()) if isinstance(result, dict) else None},
    )
    return result


# ── Expense Routing ──────────────────────────────────────────────────────────


@router.post("/expense/route")
def route_claim(employee_id: int, amount: float, category: str, description: str,
                db: Session = Depends(get_db)):
    router = get_expense_router(db)
    return router.route_expense_claim(
        employee_id=employee_id,
        amount=Decimal(str(amount)),
        category=category,
        description=description
    )


@router.get("/expense/deadline")
def get_deadline(employee_id: int, submission_date: str, priority: str = "normal",
                 db: Session = Depends(get_db)):
    router = get_expense_router(db)
    dt = datetime.fromisoformat(submission_date)
    return {"deadline": router.calculate_reimbursement_deadline(dt, priority).isoformat()}


@router.get("/expense/chain/{employee_id}")
def get_chain(employee_id: int, amount: float, db: Session = Depends(get_db)):
    router = get_expense_router(db)
    return {"approval_chain": router.get_approval_chain(employee_id, Decimal(str(amount)))}


@router.get("/contractor-milestones")
def list_contractor_milestones(db: Session = Depends(get_db)):
    """Return contractor payment/delivery milestones."""
    rows = db.execute(
        text("""
            SELECT m.id, m.employee_id, e.employee_code, m.milestone_type,
                   m.due_date, m.status
            FROM contractor_milestones m
            LEFT JOIN employees e ON e.id = m.employee_id
            ORDER BY m.due_date ASC
        """)
    ).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "milestone_type": r[3],
            "due_date": r[4],
            "status": r[5],
        }
        for r in rows
    ]

