"""Badge billing router — thin HTTP surface for supplier badge billing records.

Per the layer contract this module only:
  * instantiates the ``APIRouter`` (R1: routers/ owns the router),
  * validates request bodies and serializes responses,
  * delegates all business logic and DB writes to
    :mod:`services.badge_billing_payment`.

It performs no ``db.add`` / ``db.commit`` itself (W1) — the service owns the
transaction.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from db.database import get_db
from data.models import BadgeBillingRecord, User
from utils.dependencies import require_admin, require_employee

from services.badge_billing_payment import (
    generate_badge_billing_record,
    get_badge_billing_record,
    list_badge_billing_records,
    pay_badge_billing_record,
)
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Badge Billing"])


class PayBadgeBillingRequest(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    currency: Optional[str] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None


class GenerateBadgeBillingRequest(BaseModel):
    supplier_id: int
    amount: float = Field(gt=0)
    currency: str = "USD"
    badge_level: Optional[str] = None
    charge_type: Optional[str] = None
    charge_source: Optional[str] = None
    country_code: Optional[str] = None
    billing_reference: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    due_at: Optional[str] = None
    notes: Optional[str] = None


class BadgeBillingBankTxnOut(BaseModel):
    id: int
    transaction_ref: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None


class BadgeBillingRecordOut(BaseModel):
    id: int
    billing_reference: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_username: Optional[str] = None
    user_id: Optional[int] = None
    badge_level: Optional[str] = None
    charge_type: Optional[str] = None
    charge_source: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    status: Optional[str] = None
    reference_id: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    due_at: Optional[str] = None
    billed_at: Optional[str] = None
    paid_at: Optional[str] = None
    payment_method: Optional[str] = None
    bank_transaction_id: Optional[int] = None
    notes: Optional[str] = None
    country_code: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class BadgeBillingPayOut(BadgeBillingRecordOut):
    bank_transaction: Optional[BadgeBillingBankTxnOut] = None


class BadgeBillingListOut(BaseModel):
    total: int
    items: list[BadgeBillingRecordOut]


def _serialize(record: BadgeBillingRecord) -> dict:
    supplier = getattr(record, "supplier", None)
    return {
        "id": record.id,
        "billing_reference": record.billing_reference,
        "supplier_id": record.supplier_id,
        "supplier_username": getattr(supplier, "username", None) if supplier else None,
        "user_id": record.user_id,
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "charge_source": record.charge_source,
        "amount": float(record.amount) if record.amount is not None else None,
        "currency": record.currency,
        "status": record.status,
        "reference_id": record.reference_id,
        "period_start": record.period_start.isoformat() if record.period_start else None,
        "period_end": record.period_end.isoformat() if record.period_end else None,
        "due_at": record.due_at.isoformat() if record.due_at else None,
        "billed_at": record.billed_at.isoformat() if record.billed_at else None,
        "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        "payment_method": record.payment_method,
        "bank_transaction_id": record.bank_transaction_id,
        "notes": record.notes,
        "country_code": record.country_code,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


@router.get("", response_model=BadgeBillingListOut)
def list_badge_billing(
    db: Session = Depends(get_db),
    _: User = Depends(require_employee),
    supplier_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    items, total = list_badge_billing_records(
        db,
        supplier_id=supplier_id,
        status=status,
        country_code=country_code,
        skip=skip,
        limit=limit,
    )
    return {"total": total, "items": [_serialize(item) for item in items]}


@router.get("/{record_id}", response_model=BadgeBillingRecordOut)
def get_badge_billing(
    record_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_employee),
):
    return _serialize(get_badge_billing_record(db, record_id))


@router.post("/generate", response_model=BadgeBillingRecordOut, status_code=status.HTTP_201_CREATED)
def generate_badge_billing(
    body: GenerateBadgeBillingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from services.badge_billing_payment import parse_dt

    record = generate_badge_billing_record(
        db,
        supplier_id=body.supplier_id,
        amount=body.amount,
        currency=body.currency,
        badge_level=body.badge_level,
        charge_type=body.charge_type,
        charge_source=body.charge_source,
        country_code=body.country_code,
        billing_reference=body.billing_reference,
        period_start=_parse_dt(body.period_start),
        period_end=_parse_dt(body.period_end),
        due_at=_parse_dt(body.due_at),
        notes=body.notes,
        created_by=current_user.id,
    )
    return _serialize(record)


@router.post("/{record_id}/pay", response_model=BadgeBillingPayOut)
def pay_badge_billing(
    record_id: int,
    body: PayBadgeBillingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_employee),
):
    record, txn = pay_badge_billing_record(
        db,
        record_id,
        amount=body.amount,
        payment_method=body.payment_method,
        currency=body.currency,
        country_code=body.country_code,
        notes=body.notes,
        updated_by=current_user.id,
    )
    result = _serialize(record)
    result["bank_transaction"] = {
        "id": txn.id,
        "transaction_ref": txn.transaction_ref,
        "amount": float(txn.amount) if txn.amount is not None else None,
        "currency": txn.currency,
    }
    return result
