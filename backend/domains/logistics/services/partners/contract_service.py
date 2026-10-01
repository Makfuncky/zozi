from __future__ import annotations

"""Contract service — partner documents and bank accounts."""

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, cast

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.governance.models.admin import LogisticsPartnerDocument
from domains.logistics.models.logistics import LogisticsPartner
from domains.logistics.services.partners.partner_service import _get_partner_for_user
from infrastructure.utils.datetime_utils import utcnow as _utcnow

ALLOWED_LP_DOC_TYPES = ("trade_license", "emirates_id", "passport", "visa", "bank_statement", "other")


def _serialize_lp_doc(doc: LogisticsPartnerDocument) -> dict:
    created_at = cast(Optional[datetime], getattr(doc, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(doc, "updated_at", None))
    expires_at = cast(Optional[datetime], getattr(doc, "expires_at", None))
    reviewed_at = cast(Optional[datetime], getattr(doc, "reviewed_at", None))
    return {
        "id": doc.id,
        "partner_id": doc.partner_id,
        "document_type": doc.document_type,
        "document_name": doc.document_name,
        "file_url": doc.file_url,
        "status": doc.status,
        "review_note": doc.review_note,
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


def get_partner_bank_account(current_user: dict, db: Session) -> dict:
    """Return the logistics partner's own bank account details."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required.")
    partner = _get_partner_for_user(current_user, db)
    partner_id = int(cast(int, partner.id))
    record = db.query(LogisticsPartnerBankAccount).filter(
        LogisticsPartnerBankAccount.partner_id == partner_id
    ).first()
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


def upsert_partner_bank_account(body: dict, current_user: dict, db: Session) -> dict:
    """Logistics partner submits or updates their payout bank account."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required.")
    partner = _get_partner_for_user(current_user, db)
    partner_id = int(cast(int, partner.id))

    record = db.query(LogisticsPartnerBankAccount).filter(
        LogisticsPartnerBankAccount.partner_id == partner_id
    ).first()
    is_new = record is None
    if is_new:
        record = LogisticsPartnerBankAccount(partner_id=partner_id)
        db.add(record)

    for field in ("beneficiary_name", "bank_name", "branch_name", "account_number",
                  "iban", "swift_code", "routing_number", "currency", "bank_country"):
        value = body.get(field)
        if value is not None:
            setattr(record, field, value)

    if not is_new and getattr(record, "verification_status", "pending") != "pending":
        setattr(record, "verification_status", "pending")
        setattr(record, "verification_note", "Resubmitted by partner — awaiting re-verification.")
        setattr(record, "provider", None)
        setattr(record, "provider_recipient_id", None)
        setattr(record, "provider_status", None)
        setattr(record, "provider_last_synced_at", None)
        setattr(record, "verified_at", None)
        setattr(record, "verified_by", None)

    db.commit()
    db.refresh(record)
    return {
        "ok": True,
        "id": record.id,
        "verification_status": record.verification_status,
        "message": "Bank account saved. Awaiting admin verification." if is_new else "Bank account updated. Awaiting re-verification.",
    }


def list_partner_documents(current_user: dict, db: Session) -> list:
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    docs = (
        db.query(LogisticsPartnerDocument)
        .filter(LogisticsPartnerDocument.partner_id == cast(int, partner.id))
        .order_by(LogisticsPartnerDocument.created_at.desc())
        .all()
    )
    return [_serialize_lp_doc(d) for d in docs]


async def upload_partner_document(
    file: UploadFile,
    document_type: str,
    document_name: str,
    expires_at_str: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    """Upload a KYC/compliance document for the authenticated logistics partner."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    if document_type not in ALLOWED_LP_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid document type. Allowed: {ALLOWED_LP_DOC_TYPES}")

    from infrastructure.utils.storage import storage as _storage
    from infrastructure.utils.file_validation import validate_upload_document
    from infrastructure.utils.constants import MAX_UPLOAD_SIZE_BYTES

    safe_name = os.path.basename(file.filename or "document.pdf")
    ext = os.path.splitext(safe_name)[1].lower() or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"lp_documents/{filename}"

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File size exceeds 10 MB limit")
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    validate_upload_document(contents, safe_name)
    url = _storage.save(key, contents, content_type=file.content_type)

    expires_at = None
    if expires_at_str:
        try:
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            pass

    partner = _get_partner_for_user(current_user["id"], db)
    doc = LogisticsPartnerDocument(
        partner_id=cast(int, partner.id),
        document_type=document_type,
        document_name=document_name or safe_name,
        file_url=url,
        status="pending",
        expires_at=expires_at,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _serialize_lp_doc(doc)


def delete_partner_document(doc_id: int, current_user: dict, db: Session) -> dict:
    """Delete a document — only allowed when status is pending or rejected."""
    if current_user.get("role") != "logistics_partner":
        raise HTTPException(status_code=403, detail="Logistics partner access required")
    partner = _get_partner_for_user(current_user["id"], db)
    doc = db.query(LogisticsPartnerDocument).filter(
        LogisticsPartnerDocument.id == doc_id,
        LogisticsPartnerDocument.partner_id == cast(int, partner.id),
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status in ("under_review", "approved"):
        raise HTTPException(status_code=409, detail="Cannot delete a document that is under review or approved")
    db.delete(doc)
    db.commit()
    return {"detail": "Document deleted"}
