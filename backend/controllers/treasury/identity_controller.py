"""Treasury cash-account controller.

Thin orchestration layer: applies business rules (RLS scoping by country) and
delegates all persistence to services.treasury.cash_write_service. It must not
call db.add/commit or the write_helpers wrappers directly.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session
from models import CashAccount, CashTransaction
from services.treasury.cash_write_service import (
    create_country_cash_account,
    create_country_cash_transaction,
    list_active_country_cash_accounts,
)


def list_cash_accounts(country_code: str, db: Session) -> list[CashAccount]:
    """Return active cash accounts for a country (RLS-scoped by caller)."""
    return list_active_country_cash_accounts(db, country_code.upper())


def create_cash_account(country_code: str, payload, db: Session) -> CashAccount:
    """Create a cash account for a country."""
    return create_country_cash_account(db, country_code, payload)


def create_cash_transaction(country_code: str, payload, current_user, db: Session) -> CashTransaction:
    """Record a cash transaction against an account, adjusting its balance."""
    return create_country_cash_transaction(db, country_code, payload, current_user)
