"""Suppliers domain — KYC document service (keyset pagination)."""
from __future__ import annotations

from sqlalchemy import or_
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierDocument
from infrastructure.utils.pagination import keyset_offset_window


def list_my_documents(
    db: Session,
    supplier_id: int,
    offset: int = 0,
    limit: int = 50,
    status: str | None = None,
    doc_type: str | None = None,
) -> dict:
    """Adoption-layer supplier's own document list using keyset_offset_window."""
    query = db.query(SupplierDocument).filter(
        SupplierDocument.supplier_id == supplier_id,
        SupplierDocument.is_deleted == False,
    )
    if status:
        query = query.filter(SupplierDocument.status == status)
    if doc_type:
        query = query.filter(SupplierDocument.doc_type == doc_type)
    items = keyset_offset_window(
        query,
        sort_keys=[(SupplierDocument.created_at, "desc"), (SupplierDocument.id, "desc")],
        offset=offset,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": d.id,
                "supplier_id": d.supplier_id,
                "doc_type": d.doc_type,
                "document_name": d.document_name,
                "file_url": d.file_url,
                "status": d.status,
                "verified": d.verified,
                "expires_at": d.expires_at.isoformat() if d.expires_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in items
        ],
        "count": len(items),
    }


def list_supplier_documents(
    db: Session,
    offset: int = 0,
    limit: int = 50,
    status: str | None = None,
    supplier_id: int | None = None,
) -> dict:
    """Adoption-layer admin document list using keyset_offset_window."""
    query = db.query(SupplierDocument).filter(SupplierDocument.is_deleted == False)
    if status:
        query = query.filter(SupplierDocument.status == status)
    if supplier_id is not None:
        query = query.filter(SupplierDocument.supplier_id == supplier_id)
    items = keyset_offset_window(
        query,
        sort_keys=[(SupplierDocument.created_at, "desc"), (SupplierDocument.id, "desc")],
        offset=offset,
        limit=limit,
    )
    return {
        "items": [
            {
                "id": d.id,
                "supplier_id": d.supplier_id,
                "doc_type": d.doc_type,
                "document_name": d.document_name,
                "file_url": d.file_url,
                "status": d.status,
                "verified": d.verified,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in items
        ],
        "count": len(items),
    }
