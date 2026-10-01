"""Suppliers router for customer module — thin delegating to domain services."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from domains.suppliers.ports import list_public_suppliers
from infrastructure.database.database import get_db
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/suppliers", tags=["customer", "suppliers"])


@router.get("/products/suppliers", status_code=200)
def list_product_suppliers(
    q: str | None = Query(None, description="Search query"),
    country: str | None = Query(None, description="Filter by country code"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size
    result = list_public_suppliers(
        db=db,
        q=q,
        country=country,
        limit=page_size,
        offset=offset,
    )
    return {
        "items": result["items"],
        "total": result["total"],
        "page": page,
        "size": page_size,
    }
