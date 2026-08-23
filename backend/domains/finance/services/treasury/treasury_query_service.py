from infrastructure.utils.datetime_utils import utcnow
"""Treasury query/service functions for EOSB, Payroll, and Double-Entry Accounting.

Relocated from the mis-housed ``routers/treasury_api.py`` so that raw SQL and
write operations live in the service layer (architectural W1 fix).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from domains.finance.models.finance import CashFlowForecast
from domains.finance.models.finance import JournalEntry
from domains.finance.models.finance import JournalEntryLine
from domains.finance.models.finance import TreasuryAccount
from domains.finance.models.finance import TreasuryTransaction
from domains.hr.ports import Employee
from infrastructure.utils.audit import AuditAction, audit_log
from domains.comms.services.utility.write_helpers import add_and_flush
from domains.comms.services.utility.write_helpers import commit_and_refresh
from domains.comms.services.utility.write_helpers import commit_only
import structlog
logger = structlog.get_logger(__name__)


def get_treasury_account(db: Session, slug: str) -> TreasuryAccount:
    """Get or create a treasury account by slug."""
    account = db.query(TreasuryAccount).filter(TreasuryAccount.slug == slug).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Treasury account '{slug}' not found")
    return account


def create_treasury_transaction(
    db: Session,
    account_id: int,
    transaction_type: str,
    amount: Decimal,
    currency: str = "USD",
    reference: Optional[str] = None,
    description: Optional[str] = None,
    audit_user_id: Optional[int] = None,
    audit_username: Optional[str] = None,
    audit_user_role: Optional[str] = None,
) -> TreasuryTransaction:
    """Create a treasury transaction."""
    transaction = TreasuryTransaction(
        account_id=account_id,
        transaction_type=transaction_type,
        amount=amount,
        currency=currency,
        reference=reference,
        description=description,
        posted_at=utcnow(),
    )
    add_and_flush(db, transaction)
    commit_and_refresh(db, transaction)
    if audit_user_id:
        audit_log(
            db=db,
            action=AuditAction.TREASURY_TRANSACTION_CREATED,
            user_id=audit_user_id,
            username=audit_username,
            user_role=audit_user_role,
            resource_type="treasury_transaction",
            resource_id=transaction.id,
            details={
                "account_id": account_id,
                "transaction_type": transaction_type,
                "amount": float(amount),
                "currency": currency,
                "reference": reference,
                "description": description,
            },
        )
    return transaction


def create_journal_entry(
    db: Session,
    reference_number: str,
    description: Optional[str],
    source: Optional[str],
    country_code: Optional[str],
    lines: List[Dict[str, Any]],
    audit_user_id: Optional[int] = None,
    audit_username: Optional[str] = None,
    audit_user_role: Optional[str] = None,
) -> JournalEntry:
    """Create a double-entry journal entry with validation."""
    total_debits = Decimal("0")
    total_credits = Decimal("0")

    for line in lines:
        amount = Decimal(str(line.get("amount", 0)))
        side = line.get("side", "").lower()
        if side == "debit":
            total_debits += amount
        elif side == "credit":
            total_credits += amount
        else:
            raise HTTPException(status_code=400, detail=f"Invalid side '{side}' for line")

    if total_debits != total_credits:
        raise HTTPException(
            status_code=400,
            detail=f"Debits ({total_debits}) must equal credits ({total_credits})",
        )

    entry = JournalEntry(
        reference_number=reference_number,
        description=description,
        source=source,
        country_code=country_code,
        entry_date=utcnow(),
    )
    add_and_flush(db, entry)
    commit_only(db)

    for line in lines:
        jel = JournalEntryLine(
            entry_id=entry.id,
            account_id=line["account_id"],
            amount=Decimal(str(line["amount"])),
            side=line["side"].lower(),
            description=line.get("description"),
        )
        add_and_flush(db, jel)

    commit_and_refresh(db, entry)

    if audit_user_id:
        audit_log(
            db=db,
            action=AuditAction.JOURNAL_ENTRY_CREATED,
            user_id=audit_user_id,
            username=audit_username,
            user_role=audit_user_role,
            resource_type="journal_entry",
            resource_id=entry.id,
            details={
                "reference_number": reference_number,
                "source": source,
                "country_code": country_code,
                "line_count": len(lines),
                "total_debits": float(total_debits),
                "total_credits": float(total_credits),
            },
        )
    return entry


def get_payroll_summary(country_code: str, db: Session) -> dict:
    """Get payroll summary for a country."""
    result = db.execute(text("""
        SELECT
            COUNT(*) as employee_count,
            COALESCE(SUM(e.salary), 0) as total_gross,
            COALESCE(SUM(e.salary) * 0.1, 0) as total_tax,
            COALESCE(SUM(e.salary) * 0.9, 0) as total_net
        FROM employees e
        WHERE e.country_code = :country AND e.employment_status = 'active'
    """), {"country": country_code.upper()}).fetchone()

    return {
        "country_code": country_code,
        "employee_count": result[0],
        "total_gross": float(result[1]),
        "total_tax": float(result[2]),
        "total_net": float(result[3]),
    }


def get_treasury_metrics(db: Session) -> dict:
    """Get overall treasury metrics using actual models."""
    total_balance = db.query(func.coalesce(func.sum(TreasuryAccount.balance), 0)).scalar() or Decimal("0")
    total_transactions = db.query(TreasuryTransaction).count()

    return {
        "total_balance": float(total_balance),
        "total_entries": total_transactions,
    }


def get_account_balance(account_id: int, db: Session) -> Decimal:
    """Calculate account balance from journal entries."""
    result = db.execute(text("""
        SELECT
            COALESCE(SUM(CASE WHEN side = 'credit' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN side = 'debit' THEN amount ELSE 0 END), 0) as balance
        FROM journal_entry_lines jel
        WHERE jel.account_id = :account_id
    """), {"account_id": account_id}).scalar()
    return result or Decimal("0")


def get_trial_balance(db: Session) -> List[Dict[str, Any]]:
    """Generate trial balance for all accounts."""
    results = db.execute(text("""
        SELECT
            a.code,
            a.name,
            ag.code as group_code,
            COALESCE(SUM(CASE WHEN jel.side = 'credit' THEN jel.amount ELSE 0 END), 0) as credits,
            COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE 0 END), 0) as debits,
            COALESCE(SUM(CASE WHEN jel.side = 'credit' THEN jel.amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN jel.side = 'debit' THEN jel.amount ELSE 0 END), 0) as balance
        FROM accounts a
        LEFT JOIN account_groups ag ON a.group_id = ag.id
        LEFT JOIN journal_entry_lines jel ON a.id = jel.account_id
        GROUP BY a.id, a.code, a.name, ag.code
        ORDER BY a.code
    """)).fetchall()

    return [
        {
            "account_code": r[0],
            "account_name": r[1],
            "group_code": r[2],
            "credits": float(r[3]),
            "debits": float(r[4]),
            "balance": float(r[5]),
        }
        for r in results
    ]


def get_cash_position(db: Session) -> Dict[str, Any]:
    """Get current cash position by treasury account."""
    results = db.execute(text("""
        SELECT
            ta.slug,
            ta.name,
            COALESCE(SUM(CASE WHEN tt.transaction_type = 'credit' THEN tt.amount ELSE 0 END), 0) as credits,
            COALESCE(SUM(CASE WHEN tt.transaction_type = 'debit' THEN tt.amount ELSE 0 END), 0) as debits
        FROM treasury_accounts ta
        LEFT JOIN treasury_transactions tt ON ta.id = tt.account_id
        WHERE ta.is_active = true
        GROUP BY ta.id, ta.slug, ta.name
    """)).fetchall()

    total_free = Decimal("0")
    accounts = []
    for r in results:
        balance = Decimal(str(r[2] or 0)) - Decimal(str(r[3] or 0))
        accounts.append({
            "account_slug": r[0],
            "account_name": r[1],
            "balance": float(balance),
        })
        if r[0] in ["cash_operating", "cash_gateway_settlement"]:
            total_free += balance

    return {
        "total_free_cash": float(total_free),
        "accounts": accounts,
    }


def get_vat_liability(db: Session, country_code: Optional[str] = None) -> Dict[str, Any]:
    """Calculate VAT liability for a country or all countries."""
    query = text("""
        SELECT
            je.country_code,
            COALESCE(SUM(CASE WHEN a.code = '2040' THEN jel.amount ELSE 0 END), 0) as vat_collected,
            COALESCE(SUM(CASE WHEN a.code = '2050' THEN jel.amount ELSE 0 END), 0) as vat_paid
        FROM journal_entries je
        JOIN journal_entry_lines jel ON je.id = jel.entry_id
        JOIN accounts a ON jel.account_id = a.id
        WHERE a.code IN ('2040', '2050')
    """)
    params = {}

    if country_code:
        query = text(str(query) + " AND je.country_code = :country_code")
        params["country_code"] = country_code

    query = text(str(query) + " GROUP BY je.country_code")

    results = db.execute(query, params).fetchall()

    total_liability = Decimal("0")
    by_country = []
    for r in results:
        liability = Decimal(str(r[1] or 0)) - Decimal(str(r[2] or 0))
        total_liability += liability
        by_country.append({
            "country_code": r[0],
            "vat_collected": float(r[1] or 0),
            "vat_paid": float(r[2] or 0),
            "net_liability": float(liability),
        })

    return {
        "total_vat_liability": float(total_liability),
        "by_country": by_country,
    }


def get_supplier_payables(db: Session, country_code: Optional[str] = None) -> Dict[str, Any]:
    """Calculate total supplier payables."""
    query = text("""
        SELECT
            je.country_code,
            COALESCE(SUM(jel.amount), 0) as total_payable
        FROM journal_entries je
        JOIN journal_entry_lines jel ON je.id = jel.entry_id
        JOIN accounts a ON jel.account_id = a.id
        WHERE a.code = '2010' AND jel.side = 'credit'
    """)
    params = {}

    if country_code:
        query = text(str(query) + " AND je.country_code = :country_code")
        params["country_code"] = country_code

    query = text(str(query) + " GROUP BY je.country_code")

    results = db.execute(query, params).fetchall()

    return [
        {
            "country_code": r[0],
            "total_payable": float(r[1]),
        }
        for r in results
    ]


def get_treasury_ledger(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """List general-ledger journal entries within an optional date range."""
    query = db.query(
        JournalEntry.id,
        JournalEntry.entry_date,
        JournalEntry.reference_number,
        JournalEntry.description,
        JournalEntry.source,
        JournalEntry.reconciled,
    )
    if start_date:
        query = query.filter(JournalEntry.entry_date >= start_date)
    if end_date:
        query = query.filter(JournalEntry.entry_date <= end_date)
    rows = query.order_by(JournalEntry.entry_date.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "entry_date": r.entry_date.isoformat() if r.entry_date else None,
            "reference_number": r.reference_number,
            "description": r.description,
            "source": r.source,
            "reconciled": r.reconciled,
        }
        for r in rows
    ]


def get_payment_transactions(
    db: Session,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List treasury payment transactions within an optional date range."""
    query = db.query(TreasuryTransaction)
    if start_date:
        query = query.filter(TreasuryTransaction.posted_at >= start_date)
    if end_date:
        query = query.filter(TreasuryTransaction.posted_at <= end_date)
    rows = query.order_by(TreasuryTransaction.posted_at.desc()).all()
    return [
        {
            "id": t.id,
            "account_id": t.account_id,
            "transaction_type": t.transaction_type,
            "amount": float(t.amount),
            "currency": t.currency,
            "reference": t.reference,
            "posted_at": t.posted_at.isoformat() if t.posted_at else None,
        }
        for t in rows
    ]


