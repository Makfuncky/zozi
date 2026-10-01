from __future__ import annotations

"""Settlement service — partner payouts and COD remittance."""

from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from domains.governance.models.admin import LogisticsCODRemittanceReceipt
from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsSettlement
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.models.logistics import Shipment
from domains.finance.models.payments import LogisticsPartnerPayout
from domains.finance.ports import apply_shipment_vehicle_selection
from domains.finance.ports import create_cod_remittance_receipt
from domains.finance.ports import deserialize_pricing_breakdown_json
from domains.finance.ports import effective_allocation_delivery_amounts
from domains.finance.ports import list_cod_remittance_receipts
from domains.finance.ports import serialize_cod_remittance_receipt
from domains.logistics.services.partners.partner_service import _get_partner_for_user
from infrastructure.utils.datetime_utils import utcnow as _utcnow


def _serialize_partner_payout(payout: LogisticsPartnerPayout) -> dict:
    created_at = cast(Optional[datetime], getattr(payout, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(payout, "updated_at", None))
    reviewed_at = cast(Optional[datetime], getattr(payout, "reviewed_at", None))
    return {
        "id": payout.id,
        "partner_id": payout.partner_id,
        "amount": float(payout.amount) if payout.amount is not None else 0.0,
        "currency": payout.currency,
        "status": payout.status,
        "period_start": payout.period_start.isoformat() if payout.period_start else None,
        "period_end": payout.period_end.isoformat() if payout.period_end else None,
        "notes": payout.notes,
        "reviewed_by": payout.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def get_partner_payouts(current_user: dict, db: Session) -> list:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    payouts = (
        db.query(LogisticsPartnerPayout)
        .filter(LogisticsPartnerPayout.partner_id == partner.id)
        .order_by(desc(LogisticsPartnerPayout.created_at))
        .limit(100)
        .all()
    )
    return [_serialize_partner_payout(p) for p in payouts]


def request_partner_payout(data: dict, current_user: dict, db: Session) -> dict:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    amount = data.get("amount")
    if amount is None:
        raise HTTPException(status_code=422, detail="amount is required")
    try:
        amount = float(amount)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="amount must be a number") from exc
    if amount <= 0:
        raise HTTPException(status_code=422, detail="amount must be positive")
    payout = LogisticsPartnerPayout(
        partner_id=partner.id,
        amount=amount,
        currency=data.get("currency", "AED"),
        status="pending",
        notes=data.get("notes"),
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return _serialize_partner_payout(payout)


def list_pending_partner_payouts(current_user: dict, db: Session) -> list:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    payouts = (
        db.query(LogisticsPartnerPayout)
        .filter(LogisticsPartnerPayout.status == "pending")
        .order_by(LogisticsPartnerPayout.created_at.asc())
        .limit(100)
        .all()
    )
    return [_serialize_partner_payout(p) for p in payouts]


def verify_partner_payout(payout_id: int, data: dict, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    payout = db.query(LogisticsPartnerPayout).filter(LogisticsPartnerPayout.id == payout_id).first()
    if not payout:
        raise HTTPException(status_code=404, detail="Payout not found")
    decision = str(data.get("status", "")).strip().lower()
    if decision not in {"approved", "rejected", "paid"}:
        raise HTTPException(status_code=422, detail="status must be one of: approved, rejected, payed")
    setattr(payout, "status", decision)
    setattr(payout, "reviewed_by", current_user["id"])
    setattr(payout, "reviewed_at", _utcnow())
    setattr(payout, "updated_at", _utcnow())
    if decision in ("approved", "paid"):
        setattr(payout, "status", "paid")
    db.commit()
    db.refresh(payout)
    return _serialize_partner_payout(payout)


def list_partner_cod_remittance_receipts(
    current_user: dict,
    db: Session,
    *,
    status: str | None = None,
    settlement_id: int | None = None,
) -> list[dict]:
    partner = _get_partner_for_user(current_user["id"], db)
    return list_cod_remittance_receipts(db, partner_id=partner.id, status=status, settlement_id=settlement_id)


async def upload_partner_cod_remittance_receipt(
    settlement_id: int,
    amount: float,
    file: UploadFile,
    bank_reference: str | None,
    notes: str | None,
    current_user: dict,
    db: Session,
) -> dict:
    import os
    import uuid
    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.file_validation import validate_upload_document
    from infrastructure.utils.constants import MAX_UPLOAD_SIZE_BYTES

    safe_name = os.path.basename(file.filename or "cod-receipt.pdf")
    ext = os.path.splitext(safe_name)[1].lower() or ".pdf"
    filename = f"cod_receipt_{uuid.uuid4().hex}{ext}"
    key = f"logistics_cod_receipts/{filename}"

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    validate_upload_document(contents, safe_name)
    url = _storage.save(key, contents, content_type=file.content_type)

    partner = _get_partner_for_user(current_user["id"], db)
    try:
        receipt = create_cod_remittance_receipt(
            settlement_id=settlement_id,
            partner_id=cast(int, partner.id),
            amount=cast(Any, amount),
            receipt_file_url=url,
            db=db,
            bank_reference=bank_reference,
            notes=notes,
        )
        db.commit()
        db.refresh(receipt)
        return serialize_cod_remittance_receipt(receipt, db)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
