"""Supplier products sub-router."""
from __future__ import annotations
from typing import Set
import os
import uuid

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from data.db import get_db
from data.schemas import CursorPage
from utils.dependencies import require_supplier
from utils.file_validation import validate_upload_image
from utils.config import settings
from utils.pagination import cursor_paginate_desc
from services.storage import storage as _storage

from services.supplier.supplier_read_service import (
    get_my_products_page,
    get_owned_product,
    set_product_image_url,
    soft_delete_product,
    update_product,
    update_product_discount,
)

router = APIRouter()


@router.get("", response_model=CursorPage)
def list_my_products(
    cursor: str | None = Query(None, description="Cursor for next page"),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    return get_my_products_page(db, current_user.id, cursor, limit)


@router.get("/{product_id}")
def get_supplier_product(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    """Get a single product by ID, verifying the supplier owns it."""
    return get_owned_product(db, product_id, current_user.id)


@router.put("/{product_id}/discount")
def update_product_discount_route(
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
    return update_product_discount(db, product_id, current_user.id, payload)


@router.put("/{product_id}")
def update_supplier_product(
    product_id: int,
    payload: dict,
    current_user=Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Update a product's basic fields (name, description, price, stock, etc.)."""
    return update_product(db, product_id, current_user.id, payload)


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
    # Fail fast if the supplier does not own this product.
    get_owned_product(db, product_id, current_user.id)

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

    # The service persists the new URL and removes the previously stored file.
    set_product_image_url(db, product_id, current_user.id, new_url)

    return {"image_url": new_url, "filename": filename, "product_id": product_id}


@router.delete("/{product_id}")
def delete_supplier_product(product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db)):
    """Soft-delete a product (sets is_deleted=True)."""
    return soft_delete_product(db, product_id, current_user.id)
