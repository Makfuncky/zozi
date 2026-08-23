"""Accounting Router — General Ledger API and Financial Report endpoints."""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional
from fastapi import Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from modules.admin.routers.admin_controller import require_admin
from modules.finance.routers import accounting_controller
from domains.finance.services.reporting.financial_reporting import FinancialReportingService
from domains.finance.services.ledger.period_close_service import get_or_create_fiscal_period
from domains.finance.services.ledger.period_close_service import get_current_fiscal_period
from domains.finance.services.ledger.period_close_service import close_period
from domains.finance.services.ledger.period_close_service import list_periods
from domains.finance.services.ledger.je_reversal_service import reverse_journal_entry
from domains.finance.services.treasury.cash_flow_forecast_service import generate_forecast as generate_cash_forecast
from modules.finance.routers.sub_ledger_controller import controller_get_ar_summary, controller_get_ap_summary, controller_post_ar_invoice, controller_post_ar_payment, controller_post_ap_payable, controller_post_ap_payment
from infrastructure.utils.audit import AuditAction, audit_log
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

class ReportPeriod(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str = 'OMR'
    persist: bool = False
    country_code: Optional[str] = None

class ClosePeriodBody(BaseModel):
    period_id: int
    notes: Optional[str] = None
    transfer_to_retained_earnings: bool = True

class ReversalBody(BaseModel):
    entry_id: int
    reason: str

class ARInvoiceBody(BaseModel):
    customer_id: int
    amount: float
    order_id: Optional[int] = None
    invoice_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class ARPaymentBody(BaseModel):
    customer_id: int
    amount: float
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class APPayableBody(BaseModel):
    supplier_id: int
    amount: float
    order_id: Optional[int] = None
    settlement_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None

class APPaymentBody(BaseModel):
    supplier_id: int
    amount: float
    settlement_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = 'OMR'
    country_code: Optional[str] = None


