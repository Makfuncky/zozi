"""Employee finance router — consolidated from 11 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from rbac.dependencies import require_admin, require_feature
from infrastructure.database.database import get_db


router = APIRouter(prefix="/api/v1/employee/finance", tags=["employee", "finance"])


# === From accounting.py ===
"""Accounting Router — General Ledger API and Financial Report endpoints."""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.finance import ports as finance_ports
from domains.finance.services.ledger.general_ledger_service import (
    reverse_journal_entry,
    get_current_fiscal_period,
    get_or_create_fiscal_period,
    list_periods,
)
from domains.logistics.ports import get_logistics_partner_by_user_id


class ReportPeriod(BaseModel):
    period_start: datetime
    period_end: datetime
    currency: str = "OMR"
    persist: bool = False
    country_code: Optional[str] = None


def _with_rls(country_code: Optional[str], db: Session):
    """Set RLS context if country_code is provided. Returns cleanup function."""
    return set_rls_context_service(db, country_code)


@router.post("/seed", summary="Seed chart of accounts (idempotent)")
def seed_chart_of_accounts(
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    return finance_ports.accounting_controller.seed_chart_of_accounts(
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
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.list_accounts(db)
    finally:
        cleanup()


@router.get("/accounts/{code}", summary="Get account by code")
def get_account(
    code: str,
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.get_account(db, code)
    finally:
        cleanup()


@router.post("/journal-entries", summary="Create a journal entry")
def create_journal_entry(
    body: finance_ports.accounting_controller.JournalEntryBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.write")),
):
    return finance_ports.accounting_controller.create_journal_entry(db, body, current_user)


@router.get("/journal-entries", summary="List journal entries")
def list_journal_entries(
    reference_type: Optional[str] = Query(None, max_length=40),
    reference_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.list_journal_entries(
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
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.get_journal_entry(db, entry_id)
    finally:
        cleanup()


@router.get("/balances/{account_code}", summary="Get account balance")
def get_balance(
    account_code: str,
    currency: str = Query("OMR", max_length=10),
    country_code: str = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.get_account_balance(db, account_code, currency)
    finally:
        cleanup()


@router.get("/trial-balance", summary="Get trial balance")
def trial_balance(
    as_of_date: Optional[date] = Query(None),
    currency: str = Query("OMR", max_length=10),
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db),
    _user=Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.accounting_controller.get_trial_balance(
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
    _rf_gate: None = Depends(require_feature("finance.reporting.generate")),
):
    cleanup = _with_rls(body.country_code, db)
    try:
        svc = finance_ports.FinancialReportingService(db)
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
    _rf_gate: None = Depends(require_feature("finance.reporting.generate")),
):
    cleanup = _with_rls(country_code, db)
    try:
        svc = finance_ports.FinancialReportingService(db)
        result = svc.generate_balance_sheet(as_of_date, currency, persist=persist, country_code=country_code)
        audit_log(
            db=db,
            action=AuditAction.FINANCIAL_REPORT_GENERATED,
            user_id=_admin.get("id"),
            username=_admin.get("username"),
            user_role=_admin.get("role"),
            resource_type="balance_sheet",
            details={"as_of_date": (as_of_date or datetime.now(timezone.utc)).isoformat(), "currency": currency, "country_code": country_code},
        )
        return result
    finally:
        cleanup()


@router.post("/reports/cash-flow", summary="Generate Cash Flow Statement")
def cash_flow(
    body: ReportPeriod,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.reporting.generate")),
):
    cleanup = _with_rls(body.country_code, db)
    try:
        svc = finance_ports.FinancialReportingService(db)
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
    _rf_gate: None = Depends(require_feature("finance.reporting.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        svc = finance_ports.FinancialReportingService(db)
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
    _rf_gate: None = Depends(require_feature("finance.period.manage")),
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
    _rf_gate: None = Depends(require_feature("finance.period.manage")),
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
    _rf_gate: None = Depends(require_feature("finance.period.manage")),
):
    result = finance_ports.close_period(
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
    _rf_gate: None = Depends(require_feature("finance.period.manage")),
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
    _rf_gate: None = Depends(require_feature("finance.ledger.reverse")),
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
    _rf_gate: None = Depends(require_feature("finance.treasury.forecast")),
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
    _rf_gate: None = Depends(require_feature("finance.subledger.read")),
):
    cleanup = _with_rls(country_code, db)
    try:
        return finance_ports.controller_get_ar_summary(db, customer_id=customer_id, status=status, country_code=country_code, limit=limit)
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
def post_ar_invoice_route(body: ARInvoiceBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.subledger.post"))
):
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
def post_ar_payment_route(body: ARPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.subledger.post"))
):
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
    _rf_gate: None = Depends(require_feature("finance.subledger.read")),
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
    _rf_gate: None = Depends(require_feature("finance.subledger.read")),
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
def post_ap_payable_route(body: APPayableBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.subledger.post"))
):
    cleanup = _with_rls(body.country_code, db)
    try:
        return finance_ports.controller_post_ap_payable(db, **body.model_dump(), admin_user=_admin)
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
def post_ap_payment_route(body: APPaymentBody, db: Session = Depends(get_db), _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.subledger.post"))
):
    cleanup = _with_rls(body.country_code, db)
    try:
        return controller_post_ap_payment(db, **body.model_dump(), admin_user=_admin)
    finally:
        cleanup()


# === From cash_management.py ===
"""
Cash Management Router — financial dashboard, ledger, settlements, payouts, and reconciliation.

