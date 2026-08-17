"""Auto-migrated service logic from routers/supplier_documents.py."""
from __future__ import annotations

from __future__ import annotations

from fastapi import Depends, HTTPException, Query

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import SupplierDocumentOut

from models import SupplierDocument, SupplierProfile, User

from infrastructure.utils.dependencies import require_admin, require_supplier

def list_my_documents(
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return (
        db.query(SupplierDocument)
        .filter(SupplierDocument.supplier_id == profile.id, SupplierDocument.is_deleted == False)  # noqa: E712
        .order_by(SupplierDocument.id.desc())
        .all()
    )

def list_all_documents(status_filter: str | None, _: User, db: Session):
    q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.filter(SupplierDocument.status == status_filter)
    return q.order_by(SupplierDocument.id.desc()).all()

def review_document(document_id: int, new_status: str, note: str | None, admin_user: User, db: Session):
    doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = new_status
    doc.review_note = note
    doc.reviewed_by = admin_user.id
    db.commit()
    return {"message": "Reviewed", "status": new_status}


