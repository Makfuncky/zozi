"""Logistics partner bank-account write operations.

Owns the DB writes for creating/listing/updating/deactivating a logistics
partner's bank accounts. Routers must not call session.add()/commit()/
refresh()/query() directly for these operations (W1).
"""
from __future__ import annotations

from typing import Optional, Tuple

from sqlalchemy.orm import Session

from domains.governance.ports import (
    get_logistics_partner_bank_account_by_id as _get_bank_acct,
    logistics_partner_bank_account_model as _LPBankAccountModel,
)
from domains.logistics.models.logistics import LogisticsPartner
import structlog

logger = structlog.get_logger(__name__)

_BANK_FIELDS = [
    "bank_name",
    "beneficiary_name",
    "account_number",
    "iban",
    "swift_code",
    "routing_number",
    "branch_name",
    "currency",
    "bank_country",
]

LPBankAccount = _LPBankAccountModel()


def get_partner_id_for_user(db: Session, user_id: int) -> Optional[int]:
    """Resolve LogisticsPartner.id for a given user_id. Returns None if not found."""
    partner = (
        db.query(LogisticsPartner)
        .filter(LogisticsPartner.user_id == user_id)
        .first()
    )
    return partner.id if partner else None


def list_partner_bank_accounts(
    db: Session, partner_id: int, page: int, page_size: int
) -> Tuple[int, list]:
    """Return (total, accounts) for the partner's bank accounts."""
    base_query = (
        db.query(LPBankAccount)
        .filter(LPBankAccount.partner_id == partner_id)
        .order_by(LPBankAccount.created_at.desc())
    )
    total = base_query.count()
    accounts = (
        base_query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return total, accounts


def create_partner_bank_account(
    db: Session, partner_id: int, payload: dict
):
    """Create a new bank account for the logistics partner."""
    account = LPBankAccount(partner_id=partner_id)
    for field in _BANK_FIELDS:
        value = payload.get(field)
        if value is not None:
            setattr(account, field, str(value).strip())
    account.is_active = True
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_partner_bank_account(
    db: Session, partner_id: int, account_id: int, payload: dict
) -> Optional[object]:
    """Update an existing partner bank account. Returns None if not found."""
    account = _get_bank_acct(db, account_id)
    if not account or account.partner_id != partner_id:
        return None
    for field in _BANK_FIELDS:
        value = payload.get(field)
        if value is not None:
            setattr(account, field, str(value).strip())
    account.is_active = True
    db.commit()
    db.refresh(account)
    return account


def deactivate_partner_bank_account(
    db: Session, partner_id: int, account_id: int
) -> Optional[object]:
    """Soft-delete a partner bank account. Returns None if not found."""
    account = _get_bank_acct(db, account_id)
    if not account or account.partner_id != partner_id:
        return None
    account.is_active = False
    db.commit()
    return account
