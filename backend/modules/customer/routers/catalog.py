"""Customer catalog router — public, customer-facing catalog browse/search.

Per ARCHITECTURE_DIAGRAM.md §3, this is a thin per-actor router:
auth context (optional) + require_feature(...) + one service call.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from domains.catalog.services.categories.category_service import list_categories
from domains.catalog.services.products.products_service import (
    autocomplete_products,
    get_product,
    get_products,
    get_recommended_products,
)
from domains.catalog.services.search import search_products
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user_optional
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/catalog", tags=["customer", "catalog"])


@router.get("/products", status_code=200)
def list_products(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = Query(None, description="Category slug or name"),
    subcategory: str | None = Query(None),
    brand: str | None = Query(None),
    color: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    min_rating: float | None = Query(None, ge=0, le=5),
    in_stock: bool = Query(False),
    sort: str | None = Query(None, description="price_asc|price_desc|rating|bestseller|discount"),
    country_code: str | None = Query(None, description="ISO country code"),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    limit = page_size
    offset = (page - 1) * page_size
    products, total = get_products(
        db,
        request,
        category=category,
        subcategory=subcategory,
        brand=brand,
        color=color,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        in_stock=in_stock,
        sort=sort,
        limit=limit,
        offset=offset,
        country_code=country_code,
    )
    return {
        "items": products,
        "total": total,
        "page": page,
        "size": page_size,
    }


@router.get("/products/{product_id}", status_code=200)
def get_product_detail(
    product_id: int,
    _: None = Depends(require_feature("catalog.read")),
    db: Session = Depends(get_db),
):
    return get_product(product_id, db)


@router.get("/categories", status_code=200)
def list_categories_route(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    parent_id: int | None = Query(None),
    country_code: str | None = Query(None, description="ISO country code"),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    items, total = list_categories(
        db,
        active_only=True,
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


@router.get("/search", status_code=200)
def search_products_route(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country_code: str | None = Query(None),
    category: str | None = Query(None),
    brand: str | None = Query(None),
    min_price: float | None = Query(None, ge=0),
    max_price: float | None = Query(None, ge=0),
    sort: str | None = Query(None),
    in_stock: bool = Query(False),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    """Hybrid search: AI-powered semantic search with structured filters."""
    filters: dict = {
        "country_code": country_code,
        "category": category,
        "brand": brand,
        "min_price": min_price,
        "max_price": max_price,
        "sort": sort,
        "in_stock": in_stock,
    }
    filters = {k: v for k, v in filters.items() if v is not None}
    result = search_products(query=q, filters=filters, limit=page_size)
    return {
        "items": result.get("results", result.get("items", [])),
        "total": result.get("total", 0),
        "query": q,
        "page": page,
        "size": page_size,
    }


@router.get("/autocomplete", status_code=200)
def autocomplete(
    q: str = Query(..., min_length=1, max_length=200),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    return {"suggestions": autocomplete_products(q, db)}


@router.get("/recommended", status_code=200)
def recommended(
    limit: int = Query(20, ge=1, le=50),
    current_user: dict | None = Depends(get_current_user_optional),
    _: None = Depends(require_feature("catalog.list")),
    db: Session = Depends(get_db),
):
    products = get_recommended_products(current_user, limit, db)
    return {"items": products, "total": len(products)}
