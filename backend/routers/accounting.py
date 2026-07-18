"""Accounting Router — General Ledger API and Financial Report endpoints."""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db.database import get_db
from controllers.admin_controller import require_admin
from controllers import accounting_controller
from services.financial_reporting import FinancialReportingService
from services.period_close_service import (
    get_or_create_fiscal_period,
    get_current_fiscal_period,
    close_period,
    list_periods,
)
from services.je_reversal_service import reverse_journal_entry
from services.cash_flow_forecast_service import generate_forecast as generate_cash_forecast
from controllers.sub_ledger_controller import (
    controller_get_ar_summary,
    controller_get_ap_summary,
    controller_post_ar_invoice,
    controller_post_ar_payment,
    controller_post_ap_payable,
    controller_post_ap_payment,
)
from controllers.audit_controller import AuditAction, audit_log
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context

router = APIRouter()


class ReportPeriod(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str = "OMR"
    persist: bool = False
    country_code: Optional[str] = None


def _with_rls(country_code: Optional[str], db: Session):
    """Set RLS context if country_code is provided. Returns cleanup function."""
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)
    def cleanup():
        if country_code:
            clear_rls_context()
    return cleanup


@router.post("/seed", summary="Seed chart of accounts (idempotent)")
def seed_chart_of_accounts(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    return accounting_controller.seed_chart_of_accounts(
        db,
        audit_user_id=_admin.get("id"),
        audit_username=_admin.get("username"),
        audit_user_role=_admin.get("role"),
    )


@router.get("/accounts", summary="List all accounts")
def list_accounts(
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.list_accounts(db)
    finally:
        cleanup()


@router.get("/accounts/{code}", summary="Get account by code")
def get_account(
    code: str,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.get_account(db, code)
    finally:
        cleanup()


@router.post("/journal-entries", summary="Create a journal entry")
def create_journal_entry(
    body: accounting_controller.JournalEntryBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    return accounting_controller.create_journal_entry(db, body, current_user)


@router.get("/journal-entries", summary="List journal entries")
def list_journal_entries(
    reference_type: Optional[str] = Query(None, max_length=40),
    reference_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.list_journal_entries(
            db, reference_type=reference_type, reference_id=reference_id, country_code=country_code, limit=limit
        )
    finally:
        cleanup()


@router.get("/journal-entries/{entry_id}", summary="Get journal entry by ID")
def get_journal_entry(
    entry_id: int,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.get_journal_entry(db, entry_id)
    finally:
        cleanup()


@router.get("/balances/{account_code}", summary="Get account balance")
def get_balance(
    account_code: str,
    currency: str = Query("OMR", max_length=10),
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.get_account_balance(db, account_code, currency)
    finally:
        cleanup()


@router.get("/trial-balance", summary="Get trial balance")
def trial_balance(
    as_of_date: Optional[date] = Query(None),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return accounting_controller.get_trial_balance(
            db, as_of_date=as_of_date, currency=currency, country_code=country_code
        )
    finally:
        cleanup()


# ── Financial Reports ──────────────────────────────────────────────────────


@router.post("/reports/income-statement", summary="Generate Income Statement (P&L)")
def income_statement(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(body.country_code, db)
    try:
        svc = FinancialReportingService(db)
        result = svc.generate_income_statement(
            body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
        )
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="income_statement",
            details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
        )
        return result
    finally:
        cleanup()


@router.post("/reports/balance-sheet", summary="Generate Balance Sheet")
def balance_sheet(
    as_of_date: Optional[datetime] = Query(None, description="Defaults to now"),
    currency: str = Query("OMR", max_length=10),
    persist: bool = Query(False),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        svc = FinancialReportingService(db)
        result = svc.generate_balance_sheet(as_of_date, currency, persist=persist, country_code=country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="balance_sheet",
            details={"as_of_date": (as_of_date or datetime.utcnow()).isoformat(), "currency": currency, "country_code": country_code},
        )
        return result
    finally:
        cleanup()


@router.post("/reports/cash-flow", summary="Generate Cash Flow Statement")
def cash_flow(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(body.country_code, db)
    try:
        svc = FinancialReportingService(db)
        result = svc.generate_cash_flow(
            body.period_start, body.period_end, body.currency, persist=body.persist, country_code=body.country_code
        )
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="cash_flow_statement",
            details={"period_start": body.period_start.isoformat(), "period_end": body.period_end.isoformat(), "currency": body.currency, "country_code": body.country_code},
        )
        return result
    finally:
        cleanup()


@router.get("/reports", summary="List saved financial reports")
def list_reports(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        svc = FinancialReportingService(db)
        return svc.list_reports(report_type=report_type, country_code=country_code, limit=limit)
    finally:
        cleanup()


# ── Fiscal Periods ──────────────────────────────────────────────────────────


class ClosePeriodBody(BaseModel):
    period_id: int
    notes: Optional[str] = None
    transfer_to_retained_earnings: bool = True


@router.post("/periods/get-or-create", summary="Get or create a fiscal period")
def get_or_create(
    country_code: str = Query(..., max_length=3),
    year: int = Query(..., ge=2020, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        period = get_or_create_fiscal_period(db, country_code, year, month)
        return {
            "id": period.id,
            "country_code": period.country_code,
            "label": f"{period.period_year}-{period.period_month:02d}",
            "status": period.status,
            "period_start": period.period_start.isoformat(),
            "period_end": period.period_end.isoformat(),
        }
    finally:
        cleanup()


@router.get("/periods/current", summary="Get current fiscal period")
def current_period(
    country_code: str = Query(..., max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        period = get_current_fiscal_period(db, country_code)
        if not period:
            return None
        return {
            "id": period.id,
            "country_code": period.country_code,
            "label": f"{period.period_year}-{period.period_month:02d}",
            "status": period.status,
            "is_locked": period.is_locked,
            "period_start": period.period_start.isoformat(),
            "period_end": period.period_end.isoformat(),
        }
    finally:
        cleanup()


@router.post("/periods/close", summary="Close a fiscal period")
def close_fiscal_period(
    body: ClosePeriodBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = close_period(
        db,
        period_id=body.period_id,
        closed_by=_admin.get("id"),
        notes=body.notes,
        transfer_to_retained_earnings=body.transfer_to_retained_earnings,
    )
    audit_log(
        db=db,
        action=AuditAction.PERIOD_CLOSED,
        user_id=_admin.get("id"),
        username=_admin.get("username"),
        user_role=_admin.get("role"),
        resource_type="fiscal_period",
        resource_id=body.period_id,
        details=result,
    )
    return result


@router.get("/periods", summary="List fiscal periods")
def list_fiscal_periods(
    country_code: Optional[str] = Query(None, max_length=3),
    status: Optional[str] = Query(None),
    limit: int = Query(24, ge=1, le=120),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        periods = list_periods(db, country_code=country_code, status=status, limit=limit)
        return [
            {
                "id": p.id,
                "country_code": p.country_code,
                "label": f"{p.period_year}-{p.period_month:02d}",
                "status": p.status,
                "is_locked": p.is_locked,
                "period_start": p.period_start.isoformat(),
                "period_end": p.period_end.isoformat(),
                "closed_at": p.closed_at.isoformat() if p.closed_at else None,
            }
            for p in periods
        ]
    finally:
        cleanup()


# ── Journal Entry Reversal ──────────────────────────────────────────────────


class ReversalBody(BaseModel):
    entry_id: int
    reason: str


@router.post("/journal-entries/reverse", summary="Reverse a journal entry")
def reverse_entry(
    body: ReversalBody,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    result = reverse_journal_entry(
        db,
        original_entry_id=body.entry_id,
        reason=body.reason,
        user_id=_admin.get("id"),
    )
    audit_log(
        db=db,
        action=AuditAction.JOURNAL_ENTRY_CREATED,
        user_id=_admin.get("id"),
        username=_admin.get("username"),
        user_role=_admin.get("role"),
        resource_type="journal_entry_reversal",
        resource_id=result["reversal_entry_id"],
        details=result,
    )
    return result


# ── Cash Flow Forecast ──────────────────────────────────────────────────────


@router.post("/cash-flow-forecast", summary="Generate cash flow forecast")
def cash_flow_forecast(
    days: int = Query(90, ge=1, le=365),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        result = generate_cash_forecast(db, days=days, currency=currency, country_code=country_code)
        audit_log(
            db=db,
            action=AuditAction.CASH_FORECAST_GENERATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="cash_flow_forecast",
            details={"days": days, "currency": currency, "country_code": country_code},
        )
        return result
    finally:
        cleanup()


# ── AR / AP Sub-Ledgers ──────────────────────────────────────────────────────


@router.get("/ar", summary="AR sub-ledger (customer receivables)")
def get_ar(
    customer_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return controller_get_ar_summary(db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
    finally:
        cleanup()


class ARInvoiceBody(BaseModel):
    customer_id: int
    amount: float
    order_id: Optional[int] = None
    invoice_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/ar-ledger/invoice", summary="Post AR invoice")
def post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_invoice(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()


class ARPaymentBody(BaseModel):
    customer_id: int
    amount: float
    invoice_id: Optional[int] = None
    order_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/ar-ledger/payment", summary="Post AR payment")
def post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ar_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()


@router.get("/ap", summary="AP Sub-ledger alias (Accounts Payable)")
def get_ap_alias(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    finally:
        cleanup()


@router.get("/ap-ledger", summary="AP Sub-ledger (Accounts Payable)")
def get_ap(
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
):
    cleanup = _with_rls(country_code, db)
    try:
        return controller_get_ap_summary(db, supplier_id=supplier_id, status=status, country_code=country_code, limit=limit)
    finally:
        cleanup()


class APPayableBody(BaseModel):
    supplier_id: int
    amount: float
    order_id: Optional[int] = None
    settlement_id: Optional[int] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/ap-ledger/payable", summary="Post AP payable")
def post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()


class APPaymentBody(BaseModel):
    supplier_id: int
    amount: float
    settlement_id: Optional[int] = None
    description: Optional[str] = None
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/ap-ledger/payment", summary="Post AP payment")
def post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin)):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()

