"""ERP-level Finance router.

Exposes AR/AP, payments register, journal browser, bank reconciliation matching,
budgets/variance, finance audit log, COA edit, and automation triggers. All
endpoints enforce finance permission delegation via `require_finance_permission`.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from dependencies.auth import get_current_user
from controllers.admin_controller import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from models import (
    Account, JournalEntry, JournalEntryLine, ARInvoice, APBill, Customer, Vendor,
    BankStatementLine, BankReconciliation, Budget, FiscalPeriod, FinanceAuditLog,
    RecurringTemplate, AccountGroup,
)
from services import erp_finance_service as erp, finance_automation as fa, general_ledger_service as gl
from services.ocr_parser import parse_bill_text

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only
logger = logging.getLogger(__name__)
router = APIRouter()


def require_finance_permission(slug: str):
    from services import permission_service as permsvc

    def _dep(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.get("role") == "admin":
            return current_user
        if permsvc.check_user_permission(current_user.get("id"), slug, db,
                                         country_code=current_user.get("country_code")):
            return current_user
        raise HTTPException(status_code=403, detail=f"Requires permission: {slug}")
    return _dep


def _with_rls(country_code: Optional[str], db: Session):
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)

    def cleanup():
        if country_code:
            clear_rls_context()
    return cleanup


# ── Chart of Accounts (edit) ───────────────────────────────────────────────────


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    group_code: Optional[str] = None
    normal_side: Optional[str] = None
    currency: Optional[str] = None


@router.put("/accounts/{code}", summary="Edit a GL account")
def update_account(code: str, body: AccountUpdate, db: Session = Depends(get_db),
                   _admin=Depends(require_finance_permission("finance.coa"))):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")
    if body.name is not None:
        acct.name = body.name
    if body.normal_side is not None:
        acct.normal_side = body.normal_side
    if body.currency is not None:
        acct.currency = body.currency
    if body.group_code is not None:
        grp = db.query(AccountGroup).filter(AccountGroup.code == body.group_code).first()
        if not grp:
            raise HTTPException(404, f"Group '{body.group_code}' not found")
        acct.group_id = grp.id
    commit_only(db)
    return {"status": "updated", "code": code}


@router.get("/coa/search", summary="List accounts (paginated, filtered)")
def list_accounts_paged(
    group_code: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    active_only: bool = False,
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.coa")),
):
    q = db.query(Account)
    if group_code:
        from models import AccountGroup
        q = q.join(AccountGroup, Account.group_id == AccountGroup.id).filter(AccountGroup.code == group_code)
    if search:
        q = q.filter(Account.name.ilike(f"%{search}%") | Account.code.ilike(f"%{search}%"))
    if active_only:
        q = q.filter(Account.is_active == True)  # noqa: E712
    total = q.count()
    rows = q.order_by(Account.code).offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"id": a.id, "code": a.code, "name": a.name, "normal_side": a.normal_side,
         "currency": a.currency, "is_active": a.is_active, "country_code": a.country_code}
        for a in rows
    ]}


# ── AR / AP ────────────────────────────────────────────────────────────────────


class ARInvoiceCreate(BaseModel):
    customer_id: int
    invoice_number: str
    invoice_date: datetime
    due_date: Optional[datetime] = None
    account_code: str = "4010"
    amount: float
    tax_amount: float = 0
    description: str = ""
    country_code: Optional[str] = None


class ARReceipt(BaseModel):
    invoice_id: int
    amount: float
    payment_date: datetime
    cash_account_code: str = "1010"
    country_code: Optional[str] = None


@router.get("/ar/aging", summary="AR aging report")
def ar_aging(as_of: date = Query(date.today()), country_code: Optional[str] = Query(None, max_length=3),
             db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.ar"))):
    return erp.ar_aging(db, as_of, country_code)


@router.get("/ar/invoices", summary="List AR invoices")
def list_ar(db: Session = Depends(get_db), country_code: Optional[str] = Query(None, max_length=3),
            limit: int = Query(200, le=500), offset: int = Query(0, ge=0),
            _admin=Depends(require_finance_permission("finance.ar"))):
    q = db.query(ARInvoice)
    if country_code:
        q = q.filter((ARInvoice.country_code == country_code) | (ARInvoice.country_code.is_(None)))
    total = q.count()
    rows = q.order_by(ARInvoice.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"id": r.id, "customer_id": r.customer_id, "invoice_number": r.invoice_number,
         "amount": float(r.amount), "due_date": r.due_date.isoformat() if r.due_date else None,
         "status": r.status, "country_code": r.country_code}
        for r in rows
    ]}


@router.post("/ar/invoices", summary="Create AR invoice + post to GL")
def create_ar(body: ARInvoiceCreate, db: Session = Depends(get_db),
              _admin=Depends(require_finance_permission("finance.ar"))):
    inv = erp.create_ar_invoice(db, customer_id=body.customer_id, invoice_number=body.invoice_number,
                                invoice_date=body.invoice_date, due_date=body.due_date, account_code=body.account_code,
                                amount=Decimal(str(body.amount)), tax_amount=Decimal(str(body.tax_amount)),
                                description=body.description, country_code=body.country_code,
                                created_by=_admin.get("id"))
    return {"id": inv.id, "status": inv.status, "journal_entry_id": inv.linked_journal_entry_id}


@router.post("/ar/invoices/receipt", summary="Record AR receipt")
def ar_receipt(body: ARReceipt, db: Session = Depends(get_db),
               _admin=Depends(require_finance_permission("finance.ar"))):
    inv = erp.receive_ar_payment(db, invoice_id=body.invoice_id, amount=Decimal(str(body.amount)),
                                 payment_date=body.payment_date, cash_account_code=body.cash_account_code,
                                 country_code=body.country_code, created_by=_admin.get("id"))
    return {"id": inv.id, "status": inv.status}


class APBillCreate(BaseModel):
    vendor_id: int
    bill_number: str
    bill_date: datetime
    due_date: Optional[datetime] = None
    account_code: str = "5030"
    amount: float
    tax_amount: float = 0
    description: str = ""
    country_code: Optional[str] = None


class APPayment(BaseModel):
    bill_id: int
    amount: float
    payment_date: datetime
    cash_account_code: str = "1010"
    country_code: Optional[str] = None


@router.get("/ap/aging", summary="AP aging report")
def ap_aging(as_of: date = Query(date.today()), country_code: Optional[str] = Query(None, max_length=3),
             db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.ap"))):
    return erp.ap_aging(db, as_of, country_code)


@router.get("/ap/bills", summary="List AP bills")
def list_ap(db: Session = Depends(get_db), country_code: Optional[str] = Query(None, max_length=3),
            limit: int = Query(200, le=500), offset: int = Query(0, ge=0),
            _admin=Depends(require_finance_permission("finance.ap"))):
    q = db.query(APBill)
    if country_code:
        q = q.filter((APBill.country_code == country_code) | (APBill.country_code.is_(None)))
    total = q.count()
    rows = q.order_by(APBill.id.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"id": r.id, "vendor_id": r.vendor_id, "bill_number": r.bill_number,
         "amount": float(r.amount), "due_date": r.due_date.isoformat() if r.due_date else None,
         "status": r.status, "country_code": r.country_code}
        for r in rows
    ]}


@router.post("/ap/bills", summary="Create AP bill + post to GL")
def create_ap(body: APBillCreate, db: Session = Depends(get_db),
              _admin=Depends(require_finance_permission("finance.ap"))):
    bill = erp.create_ap_bill(db, vendor_id=body.vendor_id, bill_number=body.bill_number,
                              bill_date=body.bill_date, due_date=body.due_date, account_code=body.account_code,
                              amount=Decimal(str(body.amount)), tax_amount=Decimal(str(body.tax_amount)),
                              description=body.description, country_code=body.country_code,
                              created_by=_admin.get("id"))
    return {"id": bill.id, "status": bill.status, "journal_entry_id": bill.linked_journal_entry_id}


@router.post("/ap/bills/payment", summary="Record AP payment")
def ap_payment(body: APPayment, db: Session = Depends(get_db),
               _admin=Depends(require_finance_permission("finance.ap"))):
    bill = erp.pay_ap_bill(db, bill_id=body.bill_id, amount=Decimal(str(body.amount)),
                           payment_date=body.payment_date, cash_account_code=body.cash_account_code,
                           country_code=body.country_code, created_by=_admin.get("id"))
    return {"id": bill.id, "status": bill.status}


# ── Payments register (GL-level) ───────────────────────────────────────────────


@router.get("/payments/register", summary="GL payments register")
def payments_register(
    start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None),
    account_code: Optional[str] = Query(None), country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.payments")),
):
    q = db.query(JournalEntryLine, JournalEntry, Account.code, Account.name).join(
        JournalEntry, JournalEntryLine.entry_id == JournalEntry.id).join(
        Account, JournalEntryLine.account_id == Account.id)
    if account_code:
        q = q.filter(Account.code == account_code)
    if country_code:
        q = q.filter(JournalEntryLine.country_code == country_code)
    if start_date:
        q = q.filter(JournalEntry.entry_date >= datetime(start_date.year, start_date.month, start_date.day))
    if end_date:
        q = q.filter(JournalEntry.entry_date <= datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))
    total = q.count()
    rows = q.order_by(JournalEntry.entry_date.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"entry_id": je.id, "reference_number": je.reference_number, "entry_date": je.entry_date.isoformat(),
         "account_code": code, "account_name": name, "side": jl.side, "amount": float(jl.amount),
         "description": jl.description, "country_code": jl.country_code}
        for jl, je, code, name in rows
    ]}


# ── Journal browser ────────────────────────────────────────────────────────────


@router.get("/journal/browse", summary="Browse journal entries (filtered, paginated)")
def browse_journal(
    search: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None), end_date: Optional[date] = Query(None),
    account_code: Optional[str] = Query(None), reference_type: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.journals")),
):
    q = db.query(JournalEntry)
    if reference_type:
        q = q.filter(JournalEntry.reference_type == reference_type)
    if country_code:
        q = q.filter(JournalEntry.country_code == country_code)
    if start_date:
        q = q.filter(JournalEntry.entry_date >= datetime(start_date.year, start_date.month, start_date.day))
    if end_date:
        q = q.filter(JournalEntry.entry_date <= datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59))
    total = q.count()
    entries = q.order_by(JournalEntry.entry_date.desc()).offset(offset).limit(limit).all()
    # Bulk-load lines for the page (avoids N+1).
    ids = [e.id for e in entries]
    line_rows = (db.query(JournalEntryLine, Account.code, Account.name).join(
        Account, JournalEntryLine.account_id == Account.id).filter(
        JournalEntryLine.entry_id.in_(ids)).all()) if ids else []
    by_entry = {}
    for jl, code, name in line_rows:
        by_entry.setdefault(jl.entry_id, []).append(
            {"account_code": code, "account_name": name, "side": jl.side, "amount": float(jl.amount)})
    return {"total": total, "items": [
        {"id": e.id, "reference_number": e.reference_number, "entry_date": e.entry_date.isoformat(),
         "reference_type": e.reference_type, "description": e.description, "currency": e.currency,
         "country_code": e.country_code, "lines": by_entry.get(e.id, [])}
        for e in entries
    ]}


# ── Bank reconciliation ────────────────────────────────────────────────────────


@router.get("/reconciliation/{import_id}", summary="Statement lines + suggested matches")
def reconciliation_view(import_id: int, db: Session = Depends(get_db),
                        _admin=Depends(require_finance_permission("finance.reconciliation"))):
    lines = db.query(BankStatementLine).filter(BankStatementLine.import_id == import_id).all()
    out = []
    for ln in lines:
        sugg = erp.suggest_matches(db, ln)
        out.append({"id": ln.id, "txn_date": ln.txn_date.isoformat() if ln.txn_date else None,
                    "description": ln.description, "amount": float(ln.amount), "status": ln.status,
                    "mapped_account_code": ln.mapped_account_code, "suggestions": sugg})
    return {"import_id": import_id, "lines": out}


@router.post("/reconciliation/{import_id}/lines/{line_id}/match", summary="Match a statement line to a JE")
def match_line(import_id: int, line_id: int, body: dict, db: Session = Depends(get_db),
               _admin=Depends(require_finance_permission("finance.reconciliation"))):
    rec = erp.match_statement_line(db, line_id=line_id, journal_entry_id=body.get("journal_entry_id"),
                                   country_code=_admin.get("country_code"), matched_by=_admin.get("id"))
    return {"status": rec.status, "statement_line_id": rec.statement_line_id}


@router.post("/reconciliation/{import_id}/auto-match", summary="Auto-match all unmatched lines")
def auto_match(import_id: int, db: Session = Depends(get_db),
               _admin=Depends(require_finance_permission("finance.reconciliation"))):
    return erp.auto_match_import(db, import_id, country_code=_admin.get("country_code"),
                                 matched_by=_admin.get("id"))


@router.get("/reconciliation-summary", summary="Reconciliation status per import")
def reconciliation_status(country_code: Optional[str] = Query(None, max_length=3),
                          db: Session = Depends(get_db),
                          _admin=Depends(require_finance_permission("finance.reconciliation"))):
    from models import BankStatementImport
    imports = db.query(BankStatementImport)
    if country_code:
        imports = imports.filter(BankStatementImport.country_code == country_code)
    out = []
    for imp in imports.order_by(BankStatementImport.id.desc()).limit(50).all():
        lines = db.query(BankStatementLine).filter(BankStatementLine.import_id == imp.id).all()
        matched = sum(1 for l in lines if l.status == "reconciled")
        out.append({"import_id": imp.id, "bank_name": imp.bank_name, "total": len(lines),
                    "matched": matched, "status": imp.status})
    return {"imports": out}


# ── Budgets ────────────────────────────────────────────────────────────────────


class BudgetSet(BaseModel):
    account_code: str
    fiscal_period_id: int
    amount: float
    currency: str = "OMR"
    country_code: Optional[str] = None
    notes: str = ""


@router.get("/budgets", summary="List budgets")
def list_budgets(fiscal_period_id: Optional[int] = Query(None), country_code: Optional[str] = Query(None, max_length=3),
                 db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.budgets"))):
    q = db.query(Budget)
    if fiscal_period_id:
        q = q.filter(Budget.fiscal_period_id == fiscal_period_id)
    if country_code:
        q = q.filter((Budget.country_code == country_code) | (Budget.country_code.is_(None)))
    return {"items": [
        {"id": b.id, "account_code": b.account_code, "fiscal_period_id": b.fiscal_period_id,
         "amount": float(b.amount), "currency": b.currency, "country_code": b.country_code}
        for b in q.all()
    ]}


@router.post("/budgets", summary="Set/create budget")
def set_budget(body: BudgetSet, db: Session = Depends(get_db),
               _admin=Depends(require_finance_permission("finance.budgets"))):
    b = erp.set_budget(db, account_code=body.account_code, fiscal_period_id=body.fiscal_period_id,
                       amount=Decimal(str(body.amount)), currency=body.currency, country_code=body.country_code,
                       notes=body.notes, created_by=_admin.get("id"))
    return {"id": b.id}


@router.get("/budgets/variance", summary="Budget vs actual variance")
def budget_variance(fiscal_period_id: int, country_code: Optional[str] = Query(None, max_length=3),
                    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.budgets"))):
    return erp.budget_variance(db, fiscal_period_id, country_code)


# ── Finance audit log ──────────────────────────────────────────────────────────


@router.get("/audit", summary="Finance audit log")
def finance_audit(
    start: Optional[date] = Query(None), end: Optional[date] = Query(None),
    action: Optional[str] = Query(None), actor_id: Optional[int] = Query(None),
    country_code: Optional[str] = Query(None, max_length=3),
    limit: int = Query(100, le=500), offset: int = Query(0, ge=0),
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.audit")),
):
    q = db.query(FinanceAuditLog)
    if action:
        q = q.filter(FinanceAuditLog.action == action)
    if actor_id:
        q = q.filter(FinanceAuditLog.actor_id == actor_id)
    if country_code:
        q = q.filter((FinanceAuditLog.country_code == country_code) | (FinanceAuditLog.country_code.is_(None)))
    if start:
        q = q.filter(FinanceAuditLog.created_at >= datetime(start.year, start.month, start.day))
    if end:
        q = q.filter(FinanceAuditLog.created_at <= datetime(end.year, end.month, end.day, 23, 59, 59))
    total = q.count()
    rows = q.order_by(FinanceAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return {"total": total, "items": [
        {"id": a.id, "action": a.action, "actor_id": a.actor_id, "entity_type": a.entity_type,
         "entity_id": a.entity_id, "country_code": a.country_code,
         "created_at": a.created_at.isoformat() if a.created_at else None, "detail": a.detail}
        for a in rows
    ]}


# ── OCR scan upload + automations ──────────────────────────────────────────────


@router.post("/expenses/scan-upload", summary="Upload a bill image/text and parse (OCR) -> expense")
async def scan_upload(
    file: UploadFile = File(...),
    vendor_name: Optional[str] = None,
    amount: Optional[float] = None,
    expense_account_code: str = "5030",
    country_code: Optional[str] = None,
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.expenses.scan")),
):
    raw = (await file.read()).decode("utf-8", errors="ignore")
    parsed = parse_bill_text(raw, filename=file.filename)
    # Allow explicit overrides from form fields.
    vendor = vendor_name or parsed.get("vendor_name")
    amt = Decimal(str(amount)) if amount is not None else (parsed.get("amount") or Decimal("0"))
    scanned = fa.post_scanned_expense(
        db, employee_id=None, vendor_name=vendor or "Unknown",
        amount=amt, currency="OMR", expense_date=datetime.utcnow(),
        category="scanned", description=parsed.get("raw_text", "")[:500],
        image_url=None, ocr_raw_text=parsed.get("raw_text"),
        ocr_confidence=Decimal(str(parsed.get("confidence", 0))),
        expense_account_code=expense_account_code, country_code=country_code,
        reviewed_by=_admin.get("id"),
    )
    return {"id": scanned.id, "status": scanned.status, "parsed": parsed,
            "journal_entry_id": scanned.posted_journal_entry_id}


@router.post("/statements/import-csv", summary="Upload + parse a bank statement CSV")
async def import_csv(
    file: UploadFile = File(...),
    bank_name: Optional[str] = None,
    currency: str = "OMR",
    country_code: Optional[str] = Query(None, max_length=3),
    db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.upload")),
):
    raw = (await file.read()).decode("utf-8", errors="ignore")
    return fa.import_bank_statement_csv(db, raw_csv=raw, bank_name=bank_name, file_name=file.filename,
                                        currency=currency, country_code=country_code, imported_by=_admin.get("id"))


@router.post("/automation/run-daily", summary="Run daily automation (depreciation, accruals, orphans)")
def run_daily(as_of: Optional[date] = Query(None), country_code: Optional[str] = Query(None, max_length=3),
              db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.assets"))):
    return fa.run_daily_automation(db, as_of=as_of, country_code=country_code, run_by=_admin.get("id"))


class RecurringCreate(BaseModel):
    name: str
    frequency: str = "monthly"
    next_run_date: Optional[datetime] = None
    description: str = ""
    lines: list[dict]
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/recurring", summary="Create recurring entry template")
def create_recurring(body: RecurringCreate, db: Session = Depends(get_db),
                     _admin=Depends(require_finance_permission("finance.coa"))):
    tpl = RecurringTemplate(name=body.name, frequency=body.frequency, next_run_date=body.next_run_date,
                            description=body.description, lines=body.lines, currency=body.currency,
                            country_code=body.country_code, created_by=_admin.get("id"))
    add_and_flush(db, tpl)
    commit_and_refresh(db, tpl)
    return {"id": tpl.id}


@router.post("/recurring/{template_id}/trigger", summary="Trigger a recurring template now")
def trigger_recurring(template_id: int, db: Session = Depends(get_db),
                      _admin=Depends(require_finance_permission("finance.coa"))):
    return fa.trigger_recurring(db, template_id=template_id, run_by=_admin.get("id"))

