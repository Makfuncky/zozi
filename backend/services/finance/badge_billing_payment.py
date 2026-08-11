"""Badge billing payment service.

Business logic for supplier badge billing records: listing, generation of
pending charges, and recording payments against a ``BadgeBillingRecord`` while
mirroring the cash movement through the canonical ``log_bank_transaction``
helper so the finance reconciliation ledger stays consistent.

The underlying ``BadgeBillingRecord`` model already lives in
``models/admin.py`` and is surfaced through the ``data.models`` shim, so this
service reuses it rather than declaring a duplicate ORM class.
"""
from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from data.models import BadgeBillingRecord, BankTransaction
from services.treasury.cash_management_service import log_bank_transaction
from utils.datetime_utils import utcnow
from utils.money import round_money, to_decimal
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as e:
        logger.exception("_parse_dt_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid ISO datetime: {value!r}",
        )


def list_badge_billing_records(
    db: Session,
    *,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    country_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """Return (items, total) for the supplied filters."""
    query = db.query(BadgeBillingRecord)
    if supplier_id is not None:
        query = query.filter(BadgeBillingRecord.supplier_id == supplier_id)
    if status is not None:
        query = query.filter(BadgeBillingRecord.status == status)
    if country_code is not None:
        query = query.filter(BadgeBillingRecord.country_code == country_code)
    query = query.order_by(desc(BadgeBillingRecord.created_at))
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_badge_billing_record(db: Session, record_id: int) -> BadgeBillingRecord:
    record = (
        db.query(BadgeBillingRecord)
        .filter(BadgeBillingRecord.id == record_id)
        .first()
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Badge billing record not found",
        )
    return record


def generate_badge_billing_record(
    db: Session,
    *,
    supplier_id: int,
    amount: Decimal,
    currency: str = "USD",
    badge_level: Optional[str] = None,
    charge_type: Optional[str] = None,
    charge_source: Optional[str] = None,
    country_code: Optional[str] = None,
    billing_reference: Optional[str] = None,
    period_start: Optional[datetime] = None,
    period_end: Optional[datetime] = None,
    due_at: Optional[datetime] = None,
    notes: Optional[str] = None,
    created_by: Optional[int] = None,
) -> BadgeBillingRecord:
    """Create a pending badge billing charge for a supplier."""
    amount_dec = to_decimal(amount)
    if amount_dec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be greater than zero",
        )

    record = BadgeBillingRecord(
        supplier_id=supplier_id,
        billing_reference=billing_reference,
        badge_level=badge_level,
        charge_type=charge_type or "badge_subscription",
        charge_source=charge_source or "system",
        amount=round_money(amount_dec),
        currency=currency,
        status="pending",
        period_start=period_start,
        period_end=period_end,
        due_at=due_at,
        notes=notes,
        created_by=created_by,
        country_code=country_code,
    )
    db.add(record)
    db.flush()
    db.commit()
    return record


def pay_badge_billing_record(
    db: Session,
    record_id: int,
    *,
    amount: Decimal,
    payment_method: str,
    currency: Optional[str] = None,
    country_code: Optional[str] = None,
    notes: Optional[str] = None,
    updated_by: Optional[int] = None,
) -> tuple[BadgeBillingRecord, BankTransaction]:
    """Record a payment against a badge billing record.

    Creates a reconcilable bank transaction via the canonical cash-management
    helper and links it to the billing record, transitioning the record to
    ``paid``.
    """
    record = get_badge_billing_record(db, record_id)
    if record.status == "paid":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Badge billing record is already paid",
        )

    amount_dec = to_decimal(amount)
    if amount_dec <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero",
        )

    txn = log_bank_transaction(
        source="badge_billing",
        transaction_type="inflow",
        category="badge_billing",
        amount=amount_dec,
        db=db,
        currency=currency or record.currency or "USD",
        supplier_id=record.supplier_id,
        description=(
            f"Badge billing payment for record #{record.id}"
            + (f" (ref {record.billing_reference})" if record.billing_reference else "")
        ),
        transaction_ref=f"BB-{record.billing_reference or record.id}",
        country_code=country_code or record.country_code,
    )

    record.bank_transaction_id = txn.id
    record.payment_method = payment_method
    record.paid_at = utcnow()
    record.billed_at = record.billed_at or utcnow()
    record.status = "paid"
    if notes is not None:
        record.notes = notes
    if updated_by is not None:
        record.updated_by = updated_by

    db.add(record)
    db.flush()
    db.commit()
    return record, txn
