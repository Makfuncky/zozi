"""Read-only supplier queries extracted from routers to satisfy layering (LC1/W1).

Routers must not perform ``db.query``/writes directly; they delegate to this module.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from data.models import OrderItem, Product, SupplierProfile
from services.storage import storage as _storage
from data.services_write_helpers import (
    commit_and_refresh,
    commit_only,
)
from services.supplier.supplier_profile_service import (  # noqa: F401  (re-exported for backward compatibility)
    create_supplier_profile,
    get_supplier_profile_by_user,
    update_supplier_profile,
)
from utils.datetime_utils import utcnow
from utils.pagination import cursor_paginate_desc


def get_supplier_analytics_summary(db: Session, user_id: int) -> dict:
    """Aggregated analytics for the supplier owning ``user_id``."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == user_id)
        .first()
    )
    if not supplier:
        raise HTTPException(404, detail="Supplier profile not found")
    total_products = (
        db.query(func.count(Product.id))
        .filter(Product.supplier_id == supplier.id)
        .scalar()
    )
    total_sales = (
        db.query(func.coalesce(func.sum(OrderItem.total_price), 0))
        .filter(OrderItem.supplier_id == supplier.id)
        .scalar()
    )
    total_orders = (
        db.query(func.count(func.distinct(OrderItem.order_id)))
        .filter(OrderItem.supplier_id == supplier.id)
        .scalar()
    )
    return {
        "total_products": total_products,
        "total_sales": float(total_sales),
        "total_orders": total_orders,
    }


def require_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    """Return the supplier profile owned by ``user_id`` (404 if absent)."""
    profile = (
        db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    )
    if not profile:
        raise HTTPException(404, "Supplier profile not found")
    return profile


def get_owned_product(db: Session, product_id: int, user_id: int) -> Product:
    """Return a product owned by ``user_id`` (404 if absent/not owned)."""
    supplier = require_supplier_profile(db, user_id)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    return product


def get_my_products_page(db: Session, user_id: int, cursor: str | None, limit: int):
    """Return a cursor-paginated page of the supplier's products."""
    supplier = require_supplier_profile(db, user_id)
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return cursor_paginate_desc(q.order_by(Product.id.desc()), cursor=cursor, page_size=limit)


def update_product_discount(db: Session, product_id: int, user_id: int, payload: dict) -> dict:
    """Set or clear a discount on the supplier's product (see router for body schema)."""
    product = get_owned_product(db, product_id, user_id)

    if payload.get("clear"):
        product.compare_price = None
        product.discount_starts_at = None
        product.discount_ends_at = None
        commit_and_refresh(db, product)
        return {"status": "success", "message": "Discount cleared", "product_id": product.id}

    if "compare_price" in payload:
        cp = payload["compare_price"]
        product.compare_price = float(cp) if cp is not None else None

    if "discount_starts_at" in payload:
        raw = payload["discount_starts_at"]
        try:
            product.discount_starts_at = (
                datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
            )
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_starts_at format: {raw}")

    if "discount_ends_at" in payload:
        raw = payload["discount_ends_at"]
        try:
            product.discount_ends_at = (
                datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
            )
        except (ValueError, TypeError):
            raise HTTPException(400, f"Invalid discount_ends_at format: {raw}")

    commit_and_refresh(db, product)

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


def update_product(db: Session, product_id: int, user_id: int, payload: dict) -> Product:
    """Update a product's basic fields (name, description, price, stock, etc.)."""
    product = get_owned_product(db, product_id, user_id)
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
    commit_and_refresh(db, product)
    return product


def set_product_image_url(db: Session, product_id: int, user_id: int, image_url: str) -> Product:
    """Persist an uploaded image URL on the supplier's product, removing the old file."""
    product = get_owned_product(db, product_id, user_id)
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
    product.image_url = image_url
    commit_and_refresh(db, product)
    return product


def soft_delete_product(db: Session, product_id: int, user_id: int) -> dict:
    """Soft-delete a product (sets is_deleted=True)."""
    supplier = require_supplier_profile(db, user_id)
    product = (
        db.query(Product)
        .filter(
            Product.id == product_id,
            Product.supplier_id == supplier.id,
            Product.is_deleted == False,
        )
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    product.is_deleted = True
    commit_only(db)
    return {"status": "success", "message": "Product deleted"}
