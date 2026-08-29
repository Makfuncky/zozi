"""Supplier bank account domain service."""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.accounts.models.banking import SupplierBankAccount


def deactivate_supplier_bank_account(
    db: Session,
    account_id: int,
    supplier_id: int,
) -> bool:
    account = (
        db.query(SupplierBankAccount)
        .filter(
            SupplierBankAccount.id == account_id,
            SupplierBankAccount.supplier_id == supplier_id,
        )
        .first()
    )
    if not account:
        return False
    account.is_active = False
    db.commit()
    return True
