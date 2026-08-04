"""Supplier documents (KYC) sub-router.

All DB work is delegated to ``services/supplier/supplier_documents_service.py``
so this router stays a thin delegator (layering: LC1/W1).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from data.dependencies_auth import get_current_user
from data.schemas import SupplierDocumentOut
from utils.dependencies import require_admin, require_supplier

from data.services_supplier_documents_service import (
    list_all_supplier_documents,
    list_supplier_documents,
    review_supplier_document,
)

from services.write_helpers import commit_only
router = APIRouter()


@router.get("", response_model=list[SupplierDocumentOut])
def list_my_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_supplier),
):
    return list_supplier_documents(current_user.id, skip=skip, limit=limit)


@router.get("/all", response_model=list[SupplierDocumentOut])
def list_all_documents(
    status_filter: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    _=Depends(require_admin),
):
    return list_all_supplier_documents(status_filter=status_filter, skip=skip, limit=limit)


@router.put("/{document_id}/review")
def review_document(
    document_id: int,
    new_status: str,
    note: str | None = None,
    admin_user=Depends(require_admin),
):
    return review_supplier_document(document_id, new_status, note, admin_user.id)