Provides endpoints for:
  - Admin: Full financial dashboard, ledger view, settlements, bank reconciliation, payouts
  - Supplier: Earnings summary, settlement history, transaction ledger
  - Logistics Partner: Delivery fee summary, COD tracking, settlement history
"""
from typing import Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

import domains.finance.services.treasury.cash_management_controller as ctrl
from infrastructure.security.dependencies import require_admin
from infrastructure.utils.auth import require_permission
from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
    BadgeBillingOut,
    BankTransactionCreate,
    BankTransactionImportItem,
    BankTransactionOut,
    BankTransactionResolutionIn,
    FinanceBankConnectionTestOut,
    FinanceBankSettingsOut,
    FinanceBankSettingsUpdate,
    FinancialSummaryOut,
    LedgerEntryOut,
    LogisticsCODRemittanceReceiptOut,
    LogisticsFinancialSummaryOut,
    LogisticsSettlementOut,
    ReconciliationSummaryOut,
    RefundLedgerOut,
    SupplierFinancialSummaryOut,
    SupplierSettlementOut,
    VATRemittanceCreate,
    VATRemittanceOut,
)
from rbac import get_current_user


# ── Pydantic request bodies ──────────────────────────────────────────────────

class FlagRequest(BaseModel):
    reason: str


class CodRemittanceRequest(BaseModel):
    amount: float


class BadgeBillingPaymentRequest(BaseModel):
    payment_method: str
    transaction_ref: Optional[str] = None
    notes: Optional[str] = None


class PayoutProcessRequest(BaseModel):
    settlement_ids: list[int] = []


class ReceiptReviewRequest(BaseModel):
    note: Optional[str] = None


# ══════════════════════════════════════════════════════════════════════════════
# ADMIN ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/admin/summary",
    response_model=FinancialSummaryOut,
    summary="Financial dashboard summary",
)
def admin_financial_summary(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_financial_summary(db)


@router.get(
    "/admin/reconciliation-summary",
    response_model=ReconciliationSummaryOut,
    summary="Bank reconciliation workload summary",
)
def admin_reconciliation_summary(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_reconciliation_summary(db)


@router.get("/admin/ledger", response_model=list[LedgerEntryOut])
def admin_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    order_id: Optional[int] = Query(None),
    supplier_id: Optional[int] = Query(None),
    settlement_status: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    category_slug: Optional[str] = Query(None),
    badge_level: Optional[str] = Query(None),
    calculation_method: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.ledger.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_ledger_entries(
        db, skip=skip, limit=limit,
        order_id=order_id, supplier_id=supplier_id,
        settlement_status=settlement_status, payment_method=payment_method,
        category_slug=category_slug, badge_level=badge_level, calculation_method=calculation_method,
    )


@router.get("/admin/badge-billings", response_model=list[BadgeBillingOut])
def admin_list_badge_billings(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    badge_level: Optional[str] = Query(None),
    charge_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_badge_billing_records(
        db,
        skip=skip,
        limit=limit,
        supplier_id=supplier_id,
        status=status,
        badge_level=badge_level,
        charge_type=charge_type,
    )


@router.post("/admin/badge-billings/{billing_id}/record-payment", response_model=BadgeBillingOut)
def admin_record_badge_billing_payment(
    billing_id: int,
    body: BadgeBillingPaymentRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.commission.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_badge_billing_payment(
        billing_id=billing_id,
        payment_method=body.payment_method,
        current_admin=current_admin,
        db=db,
        transaction_ref=body.transaction_ref,
        notes=body.notes,
    )
    commit_db(db)
    return result


@router.get("/admin/supplier-settlements", response_model=list[SupplierSettlementOut])
def admin_list_supplier_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_supplier_settlements(db, skip=skip, limit=limit, supplier_id=supplier_id, status=status)


@router.get("/admin/logistics-settlements", response_model=list[LogisticsSettlementOut])
def admin_list_logistics_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    partner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.payout.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_logistics_settlements(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


@router.get("/admin/bank-transactions", response_model=list[BankTransactionOut])
def admin_list_bank_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    reconciled: Optional[bool] = Query(None),
    flagged: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_bank_transactions(
        db, skip=skip, limit=limit,
        source=source, category=category,
        reconciled=reconciled, flagged=flagged,
    )


@router.get("/admin/refunds", response_model=list[RefundLedgerOut])
def admin_list_refunds(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_refunds(db, skip=skip, limit=limit, status=status)


@router.get("/admin/vat-remittances", response_model=list[VATRemittanceOut])
def admin_list_vat_remittances(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_vat_remittance_records(db, skip=skip, limit=limit)


@router.get("/admin/bank-settings", response_model=FinanceBankSettingsOut)
def admin_get_bank_settings(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_get_finance_bank_settings(db)


@router.get("/admin/transfer-providers")
def admin_list_transfer_providers(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_transfer_providers(db)


@router.post("/admin/bank-settings/test-connection", response_model=FinanceBankConnectionTestOut)
def admin_test_bank_settings_connection(
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_test_finance_bank_connection(db)


@router.put("/admin/bank-settings", response_model=FinanceBankSettingsOut)
def admin_upsert_bank_settings(
    body: FinanceBankSettingsUpdate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_upsert_finance_bank_settings(body.model_dump(), current_admin, db)
    commit_db(db)
    return result


@router.post("/admin/vat-remittances", response_model=VATRemittanceOut, status_code=201)
def admin_record_vat_remittance(
    body: VATRemittanceCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_vat_remittance(body.model_dump(), current_admin, db)
    commit_db(db)
    return result


@router.post("/admin/bank-transactions", response_model=BankTransactionOut, status_code=201)
def admin_create_bank_transaction(
    data: BankTransactionCreate,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_create_bank_transaction(data.model_dump(), db)
    commit_db(db)
    return result


@router.post("/admin/bank-transactions/import")
def admin_import_bank_transactions(
    items: list[BankTransactionImportItem],
    auto_reconcile: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_import_bank_transactions(
        [item.model_dump() for item in items],
        current_admin,
        db,
        auto_reconcile=auto_reconcile,
    )
    commit_db(db)
    return result


@router.post("/admin/bank-transactions/{txn_id}/reconcile", response_model=BankTransactionOut)
def admin_reconcile_transaction(
    txn_id: int,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reconcile_transaction(txn_id, current_admin, db)
    commit_db(db)
    return result


@router.post("/admin/bank-transactions/{txn_id}/flag", response_model=BankTransactionOut)
def admin_flag_transaction(
    txn_id: int,
    body: FlagRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_flag_transaction(txn_id, body.reason, db)
    commit_db(db)
    return result


@router.post("/admin/bank-transactions/{txn_id}/resolve", response_model=BankTransactionOut)
def admin_resolve_transaction(
    txn_id: int,
    body: BankTransactionResolutionIn,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_resolve_transaction_exception(txn_id, body.model_dump(), current_admin, db)
    commit_db(db)
    return result


@router.post("/admin/bank-transactions/auto-reconcile")
def admin_auto_reconcile_transactions(
    limit: int = Query(100, ge=1, le=500),
    source: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.bank.read")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_auto_reconcile_transactions(
        current_admin,
        db,
        limit=limit,
        source=source,
        category=category,
    )
    commit_db(db)
    return result


@router.post("/admin/payouts/supplier/process")
def admin_trigger_supplier_payouts(
    body: Optional[PayoutProcessRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.payout.write")),
):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_supplier_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    commit_db(db)
    return {"processed": len(results), "payouts": results}


@router.post("/admin/payouts/logistics/process")
def admin_trigger_logistics_payouts(
    body: Optional[PayoutProcessRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.payout.write")),
):
    require_permission("payouts.verify", current_admin)
    results = ctrl.admin_trigger_logistics_payouts(db, settlement_ids=(body.settlement_ids if body else None))
    commit_db(db)
    return {"processed": len(results), "payouts": results}


@router.post("/admin/payouts/{kind}/dispatch")
def admin_dispatch_payouts(
    kind: str,
    provider: Optional[str] = Query(None),
    dry_run: bool = Query(True),
    background: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.payout.write")),
):
    require_permission("payouts.verify", current_admin)
    if background:
        return ctrl.admin_queue_dispatch_transfer_batch(
            kind,
            current_admin,
            provider=provider,
            dry_run=dry_run,
        )

    result = ctrl.admin_dispatch_transfer_batch(
        kind,
        current_admin,
        db,
        provider=provider,
        dry_run=dry_run,
    )
    commit_db(db)
    return result


@router.post("/admin/cod-remittance/{settlement_id}")
def admin_record_cod_remittance(
    settlement_id: int,
    body: CodRemittanceRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.manage")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_record_cod_remittance(settlement_id, body.amount, current_admin, db)
    commit_db(db)
    return {"status": "ok", "settlement_id": result.id, "cod_remittance_status": result.cod_remittance_status}


@router.get("/admin/cod-remittance-receipts", response_model=list[LogisticsCODRemittanceReceiptOut])
def admin_list_cod_remittance_receipts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    partner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.manage")),
):
    require_permission("payouts.verify", current_admin)
    return ctrl.admin_list_cod_remittance_receipts(db, skip=skip, limit=limit, partner_id=partner_id, status=status)


@router.post("/admin/cod-remittance-receipts/{receipt_id}/verify", response_model=LogisticsCODRemittanceReceiptOut)
def admin_verify_cod_remittance_receipt(
    receipt_id: int,
    body: Optional[ReceiptReviewRequest] = Body(default=None),
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.manage")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_verify_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note if body else None)
    commit_db(db)
    return result


@router.post("/admin/cod-remittance-receipts/{receipt_id}/reject", response_model=LogisticsCODRemittanceReceiptOut)
def admin_reject_cod_remittance_receipt(
    receipt_id: int,
    body: ReceiptReviewRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("finance.treasury.manage")),
):
    require_permission("payouts.verify", current_admin)
    result = ctrl.admin_reject_cod_remittance_receipt(receipt_id, current_admin, db, note=body.note or "")
    commit_db(db)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# SUPPLIER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/supplier/summary", response_model=SupplierFinancialSummaryOut)
def supplier_financial_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return {"error": "Supplier access required"}, 403
    return ctrl.supplier_get_financial_summary(current_user["id"], db)


@router.get("/supplier/settlements", response_model=list[SupplierSettlementOut])
def supplier_list_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_settlements(current_user["id"], db, skip=skip, limit=limit, status=status)


@router.get("/supplier/ledger", response_model=list[LedgerEntryOut])
def supplier_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    if current_user.get("role") not in ("supplier", "admin"):
        return []
    return ctrl.supplier_list_ledger_entries(current_user["id"], db, skip=skip, limit=limit)


# ══════════════════════════════════════════════════════════════════════════════
# LOGISTICS PARTNER ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/logistics/summary", response_model=LogisticsFinancialSummaryOut)
def logistics_financial_summary(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    partner = get_logistics_partner_by_user_id(db, current_user["id"])
    if not partner:
        return {"error": "Logistics partner not found"}, 404
    return ctrl.logistics_get_financial_summary(partner.id, db)


@router.get("/logistics/settlements", response_model=list[LogisticsSettlementOut])
def logistics_list_settlements(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    partner = get_logistics_partner_by_user_id(db, current_user["id"])
    if not partner:
        return []
    return ctrl.logistics_list_settlements(partner.id, db, skip=skip, limit=limit, status=status)


@router.get("/logistics/ledger", response_model=list[LedgerEntryOut])
def logistics_list_ledger(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    partner = get_logistics_partner_by_user_id(db, current_user["id"])
    if not partner:
        return []
    return ctrl.logistics_list_ledger_entries(partner.id, db, skip=skip, limit=limit)



# === From expenses.py ===
"""Expense Claims API"""


# === From expense_controller.py ===
"""Expense router.

