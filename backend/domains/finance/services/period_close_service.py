"""Period Close Service — fiscal period management, year-end procedures.

Handles opening/closing accounting periods, transferring P&L balances
to retained earnings, and locking periods against further edits.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import (
    Account,
    AccountBalance,
    AccountGroup,
    FiscalPeriod,
    JournalEntry,
    JournalEntryLine,
)
from services.finance.general_ledger_service import create_journal_entry, get_account_by_code
from db.schemas import JournalEntryCreate, JournalLineInput
from utils.money import round_money

logger = logging.getLogger(__name__)


def get_or_create_fiscal_period(
    db: Session,
    country_code: str,
    year: int,
    month: int,
) -> FiscalPeriod:
    """Get existing period or create a new open one."""
    period = (
        db.query(FiscalPeriod)
        .filter(
            FiscalPeriod.country_code == country_code,
            FiscalPeriod.period_year == year,
            FiscalPeriod.period_month == month,
        )
        .first()
    )
    if period:
        return period

    from calendar import monthrange
    period_start = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    period_end = datetime(year, month, last_day, 23, 59, 59)

    period = FiscalPeriod(
        country_code=country_code,
        period_year=year,
        period_month=month,
        period_start=period_start,
        period_end=period_end,
        status="open",
    )
    db.add(period)
    db.commit()
    db.refresh(period)
    return period


def get_current_fiscal_period(
    db: Session,
    country_code: str,
) -> Optional[FiscalPeriod]:
    """Get the current open fiscal period for a country."""
    now = datetime.utcnow()
    return (
        db.query(FiscalPeriod)
        .filter(
            FiscalPeriod.country_code == country_code,
            FiscalPeriod.period_start <= now,
            FiscalPeriod.period_end >= now,
        )
        .first()
    )


def close_period(
    db: Session,
    period_id: int,
    closed_by: int,
    notes: Optional[str] = None,
    transfer_to_retained_earnings: bool = True,
) -> dict:
    """Close a fiscal period.

    1. Validates no entries are pending/un-posted
    2. Transfers P&L balances to Retained Earnings
    3. Locks the period against further edits
    """
    period = db.query(FiscalPeriod).filter(FiscalPeriod.id == period_id).first()
    if not period:
        raise ValueError(f"Period {period_id} not found")
    if period.status == "closed":
        raise ValueError(f"Period {period_id} is already closed")
    if period.is_locked:
        raise ValueError(f"Period {period_id} is locked")

    country = period.country_code

    # 1. Check for pending journal entries in period
    pending = db.query(JournalEntry).filter(
        JournalEntry.period_id == period_id,
        JournalEntry.is_deleted == False,
    ).count()

    if pending == 0:
        # Period might have unassigned entries — assign them
        db.query(JournalEntry).filter(
            JournalEntry.entry_date >= period.period_start,
            JournalEntry.entry_date <= period.period_end,
            JournalEntry.period_id.is_(None),
            JournalEntry.is_deleted == False,
        ).update({"period_id": period_id})
        db.commit()

    # 2. Transfer P&L to retained earnings if requested
    transfer_result = None
    if transfer_to_retained_earnings:
        transfer_result = _transfer_pnl_to_retained_earnings(
            db, country, period, closed_by
        )

    # 3. Lock the period
    period.status = "closed"
    period.is_locked = True
    period.closed_at = datetime.utcnow()
    period.closed_by = closed_by
    period.notes = notes
    db.commit()

    return {
        "period_id": period.id,
        "country_code": country,
        "period_label": f"{period.period_year}-{period.period_month:02d}",
        "status": "closed",
        "closed_at": period.closed_at.isoformat(),
        "transfer_to_retained_earnings": transfer_result,
    }


def _transfer_pnl_to_retained_earnings(
    db: Session,
    country_code: str,
    period: FiscalPeriod,
    user_id: int,
) -> dict:
    """Close P&L accounts by transferring net income to Retained Earnings."""
    # Aggregate revenue & expense balances for this period
    revenue_accounts = (
        db.query(Account)
        .join(AccountGroup)
        .filter(AccountGroup.account_type == "Revenue")
        .all()
    )
    expense_accounts = (
        db.query(Account)
        .join(AccountGroup)
        .filter(AccountGroup.account_type == "Expense")
        .all()
    )

    total_revenue = Decimal("0.00")
    revenue_lines = []
    for acct in revenue_accounts:
        bal = _get_period_balance(db, acct.id, period)
        if bal != 0:
            total_revenue += bal
            revenue_lines.append({
                "account_code": acct.code,
                "account_name": acct.name,
                "balance": float(bal),
            })

    total_expenses = Decimal("0.00")
    expense_lines = []
    for acct in expense_accounts:
        bal = _get_period_balance(db, acct.id, period)
        if bal != 0:
            total_expenses += bal
            expense_lines.append({
                "account_code": acct.code,
                "account_name": acct.name,
                "balance": float(bal),
            })

    net_income = round_money(total_revenue - total_expenses)

    if net_income == 0:
        return {"net_income": 0, "message": "No P&L balance to transfer"}

    # Create closing journal entry
    retained = get_account_by_code(db, "3010")
    if not retained:
        raise ValueError("Retained Earnings (3010) account not found — run seed/repair first")

    lines = []
    if net_income > 0:
        # Dr. Revenue accounts, Cr. Retained Earnings
        for acct in revenue_accounts:
            bal = _get_period_balance(db, acct.id, period)
            if bal != 0:
                lines.append(JournalLineInput(
                    account_code=acct.code,
                    side="debit",
                    amount=bal,
                    description=f"Period close transfer for {period.period_year}-{period.period_month:02d}",
                ))
        lines.append(JournalLineInput(
            account_code="3010",
            side="credit",
            amount=net_income,
            description=f"Net income transfer for {period.period_year}-{period.period_month:02d}",
        ))
    else:
        # Net loss: Dr. Retained Earnings, Cr. Expense accounts
        lines.append(JournalLineInput(
            account_code="3010",
            side="debit",
            amount=abs(net_income),
            description=f"Net loss transfer for {period.period_year}-{period.period_month:02d}",
        ))
        for acct in expense_accounts:
            bal = _get_period_balance(db, acct.id, period)
            if bal != 0:
                lines.append(JournalLineInput(
                    account_code=acct.code,
                    side="credit",
                    amount=bal,
                    description=f"Period close expense clearing for {period.period_year}-{period.period_month:02d}",
                ))

    ref = f"CLOSE-{country_code}-{period.period_year}-{period.period_month:02d}"
    journal_entry = create_journal_entry(
        db,
        JournalEntryCreate(
            entry_date=period.period_end,
            reference_type="period_close",
            reference_id=period.id,
            reference_number=ref,
            description=f"Period closing entry for {period.period_year}-{period.period_month:02d} ({country_code})",
            currency="OMR",
            lines=lines,
        ),
        user_id=user_id,
    )

    return {
        "net_income": float(net_income),
        "total_revenue": float(total_revenue),
        "total_expenses": float(total_expenses),
        "journal_entry_id": journal_entry.id,
        "revenue_accounts": revenue_lines,
        "expense_accounts": expense_lines,
    }


def _get_period_balance(db: Session, account_id: int, period: FiscalPeriod) -> Decimal:
    """Get the net change for an account within a fiscal period."""
    result = db.query(
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "debit"),
            0,
        ) -
        func.coalesce(
            func.sum(JournalEntryLine.amount).filter(JournalEntryLine.side == "credit"),
            0,
        )
    ).select_from(JournalEntryLine).join(
        JournalEntry, JournalEntryLine.entry_id == JournalEntry.id
    ).filter(
        JournalEntryLine.account_id == account_id,
        JournalEntry.entry_date >= period.period_start,
        JournalEntry.entry_date <= period.period_end,
        JournalEntry.is_deleted == False,
        JournalEntry.reversal_of_id.is_(None),
    ).scalar()

    acct = db.query(Account).filter(Account.id == account_id).first()
    amount = result or Decimal("0.00")
    if acct and acct.normal_side == "credit":
        return -amount
    return amount


def list_periods(
    db: Session,
    country_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 24,
) -> list[FiscalPeriod]:
    """List fiscal periods with optional filters."""
    q = db.query(FiscalPeriod).order_by(FiscalPeriod.period_year.desc(), FiscalPeriod.period_month.desc())
    if country_code:
        q = q.filter(FiscalPeriod.country_code == country_code)
    if status:
        q = q.filter(FiscalPeriod.status == status)
    return q.limit(limit).all()

