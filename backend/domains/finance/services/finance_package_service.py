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
from infrastructure.utils.audit import AuditAction, audit_log
from infrastructure.database.database import get_db
from domains.finance.services.contractor_milestone_read_service import list_contractor_milestones
from domains.finance.services.expense_routing import ExpenseRoutingEngine
from domains.finance.services.expense_routing import get_expense_router
from domains.finance.services.financial_reporting import FinancialReportingService
from domains.hr.ports import PayrollEngine
from domains.finance.services.treasury_adapter import TreasuryAdapter
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
