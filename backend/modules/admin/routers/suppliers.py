"""Admin suppliers router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status, Request

from infrastructure.database.database import get_db
from sqlalchemy.orm import Session
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.suppliers.services.governance.admin_suppliers_service import (
    admin_get_supplier,
    admin_get_supplier_products,
    admin_list_suppliers,
    admin_resolve_supplier_slug,
)

router = APIRouter(prefix="/api/v1/admin/suppliers", tags=["admin", "suppliers"])


@router.get("/admin_suppliers_routes/health")
def health(_: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.profile.read"))
):
    """Liveness probe for this router."""
    return {"status": "ok", "router": "admin_suppliers_routes", "prefix": "/api/v1/admin"}


@router.get("")
def list_public_suppliers(
    request: Request,
    q: str | None = Query(None, min_length=1, max_length=200),
    names: str | None = Query(None, max_length=500),
    country: str | None = Query(None, min_length=2, max_length=10),
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.profile.read")),
):
    """List suppliers with keyset/cursor pagination."""
    return admin_list_suppliers(db, q, country, limit, cursor)


@router.get("/resolve/{slug}")
def resolve_public_supplier_slug(
    slug: str,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.profile.read")),
):
    """Resolve a supplier by slug."""
    return admin_resolve_supplier_slug(db, slug)


@router.get("/{supplier_id}")
def get_public_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.profile.read")),
):
    """Get a supplier by ID."""
    return admin_get_supplier(db, supplier_id)


@router.get("/{supplier_id}/products")
def get_supplier_products_public(
    supplier_id: int,
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    db: Session = Depends(get_db),
    _admin: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.products.manage")),
):
    """List supplier products with keyset/cursor pagination."""
    return admin_get_supplier_products(db, supplier_id, limit, cursor)


@router.get("/public_suppliers_routes/health")
def health_public(_: dict = Depends(require_admin),
    _rf_gate: None = Depends(require_feature("suppliers.profile.read"))
):
    """Liveness probe for public suppliers routes."""
    return {"status": "ok", "router": "public_suppliers_routes", "prefix": "/api/v1/admin"}
