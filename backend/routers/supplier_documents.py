"""Supplier documents (KYC) sub-router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.database import get_db
from models import SupplierDocument, SupplierProfile, User
from db.schemas import SupplierDocumentOut
from utils.dependencies import get_current_user, require_admin, require_supplier

router = APIRouter()


@router.get("", response_model=list[SupplierDocumentOut])
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


@router.get("/all", response_model=list[SupplierDocumentOut])
def list_all_documents(
    status_filter: str | None = Query(None),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    q = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)  # noqa: E712
    if status_filter:
        q = q.filter(SupplierDocument.status == status_filter)
    return q.order_by(SupplierDocument.id.desc()).all()


@router.put("/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str,
    note: str | None = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    doc = db.query(SupplierDocument).filter(SupplierDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.status = new_status
    doc.review_note = note
    doc.reviewed_by = admin_user.id
    db.commit()
    return {"message": "Reviewed", "status": new_status}
