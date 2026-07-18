from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from models import JournalEntry
from services.payroll_engine import PayrollEngine
from services.treasury_adapter import TreasuryAdapter
from services.financial_reporting import FinancialReportingService
from controllers.auth_controller import get_current_user
from controllers.audit_controller import AuditAction, audit_log
from utils.country_rls import get_current_country_scope as get_country_scope
from middleware.country_rls import CountryAccessScope
from utils.ip_utils import get_request_ip

logger = logging.getLogger(__name__)

router = APIRouter()


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

