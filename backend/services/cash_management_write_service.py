from typing import List
"""Cash management service — DB read and write operations for cash accounts and transactions."""

from typing import Optional

from sqlalchemy.orm import Session

from models import CashAccount, CashTransaction


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


# ── Read helpers ─────────────────────────────────────────────────────────────

def list_cash_accounts(db: Session, country_code: str, skip: int = 0, limit: int = 20) -> list[CashAccount]:
    """List active cash accounts for a country."""
    return (
        db.query(CashAccount)
        .filter(CashAccount.is_active == True, CashAccount.country_code == country_code)
        .order_by(CashAccount.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_cash_account(db: Session, account_id: int, country_code: str) -> Optional[CashAccount]:
    """Fetch a single cash account by ID within a country."""
    return db.query(CashAccount).filter(
        CashAccount.id == account_id,
        CashAccount.country_code == country_code,
    ).first()