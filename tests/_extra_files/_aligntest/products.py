"""Public product router (LAYER 2).

Endpoint declarations only. Reads are delegated to
``controllers.products_controller`` (the existing catalogue read/query
controller) and every write to ``controllers.catalog.product_controller``,
which owns the service calls.

Previously this file performed ``db.query`` / ``db.add`` / ``db.commit``
inline (audit LC1 + W1: 6 session writes) and built ``Product`` instances by
hand from an unvalidated dict — allowing mass-assignment of trust flags such
as ``is_verified`` and ``is_approved``.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from controllers.catalog import product_controller as catalog_ctrl
from controllers.products_controller import (
    _bump_product_cache_version,
)
from controllers.products_controller import (
    get_product as get_product_controller,
)
from controllers.products_controller import (
    get_product_by_barcode as get_product_by_barcode_controller,
)
from controllers.products_controller import (
    get_products as get_products_controller,
)
from controllers.products_controller import (
    get_supplier_names as get_supplier_names_controller,
)
from data.db import get_db
import structlog
logger = structlog.get_logger(__name__)

router = APIRouter()


def _require_product_manager(current_user: dict = Depends(get_current_user)) -> dict:
    """Allow only admins and suppliers to mutate the catalogue."""
    if str(current_user.get("role") or "").lower() not in {"admin", "supplier"}:
        raise HTTPException(status_code=403, detail="Supplier or admin access required")
    return current_user


@router.get("")
@router.get("/")
async def list_products(
    request: Request,
    response: Response,
    q: str | None = None,
    category: str | None = None,
    subcategory: str | None = None,
    brand: str | None = None,
    brands: str | None = None,
    color: str | None = None,
    region: str | None = None,
    supplier: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    new_arrivals: bool = False,
    best_sellers: bool = False,
    trending: bool = False,
    in_stock: bool = False,
    min_discount: int | None = None,
    deals: bool = False,
    sort: str | None = None,
    sale_id: int | None = None,
    has_video: bool = False,
    limit: int = Query(24, ge=1, le=100),
    offset: int = Query(0, ge=0),
    attributes: str | None = None,
    db: Session = Depends(get_db),
) -> Any:
    """Browse the public catalogue with filters, sorting and pagination."""
    resolved_region = region or getattr(request.state, "country_code", None)
    resolved_country = getattr(request.state, "country_code", None)
    return get_products_controller(
        db=db,
        response=response,
        q=q,
        category=category,
        subcategory=subcategory,
        brand=brand,
        brands=brands,
        color=color,
        region=resolved_region,
        supplier=supplier,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        max_rating=max_rating,
        new_arrivals=new_arrivals,
        best_sellers=best_sellers,
        trending=trending,
        in_stock=in_stock,
        min_discount=min_discount,
        deals=deals,
        sort=sort,
        sale_id=sale_id,
        limit=limit,
        offset=offset,
        country_code=resolved_country,
        has_video=has_video,
        attributes=attributes,
    )


@router.get("/suppliers", response_model=list)
async def list_product_suppliers(db: Session = Depends(get_db)) -> Any:
    """List the distinct supplier names present in the catalogue."""
    return get_supplier_names_controller(db)


@router.get("/barcode/{code}")
async def get_product_by_barcode(code: str, db: Session = Depends(get_db)) -> Any:
    """Resolve a barcode to its product detail payload."""
    product = get_product_by_barcode_controller(code, db)
    return get_product_controller(int(product.id), db)


@router.get("/h/{slug_hash}")
async def get_product_by_hash(slug_hash: str, db: Session = Depends(get_db)) -> Any:
    """Resolve a short share-link hash to its product detail payload."""
    product = catalog_ctrl.get_product_by_slug_hash_or_404(db, slug_hash)
    return get_product_controller(int(product.id), db)


@router.get("/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)) -> Any:
    """Fetch a single product detail payload."""
    return get_product_controller(product_id, db)


@router.post("")
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: dict,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
) -> Any:
    """Create a product (admin or supplier)."""
    product = catalog_ctrl.create_product(db, payload, current_user)
    _bump_product_cache_version()
    return product


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    payload: dict,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
) -> Any:
    """Update a product the caller owns (or any product, for admins)."""
    product = catalog_ctrl.update_product_as_manager(
        db, product_id, payload, current_user
    )
    _bump_product_cache_version()
    return product


@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: int,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
) -> dict:
    """Soft-delete a product the caller owns (or any product, for admins)."""
    catalog_ctrl.soft_delete_product(db, product_id, current_user)
    _bump_product_cache_version()
    return {"message": "Product deactivated"}