def get_cash_flow_forecast(db: Session) -> List[Dict[str, Any]]:
    """List cash-flow forecast records."""
    rows = (
        db.query(CashFlowForecast)
        .order_by(CashFlowForecast.forecast_date.desc())
        .all()
    )
    return [
        {
            "id": f.id,
            "forecast_date": f.forecast_date.isoformat() if f.forecast_date else None,
            "period_start_at": f.period_start_at.isoformat() if f.period_start_at else None,
            "period_end_at": f.period_end_at.isoformat() if f.period_end_at else None,
            "net_cash_flow": float(f.net_cash_flow) if f.net_cash_flow is not None else 0.0,
            "opening_balance": float(f.opening_balance) if f.opening_balance is not None else 0.0,
            "closing_balance": float(f.closing_balance) if f.closing_balance is not None else 0.0,
        }
        for f in rows
    ]


def calculate_eosb(employee_id: int, db: Session) -> dict:
    """Calculate the End-of-Service Benefit (EOSB) for an employee.

    Placeholder implementation that returns the employee's basic compensation
    inputs. The full actuarial computation is owned by the payroll engine; this
    entry point is retained on the query service so the controller layer has a
    single import surface (CIR2).
    """
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail=f"Employee {employee_id} not found")

    base_salary = getattr(employee, "salary", Decimal("0")) or Decimal("0")
    return {
        "employee_id": employee_id,
        "base_salary": float(base_salary),
        "years_of_service": 0,
        "eosb_amount": 0.0,
        "currency": "USD",
    }
