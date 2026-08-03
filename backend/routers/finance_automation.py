"""Finance Automation Router — OCR bills, bank mapping, depreciation, accruals, COA CRUD."""
from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.db import get_db
from data.controllers_admin_controller import require_admin
from data.dependencies_auth import get_current_user
from services import finance_automation as fa
from services import general_ledger_service as gl
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from data.models import Account, AccountGroup, AccountBalance, BankMappingRule, BankStatementLine

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, flush_only
logger = logging.getLogger(__name__)
router = APIRouter()


def require_finance_permission(slug: str):
    """Allow full admins OR users granted a specific finance permission (delegation)."""
    from data.controllers_admin_controller import require_admin
    from services import permission_service as permsvc

    def _dep(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        if current_user.get("role") == "admin":
            return current_user
        if permsvc.check_user_permission(current_user.get("id"), slug, db, country_code=current_user.get("country_code")):
            return current_user
        raise HTTPException(status_code=403, detail=f"Requires permission: {slug}")
    return _dep


class _AdminResp(BaseModel):
    pass


def _with_rls(country_code: Optional[str], db: Session):
    if country_code:
        get_country_or_404(country_code.upper(), db)
        set_rls_context({country_code.upper()}, is_restricted=True)

    def cleanup():
        if country_code:
            clear_rls_context()
    return cleanup


# ── Chart of Accounts CRUD ──────────────────────────────────────────────────


class AccountCreate(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    group_code: str = Field(..., max_length=10)
    normal_side: str
    currency: str = "OMR"
    country_code: Optional[str] = None


@router.post("/accounts", summary="Create a GL account (admin CRUD)")
def create_account(body: AccountCreate, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.coa"))):
    cleanup = _with_rls(body.country_code, db)
    try:
        if db.query(Account).filter(Account.code == body.code).first():
            raise HTTPException(409, f"Account '{body.code}' already exists")
        grp = db.query(AccountGroup).filter(AccountGroup.code == body.group_code).first()
        if not grp:
            raise HTTPException(404, f"Account group '{body.group_code}' not found")
        acct = Account(code=body.code, name=body.name, group_id=grp.id,
                       normal_side=body.normal_side, currency=body.currency,
                       country_code=body.country_code)
        add_and_flush(db, acct)
        flush_only(db)
        add_and_flush(db, AccountBalance(account_id=acct.id, currency=body.currency, balance=Decimal("0.00")))
        commit_and_refresh(db, acct)
        return gl.list_accounts(db)
    finally:
        cleanup()


@router.post("/accounts/{code}/deactivate", summary="Deactivate a GL account")
def deactivate_account(code: str, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.coa"))):
    acct = db.query(Account).filter(Account.code == code).first()
    if not acct:
        raise HTTPException(404, f"Account '{code}' not found")
    acct.is_active = False
    commit_only(db)
    return {"status": "deactivated", "code": code}


# ── Mapping rules ─────────────────────────────────────────────────────────────


class MappingRuleCreate(BaseModel):
    name: str
    match_pattern: str
    account_code: str
    normal_side: str
    country_code: Optional[str] = None
    description_contains: Optional[str] = None
    category: Optional[str] = None
    priority: int = 100


@router.post("/mapping-rules", summary="Create bank-statement -> GL mapping rule")
def create_rule(body: MappingRuleCreate, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.mapping"))):
    rule = fa.create_mapping_rule(
        db, name=body.name, match_pattern=body.match_pattern, account_code=body.account_code,
        normal_side=body.normal_side, country_code=body.country_code,
        description_contains=body.description_contains, category=body.category,
        priority=body.priority, created_by=_admin.get("id"),
    )
    return {"id": rule.id, "account_code": rule.account_code, "match_pattern": rule.match_pattern}


@router.get("/mapping-rules", summary="List mapping rules")
def list_rules(country_code: Optional[str] = Query(None, max_length=3), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.mapping"))):
    q = db.query(BankMappingRule)
    if country_code:
        q = q.filter((BankMappingRule.country_code == country_code) | (BankMappingRule.country_code.is_(None)))
    return [
        {"id": r.id, "name": r.name, "match_pattern": r.match_pattern,
         "account_code": r.account_code, "normal_side": r.normal_side, "category": r.category,
         "priority": r.priority, "is_active": r.is_active}
        for r in q.order_by(BankMappingRule.priority.asc()).offset(skip).limit(limit).all()
    ]


class StatementLineIn(BaseModel):
    description: str
    amount: float
    reference: Optional[str] = None
    txn_date: Optional[datetime] = None


class StatementImportBody(BaseModel):
    bank_name: Optional[str] = None
    file_name: Optional[str] = None
    currency: str = "OMR"
    country_code: Optional[str] = None
    lines: list[StatementLineIn]


@router.post("/statements/import", summary="Import bank statement lines and auto-map")
def import_statement(body: StatementImportBody, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.mapping"))):
    imp = fa.import_bank_statement(
        db, lines=[l.model_dump() for l in body.lines], bank_name=body.bank_name,
        file_name=body.file_name, currency=body.currency, country_code=body.country_code,
        imported_by=_admin.get("id"),
    )
    return {"import_id": imp.id, "total_lines": imp.total_lines,
            "matched_lines": imp.matched_lines, "unmatched_lines": imp.unmatched_lines}


@router.get("/statements/{import_id}/lines", summary="List statement lines for an import")
def statement_lines(import_id: int, skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.mapping"))):
    return [
        {"id": l.id, "description": l.description, "amount": float(l.amount),
         "mapped_account_code": l.mapped_account_code, "mapped_side": l.mapped_side,
         "status": l.status}
        for l in db.query(BankStatementLine).filter(BankStatementLine.import_id == import_id).offset(skip).limit(limit).all()
    ]


@router.post("/statements/{import_id}/post", summary="Post all mapped lines to GL")
def post_statement(import_id: int, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.bank.mapping"))):
    return fa.auto_post_mapped_lines(db, import_id, run_by=_admin.get("id"))


# ── OCR scanned expenses ─────────────────────────────────────────────────────


class ScannedExpenseBody(BaseModel):
    vendor_name: str
    amount: float
    employee_id: Optional[int] = None
    currency: str = "OMR"
    expense_date: Optional[datetime] = None
    tax_amount: float = 0
    category: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    ocr_raw_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    expense_account_code: str = "5030"
    country_code: Optional[str] = None


@router.post("/expenses/scan", summary="Scan a bill (OCR) and post as expense to GL")
def scan_expense(body: ScannedExpenseBody, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.expenses.scan"))):
    scanned = fa.post_scanned_expense(
        db, employee_id=body.employee_id, vendor_name=body.vendor_name,
        amount=Decimal(str(body.amount)), currency=body.currency,
        expense_date=body.expense_date, tax_amount=Decimal(str(body.tax_amount)),
        category=body.category, description=body.description, image_url=body.image_url,
        ocr_raw_text=body.ocr_raw_text, ocr_confidence=Decimal(str(body.ocr_confidence)) if body.ocr_confidence else None,
        expense_account_code=body.expense_account_code, country_code=body.country_code,
        reviewed_by=_admin.get("id"),
    )
    return {"id": scanned.id, "status": scanned.status,
            "journal_entry_id": scanned.posted_journal_entry_id}


@router.get("/expenses/scanned", summary="List scanned expenses")
def list_scanned(country_code: Optional[str] = Query(None, max_length=3), db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.expenses.scan"))):
    from data.models import ScannedExpense
    q = db.query(ScannedExpense)
    if country_code:
        q = q.filter(ScannedExpense.country_code == country_code)
    return [
        {"id": e.id, "vendor_name": e.vendor_name, "amount": float(e.amount),
         "status": e.status, "account_code": e.expense_account_code,
         "created_at": e.created_at.isoformat() if e.created_at else None}
        for e in q.order_by(ScannedExpense.id.desc()).limit(200).all()
    ]


# ── Fixed assets & depreciation ───────────────────────────────────────────────


class FixedAssetCreate(BaseModel):
    name: str
    category: Optional[str] = None
    purchase_date: datetime
    purchase_cost: float
    salvage_value: float = 0
    useful_life_months: int
    asset_code: Optional[str] = None
    asset_account_code: str = "1100"
    depreciation_account_code: str = "5070"
    accumulated_depr_account_code: str = "1190"
    country_code: Optional[str] = None


@router.post("/fixed-assets", summary="Register a fixed asset")
def create_asset(body: FixedAssetCreate, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.assets"))):
    from data.models import FixedAsset
    asset = FixedAsset(**body.model_dump(exclude_none=True), created_by=_admin.get("id"))
    add_and_flush(db, asset)
    commit_and_refresh(db, asset)
    return {"id": asset.id, "name": asset.name, "status": asset.status}


@router.get("/fixed-assets", summary="List fixed assets")
def list_assets(country_code: Optional[str] = Query(None, max_length=3), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.assets"))):
    from data.models import FixedAsset
    q = db.query(FixedAsset)
    if country_code:
        q = q.filter((FixedAsset.country_code == country_code) | (FixedAsset.country_code.is_(None)))
    return [
        {"id": a.id, "name": a.name, "category": a.category, "purchase_cost": float(a.purchase_cost),
         "salvage_value": float(a.salvage_value), "useful_life_months": a.useful_life_months,
         "accumulated_depreciation": float(a.accumulated_depreciation or 0),
         "status": a.status, "country_code": a.country_code}
        for a in q.order_by(FixedAsset.id.desc()).offset(skip).limit(limit).all()
    ]


@router.post("/fixed-assets/depreciate", summary="Run depreciation for all active assets")
def depreciate(as_of: Optional[date] = Query(None), country_code: Optional[str] = Query(None, max_length=3),
               db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.assets"))):
    return fa.run_depreciation(db, as_of=as_of, country_code=country_code, run_by=_admin.get("id"))


# ── Accruals ───────────────────────────────────────────────────────────────────


class AccrualCreate(BaseModel):
    accrual_type: str  # expense | revenue
    amount: float
    expense_account_code: str
    accrual_account_code: str
    accrual_date: datetime
    description: Optional[str] = None
    reversal_date: Optional[datetime] = None
    country_code: Optional[str] = None


@router.post("/accruals", summary="Create an accrual (and post to GL)")
def create_accrual(body: AccrualCreate, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.accruals"))):
    accrual = fa.create_accrual(
        db, accrual_type=body.accrual_type, amount=Decimal(str(body.amount)),
        expense_account_code=body.expense_account_code, accrual_account_code=body.accrual_account_code,
        accrual_date=body.accrual_date, description=body.description,
        reversal_date=body.reversal_date, country_code=body.country_code, created_by=_admin.get("id"),
    )
    return {"id": accrual.id, "status": accrual.status, "journal_entry_id": accrual.journal_entry_id}


@router.get("/accruals", summary="List accruals")
def list_accruals(country_code: Optional[str] = Query(None, max_length=3), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.accruals"))):
    from data.models import Accrual
    q = db.query(Accrual)
    if country_code:
        q = q.filter((Accrual.country_code == country_code) | (Accrual.country_code.is_(None)))
    return [
        {"id": a.id, "accrual_type": a.accrual_type, "amount": float(a.amount),
         "description": a.description, "status": a.status, "country_code": a.country_code}
        for a in q.order_by(Accrual.id.desc()).offset(skip).limit(limit).all()
    ]


@router.post("/accruals/{accrual_id}/reverse", summary="Reverse an open accrual")
def reverse_accrual(accrual_id: int, db: Session = Depends(get_db), _admin=Depends(require_finance_permission("finance.accruals"))):
    accrual = fa.reverse_accrual(db, accrual_id, run_by=_admin.get("id"))
    return {"id": accrual.id, "status": accrual.status, "reversal_entry_id": accrual.reversal_entry_id}
