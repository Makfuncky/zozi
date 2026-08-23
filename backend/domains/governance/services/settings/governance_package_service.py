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
from infrastructure.utils.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.admin import EmployeeExpense
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeLeaveLedger
from domains.comms.services.admin.asset_tracking import AssetTrackingService
from domains.governance.services.audit.compliance_engine import GCCComplianceEngine
from domains.governance.services.audit.compliance_engine import get_compliance_engine
from domains.finance.ports import ExpenseProcessingService
from domains.hr.ports import LeaveAccrualEngine
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
