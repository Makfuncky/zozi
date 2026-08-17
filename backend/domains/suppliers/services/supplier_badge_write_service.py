"""Real implementation of supplier badge billing operations.

The historical ``services.supplier.supplier_badge_service`` is a lazy re-export shim whose
body was lost in the layered reorg; this module holds the surviving
implementation(s) and is wired into that shim through its ``_REEXPORTS`` map.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import BadgeBillingRecord
from _legacy.models.finance import BankTransaction
from services.treasury.cash_management_service import log_bank_transaction
import structlog
logger = structlog.get_logger(__name__)


def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_admin: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> BadgeBillingRecord:
    """Record payment against a supplier badge billing record.

    Marks the billing record paid, links (or creates) the carrying bank
    transaction for reconciliation, and returns the (uncommitted) ORM row.
    The caller owns the transaction ``commit``.
    """
    record = (
        db.query(BadgeBillingRecord)
        .filter(BadgeBillingRecord.id == billing_id)
        .first()
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Badge billing record not found")

    record.status = "paid"
    record.payment_method = payment_method
    record.paid_at = datetime.utcnow()
    if notes is not None:
        record.notes = notes

    if transaction_ref:
        existing = (
            db.query(BankTransaction)
            .filter(BankTransaction.transaction_ref == transaction_ref)
            .first()
        )
        if existing is None:
            existing = log_bank_transaction(
                source="badge_billing",
                transaction_type="inflow",
                category="badge_billing_payment",
                amount=record.amount,
                db=db,
                supplier_id=record.supplier_id,
                description=f"Badge billing payment for record #{record.id}",
                transaction_ref=transaction_ref,
                country_code=record.country_code,
            )
        record.bank_transaction_id = existing.id

    return record
