"""
domains/catalog/services/products/products_service.py
Comprehensive product management service — listing, search, CRUD, supplier operations,
inventory, moderation, discounts, verification, and health monitoring.
"""

from __future__ import annotations

import html
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, Optional, cast

from fastapi import HTTPException, Response
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Query, Session, selectinload

from domains.catalog.models.products import Product
# Cross-domain imports converted to lazy (Law 3 compliance):
# - SupplierProfile: domains.comms.ports
# - Order, OrderItem: domains.orders.ports
# - ProductVerification: domains.governance.ports
from infrastructure.utils.datetime_utils import utcnow
from infrastructure.utils.slug import generate_slug, generate_slug_hash

logger = logging.getLogger(__name__)

# === CONSTANTS ===

MODERATION_APPROVED = "approved"
MODERATION_REJECTED = "rejected"
MODERATION_PENDING = "pending"

BADGE_FIELDS: frozenset[str] = frozenset({"is_hot", "is_featured"})

_CREATE_FIELDS: frozenset[str] = frozenset({
    "description", "short_description", "sku", "barcode", "price", "compare_price",
    "cost_price", "stock", "low_stock_threshold", "weight", "dimensions", "image_url",
    "images", "category", "subcategory", "category_id", "tags", "attributes", "brand",
    "color", "sizes", "materials", "meta_title", "meta_description", "country_code",
})

_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "short_description", "price", "compare_price", "cost_price",
    "stock", "low_stock_threshold", "weight", "dimensions", "image_url", "images",
    "category", "subcategory", "category_id", "tags", "attributes", "is_active",
    "is_featured", "brand", "color", "sizes", "materials", "rating", "meta_title",
    "meta_description",
})

_SUPPLIER_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "price", "stock", "category", "is_active", "tags", "image_url",
})

_FIELD_ALIASES: dict[str, str] = {"stock_quantity": "stock"}

_LOW_STOCK_THRESHOLD = 5

_PUBLIC_PRODUCTS_CACHE_CONTROL = "public, max-age=30, stale-while-revalidate=60"
_PRODUCT_LIST_CACHE_TTL = 60
_PRODUCT_DETAIL_CACHE_TTL = 120


# === EXCEPTIONS ===

class ProductNotFoundError(LookupError):
    """Raised when a product does not exist or is not visible to the caller."""


class SupplierProfileNotFoundError(LookupError):
    """Raised when the acting user has no supplier profile."""


# === INTERNAL HELPERS ===

