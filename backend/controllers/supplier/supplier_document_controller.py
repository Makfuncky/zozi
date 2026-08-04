"""
Supplier Document (Papers Verification) Controller.
Handles supplier KYC document submission, admin review, and expiry tracking.
"""
from __future__ import annotations
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, cast

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models import SupplierDocument, SupplierProfile, User, Notification
from utils.audit_log import AuditAction, audit_log
from services.write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
    delete_only,
)

logger = logging.getLogger(__name__)
_utcnow = lambda: datetime.now(timezone.utc).replace(tzinfo=None)  # noqa: E731


def _build_list_page_payload(items: list[dict], total: int, *, offset: int = 0, page_size: Optional[int] = None) -> dict:
    resolved_page_size = page_size if page_size is not None else len(items)
    if resolved_page_size <= 0:
        resolved_page_size = max(total, 1)
    return {
        "data": items,
        "total": total,
        "page": (offset // resolved_page_size) + 1,
        "pageSize": resolved_page_size,
    }

ALLOWED_DOC_TYPES = (
    "trade_license", "vat_certificate", "passport",
    "company_registration", "bank_statement", "other",
)
ALLOWED_STATUSES = ("pending", "under_review", "approved", "rejected", "expired")


def _serialize_doc(doc: SupplierDocument) -> dict:
    expires_at = cast(Optional[datetime], getattr(doc, "expires_at", None))
    reviewed_at = cast(Optional[datetime], getattr(doc, "reviewed_at", None))
    created_at = cast(Optional[datetime], getattr(doc, "created_at", None))
    updated_at = cast(Optional[datetime], getattr(doc, "updated_at", None))
    return {
        "id": doc.id,
        "supplier_id": doc.supplier_id,
        "document_type": doc.doc_type,
        "document_name": getattr(doc, "document_name", None),
        "file_url": doc.file_url,
        "status": getattr(doc, "status", None),
        "expires_at": expires_at.isoformat() if expires_at else None,
        "review_note": getattr(doc, "review_note", None),
        "reviewed_by": doc.reviewed_by,
        "reviewed_at": reviewed_at.isoformat() if reviewed_at else None,
        "created_at": created_at.isoformat() if created_at else None,
        "updated_at": updated_at.isoformat() if updated_at else None,
    }


# â”€â”€ Supplier: submit documents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def _get_supplier_profile_id(current_user: dict, db: Session) -> int:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user["id"]).first()
    return profile.id if profile else current_user["id"]


def _documents_query_for_owner(current_user: dict, db: Session):
    profile_id = _get_supplier_profile_id(current_user, db)
    return db.query(SupplierDocument).filter(
        SupplierDocument.supplier_id.in_([profile_id, current_user["id"]])
    )


def list_my_documents(current_user: dict, db: Session, limit: Optional[int] = None, offset: int = 0) -> dict:
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")
    query = _documents_query_for_owner(current_user, db)
    total = query.count()
    docs_query = query.order_by(desc(SupplierDocument.created_at), SupplierDocument.id.desc())
    if offset:
        docs_query = docs_query.offset(offset)
    if limit is not None:
        docs_query = docs_query.limit(limit)
    docs = docs_query.all()
    serialized = [_serialize_doc(d) for d in docs]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=limit if limit is not None else len(serialized))


def submit_document(data: dict, current_user: dict, db: Session) -> dict:
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")

    doc_type = data.get("document_type", "other")
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid document type. Allowed: {ALLOWED_DOC_TYPES}")

    file_url = data.get("file_url", "").strip()
    doc_name = data.get("document_name", "").strip()
    if not file_url or not doc_name:
        raise HTTPException(status_code=422, detail="file_url and document_name are required")

    expires_at = None
    if data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")).replace(tzinfo=None)
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid expires_at date format")

    supplier_profile_id = _get_supplier_profile_id(current_user, db)
    doc = SupplierDocument(
        supplier_id=supplier_profile_id,
        doc_type=doc_type,
        document_name=doc_name,
        file_url=file_url,
        status="pending",
        expires_at=expires_at,
    )
    add_and_flush(db, doc)
    commit_and_refresh(db, doc)
    return _serialize_doc(doc)


async def upload_and_submit_document(
    file: UploadFile,
    document_type: str,
    document_name: str,
    expires_at_str: Optional[str],
    current_user: dict,
    db: Session,
) -> dict:
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")

    if document_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid document type. Allowed: {ALLOWED_DOC_TYPES}")

    from services.storage import storage as _storage
    from utils.file_validation import validate_upload_document
    from utils.constants import MAX_UPLOAD_SIZE_BYTES

    safe_name = os.path.basename(file.filename or "document.pdf")
    ext = os.path.splitext(safe_name)[1].lower() or ".pdf"
    filename = f"{uuid.uuid4().hex}{ext}"
    key = f"supplier_documents/{filename}"

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

    supplier_profile_id = _get_supplier_profile_id(current_user, db)
    doc = SupplierDocument(
        supplier_id=supplier_profile_id,
        doc_type=document_type,
        document_name=document_name or file.filename or "document",
        file_url=url,
        status="pending",
        expires_at=expires_at,
    )
    add_and_flush(db, doc)
    commit_and_refresh(db, doc)
    return _serialize_doc(doc)


