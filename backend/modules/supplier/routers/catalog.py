"""Supplier catalog router — consolidated from 6 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/supplier/catalog", tags=["supplier", "catalog"])


# === From product_moderation.py ===
"""product moderation router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/product_moderation/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_moderation", "prefix": "/api/v1/product-moderation"}


# === From product_verification.py ===
"""product verification router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/product_verification/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_verification", "prefix": "/api/v1/product-verifications"}


# === From product_videos.py ===
"""product videos router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/product_videos/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "product_videos", "prefix": "/api/v1/product-videos"}


# === From products.py ===
"""Product routes restored around the recovered public contract."""

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from rbac import get_current_user
from domains.catalog.services.products.products_service import _bump_product_cache_version
from domains.catalog.services.products.products_service import get_product as get_product_controller
from domains.catalog.services.products.products_service import get_product_by_barcode as get_product_by_barcode_controller
from domains.catalog.services.products.products_service import get_products as get_products_controller
from domains.catalog.services.products.products_service import get_supplier_names as get_supplier_names_controller
from infrastructure.database.database import get_db
from domains.catalog.models.products import Product
from infrastructure.utils.slug import generate_slug, generate_slug_hash


def _require_product_manager(current_user: dict = Depends(get_current_user)) -> dict:
    if str(current_user.get("role") or "").lower() not in {"admin", "supplier"}:
        raise HTTPException(status_code=403, detail="Supplier or admin access required")
    return current_user


