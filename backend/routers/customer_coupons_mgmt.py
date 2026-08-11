"""Coupon routes with compatibility for recovered request and response contracts.

Thin HTTP layer: request parsing/validation lives here; all coupon persistence
and validation business logic is delegated to ``services.commerce.coupons_write_service``
so the router stays free of ``db.query``/``db.add``/``db.commit``. Endpoints, auth and
response shapes are unchanged from the previous inline implementation.
"""
from fastapi import APIRouter, Body, Depends, Request, status

from controllers.security.auth_controller import get_current_user
from db.database import get_db
from utils.dependencies import require_admin
from services.commerce.coupons_write_service import (
    create_coupon_from_payload,
    delete_coupon_by_id,
    list_coupons_paginated,
    validate_coupon,
)

router = APIRouter(prefix="/api/v1")


@router.post("/validate")
def validate_coupon(
    request: Request,
    payload: dict | None = Body(default=None),
    _: dict = Depends(get_current_user),
    db: object = Depends(get_db),
):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get("code") or "").strip()
    order_total = payload.get("order_total", payload.get("order_subtotal"))
    return validate_coupon(db, code, order_total)


@router.get("")
def list_coupons(
    _: dict = Depends(require_admin),
    db: object = Depends(get_db),
    page: int = 1,
    page_size: int = 20,
):
    return list_coupons_paginated(db, page, page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_coupon(
    request: Request,
    payload: dict | None = Body(default=None),
    _: dict = Depends(require_admin),
    db: object = Depends(get_db),
):
    payload = {**dict(request.query_params), **(payload or {})}
    return create_coupon_from_payload(db, payload)


@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: str, _: dict = Depends(require_admin), db: object = Depends(get_db)):
    return delete_coupon_by_id(db, coupon_id)