def delete_my_document(doc_id: int, current_user: dict, db: Session) -> dict:
    if current_user.get("role") not in ("supplier", "admin"):
        raise HTTPException(status_code=403, detail="Supplier access required")

    doc = db.query(SupplierDocument).filter(SupplierDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if current_user.get("role") == "supplier":
        owner_id = _get_supplier_profile_id(current_user, db)
        if doc.supplier_id not in (owner_id, current_user["id"]):
            raise HTTPException(status_code=403, detail="Access denied")

    if doc.status in ("under_review", "approved"):
        raise HTTPException(status_code=409, detail="Cannot delete a document that is under review or approved")

    delete_only(db, doc)
    commit_only(db)
    return {"detail": "Document deleted"}


# â”€â”€ Admin: review documents â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def admin_list_documents(
    current_user: dict,
    db: Session,
    supplier_id: Optional[int] = None,
    status: Optional[str] = None,
    doc_type: Optional[str] = None,
    limit: Optional[int] = None,
    offset: int = 0,
) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Admin access required")

    q = db.query(SupplierDocument)
    if supplier_id:
        q = q.filter(SupplierDocument.supplier_id == supplier_id)
    if status:
        q = q.filter(SupplierDocument.status == status)
    if doc_type:
        q = q.filter(SupplierDocument.document_type == doc_type)
    total = q.count()
    docs_query = q.order_by(desc(SupplierDocument.created_at), SupplierDocument.id.desc())
    if offset:
        docs_query = docs_query.offset(offset)
    if limit is not None:
        docs_query = docs_query.limit(limit)
    docs = docs_query.all()
    serialized = [_serialize_doc(d) for d in docs]
    return _build_list_page_payload(serialized, total, offset=offset, page_size=limit if limit is not None else len(serialized))


def admin_review_document(
    doc_id: int,
    data: dict,
    current_user: dict,
    db: Session,
) -> dict:
    role = current_user.get("role")
    if role not in ("admin", "sub_admin", "moderator"):
        raise HTTPException(status_code=403, detail="Admin access required")

    doc = db.query(SupplierDocument).filter(SupplierDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    new_status = data.get("status")
    if new_status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=422, detail=f"Invalid status. Allowed: {ALLOWED_STATUSES}")

    setattr(doc, "status", new_status)
    setattr(doc, "review_note", data.get("review_note"))
    setattr(doc, "reviewed_by", current_user["id"])
    setattr(doc, "reviewed_at", _utcnow())
    setattr(doc, "updated_at", _utcnow())

    # Update supplier profile verified_documents list if approved
    if new_status == "approved":
        profile = db.query(SupplierProfile).filter(
            SupplierProfile.id == doc.supplier_id
        ).first()
        if not profile:
            profile = db.query(SupplierProfile).filter(
                SupplierProfile.user_id == doc.supplier_id
            ).first()
        if profile:
            verified_documents = cast(Optional[str], getattr(profile, "verified_documents", None))
            try:
                existing = json.loads(verified_documents or "[]")
            except (ValueError, TypeError):
                existing = []
            entry = {"doc_id": doc.id, "type": doc.document_type, "url": doc.file_url}
            if not any(e.get("doc_id") == doc.id for e in existing):
                existing.append(entry)
            setattr(profile, "verified_documents", json.dumps(existing))
            # Auto-advance verification_status once first doc is approved
            if profile.verification_status in (None, "pending", "documents_submitted"):
                setattr(profile, "verification_status", "verified")
            setattr(profile, "updated_at", _utcnow())

    commit_and_refresh(db, doc)

    # In-app notification to supplier
    human_type = doc.document_type.replace("_", " ").title()
    if new_status == "approved":
        notif_title = f"Document Approved: {human_type}"
        notif_msg = f"Your {human_type} has been verified and approved."
    elif new_status == "rejected":
        note = doc.review_note or "No reason provided."
        notif_title = f"Document Rejected: {human_type}"
        notif_msg = f"Your {human_type} was rejected. Reason: {note}"
    else:
        notif_title = notif_msg = None

    if notif_title:
        add_and_flush(db, Notification(
            user_id=doc.supplier_id,
            type="supplier_document",
            title=notif_title,
            message=notif_msg,
            link="/supplier/documents",
        ))
        commit_only(db)

    # Email notification to supplier â€” non-blocking
    supplier_user = db.query(User).filter(User.id == doc.supplier_id).first()
    supplier_email = cast(Optional[str], getattr(supplier_user, "email", None)) if supplier_user else None
    if supplier_user and supplier_email and notif_title:
        try:
            from utils.email_service import send_email
            html_body = f"""
            <h2 style="font-family:Arial,sans-serif;color:#1f2937">{notif_title}</h2>
            <p style="font-family:Arial,sans-serif;color:#374151">{notif_msg}</p>
            <p style="font-family:Arial,sans-serif;color:#6b7280">
              Log in to your <a href="/supplier/documents">supplier portal</a> to view details.
            </p>"""
            send_email(to=supplier_email, subject=notif_title, html=html_body)
        except Exception as exc:
            logger.warning("Supplier document email failed (non-fatal): %s", exc)

    audit_log(
        db=db,
        user_id=current_user["id"],
        username=current_user.get("username", ""),
        user_role=role,
        action=AuditAction.SUPPLIER_VERIFIED if new_status == "approved" else AuditAction.SUPPLIER_REJECTED,
        resource_type="supplier_document",
        resource_id=str(doc.id),
        details={"supplier_id": doc.supplier_id, "status": new_status},
    )
    return _serialize_doc(doc)