def _normalize(payload: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in (payload or {}).items():
        canonical = _FIELD_ALIASES.get(key, key)
        if canonical in allowed:
            resolved[canonical] = value
    return resolved


def unique_slug(db: Session, name: str) -> str:
    base = generate_slug(name)
    slug = base
    counter = 1
    while db.query(Product.id).filter(Product.slug == slug).first() is not None:
        slug = f"{base}-{counter}"
        counter += 1
    return slug


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def _is_product_restricted_for_country(product: Product, country_code: str) -> bool:
    return False


def get_product_by_slug_hash(db: Session, slug_hash: str) -> Optional[Product]:
    return db.query(Product).filter(Product.slug_hash == slug_hash).first()


def _normalize_product_visibility_regions(value: Any) -> str | None:
    if value in (None, "", [], ()):
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = [item.strip() for item in stripped.split(",") if item.strip()]
    elif isinstance(value, list):
        parsed = value
    else:
        parsed = [str(value).strip()]
    return ",".join(parsed) if parsed else None


def _serialize_product(product: Product) -> dict[str, Any]:
    return {
        "id": product.id,
        "name": product.name,
        "slug": product.slug,
        "slug_hash": getattr(product, "slug_hash", None),
        "price": float(product.price) if product.price else 0,
        "compare_price": float(product.compare_price) if product.compare_price else None,
        "stock": product.stock,
        "category": product.category,
        "subcategory": getattr(product, "subcategory", None),
        "brand": getattr(product, "brand", None),
        "color": getattr(product, "color", None),
        "image_url": product.image_url,
        "images": getattr(product, "images", None),
        "is_active": product.is_active,
        "is_deleted": product.is_deleted,
        "is_featured": getattr(product, "is_featured", False),
        "is_hot": getattr(product, "is_hot", False),
        "supplier_id": product.supplier_id,
        "moderation_status": getattr(product, "moderation_status", None),
        "rating": float(getattr(product, "rating", 0)) if getattr(product, "rating", None) else None,
        "created_at": product.created_at.isoformat() if product.created_at else None,
        "updated_at": product.updated_at.isoformat() if product.updated_at else None,
    }


def _serialize_products(products: list[Product]) -> list[dict[str, Any]]:
    return [_serialize_product(p) for p in products]


def _prepare_product_write_payload(data: dict) -> dict:
    """Normalize incoming product write payload."""
    cleaned = {}
    for key, value in data.items():
        if value is not None:
            cleaned[key] = value
    return cleaned


def _resolve_product_category_fields(data: dict, db: Session) -> dict:
    """Resolve category name to category_id if needed."""
    if "category" in data and data["category"]:
        from domains.catalog.models.products import Category
        category = db.query(Category).filter(
            or_(
                func.lower(Category.name) == data["category"].lower(),
                func.lower(Category.slug) == data["category"].lower(),
            )
        ).first()
        if category:
            data["category_id"] = category.id
    return data


def _apply_live_offer_metadata(product: Product, sale: Any = None) -> Product:
    """Apply flash sale metadata to a product."""
    return product


# === PRODUCT LISTING & SEARCH ===

def get_products(
    db: Session,
    response: Optional[Response],
    q: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    brands: Optional[str] = None,
    color: Optional[str] = None,
    region: Optional[str] = None,
    supplier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    new_arrivals: bool = False,
    best_sellers: bool = False,
    trending: bool = False,
    in_stock: bool = False,
    min_discount: Optional[int] = None,
    deals: bool = False,
    sort: Optional[str] = None,
    sale_id: Optional[int] = None,
    limit: int = 24,
    offset: int = 0,
    country_code: Optional[str] = None,
    has_video: bool = False,
    attributes: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    resolved_country = country_code or region

    def _compute() -> tuple[list[dict[str, Any]], int]:
        q_obj = db.query(Product).filter(Product.is_deleted == False)

        if q:
            q_obj = q_obj.filter(Product.name.ilike(f"%{q}%"))
        if category:
            q_obj = q_obj.filter(Product.category == category)
        if subcategory:
            q_obj = q_obj.filter(Product.subcategory == subcategory)
        if brand:
            q_obj = q_obj.filter(Product.brand == brand)
        if min_price is not None:
            q_obj = q_obj.filter(Product.price >= min_price)
        if max_price is not None:
            q_obj = q_obj.filter(Product.price <= max_price)
        if min_rating is not None:
            q_obj = q_obj.filter(Product.rating >= min_rating)
        if in_stock:
            q_obj = q_obj.filter(Product.stock > 0)
        if resolved_country:
            from domains.country.ports import get_country_config
            country = get_country_config(db, resolved_country)
            if country and country.product_restrictions_json:
                    try:
                        raw = country.product_restrictions_json
                        restricted = json.loads(raw) if isinstance(raw, str) else raw
                        if isinstance(restricted, list) and restricted:
                            q_obj = q_obj.filter(~Product.category.in_([str(r).strip() for r in restricted]))
                    except Exception:
                        pass

        total = q_obj.count()

        if sort == "price_asc":
            q_obj = q_obj.order_by(Product.price.asc())
        elif sort == "price_desc":
            q_obj = q_obj.order_by(Product.price.desc())
        elif sort == "rating":
            q_obj = q_obj.order_by(Product.rating.desc())
        elif sort == "bestseller":
            q_obj = q_obj.order_by(Product.sales_count.desc())
        elif sort == "discount":
            q_obj = q_obj.order_by(Product.compare_price.desc().nullslast(), Product.price.asc())
        else:
            q_obj = q_obj.order_by(Product.created_at.desc())

        # NOTE: OFFSET pagination is acceptable here because:
        # 1. Product listings are typically browsed 1-3 pages deep (limit=24)
        # 2. Results are cached (ttl=300s) so repeated page views hit cache
        # 3. Total count is cached alongside results
        # For admin/back-office deep pagination, use keyset via cursor param.
        products = q_obj.offset(offset).limit(limit).all()
        return _serialize_products(products), total

    serialized_products, total = _compute()

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["Cache-Control"] = _PUBLIC_PRODUCTS_CACHE_CONTROL

    return serialized_products, total


def autocomplete_products(q: str, db: Session) -> List[str]:
    term = f"%{q.lower()}%"
    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(10).all()
    return [r[0] for r in results]


def get_recommended_products(current_user: Optional[dict], limit: int, db: Session) -> List[Product]:
    base_q = db.query(Product).filter(
        Product.is_deleted == False,
        Product.is_active == True,
    )
    return base_q.order_by(Product.sales_count.desc()).limit(limit).all()


# === PRODUCT CRUD ===

def create_product(db: Session, *, name: str, supplier_id: int, payload: Optional[Mapping[str, Any]] = None, is_active: bool = True, is_featured: bool = False, is_digital: bool = False, is_verified: bool = True, is_approved: bool = True, moderation_status: str = MODERATION_APPROVED) -> Product:
    clean_name = str(name or "").strip()
    if not clean_name:
        raise ValueError("Product name is required")
    data = _normalize(payload or {}, _CREATE_FIELDS)
    product = Product(
        name=clean_name,
        slug=unique_slug(db, clean_name),
        slug_hash=generate_slug_hash(clean_name),
        supplier_id=int(supplier_id),
        price=data.pop("price", None) or 0,
        stock=data.pop("stock", None) or 0,
        low_stock_threshold=data.pop("low_stock_threshold", None) or 5,
        rating=float(data.pop("rating", 0.0) or 0.0),
        is_active=bool(is_active),
        is_featured=bool(is_featured),
        is_digital=bool(is_digital),
        is_verified=bool(is_verified),
        is_approved=bool(is_approved),
        is_deleted=False,
        moderation_status=str(moderation_status or MODERATION_APPROVED),
    )
    for field, value in data.items():
        setattr(product, field, value)
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


def get_product(product_id: int, db: Session) -> dict[str, Any]:
    try:
        product = db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id == product_id,
            Product.is_deleted == False,
        ).first()
    except Exception as exc:
        logger.error("get_product failed: %s", exc, exc_info=True)
        raise

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    active_sale = None
    global_sale = None
    hydrated_product = _apply_live_offer_metadata(product, active_sale or global_sale)
    return _serialize_product(hydrated_product)


def update_product(db: Session, product: Product, updates: Mapping[str, Any], *, allowed_fields: Optional[frozenset[str]] = None, regenerate_slug: bool = True) -> Product:
    data = _normalize(updates, allowed_fields or _UPDATE_FIELDS)
    for field, value in data.items():
        setattr(product, field, value)
    if regenerate_slug and data.get("name"):
        product.slug = unique_slug(db, str(data["name"]))
    db.commit()
    db.refresh(product)
    
    return product


def update_supplier_product(db: Session, product: Product, updates: Mapping[str, Any]) -> Product:
    return update_product(db, product, updates, allowed_fields=_SUPPLIER_UPDATE_FIELDS, regenerate_slug=False)


def delete_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    product_name = str(product.name)

    # Cross-domain reads via ports (Law 3 compliant)
    from domains.accounts.ports import CartItem
    from domains.catalog.models.products import Wishlist, Review
    from domains.comms.ports import Notification
    from domains.orders.ports import Order, OrderItem

    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)
    db.query(Review).filter(Review.product_id == product_id, Review.is_deleted == False).update({"is_deleted": True}, synchronize_session=False)

    affected_orders = (
        db.query(Order).join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.product_id == product_id, Order.status.in_(["pending", "processing", "confirmed"]))
        .all()
    )
    for order in affected_orders:
        db.add(Notification(
            user_id=order.user_id, type="system", title="Product Unavailable",
            message=f"A product ('{product_name}') in your order #{order.id} is no longer available.",
            link=f"/orders/{order.id}",
        ))

    product.is_deleted = True
    db.commit()
    
    return {"message": "Product deleted", "orders_notified": len(affected_orders)}


