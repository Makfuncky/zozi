'Treasury cash-account controller.\n\nHolds the read/write logic for country-scoped cash accounts and cash\ntransactions. Previously this logic lived inline in\n``routers.admin_treasury_identity`` (CG1: model instantiation in router,\nW1: ``db.add``/``db.commit`` in router). Routers now only set RLS context,\nauthorize, and delegate here.\n'
from __future__ import annotations
from fastapi import HTTPException
from services.db_read import query as db_read_query, execute as db_read_execute
from sqlalchemy.orm import Session
from models import CashAccount, CashTransaction
from services.write_helpers import commit_and_refresh

def list_cash_accounts(country_code: str, db: Session) -> list[CashAccount]:
    """Return active cash accounts for a country (RLS-scoped by caller)."""
    return db_read_query(db, CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()

def create_cash_account(country_code: str, payload, db: Session) -> CashAccount:
    """Create a cash account for a country."""
    account = CashAccount(**payload.model_dump(), country_code=country_code.upper())
    return commit_and_refresh(db, account)

def create_cash_transaction(country_code: str, payload, current_user, db: Session) -> CashTransaction:
    """Record a cash transaction against an account, adjusting its balance."""
    account = db_read_query(db, CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
    if not account:
        raise HTTPException(404, 'Account not found')
    if payload.transaction_type == 'debit':
        account.balance -= payload.amount
    else:
        account.balance += payload.amount
    tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=getattr(current_user, 'id', None), country_code=country_code.upper())
    return commit_and_refresh(db, tx)
