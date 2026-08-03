"""
Public Suppliers Router — unauthenticated customer-facing supplier endpoints.

GET /suppliers              — list active, verified suppliers (discovery)
GET /suppliers/{id}         — full public supplier profile
GET /suppliers/{id}/products — paginated products by this supplier
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from data.db import get_db
import controllers.supplier_controller as ctrl

router = APIRouter()


@router.get("")
def list_public_suppliers(
    request: Request,
    q: str | None = Query(None, min_length=1, max_length=200),
    names: str | None = Query(None, max_length=500),
    country: str | None = Query(None, min_length=2, max_length=10),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return verified/active suppliers for customer discovery."""
    resolved_country = (
        country
        or request.headers.get("X-Country-Code")
        or getattr(request.state, "country_code", None)
    )
    return ctrl.list_public_suppliers(
        q=q,
        names=names,
        country=resolved_country,
        limit=limit,
        offset=offset,
        db=db,
    )


@router.get("/resolve/{slug}")
def resolve_public_supplier_slug(
    slug: str,
    db: Session = Depends(get_db),
):
    """Resolve a human-friendly supplier slug from username or store name."""
    return ctrl.resolve_public_supplier_slug(slug=slug, db=db)


@router.get("/{supplier_id}")
def get_public_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
):
    """Return the customer-facing profile of one supplier."""
    return ctrl.get_public_supplier_profile(supplier_id=supplier_id, db=db)


@router.get("/{supplier_id}/products")
def get_supplier_products_public(
    supplier_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Return paginated active products sold by the given supplier."""
    return ctrl.get_public_supplier_products(
        supplier_id=supplier_id, limit=limit, offset=offset, db=db
    )

