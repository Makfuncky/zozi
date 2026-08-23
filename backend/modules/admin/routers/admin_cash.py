"""Admin cash management router."""

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import (
    CashAccountCreate,
    CashAccountOut,
    CashTransactionCreate,
    CashTransactionOut,
)
from domains.governance.models.user import User
from domains.finance.models.finance import CashAccount
from domains.finance.models.finance import CashTransaction
from domains.comms.services.utility.misc_write_service import create_cash_account as create_cash_account_model
from domains.comms.services.utility.misc_write_service import create_cash_transaction as create_cash_transaction_model
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.dependencies import require_admin
from infrastructure.utils.rls_interceptor import clear_rls_context, set_rls_context

router = APIRouter()


@router.get("/{country_code}/accounts", response_model=list[CashAccountOut])
def list_accounts(country_code: str = Path(..., description="ISO country code"), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        return db.query(CashAccount).filter(CashAccount.is_active == True, CashAccount.country_code == country_code.upper()).all()
    finally:
        clear_rls_context()


@router.post("/{country_code}/accounts", response_model=CashAccountOut, status_code=201)
def create_account(country_code: str = Path(..., description="ISO country code"), payload: CashAccountCreate = None, _: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account_data = payload.model_dump()
        account_data["country_code"] = country_code.upper()
        a = create_cash_account_model(db, **account_data)
        return a
    finally:
        clear_rls_context()


@router.post("/{country_code}/transactions", response_model=CashTransactionOut, status_code=201)
def create_transaction(country_code: str = Path(..., description="ISO country code"), payload: CashTransactionCreate = None, current_user: User = Depends(require_admin), db: Session = Depends(get_db)):
    get_country_or_404(country_code.upper(), db)
    set_rls_context({country_code.upper()}, is_restricted=True)
    try:
        account = db.query(CashAccount).filter(CashAccount.id == payload.account_id, CashAccount.country_code == country_code.upper()).first()
        if not account: raise HTTPException(404, "Account not found")
        if payload.transaction_type == "debit":
            account.balance -= payload.amount
        else:
            account.balance += payload.amount
        tx_data = payload.model_dump()
        tx_data["balance_after"] = account.balance
        tx_data["performed_by"] = current_user.id
        tx_data["country_code"] = country_code.upper()
        tx = create_cash_transaction_model(db, **tx_data)
        return tx
    finally:
        clear_rls_context()

