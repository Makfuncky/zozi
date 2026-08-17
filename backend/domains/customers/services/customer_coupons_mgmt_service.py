"""Auto-migrated service logic from routers/customer_coupons_mgmt.py."""
from __future__ import annotations

from fastapi import Body, Depends, Request, status

from rbac.routers.auth_controller import get_current_user

from infrastructure.database.database import get_db

from infrastructure.utils.dependencies import require_admin

from services.commerce.coupons_write_service import (
    create_coupon_from_payload,
    delete_coupon_by_id,
    list_coupons_paginated,
    validate_coupon,
)

def validate_coupon(request: Request, payload: dict | None, _: dict, db: object):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get("code") or "").strip()
    order_total = payload.get("order_total", payload.get("order_subtotal"))
    return validate_coupon(db, code, order_total)

def list_coupons(_: dict, db: object, page: int, page_size: int):
    return list_coupons_paginated(db, page, page_size)

def create_coupon(request: Request, payload: dict | None, _: dict, db: object):
    payload = {**dict(request.query_params), **(payload or {})}
    return create_coupon_from_payload(db, payload)

def delete_coupon(coupon_id: str, _: dict, db: object):
    return delete_coupon_by_id(db, coupon_id)


