"""Supplier orders router — thin wrappers over supplier orders domain services."""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, File, UploadFile, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_supplier
from rbac.dependencies import require_feature

from domains.suppliers.ports import (
    get_parcel_verification_history,
    get_reference_image,
    get_supplier_label,
    list_supplier_orders,
    replace_reference_image,
    upload_parcel_proof,
    verify_parcel_proof,
)

router = APIRouter(prefix="/api/v1/supplier/orders", tags=["supplier", "orders"])


@router.get("")
def list_supplier_orders_route(
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.list")
    return list_supplier_orders(current_user, db)


@router.get("/{order_id}/label")
def get_supplier_label_route(
    order_id: int,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.read")
    return get_supplier_label(current_user, order_id, db)


@router.post("/{order_id}/parcel-proof")
async def upload_parcel_proof_route(
    order_id: int,
    file: UploadFile = File(...),
    notes: str = Form(""),
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.write")
    content = await file.read()
    return upload_parcel_proof(current_user, order_id, content, file.filename, file.content_type, notes, db)


@router.post("/{order_id}/parcel-proof/verify")
async def verify_parcel_proof_route(
    order_id: int,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.write")
    return verify_parcel_proof(current_user, order_id, db)


@router.post("/{order_id}/parcel-proof/reference")
async def replace_reference_image_route(
    order_id: int,
    file: UploadFile = File(...),
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.write")
    content = await file.read()
    return replace_reference_image(current_user, order_id, content, file.filename, file.content_type, db)


@router.get("/{order_id}/parcel-proof/reference-image")
def get_reference_image_route(
    order_id: int,
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.read")
    url = get_reference_image(current_user, order_id, db)
    return RedirectResponse(url=url, status_code=302)


@router.get("/parcel-verification-history")
def get_parcel_verification_history_route(
    limit: int = Query(10, ge=1, le=100),
    current_user: Any = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    require_feature("orders.read")
    return get_parcel_verification_history(current_user, limit, db)