Thin delegating router for ``controllers.finance.expense_controller`` (covers expense,
financial, payroll, treasury and contractor-milestones surfaces).

NOTE: the referenced controller module does not yet exist; this router owns its own
empty ``APIRouter`` so the app boots. Implement
``controllers.finance.expense_controller`` and replace the import once ready.
"""
from fastapi import APIRouter

expense_router = APIRouter(prefix="/api/v1/employee/finance/expense", tags=["employee", "finance", "expense-stub"])


# === From invoices.py ===
"""
Invoices Router — supply chain invoice management.
All business logic in controllers/invoice_controller.py.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session

import domains.finance.services.ledger.invoice_controller as ctrl
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from infrastructure.utils.invoice_html import generate_invoice_html, generate_invoice_pdf_bytes


@expense_router.get("/")
def list_invoices(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    order_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.read")),
):
    """List invoices — filtered by role (supplier sees own, admin sees all)."""
    return ctrl.list_invoices(current_user, db, page=page, page_size=page_size, status=status, order_id=order_id)


@expense_router.get("/overview")
def invoice_overview(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.read")),
):
    """Admin overview — totals and recent invoices."""
    if current_user.get("role") not in ("admin", "sub_admin", "moderator"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Admin access required")
    return ctrl.get_invoice_overview(db)


@expense_router.get("/{invoice_id}/html", response_class=HTMLResponse)
def get_invoice_html(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.read")),
):
    """Render invoice as printable HTML (browser print-to-PDF)."""
    inv_data = ctrl.get_invoice(invoice_id, current_user, db)
    return HTMLResponse(content=generate_invoice_html(inv_data))


@expense_router.get("/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.read")),
):
    """Render invoice as downloadable PDF."""
    inv_data = ctrl.get_invoice(invoice_id, current_user, db)
    pdf_bytes = generate_invoice_pdf_bytes(inv_data)
    filename = f"{inv_data['invoice_number']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@expense_router.get("/{invoice_id}")
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.read")),
):
    return ctrl.get_invoice(invoice_id, current_user, db)


