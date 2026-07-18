"""Admin cash management router."""
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from db.database import get_db
from models import CashAccount, CashTransaction, User
from db.schemas import CashAccountCreate, CashAccountOut, CashTransactionCreate, CashTransactionOut
from utils.dependencies import require_admin
from utils.country_rls import get_country_or_404
from utils.rls_interceptor import set_rls_context, clear_rls_context
from decimal import Decimal

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
        a = CashAccount(**payload.model_dump(), country_code=country_code.upper())
        db.add(a); db.commit(); db.refresh(a)
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
        tx = CashTransaction(**payload.model_dump(), balance_after=account.balance, performed_by=current_user.id, country_code=country_code.upper())
        db.add(tx); db.commit(); db.refresh(tx)
        return tx
    finally:
        clear_rls_context()

