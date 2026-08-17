"""Read helpers for admin cash-account listing.

Extracted from ``routers/admin_treasury_identity.py`` so the router stays a
thin HTTP layer (W1: routers must not issue DB queries directly).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from _legacy.models import CashAccount


def list_country_cash_accounts(db: Session, *, country_code: str) -> list[CashAccount]:
    """Active cash accounts for a country (country RLS set by the router)."""
    return db.query(CashAccount).filter(
        CashAccount.is_active == True,
        CashAccount.country_code == country_code,
    ).all()