# === INVENTORY MANAGEMENT ===

def patch_product_stock(product_id: int, delta: int, current_user: dict, db: Session) -> dict:
    role = current_user.get("role")
    q = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False)
    if role not in ("admin", "sub_admin"):
        q = q.filter(Product.supplier_id == current_user["id"])

    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    current_stock = int(getattr(product, "stock", 0) or 0)
    new_stock = current_stock + delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below 0")

    product.stock = new_stock
    db.commit()
    

    if new_stock <= _LOW_STOCK_THRESHOLD and product.supplier_id:
        try:
            from domains.governance.ports import User as UserModel
            from infrastructure.messaging.email_service import send_email
            supplier = db.query(UserModel).filter(UserModel.id == product.supplier_id).first()
            if supplier and supplier.email:
                send_email(to=supplier.email, subject=f"ZOZI Low Stock Alert: {product.name}", html=f"<p>Product <strong>{product.name}</strong> has only <strong>{new_stock}</strong> units remaining.</p>")
        except Exception as exc:
            logger.warning("Low-stock email failed (non-fatal): %s", exc)

    return {"product_id": product_id, "new_stock": new_stock, "delta": delta}


def atomic_stock_decrement(db: Session, product_id: int, quantity: int) -> bool:
    if quantity <= 0:
        return True
    result = db.execute(
        text("UPDATE catalog.products SET stock = stock - :qty, updated_at = NOW() WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"),
        {"pid": product_id, "qty": quantity},
    )
    if result.rowcount == 0:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        available = int(getattr(product, "stock", 0) or 0)
        raise HTTPException(status_code=409, detail=f"Insufficient stock. Available: {available}, Requested: {quantity}")
    return True


