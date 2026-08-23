"""
Finance Domain — payroll, treasury, expense routing, contractor milestones.

Legacy hand-written router (thin HTTP layer). All business logic and DB access
live in the finance/treasury/hr services; this module only adapts HTTP requests
to those services.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.utils.audit import AuditAction, audit_log
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.finance.services.accounts.contractor_milestone_read_service import list_contractor_milestones
from domains.finance.services.ledger.expense_routing import ExpenseRoutingEngine
from domains.finance.services.ledger.expense_routing import get_expense_router
from domains.finance.services.reporting.financial_reporting import FinancialReportingService
from domains.hr.services.payroll_engine import PayrollEngine
from domains.finance.services.treasury.treasury_adapter import TreasuryAdapter

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
def list_contractor_milestones_route(db: Session = Depends(get_db)):
    """Return contractor payment/delivery milestones."""
    return list_contractor_milestones(db)