def _unique_slug(name: str, db: Session) -> str:
    base_slug = generate_slug(name)
    slug = base_slug
    counter = 1
    while db.query(Product).filter(Product.slug == slug).first() is not None:
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
    product = db.query(Product).filter(Product.slug_hash == slug_hash).first()
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

    product = Product(
        name=name,
        slug=_unique_slug(name, db),
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
    db.add(product)
    db.commit()
    db.refresh(product)
    _bump_product_cache_version()
    return product


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    payload: dict,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
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
    for source_key, target_key in field_map.items():
        if source_key in payload:
            setattr(product, target_key, payload[source_key])
    if "name" in payload and payload["name"]:
        product.slug = _unique_slug(str(payload["name"]), db)
    db.commit()
    db.refresh(product)
    _bump_product_cache_version()
    return product


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    current_user: dict = Depends(_require_product_manager),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if str(current_user.get("role") or "").lower() != "admin" and int(product.supplier_id or 0) != int(current_user["id"]):
        raise HTTPException(status_code=404, detail="Product not found or not yours")
    product.is_active = False
    product.is_deleted = True
    db.commit()
    _bump_product_cache_version()
    return {"message": "Product deactivated"}


# === From supplier_products.py ===
"""Supplier products sub-router."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.catalog.models.products import Product
from domains.suppliers.models.suppliers import SupplierProfile
from infrastructure.utils.storage import storage as _storage
from infrastructure.utils.config import settings
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.dependencies import require_supplier
from infrastructure.utils.file_validation import validate_upload_image
from infrastructure.utils.pagination import paginated_response


@router.get("")
def list_my_products(page: int = Query(1, ge=1), size: int = Query(20), current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return paginated_response(q, page, size)


@router.get("/{product_id}")
def get_supplier_product(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    """Get a single product by ID, verifying the supplier owns it."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    return product


@router.put("/{product_id}/discount")
def update_product_discount(
    product_id: int,
    payload: dict,
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Set or remove a discount on the supplier's product.

    Body:
      compare_price (float, optional): Original/compare-at price (set to show discount)
      discount_starts_at (str, optional): ISO datetime when discount begins
      discount_ends_at (str, optional): ISO datetime when discount ends
      clear (bool, optional): If true, clears the discount fields
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")

    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")

    # Clear discount
    if payload.get("clear"):
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
        db.commit()
        db.refresh(product)
        return {"status": "success", "message": "Discount cleared", "product_id": product.id}

    # Set compare_price (original price, showing the discount)
    if "compare_price" in payload:
        cp = payload["compare_price"]
        product.compare_price = float(cp) if cp is not None else None

    # Set discount schedule
    if "discount_starts_at" in payload:
        raw = payload["discount_starts_at"]
        try:
            product.discount_starts_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_starts_at format: {raw}")

    if "discount_ends_at" in payload:
        raw = payload["discount_ends_at"]
        try:
            product.discount_ends_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_ends_at format: {raw}")

    db.commit()
    db.refresh(product)

    discount_pct = 0
    now = utcnow()
    if product.compare_price and product.price and float(product.compare_price) > 0:
        discount_pct = round(
            (1 - float(product.price) / float(product.compare_price)) * 100, 1
        )

    is_active = bool(product.compare_price and product.compare_price > product.price)
    if product.discount_starts_at and product.discount_ends_at:
        is_active = is_active and product.discount_starts_at <= now <= product.discount_ends_at
    elif product.discount_starts_at:
        is_active = is_active and product.discount_starts_at <= now

    return {
        "status": "success",
        "product_id": product.id,
        "price": float(product.price),
        "compare_price": float(product.compare_price) if product.compare_price else None,
        "discount_percentage": discount_pct,
        "discount_active": is_active,
    }


@router.put("/{product_id}")
def update_supplier_product(
    product_id: int,
    payload: dict,
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Update a product's basic fields (name, description, price, stock, etc.)."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")

    # Map allowed fields from payload
    field_map = {
        "name": "name",
        "description": "description",
        "price": "price",
        "stock": "stock",
        "stock_quantity": "stock",
        "category": "category",
        "is_active": "is_active",
        "tags": "tags",
        "image_url": "image_url",
    }
    for key, attr in field_map.items():
        if key in payload:
            setattr(product, attr, payload[key])

    db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/image")
async def upload_supplier_product_image(
    product_id: int,
    file: UploadFile = File(...),
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Upload/replace a product image.

    Accepts multipart image upload, validates it, saves it to the
    configured upload directory, and updates the product's ``image_url``.
    Returns the new image URL.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")

    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")

    # Read and validate
    content = await file.read()
    max_size = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(400, f"File too large (max {getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)}MB)")

    validate_upload_image(content, file.filename or "product.jpg")

    # Save file
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    key = f"products/{filename}"
    new_url = _storage.save(key, content, content_type=file.content_type)

    # Delete old file if it is managed by the storage backend
    old_url = product.image_url or ""
    if old_url:
        old_key = None
        if old_url.startswith("/uploads/"):
            old_key = old_url.lstrip("/")
        elif getattr(_storage, "cdn_base", "") and old_url.startswith(_storage.cdn_base):
            old_key = old_url[len(_storage.cdn_base):].lstrip("/")
        if old_key:
            try:
                _storage.delete(old_key)
            except Exception:
                pass

    product.image_url = new_url
    db.commit()
    db.refresh(product)

    return {"image_url": new_url, "filename": filename, "product_id": product.id}


@router.delete("/{product_id}")
def delete_supplier_product(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    """Soft-delete a product (sets is_deleted=True)."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id, Product.is_deleted == False)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_deleted = True
    db.commit()
    return {"status": "success", "message": "Product deleted"}


# === From supplier_products_upload.py ===
"""Supplier products sub-router (thin HTTP layer).

Delegates all product read/update logic to
``services.supplier.supplier_products_upload_service``. File reading, size limits
and image validation stay here (request concerns); storage + DB mutations are in
the service. Endpoint paths, auth and response shapes are unchanged.
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.catalog.models.products import Product
from infrastructure.utils.dependencies import require_supplier
from infrastructure.utils.config import settings
from infrastructure.utils.file_validation import validate_upload_image
from infrastructure.utils.storage import storage as _storage
from domains.catalog.services.products.products_service import delete_supplier_product
from domains.catalog.services.products.products_service import get_supplier_product
from domains.catalog.services.products.products_service import list_my_products
from domains.catalog.services.products.products_service import update_product_discount
from domains.catalog.services.products.products_service import update_supplier_product
from domains.suppliers.services._auto_stubs import upload_supplier_product_image


@router.get("")
def list_my_products(page: int = Query(1, ge=1), size: int = Query(20), current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    return list_my_products(db, current_user, page, size)


@router.get("/{product_id}")
def get_supplier_product_route(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    return get_supplier_product(db, current_user, product_id)


@router.put("/{product_id}/discount")
def update_product_discount_route(product_id: int, payload: dict, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    return update_product_discount(db, current_user, product_id, payload)


@router.put("/{product_id}")
def update_supplier_product_route(product_id: int, payload: dict, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    return update_supplier_product(db, current_user, product_id, payload)


@router.post("/{product_id}/image")
async def upload_supplier_product_image_route(product_id: int, file: UploadFile = File(...), current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    content = await file.read()
    max_size = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(400, f"File too large (max {getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)}MB)")
    validate_upload_image(content, file.filename or "product.jpg")
    return upload_supplier_product_image(db, current_user, product_id, content, file.filename, file.content_type, _storage)


@router.delete("/{product_id}")
def delete_supplier_product_route(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    return delete_supplier_product(db, current_user, product_id)

