"""Supplier product image upload service.

Handles image upload, validation, and storage for supplier product images.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.catalog.ports import Product
from domains.comms.ports import SupplierProfile
from infrastructure.utils.storage import storage as _storage

logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_SIZE = 10 * 1024 * 1024  # 10 MB


def upload_supplier_product_image(
    db: Session,
    user_id: int,
    product_id: int,
    content: bytes,
    filename: str | None,
    content_type: str | None,
) -> dict:
    """Upload and associate an image with a supplier product.

    Validates ownership, file type, and size before storing.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == supplier.id,
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG, and WebP images are accepted")

    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 10 MB limit")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(filename or ".jpg")[1] or ".jpg"
    key = f"product_images/{product_id}/{timestamp}{ext}"
    url = _storage.save(key, content, content_type=content_type)

    product.image_url = url
    db.commit()

    return {"status": "success", "image_url": url}
