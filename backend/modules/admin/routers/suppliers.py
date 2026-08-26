"""Admin suppliers router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .documents import router as documents_router
from infrastructure.database.database import get_db
from sqlalchemy.orm import Session
import domains.suppliers.services.supplier_controller as ctrl
import logging as _l; _l.getLogger(__name__).warning("skip documents_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip products_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip suppliers_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/suppliers", tags=["admin", "suppliers"])

@router.get("/admin_suppliers_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_suppliers_routes", "prefix": "/api/v1/admin"}



@router.get("")
def list_public_suppliers(
    request: Request,
    q: str | None = Query(None, min_length=1, max_length=200),
    names: str | None = Query(None, max_length=500),
    country: str | None = Query(None, min_length=2, max_length=10),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),


@router.get("/resolve/{slug}")
def resolve_public_supplier_slug(
    slug: str,
    db: Session = Depends(get_db),


@router.get("/{supplier_id}")
def get_public_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),


@router.get("/{supplier_id}/products")
def get_supplier_products_public(
    supplier_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),


@router.get("/public_suppliers_routes/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "public_suppliers_routes", "prefix": "/api/v1/suppliers"}


