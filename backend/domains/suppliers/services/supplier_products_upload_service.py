"""Supplier products read/update service.

Logic moved verbatim from ``routers.supplier_products_upload`` so the router is a
thin HTTP layer. Endpoint paths, auth and response shapes are unchanged: list
and discount endpoints return dicts, the single-product / update endpoints return
the ORM ``Product`` (serialized by FastAPI), and delete returns a status dict.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from _legacy.models import Product, SupplierProfile
from utils.datetime_utils import utcnow
from utils.pagination import paginated_response
import structlog

logger = structlog.get_logger(__name__)


def _get_owning_supplier(current_user: Any, db: Session) -> SupplierProfile:
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    return supplier


def list_my_products(db: Session, current_user: Any, page: int, size: int) -> dict:
    supplier = _get_owning_supplier(current_user, db)
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return paginated_response(q, page, size)


def get_supplier_product(db: Session, current_user: Any, product_id: int) -> Product:
    supplier = _get_owning_supplier(current_user, db)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")
    return product


def update_product_discount(db: Session, current_user: Any, product_id: int, payload: dict) -> dict:
    supplier = _get_owning_supplier(current_user, db)
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


def update_supplier_product(db: Session, current_user: Any, product_id: int, payload: dict) -> Product:
    supplier = _get_owning_supplier(current_user, db)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")

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


def upload_supplier_product_image(
    db: Session,
    current_user: Any,
    product_id: int,
    content: bytes,
    filename: Optional[str],
    content_type: Optional[str],
    storage,
) -> dict:
    supplier = _get_owning_supplier(current_user, db)
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.supplier_id == supplier.id)
        .first()
    )
    if not product:
        raise HTTPException(404, "Product not found")

    ext = filename.rsplit(".", 1)[-1] if "." in (filename or "") else "jpg"
    safe_filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    key = f"products/{safe_filename}"
    new_url = storage.save(key, content, content_type=content_type)

    # Delete old file if it is managed by the storage backend
    old_url = product.image_url or ""
    if old_url:
        old_key = None
        if old_url.startswith("/uploads/"):
            old_key = old_url.lstrip("/")
        elif getattr(storage, "cdn_base", "") and old_url.startswith(storage.cdn_base):
            old_key = old_url[len(storage.cdn_base):].lstrip("/")
        if old_key:
            try:
                storage.delete(old_key)
            except Exception:
                pass

    product.image_url = new_url
    db.commit()
    db.refresh(product)

    return {"image_url": new_url, "filename": safe_filename, "product_id": product.id}


def delete_supplier_product(db: Session, current_user: Any, product_id: int) -> dict:
    supplier = _get_owning_supplier(current_user, db)
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
