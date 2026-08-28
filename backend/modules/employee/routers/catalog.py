"""Employee catalog router — read-only catalog access for staff.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from domains.catalog.services.categories.category_service import list_categories
from domains.catalog.services.products.products_service import (
    get_product,
    get_products,
    get_products_health,
)
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_employee
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/employee/catalog", tags=["employee", "catalog"])


@router.get("/products", status_code=200)
def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
    in_stock: bool = Query(False),
    sort: str | None = Query(None),
    country_code: str | None = Query(None),
    _: None = Depends(require_feature("catalog.list")),
    _staff: dict = Depends(require_employee),
    db: Session = Depends(get_db),
):
    products, total = get_products(
        db,
        request,
        category=category,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        in_stock=in_stock,
        sort=sort,
        limit=page_size,
        offset=(page - 1) * page_size,
        country_code=country_code,
    )
    return {"items": products, "total": total, "page": page, "size": page_size}


@router.get("/products/{product_id}", status_code=200)
def get_product_detail(
    product_id: int,
    _: None = Depends(require_feature("catalog.read")),
    _staff: dict = Depends(require_employee),
    db: Session = Depends(get_db),
):
    return get_product(product_id, db)


@router.get("/categories", status_code=200)
def list_categories_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    parent_id: int | None = Query(None),
    country_code: str | None = Query(None),
    _: None = Depends(require_feature("catalog.list")),
    _staff: dict = Depends(require_employee),
    db: Session = Depends(get_db),
):
    items, total = list_categories(
        db,
        active_only=False,
        parent_id=parent_id,
        country_code=country_code,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [
            {
                "id": c.id,
                "slug": getattr(c, "slug", None),
                "name": getattr(c, "name", None),
                "parent_id": getattr(c, "parent_id", None),
                "sort_order": getattr(c, "sort_order", 0),
                "country_code": getattr(c, "country_code", None),
            }
            for c in items
        ],
        "total": total,
        "page": page,
        "size": page_size,
    }


@router.get("/health", status_code=200)
def catalog_health(
    _: None = Depends(require_feature("catalog.list")),
    _staff: dict = Depends(require_employee),
):
    """Catalog service health (read-only diagnostic)."""
    return get_products_health()
