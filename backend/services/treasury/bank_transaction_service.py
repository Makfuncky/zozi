"""
Bank Transaction Service — neutral home for bank-transaction creation.

This module exists to break the historical circular dependency between
``cash_management_service`` and ``supplier_badge_service`` (both lazily
imported the other at runtime). ``log_bank_transaction`` now lives here so
either service can depend on it without forming a cycle.
"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session

from models import BankTransaction
from utils.datetime_utils import utcnow as _utcnow
from utils.money import round_money


def log_bank_transaction(
    source: str,
    transaction_type: str,
    category: str,
    amount: Decimal,
    db: Session,
    currency: str = "OMR",
    order_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    logistics_id: Optional[int] = None,
    payout_id: Optional[int] = None,
    refund_id: Optional[int] = None,
    description: Optional[str] = None,
    transaction_ref: Optional[str] = None,
    transaction_date: Optional[datetime] = None,
    country_code: Optional[str] = None,
) -> BankTransaction:
    """Log a bank transaction for reconciliation tracking."""
    if not transaction_ref:
        transaction_ref = f"ZOZI-{uuid.uuid4().hex[:12].upper()}"

    txn = BankTransaction(
        transaction_ref=transaction_ref,
        source=source,
        transaction_type=transaction_type,
        category=category,
        amount=round_money(amount),
        currency=currency,
        linked_order_id=order_id,
        linked_supplier_id=supplier_id,
        linked_logistics_id=logistics_id,
        linked_payout_id=payout_id,
        linked_refund_id=refund_id,
        description=description,
        reconciled=False,
        transaction_date=transaction_date or _utcnow(),
        country_code=country_code,
    )
    db.add(txn)
    db.flush()
    return txn


class BankTransactionLogger:
    def __init__(self, db: Session, **txn_params):
        self.db = db
        self.txn_params = txn_params
        self._transaction = None

    def log(self):
        self._transaction = log_bank_transaction(db=self.db, **self.txn_params)
        return self._transaction

    def commit(self):
        if self._transaction:
            self.db.commit()
            self.db.refresh(self._transaction)
            return self._transaction
        return None
