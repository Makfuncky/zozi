"""
Supplier Documents (KYC) Service
================================
Read/write helpers for the supplier KYC document endpoints.

This module owns the DB work that previously lived in ``routers/supplier/
supplier_documents.py`` so the router stays a thin delegator (layering: LC1/W1).
"""
from __future__ import annotations

from fastapi import HTTPException

from data.db import get_db_context
from data.models import SupplierDocument, SupplierProfile
from data.services_write_helpers import commit_only


def list_supplier_documents(user_id: int, skip: int = 0, limit: int = 20):
    """Return the non-deleted KYC documents owned by the supplier for ``user_id``."""
    with get_db_context() as db:
        profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Supplier profile not found")
        return (
            db.query(SupplierDocument)
            .filter(SupplierDocument.supplier_id == profile.id, SupplierDocument.is_deleted == False)
            .order_by(SupplierDocument.id.desc())
            .offset(skip).limit(limit)
            .all()
        )


def list_all_supplier_documents(
    status_filter=None,
    skip: int = 0,
    limit: int = 20,
):
    """Return every non-deleted supplier document, optionally filtered by status."""
    with get_db_context() as db:
        q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)
        if status_filter:
            q = q.filter(SupplierDocument.status == status_filter)
        return q.order_by(SupplierDocument.id.desc()).offset(skip).limit(limit).all()


def review_supplier_document(
    document_id: int,
    new_status: str,
    note,
    reviewer_id: int,
) -> dict:
    """Apply an admin review decision to a supplier document."""
    with get_db_context() as db:
        doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        doc.status = new_status
        doc.review_note = note
        doc.reviewed_by = reviewer_id
        commit_only(db)
        return {"message": "Reviewed", "status": new_status}
