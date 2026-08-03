"""Coupon routes with compatibility for recovered request and response contracts."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.db import get_db
from data.schemas import CursorPage
from data.models import Coupon, CouponUsage
from utils.datetime_utils import utcnow
from utils.pagination import cursor_paginate_desc

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, delete_only
router = APIRouter()


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


def _parse_datetime(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


@router.get("/validate")
@router.post("/validate")
def validate_coupon(
    request: Request,
    code: str = Query(None),
    order_amount: Decimal = Query(None),
    payload: dict | None = Body(default=None),
    db: Session = Depends(get_db),
):
    """Validate a coupon code for a given order amount.

    Accepts both GET (query params) and POST (body) for compatibility.
    No auth required — used by checkout flow.
    """
    if code is None and payload:
        code = payload.get("code")
    if order_amount is None and payload:
        order_amount = payload.get("order_amount", payload.get("order_total", payload.get("order_subtotal")))

    code = str(code or request.query_params.get("code", "")).strip()
    if order_amount is None:
        order_amount = request.query_params.get("order_amount")
    if not code or order_amount is None:
        return {"valid": False, "error": "code and order_amount are required"}

    coupon = db.query(Coupon).filter(Coupon.code == code, Coupon.is_active == True).first()
    if coupon is None:
        return {"valid": False, "error": "Coupon not found"}

    now = utcnow()
    total = _to_decimal(order_amount)
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
        return {"valid": False, "error": "Coupon not active yet"}
    if coupon.expires_at and coupon.expires_at < now:
        return {"valid": False, "error": "Coupon expired"}
    if usage_limit is not None and _to_int(usage_count) >= _to_int(usage_limit):
        return {"valid": False, "error": "Usage limit reached"}
    if total < minimum_order:
        return {"valid": False, "error": f"Minimum order {minimum_order}"}

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


@router.get("", response_model=CursorPage)
def list_coupons(_: dict = Depends(_require_admin), db: Session = Depends(get_db), cursor: str | None = Query(None, description="Cursor for next page"), limit: int = Query(20, ge=1, le=100)):
    q = db.query(Coupon).order_by(Coupon.id.desc())
    return cursor_paginate_desc(q, cursor=cursor, page_size=limit)


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

    starts_at = _parse_datetime(payload.get("starts_at", payload.get("valid_from")))
    expires_at = _parse_datetime(payload.get("expires_at", payload.get("valid_until")))

    usage_limit_raw = payload.get("usage_limit", payload.get("max_uses"))
    usage_limit = None
    if usage_limit_raw not in (None, "", "none", "null", "nan"):
        usage_limit = _to_int(usage_limit_raw)

    coupon = Coupon(
        code=code,
        title=payload.get("title"),
        description=payload.get("description"),
        discount_type=discount_type,
        discount_value=discount_value,
        maximum_discount=payload.get("maximum_discount"),
        minimum_order=minimum_order,
        min_order_amount=minimum_order,
        usage_limit=usage_limit,
        is_active=bool(payload.get("is_active", True)),
        starts_at=starts_at,
        expires_at=expires_at,
    )
    add_and_flush(db, coupon)
    commit_and_refresh(db, coupon)
    return coupon


@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter((Coupon.code == coupon_id) | (Coupon.id == int(coupon_id) if coupon_id.isdigit() else False)).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail="Coupon not found")
    if db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).first() is not None:
        raise HTTPException(status_code=409, detail="Archive or disable it instead of deleting a coupon with usage history")
    delete_only(db, coupon)
    commit_only(db)
    return {"message": "Deleted"}

