"""Admin cash management service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from infrastructure.database.schemas import (
    CashAccountCreate,
    CashAccountOut,
    CashTransactionCreate,
    CashTransactionOut,
)
from domains.finance.models.finance import CashAccount

# TODO: Module not yet created
# from domains.comms.services.utility.misc_write_service import create_cash_account as create_cash_account_model
# TODO: Module not yet created
# from domains.comms.services.utility.misc_write_service import create_cash_transaction as create_cash_transaction_model

from domains.country.utils.country_rls import get_country_or_404
from infrastructure.database.rls_interceptor import clear_rls_context, set_rls_context


def list_accounts(country_code: str, db: Session) -> list[CashAccountOut]:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(
            CashAccount.is_active == True,
            CashAccount.country_code == country_code.upper()
        ).all()
    finally:
        clear_rls_context()


def create_account(country_code: str, payload: CashAccountCreate, db: Session) -> CashAccountOut:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account_data = payload.model_dump()
        account_data["country_code"] = country_code.upper()
        return create_cash_account_model(db, **account_data)
    finally:
        clear_rls_context()


def create_transaction(country_code: str, payload: CashTransactionCreate, current_user_id: int, db: Session) -> CashTransactionOut:
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(
            CashAccount.id == payload.account_id,
            CashAccount.country_code == country_code.upper()
        ).first()
        if not account:
            raise ValueError("Account not found")
        if payload.transaction_type == "debit":
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx_data = payload.model_dump()
        tx_data["balance_after"] = account.balance
        tx_data["performed_by"] = current_user_id
        tx_data["country_code"] = country_code.upper()
        return create_cash_transaction_model(db, **tx_data)
    finally:
        clear_rls_context()