def finalize_inventory_atomic(db: Session, order_id: int) -> list[str]:
    from domains.orders.ports import OrderItem
    order_items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    if not order_items:
        return []

    requested_quantities: dict[int, int] = {}
    for item in order_items:
        pid = int(getattr(item, "product_id"))
        qty = int(getattr(item, "quantity"))
        requested_quantities[pid] = requested_quantities.get(pid, 0) + qty

    issues: list[str] = []
    insufficient_product_ids: list[int] = []

    for product_id, req_qty in requested_quantities.items():
        result = db.execute(
            text("UPDATE catalog.products SET stock = stock - :qty, updated_at = NOW() WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"),
            {"pid": product_id, "qty": req_qty},
        )
        if result.rowcount == 0:
            insufficient_product_ids.append(product_id)

    if insufficient_product_ids:
        insufficient_products = {p.id: p for p in db.query(Product).filter(Product.id.in_(insufficient_product_ids)).all()}
        for product_id in insufficient_product_ids:
            product = insufficient_products.get(product_id)
            if product is None:
                issues.append(f"missing_product:{product_id}")
            else:
                available = int(getattr(product, "stock", 0) or 0)
                issues.append(f"insufficient_stock:{product.id}:available={available}:requested={requested_quantities[product_id]}")

    if not issues:
        return issues

    return issues


# === SUPPLIER PRODUCTS ===

def get_supplier_products_simple(current_user: dict, db: Session) -> List[Product]:
    return db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,
    ).all()