@expense_router.post("/", status_code=201)
def create_invoice(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.create")),
):
    """Create an invoice from an existing order."""
    return ctrl.create_invoice_from_order(data, current_user, db)


@expense_router.put("/{invoice_id}/status")
def update_status(
    invoice_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("finance.invoice.create")),
):
    """Advance invoice status through supply chain stages."""
    return ctrl.update_invoice_status(invoice_id, data, current_user, db)


# === From finance_automation.py ===
"""finance automation router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@expense_router.get("/finance_automation/health")
def health(    _rf_gate: None = Depends(require_feature("finance.audit.read"))):
    """Liveness probe for this router."""
    return {"status": "ok", "router": "finance_automation", "prefix": "/api/v1/accounting"}


# === From finance_package.py ===
"""
Finance Domain — payroll, treasury, expense routing, contractor milestones.

Legacy hand-written router (thin HTTP layer). All business logic and DB access
live in the finance/treasury/hr services; this module only adapts HTTP requests
to those services.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.audit.ports import AuditAction, audit_log
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.finance.services.treasury.cash_management_service import list_contractor_milestones
from domains.finance.services.ledger.general_ledger_service import (
    ExpenseRoutingEngine,
    get_expense_router,
)
from domains.hr.ports import PayrollEngine

logger = logging.getLogger(__name__)


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


