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
from fastapi import Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from domains.orders.services.coupons_controller import create_coupon as ctrl_create
from domains.orders.services.coupons_controller import delete_coupon as ctrl_delete
from domains.orders.services.coupons_controller import list_coupons as ctrl_list
from domains.orders.services.coupons_controller import validate_coupon as ctrl_validate
from infrastructure.database.schemas import CouponCreate
from infrastructure.utils.dependencies import get_current_user, get_db, require_admin
import structlog
logger = structlog.get_logger(__name__)

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