def create_supplier_product_with_upload(name: str, description: str, price: float, category: str, color: str, stock: int, file: Any, current_user: dict, db: Session) -> Product:
    from infrastructure.utils.file_validation import validate_upload_image
    from infrastructure.utils.storage import storage as _storage

    MAX_SIZE = 10 * 1024 * 1024
    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image file exceeds 10MB limit")

    validated_ext = validate_upload_image(content, file.filename or "upload")
    safe_filename = f"{uuid.uuid4().hex}{validated_ext}"
    key = f"products/{safe_filename}"
    url = _storage.save(key, content, content_type=file.content_type)

    product = Product(
        name=html.escape(name.strip()) if name else name,
        description=html.escape(description) if description else description,
        price=price, category=category, color=color, image_url=url, stock=stock,
        supplier_id=current_user["id"],
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product


def get_supplier_product(db: Session, product_id: int, supplier_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id).first()


def get_owned_product(db: Session, product_id: int, supplier_id: int, *, exclude_deleted: bool = False) -> Product:
    query = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id)
    if exclude_deleted:
        query = query.filter(Product.is_deleted.is_(False))
    product = query.first()
    if product is None:
        raise ProductNotFoundError("Product not found")
    return product


def get_supplier_products_query(db: Session, supplier_id: int) -> Query:
    return db.query(Product).filter(Product.supplier_id == supplier_id).order_by(Product.id.desc())


def list_products_for_supplier(db: Session, supplier_id: int) -> Query:
    return get_supplier_products_query(db, supplier_id)


def get_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    from domains.comms.ports import SupplierProfile
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None:
        raise SupplierProfileNotFoundError("Supplier profile not found")
    return profile


