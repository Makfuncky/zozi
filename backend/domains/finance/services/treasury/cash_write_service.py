from __future__ import annotations
from typing import List
"""Cash management write service — DB read and write operations for cash accounts and transactions."""

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.finance.models.finance import CashAccount
from domains.finance.models.finance import CashTransaction
import structlog
logger = structlog.get_logger(__name__)


def create_cash_account(db: Session, **account_data) -> CashAccount:
    account = CashAccount(**account_data)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_cash_account(db: Session, account: CashAccount, updates: dict) -> CashAccount:
    for key, value in updates.items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


def delete_cash_account(db: Session, account: CashAccount) -> None:
    db.delete(account)
    db.commit()


def create_cash_transaction(db: Session, **transaction_data) -> CashTransaction:
    transaction = CashTransaction(**transaction_data)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


def update_cash_transaction(db: Session, transaction: CashTransaction, updates: dict) -> CashTransaction:
    for key, value in updates.items():
        setattr(transaction, key, value)
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_cash_transaction(db: Session, transaction: CashTransaction) -> None:
    db.delete(transaction)
    db.commit()


def create_country_cash_account(db: Session, country_code: str, payload) -> CashAccount:
    """Create a country-scoped cash account and commit."""
    account = CashAccount(**payload.model_dump(), country_code=country_code.upper())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def create_country_cash_transaction(db: Session, country_code: str, payload, current_user) -> CashTransaction:
    """Record a cash transaction against an account, adjusting its balance, and commit."""
    account = db.query(CashAccount).filter(
        CashAccount.id == payload.account_id,
        CashAccount.country_code == country_code.upper(),
    ).first()
    if not account:
        raise HTTPException(404, 'Account not found')
    if payload.transaction_type == 'debit':
        account.balance -= payload.amount
    else:
        account.balance += payload.amount
    tx = CashTransaction(
        **payload.model_dump(),
        balance_after=account.balance,
        performed_by=getattr(current_user, 'id', None),
        country_code=country_code.upper(),
    )
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


# ── Read helpers ─────────────────────────────────────────────────────────────

def list_cash_accounts(db: Session, country_code: str, skip: int = 0, limit: int = 20) -> list[CashAccount]:
    """List active cash accounts for a country."""
    return (
        db.query(CashAccount)
        .filter(CashAccount.is_active == True, CashAccount.country_code == country_code)
        .order_by(CashAccount.id.desc())
        
        .limit(limit)
        .all()
    )


def get_cash_account(db: Session, account_id: int, country_code: str) -> Optional[CashAccount]:
    """Fetch a single cash account by ID within a country."""
    return db.query(CashAccount).filter(
        CashAccount.id == account_id,
        CashAccount.country_code == country_code,
    ).first()


def list_active_country_cash_accounts(db: Session, country_code: str) -> list[CashAccount]:
    """Return all active cash accounts for a country (no pagination)."""
    return db.query(CashAccount).filter(
        CashAccount.is_active == True,
        CashAccount.country_code == country_code,
    ).all()