@expense_router.post("/payroll/process")
def process_payroll(
    request: PayrollProcessRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.payroll.manage")),
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


@expense_router.get("/financial/cash-flow")
def get_cash_flow(
    days: int = 30,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.audit.read")),
):
    service = finance_ports.FinancialReportingService(db)
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


@expense_router.get("/financial/profitability")
def get_profitability(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.audit.read")),
):
    service = finance_ports.FinancialReportingService(db)
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


@expense_router.post("/expense/route")
def route_claim(employee_id: int, amount: float, category: str, description: str,
                db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    router = get_expense_router(db)
    return router.route_expense_claim(
        employee_id=employee_id,
        amount=Decimal(str(amount)),
        category=category,
        description=description
    )


@expense_router.get("/expense/deadline")
def get_deadline(employee_id: int, submission_date: str, priority: str = "normal",
                 db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    router = get_expense_router(db)
    dt = datetime.fromisoformat(submission_date)
    return {"deadline": router.calculate_reimbursement_deadline(dt, priority).isoformat()}


@expense_router.get("/expense/chain/{employee_id}")
def get_chain(employee_id: int, amount: float, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.ledger.write"))
):
    router = get_expense_router(db)
    return {"approval_chain": router.get_approval_chain(employee_id, Decimal(str(amount)))}


@expense_router.get("/contractor-milestones")
def list_contractor_milestones_route(db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.subledger.read"))
):
    """Return contractor payment/delivery milestones."""
    return list_contractor_milestones(db)


# === From treasury.py ===
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.audit.ports import AuditAction, audit_log


@expense_router.get("/metrics")
def treasury_metrics(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    result = get_treasury_metrics(db)
    audit_log(
        db=db,
        action=AuditAction.TRIAL_BALANCE_VIEWED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="treasury_metrics",
    )
    return result


@expense_router.get("/cash-position")
def cash_position(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    result = get_cash_position(db)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="cash_position",
    )
    return result


@expense_router.get("/vat-liability")
def vat_liability(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    result = get_vat_liability(db, country_code)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="vat_liability",
        details={"country_code": country_code},
    )
    return result


@expense_router.get("/supplier-payables")
def supplier_payables(
    country_code: str = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("finance.treasury.read")),
):
    result = get_supplier_payables(db, country_code)
    audit_log(
        db=db,
        action=AuditAction.FINANCIAL_REPORT_GENERATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="supplier_payables",
        details={"country_code": country_code},
    )
    return result