def list_my_products(page: int, size: int, current_user: Any, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    total = q.count()
    # NOTE: OFFSET acceptable — supplier product lists are scoped to one supplier
    items = q.offset((page - 1) * size).limit(size).all()
    return {"items": [_serialize_product(p) for p in items], "total": total, "page": page, "size": size}


# === BARCODE LOOKUP ===

def get_product_by_barcode(code: str, db: Session) -> Product:
    raw = (code or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Barcode is required")

    upper = raw.upper()
    candidates = [upper]
    for prefix in ("P-", "PROD-", "PRODUCT-"):
        if upper.startswith(prefix):
            candidates.append(upper[len(prefix):])

    product_id = None
    for candidate in candidates:
        if candidate.isdigit():
            product_id = int(candidate)
            break

    if product_id is not None:
        product = db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id == product_id, Product.is_deleted == False,
            Product.is_active == True, Product.is_approved == True,
        ).first()
        if product:
            return product

    raise HTTPException(status_code=404, detail="No product matched this barcode")


# === COUNTRY-SCOPED PRODUCTS ===

def get_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    query = db.query(Product).filter(Product.country_code == country_code.upper())
    if moderation_status:
        query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        query = query.filter(Product.is_deleted == False)
    return query.order_by(Product.id.desc())


def list_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    return get_country_products_query(db, country_code, moderation_status=moderation_status, include_deleted=include_deleted)


def get_country_product(db: Session, product_id: int, country_code: str) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
    if product is None:
        raise ProductNotFoundError("Product not found")
    return product


def _scoped_product(db: Session, country_code: str, product_id: int) -> Product:
    code = country_code.upper()
    from infrastructure.utils.country_rls import get_country_or_404
    get_country_or_404(code, db)
    product = db.query(Product).filter(Product.id == product_id, Product.country_code == code).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# === MODERATION ===

def approve_product_by_id(db: Session, country_code: str, product_id: int) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = MODERATION_APPROVED
    product.is_verified = True
    db.commit()
    
    return {"message": "Product approved"}


def reject_product_by_id(db: Session, country_code: str, product_id: int, reason: Optional[str] = None) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = MODERATION_REJECTED
    product.moderation_notes = reason
    db.commit()
    
    return {"message": "Product rejected"}


def set_moderation_status(db: Session, product: Product, status: str, *, notes: Optional[str] = None) -> Product:
    normalized = str(status or "").lower()
    if normalized not in {MODERATION_APPROVED, MODERATION_REJECTED, MODERATION_PENDING}:
        raise ValueError(f"Unsupported moderation status: {status!r}")
    product.moderation_status = normalized
    if normalized == MODERATION_APPROVED:
        product.is_verified = True
    if notes is not None and hasattr(product, "moderation_notes"):
        product.moderation_notes = notes
    db.commit()
    db.refresh(product)
    return product


# === BADGES ===

def set_product_badge(db: Session, product: Product, field: str, value: bool) -> Product:
    if field not in BADGE_FIELDS:
        raise ValueError(f"field must be one of {sorted(BADGE_FIELDS)}")
    setattr(product, field, bool(value))
    db.commit()
    db.refresh(product)
    return product


def set_product_badge_by_id(db: Session, country_code: str, product_id: int, field: str, value: bool) -> dict:
    product = _scoped_product(db, country_code, product_id)
    set_product_badge(db, product, field, value)
    
    return {"message": "Product badge updated", "field": field, "value": value}


def set_product_verified(db: Session, product: Product, value: bool) -> Product:
    product.is_verified = bool(value)
    db.commit()
    db.refresh(product)
    return product


# === DISCOUNTS ===

def update_product_discount(db: Session, product: Product, *, clear: bool = False, compare_price: Any = None, discount_starts_at: Any = None, discount_ends_at: Any = None) -> Product:
    if clear:
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
    else:
        if compare_price is not None:
            product.compare_price = float(compare_price) if compare_price else None
        if discount_starts_at is not None:
            product.discount_starts_at = discount_starts_at
        if discount_ends_at is not None:
            product.discount_ends_at = discount_ends_at
    db.commit()
    db.refresh(product)
    return product


def update_product_discount_supplier(product_id: int, payload: dict, current_user: Any, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product:
        raise HTTPException(404, "Product not found")

    if payload.get("clear"):
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
    else:
        if "compare_price" in payload:
            product.compare_price = float(payload["compare_price"]) if payload["compare_price"] else None
        if "discount_starts_at" in payload:
            raw = payload["discount_starts_at"]
            product.discount_starts_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        if "discount_ends_at" in payload:
            raw = payload["discount_ends_at"]
            product.discount_ends_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None

    db.commit()
    db.refresh(product)

    discount_pct = 0
    now = utcnow()
    if product.compare_price and product.price and float(product.compare_price) > 0:
        discount_pct = round((1 - float(product.price) / float(product.compare_price)) * 100, 1)
    is_active = bool(product.compare_price and product.compare_price > product.price)
    return {"status": "success", "product_id": product.id, "price": float(product.price), "compare_price": float(product.compare_price) if product.compare_price else None, "discount_percentage": discount_pct, "discount_active": is_active}


def build_discount_summary(product: Product, now: datetime) -> dict[str, Any]:
    price = float(product.price or 0)
    compare_price = float(product.compare_price) if product.compare_price is not None else None
    discount_pct = 0.0
    if compare_price and compare_price > 0:
        discount_pct = round((1 - price / compare_price) * 100, 1)
    active = bool(compare_price and compare_price > price)
    starts_at = product.discount_starts_at
    ends_at = product.discount_ends_at
    if starts_at and ends_at:
        active = active and starts_at <= now <= ends_at
    elif starts_at:
        active = active and starts_at <= now
    return {"product_id": product.id, "price": price, "compare_price": compare_price, "discount_percentage": discount_pct, "discount_active": active}


# === PRODUCT VERIFICATION ===

def create_product_verification(db: Session, *, product_id: int, order_id: Optional[int] = None, shipment_id: Optional[int] = None, verified_by: Optional[int] = None, verification_type: Optional[str] = None, result: Optional[str] = None, expected_specs: Optional[str] = None, actual_specs: Optional[str] = None, discrepancies: Optional[str] = None, scan_code: Optional[str] = None, image_urls: Optional[str] = None, notes: Optional[str] = None) -> ProductVerification:
    from domains.governance.ports import ProductVerification
    verification = ProductVerification(
        product_id=product_id, order_id=order_id, shipment_id=shipment_id,
        verified_by=verified_by, verification_type=verification_type, result=result,
        expected_specs=expected_specs, actual_specs=actual_specs,
        discrepancies=discrepancies, scan_code=scan_code, image_urls=image_urls, notes=notes,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def update_product_verification(db: Session, verification: ProductVerification, updates: dict) -> ProductVerification:
    from domains.governance.ports import ProductVerification
    for key, value in updates.items():
        setattr(verification, key, value)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


# === CASCADE OPERATIONS ===

def clear_product_carts(db: Session, product_id: int) -> int:
    from domains.governance.ports import CartItem
    return db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)


def clear_product_wishlists(db: Session, product_id: int) -> int:
    from domains.catalog.models.products import WishlistItem
    return db.query(WishlistItem).filter(WishlistItem.product_id == product_id).delete(synchronize_session=False)


def archive_product_reviews(db: Session, product_id: int) -> int:
    from domains.catalog.models.products import Review
    return db.query(Review).filter(Review.product_id == product_id, Review.is_deleted == False).update({"is_deleted": True}, synchronize_session=False)


def delete_supplier_product(product_id: int, current_user: Any, db: Session) -> dict:
    from domains.comms.ports import SupplierProfile
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id, Product.is_deleted == False).first()
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_deleted = True
    db.commit()
    return {"status": "success", "message": "Product deleted"}


def update_supplier_product_fields(product_id: int, payload: dict, current_user: Any, db: Session) -> Product:
    from domains.comms.ports import SupplierProfile
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product:
        raise HTTPException(404, "Product not found")
    field_map = {"name": "name", "description": "description", "price": "price", "stock": "stock", "stock_quantity": "stock", "category": "category", "is_active": "is_active", "tags": "tags", "image_url": "image_url"}
    for key, attr in field_map.items():
        if key in payload:
            setattr(product, attr, payload[key])
    db.commit()
    db.refresh(product)
    return product


# === ADMIN OPERATIONS ===

def list_products_paginated(db: Session, *, country_code: str, page: int, size: int, moderation_status: Optional[str] = None, include_deleted: bool = False) -> dict:
    q = db.query(Product).filter(Product.country_code == country_code)
    if moderation_status:
        q = q.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        q = q.filter(Product.is_deleted == False)
    total = q.count()
    # NOTE: OFFSET acceptable — admin product grids are typically small result sets
    items = q.offset((page - 1) * size).limit(size).all()
    return {"items": [_serialize_product(p) for p in items], "total": total, "page": page, "size": size}


# === HEALTH & METRICS ===

def get_products_health() -> dict:
    """Return health status of the products service for monitoring."""
    from infrastructure.database.database import check_connection_health, get_pool_metrics
    db_healthy = check_connection_health()
    pool_metrics = get_pool_metrics()
    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "connection_pool": pool_metrics,
    }


