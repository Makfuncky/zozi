"""Service methods for ERP finance read operations.

Covers ERP transactions plus the GL/AR/AP/reconciliation/budget/audit
read queries used by the finance_erp router (LC1: routers stay thin).
"""
from __future__ import annotations
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from data.models import (
    Account,
    AccountGroup,
    APBill,
    ARInvoice,
    BankStatementImport,
    BankStatementLine,
    Budget,
    ErpTransaction,
    FinanceAuditLog,
    JournalEntry,
    JournalEntryLine,
)


# ── ERP transactions (pre-existing) ────────────────────────────────────────


def get_erp_transactions(
    db: Session,
    status: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[ErpTransaction]:
    """Get ERP transactions with optional status filter."""
    q = db.query(ErpTransaction)
    if status:
        q = q.filter(ErpTransaction.status == status)
    return q.order_by(ErpTransaction.created_at.desc()).offset(skip).limit(limit).all()


def get_erp_transaction_by_id(db: Session, transaction_id: int) -> ErpTransaction | None:
    """Get an ERP transaction by ID."""
    return db.query(ErpTransaction).filter(ErpTransaction.id == transaction_id).first()


def get_erp_dashboard_metrics(db: Session) -> dict:
    """Get ERP dashboard metrics."""
    from sqlalchemy import func as sqlfunc
    total_txns = db.query(sqlfunc.count(ErpTransaction.id)).scalar() or 0
    pending = (
        db.query(sqlfunc.count(ErpTransaction.id))
        .filter(ErpTransaction.status == "pending")
        .scalar()
        or 0
    )
    total_value = (
        db.query(sqlfunc.sum(ErpTransaction.amount))
        .filter(ErpTransaction.status == "completed")
        .scalar()
        or 0
    )
    return {
        "total_transactions": total_txns,
        "pending_count": pending,
        "total_value": float(total_value),
    }


def get_erp_reconciliation_report(db: Session, date_from: str, date_to: str) -> list[dict]:
    """Get ERP reconciliation report for a date range."""
    results = (
        db.query(
            ErpTransaction.date,
            ErpTransaction.type,
            ErpTransaction.amount,
            ErpTransaction.status,
        )
        .filter(
            ErpTransaction.date >= datetime.fromisoformat(date_from),
            ErpTransaction.date <= datetime.fromisoformat(date_to),
        )
        .all()
    )
    return [
        {"date": r[0], "type": r[1], "amount": r[2], "status": r[3]} for r in results
    ]


# ── Chart of accounts ──────────────────────────────────────────────────────


def get_account_by_code(db: Session, code: str) -> Account | None:
    """Get a GL account by its code."""
    return db.query(Account).filter(Account.code == code).first()


def get_account_group_by_code(db: Session, code: str) -> AccountGroup | None:
    """Get an account group by its code."""
    return db.query(AccountGroup).filter(AccountGroup.code == code).first()


def list_accounts_paged(
    db: Session,
    group_code: Optional[str] = None,
    search: Optional[str] = None,
    active_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[Account]]:
    """List accounts with optional group/search/active filters (offset pagination)."""
    q = db.query(Account)
    if group_code:
        q = q.join(AccountGroup, Account.group_id == AccountGroup.id).filter(
            AccountGroup.code == group_code
        )
    if search:
        q = q.filter(
            Account.name.ilike(f"%{search}%") | Account.code.ilike(f"%{search}%")
        )
    if active_only:
        q = q.filter(Account.is_active == True)  # noqa: E712
    total = q.count()
    rows = q.order_by(Account.code).offset(offset).limit(limit).all()
    return total, rows


# ── AR / AP ────────────────────────────────────────────────────────────────


def list_ar_invoices(
    db: Session,
    country_code: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[int, list[ARInvoice]]:
    """List AR invoices (newest first, optional country filter)."""
    q = db.query(ARInvoice)
    if country_code:
        q = q.filter(
            (ARInvoice.country_code == country_code) | (ARInvoice.country_code.is_(None))
        )
    total = q.count()
    rows = q.order_by(ARInvoice.id.desc()).offset(offset).limit(limit).all()
    return total, rows


def list_ap_bills(
    db: Session,
    country_code: Optional[str] = None,
    limit: int = 200,
    offset: int = 0,
) -> tuple[int, list[APBill]]:
    """List AP bills (newest first, optional country filter)."""
    q = db.query(APBill)
    if country_code:
        q = q.filter(
            (APBill.country_code == country_code) | (APBill.country_code.is_(None))
        )
    total = q.count()
    rows = q.order_by(APBill.id.desc()).offset(offset).limit(limit).all()
    return total, rows


# ── GL payments register / journal browser ────────────────────────────────


def list_payments_register(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    account_code: Optional[str] = None,
    country_code: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list]:
    """GL payments register: journal lines joined with entries + accounts."""
    q = (
        db.query(JournalEntryLine, JournalEntry, Account.code, Account.name)
        .join(JournalEntry, JournalEntryLine.entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
    )
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
    return total, rows


def browse_journal_entries(
    db: Session,
    reference_type: Optional[str] = None,
    country_code: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[JournalEntry]]:
    """Browse journal entries with optional filters (offset pagination)."""
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
    return total, entries


def get_journal_line_rows(db: Session, entry_ids: list[int]) -> list:
    """Bulk-load journal lines with account codes for a set of entries (avoids N+1)."""
    if not entry_ids:
        return []
    return (
        db.query(JournalEntryLine, Account.code, Account.name)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .filter(JournalEntryLine.entry_id.in_(entry_ids))
        .all()
    )


# ── Bank reconciliation ────────────────────────────────────────────────────


def list_statement_lines(
    db: Session,
    import_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[BankStatementLine]:
    """List statement lines for an import (offset pagination)."""
    return (
        db.query(BankStatementLine)
        .filter(BankStatementLine.import_id == import_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_statement_imports(
    db: Session,
    country_code: Optional[str] = None,
    limit: int = 50,
) -> list[BankStatementImport]:
    """List bank statement imports (newest first, optional country filter)."""
    q = db.query(BankStatementImport)
    if country_code:
        q = q.filter(BankStatementImport.country_code == country_code)
    return q.order_by(BankStatementImport.id.desc()).limit(limit).all()


def get_lines_for_import(db: Session, import_id: int) -> list[BankStatementLine]:
    """Get all statement lines for an import (used for match counts)."""
    return (
        db.query(BankStatementLine)
        .filter(BankStatementLine.import_id == import_id)
        .all()
    )


# ── Budgets ────────────────────────────────────────────────────────────────


def list_budgets(
    db: Session,
    fiscal_period_id: Optional[int] = None,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[int, list[Budget]]:
    """List budgets with optional fiscal-period/country filters."""
    q = db.query(Budget)
    if fiscal_period_id:
        q = q.filter(Budget.fiscal_period_id == fiscal_period_id)
    if country_code:
        q = q.filter(
            (Budget.country_code == country_code) | (Budget.country_code.is_(None))
        )
    total = q.count()
    rows = q.offset(skip).limit(limit).all()
    return total, rows


# ── Finance audit log ──────────────────────────────────────────────────────


def list_finance_audit_log(
    db: Session,
    start: Optional[date] = None,
    end: Optional[date] = None,
    action: Optional[str] = None,
    actor_id: Optional[int] = None,
    country_code: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, list[FinanceAuditLog]]:
    """List finance audit log entries with optional filters."""
    q = db.query(FinanceAuditLog)
    if action:
        q = q.filter(FinanceAuditLog.action == action)
    if actor_id:
        q = q.filter(FinanceAuditLog.actor_id == actor_id)
    if country_code:
        q = q.filter(
            (FinanceAuditLog.country_code == country_code)
            | (FinanceAuditLog.country_code.is_(None))
        )
    if start:
        q = q.filter(FinanceAuditLog.created_at >= datetime(start.year, start.month, start.day))
    if end:
        q = q.filter(FinanceAuditLog.created_at <= datetime(end.year, end.month, end.day, 23, 59, 59))
    total = q.count()
    rows = q.order_by(FinanceAuditLog.created_at.desc()).offset(offset).limit(limit).all()
    return total, rows
