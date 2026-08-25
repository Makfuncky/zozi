"""Customer promotions router — consolidated from 5 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/customer/promotions", tags=["customer", "promotions"])


# === From coupons.py ===
"""Coupon routes with compatibility for recovered request and response contracts."""
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.admin import CouponUsage
from domains.catalog.models.promotions import Coupon
from infrastructure.utils.datetime_utils import utcnow

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
):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get("code") or "").strip()
    order_total = payload.get("order_total", payload.get("order_subtotal"))
    if not code or order_total is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="code and order_total are required")

    coupon = db.query(Coupon).filter(Coupon.code == code, Coupon.is_active == True).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")

    now = utcnow()
    total = _to_decimal(order_total)
    minimum_order_raw = getattr(coupon, "minimum_order", None)
    if minimum_order_raw is None:
        minimum_order_raw = getattr(coupon, "min_order", 0)
    minimum_order = _to_decimal(minimum_order_raw)
    usage_limit = getattr(coupon, "usage_limit", None)
    if usage_limit is None:
        usage_limit = getattr(coupon, "max_uses", None)
    usage_count = getattr(coupon, "usage_count", None)
    if usage_count is None:
        usage_count = getattr(coupon, "uses_count", 0)
    discount_value_raw = getattr(coupon, "discount_value", None)
    if discount_value_raw is None:
        discount_value_raw = getattr(coupon, "value", 0)
    if coupon.starts_at and coupon.starts_at > now:
        raise HTTPException(status_code=400, detail="Coupon not active yet")
    if coupon.expires_at and coupon.expires_at < now:
        raise HTTPException(status_code=400, detail="Coupon expired")
    if usage_limit is not None and _to_int(usage_count) >= _to_int(usage_limit):
        raise HTTPException(status_code=400, detail="Usage limit reached")
    if total < minimum_order:
        raise HTTPException(status_code=422, detail=f"Minimum order {minimum_order}")

    discount_type = str(coupon.discount_type or "").lower()
    discount = (
        total * _to_decimal(discount_value_raw) / Decimal("100")
        if discount_type in {"percent", "percentage"}
        else _to_decimal(discount_value_raw)
    )
    if coupon.maximum_discount is not None:
        discount = min(discount, _to_decimal(coupon.maximum_discount))
    new_total = max(Decimal("0"), total - discount)
    return {
        "valid": True,
        "discount_amount": float(discount),
        "new_total": float(new_total),
        "coupon": coupon,
    }


@router.get("")
def list_coupons(_: dict = Depends(_require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    total = db.query(Coupon).count()
    coupons = db.query(Coupon).offset((page - 1) * page_size).limit(page_size).all()
    return {"data": coupons, "total": total, "page": page, "page_size": page_size}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_coupon(
    request: Request,
    payload: dict | None = Body(default=None),
    _: dict = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail="Coupon code is required")
    if db.query(Coupon).filter(Coupon.code == code).first() is not None:
        raise HTTPException(status_code=409, detail="Coupon already exists")

    discount_type = _normalize_discount_type(payload.get("discount_type") or "percent")
    if discount_type is None:
        raise HTTPException(status_code=422, detail="discount_type must be one of: percent, fixed")

    discount_value = _to_decimal(payload.get("discount_value", payload.get("value")))
    minimum_order = _to_decimal(payload.get("minimum_order", payload.get("min_order", payload.get("min_order_amount", 0))))
    usage_limit_raw = payload.get("usage_limit", payload.get("max_uses"))
    usage_limit = None
    if usage_limit_raw not in (None, "", "none", "null", "nan"):
        usage_limit = _to_int(usage_limit_raw)

    coupon = Coupon(
        code=code,
        title=payload.get("title"),
        description=payload.get("description"),
        discount_type=discount_type,
        value=discount_value,
        discount_value=discount_value,
        maximum_discount=payload.get("maximum_discount"),
        min_order=minimum_order,
        minimum_order=minimum_order,
        max_uses=usage_limit,
        usage_limit=usage_limit,
        per_user_limit=payload.get("per_user_limit"),
        applicable_to=payload.get("applicable_to"),
        is_active=bool(payload.get("is_active", True)),
        starts_at=payload.get("starts_at"),
        expires_at=payload.get("expires_at"),
    )
    # Defensive guard against recovered runtime paths that can leak legacy values.
    coupon.discount_type = _normalize_discount_type(coupon.discount_type) or "percent"
    db.add(coupon)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        normalized_discount_type = _normalize_discount_type(coupon.discount_type)
        if normalized_discount_type is None:
            raise exc
        coupon.discount_type = normalized_discount_type
        db.add(coupon)
        db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter((Coupon.code == coupon_id) | (Coupon.id == int(coupon_id) if coupon_id.isdigit() else False)).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).first() is not None:
        raise HTTPException(status_code=409, detail="Archive or disable it instead of deleting a coupon with usage history")
    db.delete(coupon)
    db.commit()
    return {"message": "Deleted"}




# === From customer_coupons_create.py ===
"""Customer coupons router (ROUTERS layer, flat file).

