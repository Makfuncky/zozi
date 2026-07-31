"""Cash management write service — DB write operations for cash accounts and transactions."""

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