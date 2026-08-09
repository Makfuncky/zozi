"""Supplier document (KYC) write operations.

Owns the DB write for reviewing a supplier document. Routers must not
mutate the session directly for this operation.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import SupplierDocument
import structlog
logger = structlog.get_logger(__name__)


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
