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
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.admin import EmployeeExpense
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeLeaveLedger
from domains.comms.services.asset_tracking import AssetTrackingService
from domains.governance.services.compliance_engine import GCCComplianceEngine
from domains.governance.services.compliance_engine import get_compliance_engine
from domains.finance.services.expense_processing import ExpenseProcessingService
from domains.hr.services.leave_accrual import LeaveAccrualEngine
from domains.country.utils.country_rls import get_current_country_scope as get_country_scope
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
