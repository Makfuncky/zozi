"""Customer coupons router (ROUTERS layer, flat file).

Thin HTTP layer: request parsing/validation, authentication, pagination query
params, and delegation to ``controllers.commerce.coupons_controller``. No direct
DB/ORM access here; all persistence lives in the services layer. Keyset
(cursor) pagination is accepted via ``cursor``/``limit`` and forwarded to the
controller — this layer performs no skip-based scanning.
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from controllers.commerce.coupons_controller import (
    create_coupon as ctrl_create,
    delete_coupon as ctrl_delete,
    list_coupons as ctrl_list,
    validate_coupon as ctrl_validate,
)
from db.schemas import CouponCreate
from utils.dependencies import get_current_user, get_db, require_admin


# Local Pydantic schemas (previously sourced from a missing `data.schemas`
# module). Kept inline so this router is self-contained.
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

router = APIRouter(prefix="/api/v1")


@router.post("/validate", response_model=CouponValidateView)
def validate_coupon_post(
    body: CouponValidateBody = Body(default=CouponValidateBody(code="")),
    db: Session = Depends(get_db),
):
    order_total = body.order_total if body.order_total is not None else body.order_amount
    if not body.code or order_total is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": 0.0, "coupon": None}
    return ctrl_validate(body.code, Decimal(str(order_total)), db)


@router.get("/validate", response_model=CouponValidateView)
def validate_coupon_get(
    code: str = Query(...),
    order_total: Optional[float] = Query(None),
    order_amount: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    total = order_total if order_total is not None else order_amount
    if not code or total is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": 0.0, "coupon": None}
    return ctrl_validate(code, Decimal(str(total)), db)


@router.get("", response_model=List[CouponView])
def list_coupons(
    limit: int = Query(200, ge=1, le=200),
    cursor: Optional[int] = Query(None, description="Coupon id to paginate after"),
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return ctrl_list(db, limit=limit, cursor=cursor)


@router.post("", response_model=CouponView, status_code=201)
def create_coupon(
    payload: CouponCreate,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
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


@router.delete("/{coupon_id}", response_model=dict)
def delete_coupon(
    coupon_id: int,
    _: object = Depends(require_admin),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return ctrl_delete(coupon_id, current_user, db)
