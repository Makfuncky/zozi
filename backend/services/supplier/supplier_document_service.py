"""Supplier document (KYC) write operations.

Owns the DB write for reviewing a supplier document. Routers must not
mutate the session directly for this operation.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models import SupplierDocument
import structlog
logger = structlog.get_logger(__name__)


def list_supplier_documents(db: Session, supplier_id: int) -> list[SupplierDocument]:
    """Return non-deleted KYC documents for a supplier, newest first."""
    return (
        db.query(SupplierDocument)
        .filter(SupplierDocument.supplier_id == supplier_id, SupplierDocument.is_deleted == False)  # noqa: E712
        .order_by(SupplierDocument.id.desc())
        .all()
    )


def list_all_supplier_documents(db: Session, status_filter: str | None = None) -> list[SupplierDocument]:
    """Return all non-deleted supplier documents, optionally filtered by status."""
    q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.filter(SupplierDocument.status == status_filter)
    return q.order_by(SupplierDocument.id.desc()).all()


def review_supplier_document(
    db: Session,
    document_id: int,
    new_status: str,
    note: str | None,
    admin_user_id: int,
) -> dict:
    doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = new_status
    doc.review_note = note
    doc.reviewed_by = admin_user_id
    db.commit()
    return {"message": "Reviewed", "status": new_status}
