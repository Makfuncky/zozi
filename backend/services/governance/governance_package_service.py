"""
Governance Domain — operational HR, expense processing, asset tracking, compliance.

Legacy hand-written router (thin HTTP layer). All business logic lives in the
hr/finance/compliance/asset services; this module only adapts HTTP requests.
"""
from __future__ import annotations
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from controllers.security.auth_controller import get_current_user
from db.database import get_db
from models import Employee, EmployeeExpense, EmployeeLeaveLedger
from services.common.asset_tracking import AssetTrackingService
from services.audit.compliance_engine import GCCComplianceEngine, get_compliance_engine
from services.finance.expense_processing import ExpenseProcessingService
from services.hr.leave_accrual import LeaveAccrualEngine
from utils.country_rls import get_current_country_scope as get_country_scope
logger = logging.getLogger(__name__)

class LeaveBalanceResponse(BaseModel):
    accrued: float
    used: float
    carried_forward: float
    available: float

class ExpenseSubmissionRequest(BaseModel):
    expense_type: str
    amount: float
    currency: str = 'OMR'
    expense_date: Optional[datetime] = None
    receipt_url: Optional[str] = None