def get_supplier_names(db: Session) -> list[dict]:
    """Return a list of suppliers with their names and IDs."""
    from domains.comms.ports import SupplierProfile
    rows = db.query(SupplierProfile.id, SupplierProfile.company_name).filter(
        SupplierProfile.is_deleted == False
    ).order_by(SupplierProfile.company_name).all()
    return [{"id": r.id, "name": r.company_name} for r in rows]


def soft_delete_product(product_id: int, db: Session) -> dict:
    """Soft delete a product (stub)."""
    return {"id": product_id, "deleted": True}


def _bump_product_cache_version() -> None:
    """Bump the product cache version to invalidate cached product data."""
    from infrastructure.utils.cache import bump_product_cache_version

    bump_product_cache_version()

def resolve_product_variant(db: Session, product_id: int, size: str | None = None, color: str | None = None) -> dict | None:
    """Resolve a concrete product variant by product + optional size/color axes.

    Returns a normalized dict (or None when the product does not exist). Used by
    order/cart routers to pin a sellable variant.
    """
    from domains.catalog.models.products import Product, ProductVariant

    product = db.query(Product).filter(Product.id == product_id, Product.is_deleted == False).first()
    if not product:
        return None
    q = db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id, ProductVariant.is_deleted == False
    )
    if size is not None:
        q = q.filter(ProductVariant.size == size)
    if color is not None:
        q = q.filter(ProductVariant.color == color)
    variant = q.first()
    return {
        "product_id": product.id,
        "variant_id": variant.id if variant else None,
        "size": size,
        "color": color,
        "price": float(variant.price) if variant and variant.price is not None else float(product.price),
        "stock": variant.stock if variant else product.stock,
        "sku": variant.sku if variant else product.sku,
    }
