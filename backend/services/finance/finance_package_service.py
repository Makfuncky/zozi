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
from fastapi import Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils.audit import AuditAction, audit_log
from controllers.security.auth_controller import get_current_user
from db.database import get_db
from services.finance.contractor_milestone_read_service import list_contractor_milestones
from services.finance.expense_routing import ExpenseRoutingEngine, get_expense_router
from services.finance.financial_reporting import FinancialReportingService
from services.hr.payroll_engine import PayrollEngine
from services.treasury.treasury_adapter import TreasuryAdapter
logger = logging.getLogger(__name__)

class PayrollProcessRequest(BaseModel):
    month: Optional[datetime] = None

class TreasuryEntryRequest(BaseModel):
    entry_type: str
    amount: float
    currency: str = 'OMR'
    debit_account_id: int
    credit_account_id: int
    description: str
    reference_id: Optional[int] = None
