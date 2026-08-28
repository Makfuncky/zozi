"""Supplier compliance service — KYC document status and audit trail."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile, SupplierDocument
from domains.audit.ports import audit_log, AuditAction

logger = logging.getLogger(__name__)

KYC_PENDING = "pending"
KYC_APPROVED = "approved"
KYC_REJECTED = "rejected"
KYC_EXPIRED = "expired"
KYC_REVOKED = "revoked"


def get_kyc_status(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return KYC document status for a supplier.

    Aggregates document states to determine overall KYC compliance.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    documents = db.query(SupplierDocument).filter(
        SupplierDocument.supplier_id == supplier_id,
        SupplierDocument.is_deleted == False,
    ).all()

    doc_summary = []
    approved_count = 0
    pending_count = 0
    rejected_count = 0
    expired_count = 0

    for doc in documents:
        status = doc.status or KYC_PENDING
        is_expired = doc.expires_at is not None and doc.expires_at < now

        if is_expired and status == KYC_APPROVED:
            status = KYC_EXPIRED

        if status == KYC_APPROVED:
            approved_count += 1
        elif status == KYC_PENDING:
            pending_count += 1
        elif status == KYC_REJECTED:
            rejected_count += 1
        elif status == KYC_EXPIRED:
            expired_count += 1

        doc_summary.append({
            "id": doc.id,
            "doc_type": doc.doc_type,
            "document_name": doc.document_name,
            "status": status,
            "verified": doc.verified,
            "expires_at": doc.expires_at.isoformat() if doc.expires_at else None,
            "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        })

    if rejected_count > 0:
        overall_status = KYC_REJECTED
    elif pending_count > 0:
        overall_status = KYC_PENDING
    elif expired_count > 0:
        overall_status = KYC_EXPIRED
    elif approved_count > 0:
        overall_status = KYC_APPROVED
    else:
        overall_status = KYC_PENDING

    return {
        "supplier_id": supplier_id,
        "overall_status": overall_status,
        "is_compliant": overall_status == KYC_APPROVED,
        "documents": {
            "total": len(documents),
            "approved": approved_count,
            "pending": pending_count,
            "rejected": rejected_count,
            "expired": expired_count,
            "items": doc_summary,
        },
        "checked_at": now.isoformat(),
    }


def get_audit_trail(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return audit trail entries for a supplier.

    Retrieves audit log entries related to this supplier's actions and
    administrative reviews.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    try:
        entries = audit_log(
            db=db,
            action=AuditAction.VIEW,
            resource_type="supplier",
            resource_id=supplier_id,
            details={"query": "audit_trail"},
        )
    except Exception:
        logger.warning("audit_log query failed for supplier %s", supplier_id)
        entries = None

    trail = []
    if entries:
        if isinstance(entries, list):
            for entry in entries:
                trail.append({
                    "id": getattr(entry, "id", None),
                    "action": getattr(entry, "action", None),
                    "user_id": getattr(entry, "user_id", None),
                    "resource_type": getattr(entry, "resource_type", None),
                    "resource_id": getattr(entry, "resource_id", None),
                    "details": getattr(entry, "details", None),
                    "created_at": getattr(entry, "created_at", None),
                })
        else:
            trail.append({
                "id": getattr(entries, "id", None),
                "action": getattr(entries, "action", None),
                "user_id": getattr(entries, "user_id", None),
                "resource_type": getattr(entries, "resource_type", None),
                "resource_id": getattr(entries, "resource_id", None),
                "details": getattr(entries, "details", None),
                "created_at": getattr(entries, "created_at", None),
            })

    return {
        "supplier_id": supplier_id,
        "entries": trail,
        "count": len(trail),
        "generated_at": now.isoformat(),
    }
