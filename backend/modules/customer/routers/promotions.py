"""Customer promotions router — consolidated from 5 source files."""

from decimal import Decimal, InvalidOperation
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
import structlog

from rbac import get_current_user
from rbac.dependencies import require_feature
from infrastructure.security.dependencies import require_admin
from infrastructure.database.database import get_db
from infrastructure.database.schemas import CouponCreate, ReviewCreate
from domains.customers.ports import (
    create_review,
    find_existing_review,
    get_product_reviews,
    review_product_exists as product_exists,
    soft_delete_review,
    delete_review_by_user,
    get_user_wishlist,
    get_wishlist_item_by_product,
    wishlist_product_exists,
    create_wishlist_item,
    delete_wishlist_item,
)
from domains.promotions.ports import (
    validate_coupon_code as svc_validate_coupon_code,
    list_coupons_paginated as svc_list_coupons_paginated,
    create_coupon_from_payload as svc_create_coupon_from_payload,
    delete_coupon_by_id as svc_delete_coupon_by_id,
    create_coupon as ctrl_create,
    delete_coupon as ctrl_delete,
    list_coupons as ctrl_list,
    validate_coupon as ctrl_validate,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/customer/promotions", tags=["customer", "promotions"])


# === From coupons.py ===
"""Coupon routes with compatibility for the recovered request and response contracts."""


def _normalize_discount_type(value: object) -> str | None:
    return {
        "percent": "percent",
        "percentage": "percent",
        "fixed": "fixed",
        "fixed_amount": "fixed",
        "amount": "fixed",
    }.get(str(value or "").strip().lower())


def _to_decimal(value: object, default: str = "0") -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return Decimal(default)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _to_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if text == "" or text.lower() in {"none", "null", "nan"}:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if str(current_user.get("role") or "").lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.post("/validate")
def validate_coupon(
    request: Request,
    payload: dict | None = Body(default=None),
    _: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coupons.redeem")),
):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get("code") or "").strip()
    order_total = payload.get("order_total", payload.get("order_subtotal"))
    if not code or order_total is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="code and order_total are required")
    return svc_validate_coupon_code(db, code, order_total)


@router.get("")
def list_coupons(_: dict = Depends(_require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    _rf_gate: None = Depends(require_feature("promotions.coupons.read"))
):
    return svc_list_coupons_paginated(db, cursor=None, page_size=page_size)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_coupon(
    request: Request,
    payload: dict | None = Body(default=None),
    _: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coupons.write")),
):
    payload = {**dict(request.query_params), **(payload or {})}
    return svc_create_coupon_from_payload(db, payload)


@router.delete("/coupons/{coupon_id}")
def delete_coupon(coupon_id: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coupons.write"))
):
    return svc_delete_coupon_by_id(db, coupon_id)


# === From customer_coupons_create.py ===
"""Customer coupons router (ROUTERS layer, flat file).

Thin HTTP layer: request parsing/validation, authentication, pagination query
params, and delegation to ``controllers.commerce.coupons_controller``. No direct
DB/ORM access here; all persistence lives in the services layer. Keyset
(cursor) pagination is accepted via ``cursor``/``limit`` and forwarded to the
controller — this layer performs no skip-based scanning.
"""


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


@router.get("/validate", response_model=CouponValidateView)
def validate_coupon_get(
    code: str = Query(...),
    order_total: Optional[float] = Query(None),
    order_amount: Optional[float] = Query(None),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.coupons.redeem")),
):
    total = order_total if order_total is not None else order_amount
    if not code or total is None:
        return {"valid": False, "discount_amount": 0.0, "new_total": 0.0, "coupon": None}
    return ctrl_validate(code, Decimal(str(total)), db)


# === From reviews.py ===
"""Reviews router."""


def _current_user_id(current_user: dict) -> int:
    return int(current_user["id"])


def _current_user_role(current_user: dict) -> str:
    return str(current_user.get("role") or "")


@router.get("/products/{product_id}")
def get_product_reviews_route(product_id: int, db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.read"))
):
    return get_product_reviews(db, product_id)


@router.post("/products/{product_id}")
def create_product_review(
    product_id: int,
    payload: dict = Body(default_factory=dict),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write")),
):
    if not product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        rating = float(payload.get("rating"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="rating must be a number")
    if rating < 1 or rating > 5:
        raise HTTPException(status_code=422, detail="Rating must be between 1 and 5")

    user_id = _current_user_id(current_user)
    if find_existing_review(db, product_id, user_id):
        raise HTTPException(status_code=409, detail="You have already reviewed this product")

    review = create_review(
        db,
        product_id=product_id,
        user_id=user_id,
        rating=rating,
        comment=payload.get("comment") or payload.get("body"),
        image_url=payload.get("image_url"),
        is_verified_purchase=False,
    )
    return review


@router.post("/reviews", status_code=status.HTTP_201_CREATED)
def create_review_route(payload: ReviewCreate,     current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write"))
):
    return create_product_review(
        product_id=payload.product_id,
        payload={"rating": payload.rating, "comment": getattr(payload, "body", None), "image_url": None},
        current_user=current_user,
        db=db,
    )


@router.delete("/reviews/{review_id}")
def delete_review(review_id: int,     current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write"))
):
    user_id = _current_user_id(current_user)
    user_role = _current_user_role(current_user)
    return delete_review_by_user(db, review_id, user_id, user_role)


# === From wishlist.py ===
"""Wishlist router."""


@router.post("/wishlist/{product_id}")
def add_to_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write"))
):
    if not wishlist_product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if existing:
        return {"product_id": product_id, "detail": "Already in wishlist"}
    item = create_wishlist_item(db, current_user["id"], product_id)
    return {"product_id": item.product_id, "detail": "Added to wishlist"}


@router.delete("/wishlist/{product_id}")
def remove_from_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("promotions.promotions.write"))
):
    item = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    delete_wishlist_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}
