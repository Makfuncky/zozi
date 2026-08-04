"""Product routes restored around the recovered public contract."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from services.catalog.products_read_service import get_all_products, get_product_by_id, search_products, get_product_categories
from services.catalog.categories_read_service import list_categories
from controllers.products_controller import (
    _bump_product_cache_version,
    get_product as get_product_controller,
    get_product_by_barcode as get_product_by_barcode_controller,
    get_products as get_products_controller,
    get_supplier_names as get_supplier_names_controller,
)
from data.db import get_db
from data.schemas import ProductSearchRequest
from services.catalog.products_write_service import (
    get_product_by_slug, get_product_by_id, get_product_by_slug_hash,
    create_product as svc_create_product, update_product as svc_update_product,
    deactivate_product as svc_deactivate_product,
)
from utils.slug import generate_slug, generate_slug_hash

router = APIRouter()


def _require_product_manager(current_user: dict = Depends(get_current_user)) -> dict:
    if str(current_user.get("role") or "").lower() not in {"admin", "supplier"}:
        raise HTTPException(status_code=403, detail="Supplier or admin access required")
    return current_user


def _unique_slug(name: str, db: Session) -> str:
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1
    while get_product_by_slug(db, slug) is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug


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
):
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


@router.post("/search")
async def search_products(
    request: Request,
    response: Response,
    search: ProductSearchRequest,
    db: Session = Depends(get_db),
):
    """Search products via POST body.

    Accepts a JSON payload mirroring the query-parameter filters of
    GET /api/v1/products.  Useful when the filter set is large or when
    clients prefer POST for complex / faceted search payloads.
    """
    resolved_country = getattr(request.state, "country_code", None)
    resolved_region = search.region or resolved_country
    return get_products_controller(
        db=db,
        response=response,
        q=search.q,
        category=search.category,
        subcategory=search.subcategory,
        brand=search.brand,
        brands=search.brands,
        color=search.color,
        region=resolved_region,
        supplier=search.supplier,
        min_price=search.min_price,
        max_price=search.max_price,
        min_rating=search.min_rating,
        max_rating=search.max_rating,
        new_arrivals=search.new_arrivals,
        best_sellers=search.best_sellers,
        trending=search.trending,
        in_stock=search.in_stock,
        min_discount=search.min_discount,
        deals=search.deals,
        sort=search.sort,
        sale_id=search.sale_id,
        limit=search.limit,
        offset=search.offset,
        country_code=resolved_country,
        has_video=search.has_video,
        attributes=search.attributes,
    )


@router.get("/suppliers")
async def list_product_suppliers(db: Session = Depends(get_db)):
    return get_supplier_names_controller(db)


@router.get("/barcode/{code}")
async def get_product_by_barcode(code: str, db: Session = Depends(get_db)):
    product = get_product_by_barcode_controller(code, db)
    return get_product_controller(int(product.id), db)


@router.get("/{product_id}")
async def get_product(product_id: int, db: Session = Depends(get_db)):
    return get_product_controller(product_id, db)


@router.get("/h/{slug_hash}")
async def get_product_by_hash(slug_hash: str, db: Session = Depends(get_db)):
    product = get_product_by_slug_hash(db, slug_hash)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return get_product_controller(int(product.id), db)


@router.post("")
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: dict,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
):
    supplier_id = payload.get("supplier_id")
    if str(current_user.get("role") or "").lower() != "admin":
        supplier_id = int(current_user["id"])
    elif supplier_id is None:
        supplier_id = int(current_user["id"])

    name = str(payload.get("name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Product name is required")

    product = svc_create_product(
        db,
        name=name,
        slug=slug,
        slug_hash=generate_slug_hash(name),
        description=payload.get("description"),
        short_description=payload.get("short_description"),
        sku=payload.get("sku"),
        price=payload.get("price") or 0,
        compare_price=payload.get("compare_price"),
        cost_price=payload.get("cost_price"),
        stock=payload.get("stock", payload.get("stock_quantity", 0)) or 0,
        low_stock_threshold=payload.get("low_stock_threshold", 5) or 5,
        weight=payload.get("weight"),
        dimensions=payload.get("dimensions"),
        image_url=payload.get("image_url"),
        images=payload.get("images"),
        category=payload.get("category"),
        category_id=payload.get("category_id"),
        tags=payload.get("tags"),
        attributes=payload.get("attributes"),
        supplier_id=int(supplier_id),
        is_active=bool(payload.get("is_active", True)),
        is_featured=bool(payload.get("is_featured", False)),
        is_digital=bool(payload.get("is_digital", False)),
        is_verified=bool(payload.get("is_verified", True)),
        moderation_status=str(payload.get("moderation_status") or "approved"),
        brand=payload.get("brand"),
        color=payload.get("color"),
        sizes=payload.get("sizes"),
        rating=float(payload.get("rating") or 0.0),
        meta_title=payload.get("meta_title"),
        meta_description=payload.get("meta_description"),
        is_approved=bool(payload.get("is_approved", True)),
        is_deleted=bool(payload.get("is_deleted", False)),
        country_code=current_user.get("country_code") or current_user.get("preferred_country") or None,
    )
    _bump_product_cache_version()
    return product


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    payload: dict,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if str(current_user.get("role") or "").lower() != "admin" and int(product.supplier_id or 0) != int(current_user["id"]):
        raise HTTPException(status_code=404, detail="Product not found or not yours")

    field_map = {
        "name": "name",
        "description": "description",
        "short_description": "short_description",
        "price": "price",
        "compare_price": "compare_price",
        "cost_price": "cost_price",
        "stock": "stock",
        "stock_quantity": "stock",
        "low_stock_threshold": "low_stock_threshold",
        "weight": "weight",
        "dimensions": "dimensions",
        "image_url": "image_url",
        "images": "images",
        "category": "category",
        "category_id": "category_id",
        "tags": "tags",
        "attributes": "attributes",
        "is_active": "is_active",
        "is_featured": "is_featured",
        "brand": "brand",
        "color": "color",
        "sizes": "sizes",
        "rating": "rating",
        "meta_title": "meta_title",
        "meta_description": "meta_description",
    }
    updates = {}
    for source_key, target_key in field_map.items():
        if source_key in payload:
            updates[target_key] = payload[source_key]
    if "name" in payload and payload["name"]:
        updates["slug"] = _unique_slug(str(payload["name"]), db)
    svc_update_product(db, product, updates)
    _bump_product_cache_version()
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
):
    product = get_product_by_id(db, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if str(current_user.get("role") or "").lower() != "admin" and int(product.supplier_id or 0) != int(current_user["id"]):
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    product.is_active = False
    product.is_deleted = True
    svc_deactivate_product(db, product)
    _bump_product_cache_version()
    return {"message": "Product deactivated"}

