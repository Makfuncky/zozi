# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Auto-migrated service logic from routers/customer_coupons_create.py."""
from __future__ import annotations

from __future__ import annotations

from decimal import Decimal

from typing import List, Optional

from fastapi import Body, Depends, Query

from pydantic import BaseModel

from sqlalchemy.orm import Session

from domains.accounts.ports import list_coupons as ctrl_list, validate_coupon as ctrl_validate
from domains.accounts.services.admin_promotions_service import create_coupon as ctrl_create
from domains.accounts.services.customer_coupons_create_service import delete_coupon as ctrl_delete

from infrastructure.database.schemas import CouponCreate

from infrastructure.utils.dependencies import get_current_user, get_db, require_admin

class CouponValidateBody(BaseModel):
    code: str
    order_total: Optional[float] = None
    order_amount: Optional[float] = None

class CouponValidateView(BaseModel):
    valid: bool
    discount_amount: float
    new_total: float
    coupon: Optional[dict] = None

class CouponView(BaseModel):
    id: int
    code: str
    discount_type: str
    discount_value: Optional[float] = None
    minimum_order: Optional[float] = None
    maximum_discount: Optional[float] = None
    usage_limit: Optional[int] = None
    usage_count: int = 0
    is_active: bool
    starts_at: Optional[str] = None
    expires_at: Optional[str] = None
    country_code: Optional[str] = None
    created_at: Optional[str] = None

import structlog

logger = structlog.get_logger(__name__)

def validate_coupon_post(body: CouponValidateBody, db: Session):
    order_total = body.order_total if body.order_total is not None else body.order_amount
    if not body.code or order_total is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": 0.0, "coupon": None}
    return ctrl_validate(body.code, Decimal(str(order_total)), db)

def validate_coupon_get(code: str, order_total: Optional[float], order_amount: Optional[float], db: Session):
    total = order_total if order_total is not None else order_amount
    if not code or total is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": 0.0, "coupon": None}
    return ctrl_validate(code, Decimal(str(total)), db)

def list_coupons(limit: int, cursor: Optional[int], _: object, db: Session):
    return ctrl_list(db, limit=limit, cursor=cursor)

def create_coupon(payload: CouponCreate, _: object, db: Session, current_user):
    return ctrl_create(
        code=payload.code,
        discount_type=payload.discount_type,
        discount_value=Decimal(str(payload.discount_value)),
        minimum_order=Decimal(str(payload.minimum_order)),
        max_uses=payload.usage_limit,
        is_active=payload.is_active,
        current_user=current_user,
        db=db,
    )

def delete_coupon(coupon_id: int, _: object, db: Session, current_user):
    return ctrl_delete(coupon_id, current_user, db)


