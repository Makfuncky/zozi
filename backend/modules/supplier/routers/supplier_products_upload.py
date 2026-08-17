"""Supplier products sub-router (thin HTTP layer).

Delegates all product read/update logic to
``services.supplier.supplier_products_upload_service``. File reading, size limits
and image validation stay here (request concerns); storage + DB mutations are in
the service. Endpoint paths, auth and response shapes are unchanged.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from db.database import get_db
from _legacy.models import Product
from utils.dependencies import require_supplier
from utils.config import settings
from utils.file_validation import validate_upload_image
from services.common.storage import storage as _storage
from services.supplier.supplier_products_upload_service import (
    delete_supplier_product,
    get_supplier_product,
    list_my_products,
    update_product_discount,
    update_supplier_product,
    upload_supplier_product_image,
)

router = APIRouter(prefix="/api/v1/supplier")


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
