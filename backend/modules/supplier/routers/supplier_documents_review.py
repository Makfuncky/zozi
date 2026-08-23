"""Supplier documents (KYC) sub-router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.models.user import User
from infrastructure.database.schemas import SupplierDocumentOut
from infrastructure.utils.dependencies import get_current_user, require_admin, require_supplier
from domains.suppliers.services.supplier_document_service import list_all_supplier_documents
from domains.suppliers.services.supplier_document_service import list_supplier_documents
from domains.suppliers.services.supplier_document_service import review_supplier_document
from domains.suppliers.services.supplier_profile_write_service import get_supplier_profile

router = APIRouter(prefix="/api/v1/supplier")


@router.get("", response_model=list[SupplierDocumentOut])
def list_my_documents(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = get_supplier_profile(current_user, db)
    return list_supplier_documents(db, profile.id)


@router.get("/all", response_model=list[SupplierDocumentOut])
def list_all_documents(status_filter: str | None = Query(None), _: User = Depends(require_admin), db: Session = Depends(get_db)):
    return list_all_supplier_documents(db, status_filter)


@router.put("/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str,
    note: str | None = None,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return review_supplier_document(db, document_id, new_status, note, admin_user.id)
