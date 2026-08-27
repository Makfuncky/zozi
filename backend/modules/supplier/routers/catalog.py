"""Supplier catalog router - thin wrappers over catalog domain services."""

from fastapi import APIRouter, Depends, Body, Query, status, File, UploadFile
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_supplier
from rbac.dependencies import require_feature

from domains.catalog.services.products.products_service import (
    delete_supplier_product,
    get_supplier_product,
    list_my_products,
    update_product_discount_supplier,
    update_supplier_product_fields,
)
from domains.suppliers.ports import (
    upload_supplier_product_image,
)

router = APIRouter(prefix="/api/v1/supplier/catalog", tags=["supplier", "catalog"])


@router.get("")
def list_my_products_route(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.list")
    return list_my_products(page, size, current_user, db)


@router.get("/{product_id}")
def get_supplier_product_route(
    product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.read")
    return get_supplier_product(db, product_id, current_user.id)


@router.put("/{product_id}")
def update_supplier_product_route(
    product_id: int, body: dict = Body(...),
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return update_supplier_product_fields(product_id, body, current_user, db)


@router.put("/{product_id}/discount")
def update_product_discount_route(
    product_id: int, body: dict = Body(...),
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    return update_product_discount_supplier(product_id, body, current_user, db)


@router.post("/{product_id}/image")
async def upload_product_image_route(
    product_id: int, file: UploadFile = File(...),
    current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.write")
    content = await file.read()
    return upload_supplier_product_image(db, current_user.id, product_id, content, file.filename, file.content_type)


@router.delete("/{product_id}")
def delete_product_route(
    product_id: int, current_user=Depends(require_supplier), db: Session = Depends(get_db),
):
    require_feature("catalog.delete")
    return delete_supplier_product(product_id, current_user, db)
