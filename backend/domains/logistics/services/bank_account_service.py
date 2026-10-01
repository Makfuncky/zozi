"""Logistics partner bank account domain service."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from domains.logistics.models.logistics_schema_models import LogisticsPartnerBankAccount


def create_logistics_bank_account(
    db: Session,
    partner_id: int,
    bank_name: str,
    beneficiary_name: Optional[str] = None,
    account_number: Optional[str] = None,
    iban: Optional[str] = None,
    swift_code: Optional[str] = None,
    routing_number: Optional[str] = None,
    branch_name: Optional[str] = None,
    currency: Optional[str] = None,
    bank_country: Optional[str] = None,
) -> LogisticsPartnerBankAccount:
    account = LogisticsPartnerBankAccount(partner_id=partner_id)
    fields = {
        "bank_name": bank_name,
        "beneficiary_name": beneficiary_name,
        "account_number": account_number,
        "iban": iban,
        "swift_code": swift_code,
        "routing_number": routing_number,
        "branch_name": branch_name,
        "currency": currency,
        "bank_country": bank_country,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(account, field, str(value).strip())
    account.is_active = True
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_logistics_bank_account(
    db: Session,
    account_id: int,
    partner_id: int,
    bank_name: str,
    beneficiary_name: Optional[str] = None,
    account_number: Optional[str] = None,
    iban: Optional[str] = None,
    swift_code: Optional[str] = None,
    routing_number: Optional[str] = None,
    branch_name: Optional[str] = None,
    currency: Optional[str] = None,
    bank_country: Optional[str] = None,
) -> Optional[LogisticsPartnerBankAccount]:
    account = (
        db.query(LogisticsPartnerBankAccount)
        .filter(
            LogisticsPartnerBankAccount.id == account_id,
            LogisticsPartnerBankAccount.partner_id == partner_id,
        )
        .first()
    )
    if not account:
        return None
    fields = {
        "bank_name": bank_name,
        "beneficiary_name": beneficiary_name,
        "account_number": account_number,
        "iban": iban,
        "swift_code": swift_code,
        "routing_number": routing_number,
        "branch_name": branch_name,
        "currency": currency,
        "bank_country": bank_country,
    }
    for field, value in fields.items():
        if value is not None:
            setattr(account, field, str(value).strip())
    account.is_active = True
    db.commit()
    db.refresh(account)
    return account


def deactivate_logistics_bank_account(
    db: Session,
    account_id: int,
    partner_id: int,
) -> bool:
    account = (
        db.query(LogisticsPartnerBankAccount)
        .filter(
            LogisticsPartnerBankAccount.id == account_id,
            LogisticsPartnerBankAccount.partner_id == partner_id,
        )
        .first()
    )
    if not account:
        return False
    account.is_active = False
    db.commit()
    return True


def list_logistics_bank_accounts(
    db: Session,
    partner_id: int,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Return paginated bank accounts for a logistics partner."""
    base_query = (
        db.query(LogisticsPartnerBankAccount)
        .filter(LogisticsPartnerBankAccount.partner_id == partner_id)
        .order_by(LogisticsPartnerBankAccount.created_at.desc())
    )
    total = base_query.count()
    accounts = (
        base_query
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "items": accounts,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size if total else 0,
    }
