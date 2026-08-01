"""Supplier products sub-router."""
from __future__ import annotations
import os
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from db.schemas import CursorPage
from models import Product, SupplierProfile
from utils.dependencies import require_supplier
from utils.datetime_utils import utcnow
from utils.file_validation import validate_upload_image
from utils.config import settings
from utils.pagination import cursor_paginate_desc
from services.storage import storage as _storage

from services.write_helpers import commit_and_refresh, commit_only
router = APIRouter()


@router.get("", response_model=CursorPage)
def list_my_products(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return cursor_paginate_desc(q.order_by(Product.id.desc()), cursor=cursor, page_size=limit)


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
        commit_and_refresh(db, product)
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

    commit_and_refresh(db, product)
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
    commit_and_refresh(db, product)

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
    commit_only(db)
    return {"status": "success", "message": "Product deleted"}


