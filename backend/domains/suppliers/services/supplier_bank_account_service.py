"""Supplier bank-account write operations.

Owns the DB write for creating/updating a supplier's bank account. Routers must
not call session.add()/commit()/refresh() directly for this operation (W1).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from models import SupplierBankAccount
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
