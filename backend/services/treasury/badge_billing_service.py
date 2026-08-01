"""Badge Billing Management Service — handling badge billing records and payments."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload

from models import BadgeBillingRecord, SupplierProfile
from services.supplier.suppliers_write_service import flush_session, add_and_flush
from services.treasury.cash_management_service import log_bank_transaction
from utils.audit_log import audit_log, AuditAction
from utils.datetime_utils import utcnow as _utcnow


def _round_badge_amount(amount) -> float:
    if amount is None:
        return 0.0
    return round(float(amount), 2)


def record_badge_billing_payment(
    billing_id: int,
    payment_method: str,
    current_user: dict,
    db: Session,
    transaction_ref: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Record payment for a badge billing record."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    record = (
        db.query(BadgeBillingRecord)
        .options(selectinload(BadgeBillingRecord.bank_transaction), selectinload(BadgeBillingRecord.supplier))
        .filter(BadgeBillingRecord.id == billing_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Badge billing record not found")
    if record.status == "paid":
        return _serialize_badge_billing_record(record)
    if record.status in {"waived", "cancelled"}:
        raise HTTPException(status_code=409, detail=f"Cannot record payment for {record.status} badge billing")

    paid_at = _utcnow()
    if _round_badge_amount(record.amount) > 0 and not record.bank_transaction_id:
        txn = log_bank_transaction(
            source="badge_billing",
            transaction_type="inflow",
            category="badge_fee",
            amount=_round_badge_amount(record.amount),
            db=db,
            currency=record.currency,
            supplier_id=record.supplier_id,
            description=f"{record.charge_type.title()} badge fee collected for {record.badge_level} tier",
            transaction_ref=transaction_ref,
            transaction_date=paid_at,
        )
        record.bank_transaction_id = txn.id
        record.bank_transaction = txn

    record.status = "paid"
    record.payment_method = payment_method.strip().lower() or "manual"
    record.paid_at = paid_at
    if notes:
        record.notes = notes if not record.notes else f"{record.notes}\n{notes}"

    flush_session(db)
    audit_log(
        db=db,
        action=AuditAction.PAYOUT_PROCESSED,
        user_id=current_user["id"],
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="BadgeBillingRecord",
        resource_id=billing_id,
        details={"payment_method": payment_method, "amount": record.amount},
        status="success",
    )
    return _serialize_badge_billing_record(record)


def _serialize_badge_billing_record(record: BadgeBillingRecord) -> dict[str, Any]:
    supplier = cast(Optional[SupplierProfile], record.supplier)
    return {
        "id": record.id,
        "supplier_id": record.supplier_id,
        "supplier_name": str(supplier.company_name) if supplier else None,
        "badge_level": record.badge_level,
        "charge_type": record.charge_type,
        "amount": float(record.amount) if record.amount else 0.0,
        "currency": record.currency,
        "tax_amount": float(record.tax_amount) if record.tax_amount else 0.0,
        "total_amount": float(record.total_amount) if record.total_amount else 0.0,
        "status": record.status,
        "paid_at": record.paid_at.isoformat() if record.paid_at else None,
        "transaction_ref": record.bank_transaction_id,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }