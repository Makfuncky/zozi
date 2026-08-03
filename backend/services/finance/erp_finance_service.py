"""ERP-level finance services: AR/AP, bank reconciliation matching, budgets.

All postings go through the canonical immutable ledger
(`general_ledger_service.create_journal_entry`) so balances and the audit trail
stay consistent.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from data.models import (
    Customer, Vendor, APBill, ARInvoice, BankStatementLine, BankReconciliation,
    JournalEntry, JournalEntryLine, Account, AccountBalance, FiscalPeriod,
    Budget, FinanceAuditLog, BankMappingRule,
)
from data.schemas import JournalEntryCreate, JournalLineInput
from services import general_ledger_service as gl
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def _audit(db: Session, action: str, entity_id: int, country_code, detail: dict, actor_id=None) -> None:
    try:
        db.add(FinanceAuditLog(
            action=action, entity_type="finance", entity_id=entity_id,
            actor_id=actor_id, country_code=country_code, detail=detail,
        ))
        db.commit()
    except Exception as e:
        logger.warning("finance audit failed: %s", e)


# ── AR (Receivables) ──────────────────────────────────────────────────────────


def create_ar_invoice(
    db: Session, *, customer_id: int, invoice_number: str, invoice_date: datetime,
    due_date: Optional[datetime], account_code: str, amount: Decimal,
    tax_amount: Decimal = Decimal("0"), description: str = "", country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> ARInvoice:
    inv = ARInvoice(
        customer_id=customer_id, invoice_number=invoice_number, invoice_date=invoice_date,
        due_date=due_date, account_code=account_code, amount=amount, tax_amount=tax_amount,
        description=description, country_code=country_code, created_by=created_by, status="issued",
    )
    db.add(inv)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=invoice_date, reference_type="ar_invoice", reference_id=inv.id,
        description=f"AR invoice {invoice_number} to customer {customer_id}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=account_code, side="debit", amount=amount,
                             description=f"Receivable {invoice_number}", entity_type="ar_invoice", entity_id=inv.id),
            JournalLineInput(account_code="4010", side="credit", amount=amount,
                             description=f"Revenue {invoice_number}", entity_type="ar_invoice", entity_id=inv.id),
        ],
    ), user_id=created_by)
    inv.linked_journal_entry_id = entry.id
    db.commit()
    db.refresh(inv)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ar_invoice", "invoice": invoice_number}, created_by)
    return inv


def receive_ar_payment(
    db: Session, *, invoice_id: int, amount: Decimal, payment_date: datetime,
    cash_account_code: str = "1010", country_code: Optional[str] = None, created_by: Optional[int] = None,
) -> ARInvoice:
    inv = db.query(ARInvoice).filter(ARInvoice.id == invoice_id).first()
    if not inv:
        raise ValueError("AR invoice not found")
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=payment_date, reference_type="ar_receipt", reference_id=invoice_id,
        description=f"Receipt for AR invoice {inv.invoice_number}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=cash_account_code, side="debit", amount=amount,
                             description="Cash receipt", entity_type="ar_invoice", entity_id=invoice_id),
            JournalLineInput(account_code=inv.account_code, side="credit", amount=amount,
                             description="Receivable cleared", entity_type="ar_invoice", entity_id=invoice_id),
        ],
    ), user_id=created_by)
    inv.paid_journal_entry_id = entry.id
    inv.status = "paid"
    db.commit()
    db.refresh(inv)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ar_receipt", "invoice": inv.invoice_number}, created_by)
    return inv


def ar_aging(db: Session, as_of: date, country_code: Optional[str] = None) -> dict:
    q = db.query(ARInvoice).filter(ARInvoice.status.in_(["issued", "partially_paid"]))
    if country_code:
        q = q.filter((ARInvoice.country_code == country_code) | (ARInvoice.country_code.is_(None)))
    buckets = {"current": Decimal("0"), "b0_30": Decimal("0"), "b31_60": Decimal("0"),
               "b61_90": Decimal("0"), "b90_plus": Decimal("0")}
    rows = []
    for inv in q.all():
        due = inv.due_date.date() if inv.due_date else inv.invoice_date.date()
        days = (as_of - due).days
        unpaid = inv.amount
        if days <= 0:
            key = "current"
        elif days <= 30:
            key = "b0_30"
        elif days <= 60:
            key = "b31_60"
        elif days <= 90:
            key = "b61_90"
        else:
            key = "b90_plus"
        buckets[key] += unpaid
        rows.append({"id": inv.id, "customer_id": inv.customer_id, "invoice_number": inv.invoice_number,
                     "amount": float(unpaid), "due_date": due.isoformat(), "days_overdue": max(days, 0)})
    return {"as_of": as_of.isoformat(), "buckets": {k: float(v) for k, v in buckets.items()},
            "total": float(sum(buckets.values())), "invoices": rows}


# ── AP (Payables) ─────────────────────────────────────────────────────────────


def create_ap_bill(
    db: Session, *, vendor_id: int, bill_number: str, bill_date: datetime,
    due_date: Optional[datetime], account_code: str, amount: Decimal,
    tax_amount: Decimal = Decimal("0"), description: str = "", country_code: Optional[str] = None,
    created_by: Optional[int] = None,
) -> APBill:
    bill = APBill(
        vendor_id=vendor_id, bill_number=bill_number, bill_date=bill_date, due_date=due_date,
        account_code=account_code, amount=amount, tax_amount=tax_amount, description=description,
        country_code=country_code, created_by=created_by, status="received",
    )
    db.add(bill)
    db.flush()
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=bill_date, reference_type="ap_bill", reference_id=bill.id,
        description=f"AP bill {bill_number} from vendor {vendor_id}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code=account_code, side="debit", amount=amount,
                             description=f"Expense {bill_number}", entity_type="ap_bill", entity_id=bill.id),
            JournalLineInput(account_code="2010", side="credit", amount=amount,
                             description=f"Payable {bill_number}", entity_type="ap_bill", entity_id=bill.id),
        ],
    ), user_id=created_by)
    bill.linked_journal_entry_id = entry.id
    db.commit()
    db.refresh(bill)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ap_bill", "bill": bill_number}, created_by)
    return bill


def pay_ap_bill(
    db: Session, *, bill_id: int, amount: Decimal, payment_date: datetime,
    cash_account_code: str = "1010", country_code: Optional[str] = None, created_by: Optional[int] = None,
) -> APBill:
    bill = db.query(APBill).filter(APBill.id == bill_id).first()
    if not bill:
        raise ValueError("AP bill not found")
    entry = gl.create_journal_entry(db, JournalEntryCreate(
        entry_date=payment_date, reference_type="ap_payment", reference_id=bill_id,
        description=f"Payment for AP bill {bill.bill_number}",
        currency="OMR", country_code=country_code,
        lines=[
            JournalLineInput(account_code="2010", side="debit", amount=amount,
                             description="Payable cleared", entity_type="ap_bill", entity_id=bill_id),
            JournalLineInput(account_code=cash_account_code, side="credit", amount=amount,
                             description="Cash payment", entity_type="ap_bill", entity_id=bill_id),
        ],
    ), user_id=created_by)
    bill.paid_journal_entry_id = entry.id
    bill.status = "paid"
    db.commit()
    db.refresh(bill)
    _audit(db, "journal_post", entry.id, country_code, {"kind": "ap_payment", "bill": bill.bill_number}, created_by)
    return bill


def ap_aging(db: Session, as_of: date, country_code: Optional[str] = None) -> dict:
    q = db.query(APBill).filter(APBill.status.in_(["received", "approved"]))
    if country_code:
        q = q.filter((APBill.country_code == country_code) | (APBill.country_code.is_(None)))
    buckets = {"current": Decimal("0"), "b0_30": Decimal("0"), "b31_60": Decimal("0"),
               "b61_90": Decimal("0"), "b90_plus": Decimal("0")}
    rows = []
    for bill in q.all():
        due = bill.due_date.date() if bill.due_date else bill.bill_date.date()
        days = (as_of - due).days
        unpaid = bill.amount
        if days <= 0:
            key = "current"
        elif days <= 30:
            key = "b0_30"
        elif days <= 60:
            key = "b31_60"
        elif days <= 90:
            key = "b61_90"
        else:
            key = "b90_plus"
        buckets[key] += unpaid
        rows.append({"id": bill.id, "vendor_id": bill.vendor_id, "bill_number": bill.bill_number,
                     "amount": float(unpaid), "due_date": due.isoformat(), "days_overdue": max(days, 0)})
    return {"as_of": as_of.isoformat(), "buckets": {k: float(v) for k, v in buckets.items()},
            "total": float(sum(buckets.values())), "bills": rows}


# ── Bank Reconciliation ───────────────────────────────────────────────────────


def suggest_matches(db: Session, line: BankStatementLine) -> list[dict]:
    """Find candidate journal-entry lines matching a statement line by amount ± date."""
    amt = abs(line.amount)
    lo = (line.txn_date or _utcnow()) 
    candidates = (
        db.query(JournalEntryLine, JournalEntry)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .filter(
            func.abs(JournalEntryLine.amount) == float(amt),
            JournalEntryLine.country_code == line.country_code if line.country_code else True,
        )
        .order_by(func.abs(func.julianday(JournalEntry.entry_date) - func.julianday(lo)).asc())
        .limit(5)
        .all()
    )
    out = []
    for jl, je in candidates:
        out.append({"journal_entry_id": je.id, "reference_number": je.reference_number,
                    "entry_date": je.entry_date.isoformat() if je.entry_date else None,
                    "account_code": jl.account_code if hasattr(jl, "account_code") else None,
                    "amount": float(jl.amount), "side": jl.side})
    return out


def match_statement_line(
    db: Session, *, line_id: int, journal_entry_id: int, country_code: Optional[str] = None,
    matched_by: Optional[int] = None,
) -> BankReconciliation:
    line = db.query(BankStatementLine).filter(BankStatementLine.id == line_id).first()
    if not line:
        raise ValueError("statement line not found")
    rec = db.query(BankReconciliation).filter(BankReconciliation.statement_line_id == line_id).first()
    if not rec:
        rec = BankReconciliation(statement_line_id=line_id)
        db.add(rec)
    rec.journal_entry_id = journal_entry_id
    rec.matched_amount = line.amount
    rec.status = "matched"
    rec.matched_by = matched_by
    rec.country_code = country_code or line.country_code
    rec.matched_at = _utcnow()
    line.status = "reconciled"
    db.commit()
    db.refresh(rec)
    _audit(db, "reconciliation", line_id, rec.country_code, {"journal_entry_id": journal_entry_id}, matched_by)
    return rec


def auto_match_import(db: Session, import_id: int, country_code: Optional[str] = None,
                      matched_by: Optional[int] = None) -> dict:
    lines = db.query(BankStatementLine).filter(
        BankStatementLine.import_id == import_id,
        BankStatementLine.status.in_(["unmapped", "mapped"]),
    ).all()
    matched = 0
    for line in lines:
        sugg = suggest_matches(db, line)
        if sugg:
            match_statement_line(db, line_id=line.id, journal_entry_id=sugg[0]["journal_entry_id"],
                                 country_code=country_code, matched_by=matched_by)
            matched += 1
    return {"import_id": import_id, "total": len(lines), "matched": matched}


# ── Budgets ───────────────────────────────────────────────────────────────────


def set_budget(db: Session, *, account_code: str, fiscal_period_id: int, amount: Decimal,
               currency: str = "OMR", country_code: Optional[str] = None, notes: str = "",
               created_by: Optional[int] = None) -> Budget:
    existing = db.query(Budget).filter(
        Budget.account_code == account_code, Budget.fiscal_period_id == fiscal_period_id,
        (Budget.country_code == country_code) | (Budget.country_code.is_(None)),
    ).first()
    if existing:
        existing.amount = amount
        existing.currency = currency
        existing.notes = notes
        existing.updated_at = _utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    b = Budget(account_code=account_code, fiscal_period_id=fiscal_period_id, amount=amount,
              currency=currency, country_code=country_code, notes=notes, created_by=created_by)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def budget_variance(db: Session, fiscal_period_id: int, country_code: Optional[str] = None) -> dict:
    period = db.query(FiscalPeriod).filter(FiscalPeriod.id == fiscal_period_id).first()
    budgets = db.query(Budget).filter(Budget.fiscal_period_id == fiscal_period_id)
    if country_code:
        budgets = budgets.filter((Budget.country_code == country_code) | (Budget.country_code.is_(None)))
    rows = []
    total_budget = Decimal("0")
    total_actual = Decimal("0")
    for b in budgets.all():
        acct = db.query(Account).filter(Account.code == b.account_code).first()
        actual = Decimal("0")
        if acct:
            bal = db.query(AccountBalance).filter(
                AccountBalance.account_id == acct.id, AccountBalance.currency == b.currency,
            ).first()
            if bal:
                actual = bal.balance if acct.normal_side == "debit" else -bal.balance
        total_budget += b.amount
        total_actual += actual
        rows.append({
            "account_code": b.account_code, "account_name": acct.name if acct else None,
            "budget": float(b.amount), "actual": float(actual),
            "variance": float(b.amount - actual),
        })
    return {
        "fiscal_period_id": fiscal_period_id,
        "period_label": f"{period.period_year}-{period.period_month:02d}" if period else None,
        "country_code": country_code,
        "total_budget": float(total_budget), "total_actual": float(total_actual),
        "total_variance": float(total_budget - total_actual), "rows": rows,
    }