Thin HTTP layer: request parsing/validation, authentication, pagination query
params, and delegation to ``controllers.commerce.coupons_controller``. No direct
DB/ORM access here; all persistence lives in the services layer. Keyset
(cursor) pagination is accepted via ``cursor``/``limit`` and forwarded to the
controller — this layer performs no skip-based scanning.
"""

from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from domains.customers.services.coupons_service import create_coupon as ctrl_create
from domains.customers.services.coupons_service import delete_coupon as ctrl_delete
from domains.customers.services.coupons_read_service import list_coupons as ctrl_list
from domains.customers.services.coupons_service import validate_coupon as ctrl_validate
from infrastructure.database.schemas import CouponCreate
from infrastructure.utils.dependencies import get_current_user, get_db, require_admin


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



# === From customer_coupons_mgmt.py ===
"""Coupon routes with compatibility for recovered request and response contracts.

Thin HTTP layer: request parsing/validation lives here; all coupon persistence
and validation business logic is delegated to ``services.commerce.coupons_write_service``
so the router stays free of ``db.query``/``db.add``/``db.commit``. Endpoints, auth and
response shapes are unchanged from the previous inline implementation.
"""
from fastapi import APIRouter, Body, Depends, Request, status

from rbac import get_current_user
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
from domains.customers.services.coupons_write_service import create_coupon_from_payload
from domains.customers.services.coupons_write_service import delete_coupon_by_id
from domains.customers.services.coupons_read_service import list_coupons_paginated
from domains.customers.services.coupons_service import validate_coupon

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



# === From reviews.py ===
"""Reviews router."""
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import ReviewCreate
from domains.governance.models.user import User
from infrastructure.utils.dependencies import get_current_user
from domains.customers.services.reviews_service import (
    create_review,
    find_existing_review,
    get_product_reviews,
    product_exists,
    soft_delete_review,
)

def _current_user_id(current_user: User | dict) -> int:
    if isinstance(current_user, dict):
        return int(current_user["id"])
    return int(current_user.id)


def _current_user_role(current_user: User | dict) -> str:
    if isinstance(current_user, dict):
        return str(current_user.get("role") or "")
    return str(current_user.role or "")


@router.get("")
def list_reviews(product_id: int = Query(...), db: Session = Depends(get_db)):
    return get_product_reviews(db, product_id)


@router.get("/products/{product_id}")
def get_product_reviews_route(product_id: int, db: Session = Depends(get_db)):
    return get_product_reviews(db, product_id)


@router.post("/products/{product_id}")
def create_product_review(
    product_id: int,
    payload: dict = Body(default_factory=dict),
    current_user: User | dict = Depends(get_current_user),
    db: Session = Depends(get_db),
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


@router.post("")
def create_review_route(payload: ReviewCreate, current_user: User | dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_product_review(
        product_id=payload.product_id,
        payload={"rating": payload.rating, "comment": getattr(payload, "body", None), "image_url": None},
        current_user=current_user,
        db=db,
    )


@router.delete("/{review_id}")
def delete_review(review_id: int, current_user: User | dict = Depends(get_current_user), db: Session = Depends(get_db)):
    from domains.catalog.models.products import Review

    review = db.query(Review).filter(Review.id == review_id, Review.is_deleted == False).first()  # noqa: E712
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    if review.user_id != _current_user_id(current_user) and _current_user_role(current_user) != "admin":
        raise HTTPException(status_code=403, detail="Not authorised")
    soft_delete_review(db, review)
    return {"detail": "Review deleted"}



# === From wishlist.py ===
"""Wishlist router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import get_current_user
from domains.customers.services.wishlist_read_service import (
    get_user_wishlist,
    get_wishlist_item_by_product,
    product_exists,
)
from domains.customers.services.wishlist_write_service import (
    create_wishlist_item,
    delete_wishlist_item,
)

@router.get("")
def get_wishlist(limit: int = 200, offset: int = 0, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_user_wishlist(db, current_user["id"], limit=limit)


@router.post("/{product_id}")
def add_to_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    if not product_exists(db, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    existing = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if existing:
        return {"product_id": product_id, "detail": "Already in wishlist"}
    item = create_wishlist_item(db, current_user["id"], product_id)
    return {"product_id": item.product_id, "detail": "Added to wishlist"}


@router.delete("/{product_id}")
def remove_from_wishlist(product_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_wishlist_item_by_product(db, current_user["id"], product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Wishlist item not found")
    delete_wishlist_item(db, item)
    return {"product_id": product_id, "detail": "Removed from wishlist"}

