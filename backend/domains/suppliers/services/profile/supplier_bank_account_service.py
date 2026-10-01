"""Supplier bank-account write operations.

Owns the DB write for creating/updating a supplier's bank account. Routers must
not call session.add()/commit()/refresh() directly for this operation (W1).
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from domains.governance.ports import SupplierBankAccount
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


def upsert_supplier_bank_account(db: Session, supplier_id: int, payload: dict) -> SupplierBankAccount:
    """Create or update the supplier's bank account and commit the change."""
    account = (
        db.query(SupplierBankAccount)
        .filter(SupplierBankAccount.supplier_id == supplier_id)
        .first()
    )
    if not account:
        account = SupplierBankAccount(supplier_id=supplier_id)
        db.add(account)

    for field in _BANK_FIELDS:
        if field in payload:
            setattr(account, field, str(payload[field]).strip())

    account.is_active = True
    db.commit()
    db.refresh(account)
    return account


def get_supplier_bank_account(db: Session, current_user: Any) -> dict:
    """Return the supplier's own bank account details."""
    supplier_id = int(current_user.id) if hasattr(current_user, "id") else int(current_user.get("id"))
    record = db.query(SupplierBankAccount).filter(SupplierBankAccount.supplier_id == supplier_id).first()
    if record is None:
        return {"configured": False}
    return {
        "configured": True,
        "id": record.id,
        "beneficiary_name": record.beneficiary_name,
        "bank_name": record.bank_name,
        "branch_name": record.branch_name,
        "account_number": record.account_number,
        "iban": record.iban,
        "swift_code": record.swift_code,
        "routing_number": record.routing_number,
        "currency": record.currency,
        "bank_country": record.bank_country,
        "verification_status": record.verification_status,
        "verification_note": record.verification_note,
        "provider": record.provider,
        "provider_recipient_id": record.provider_recipient_id,
        "provider_status": record.provider_status,
        "provider_last_synced_at": record.provider_last_synced_at.isoformat() if record.provider_last_synced_at else None,
        "verified_at": record.verified_at.isoformat() if record.verified_at else None,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def upsert_supplier_bank_account_from_router(body: dict, current_user: Any, db: Session) -> dict:
    """Adapter for router: supplier submits or updates their payout bank account."""
    supplier_id = int(current_user.id) if hasattr(current_user, "id") else int(current_user.get("id"))
    account = upsert_supplier_bank_account(db, supplier_id, body)
    return {
        "id": account.id,
        "bank_name": account.bank_name,
        "beneficiary_name": account.beneficiary_name,
        "verification_status": account.verification_status,
        "is_active": account.is_active,
    }
