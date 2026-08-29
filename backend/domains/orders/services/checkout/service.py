"""Checkout sub-domain — address book management and coupon validation.

Merged from: commerce_read_service.py, commerce_write_service.py,
             public_commerce_validation_service.py
"""
from __future__ import annotations

import importlib
from decimal import Decimal, InvalidOperation
from typing import Optional

from fastapi import Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.promotions.models.coupon_usage import CouponUsage
from domains.promotions.models.promotions import Coupon
from domains.accounts.ports import get_current_user
from domains.governance.ports import create_address
from infrastructure.database.database import get_db
from infrastructure.utils.datetime_utils import utcnow
import structlog

logger = structlog.get_logger(__name__)


# ── Address reads ─────────────────────────────────────────────────────────────

def list_user_addresses(db: Session, user_id: int, limit: int = 100, offset: int = 0) -> list:
    return (
        db.query(Address)
        .filter(Address.user_id == int(user_id))
        .order_by(Address.is_default.desc(), Address.created_at.asc())
        .offset(max(0, offset))
        .limit(min(max(1, limit), 100))
        .all()
    )


def get_user_address(db: Session, address_id: int, user_id: int) -> Address:
    address = (
        db.query(Address)
        .filter(Address.id == address_id, Address.user_id == user_id)
        .first()
    )
    if address is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
    return address


# ── Address writes ────────────────────────────────────────────────────────────

def unset_other_default_addresses(
    db: Session, user_id: int, address_id: Optional[int] = None
) -> int:
    """Clear the ``is_default`` flag on every other address for *user_id*."""
    query = db.query(Address).filter(
        Address.user_id == user_id,
        Address.is_default.is_(True),
        Address.is_deleted.is_(False),
    )
    if address_id is not None:
        query = query.filter(Address.id != address_id)
    updated = query.update(
        {Address.is_default: False}, synchronize_session=False
    )
    db.commit()
    return updated


def unset_default_addresses(db: Session, user_id: int) -> int:
    """Clear ``is_default`` on every default address owned by *user_id*."""
    return (
        db.query(Address)
        .filter(Address.user_id == user_id, Address.is_default == True)
        .update({"is_default": False})
    )


def create_address(
    db: Session,
    *,
    user_id: int,
    full_name: str,
    address_line1: str,
    city: str,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    country: str = "US",
    is_default: bool = False,
    label: Optional[str] = None,
    phone: Optional[str] = None,
):
    """Persist a new customer address and return the saved row."""
    try:
        return create_address(
            db,
            user_id=user_id,
            full_name=full_name,
            address_line1=address_line1,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default,
            label=label,
            phone=phone,
        )
    except IntegrityError as exc:
        db.rollback()
        logger.warning("create_address integrity_error user_id=%s: %s", user_id, exc)
        raise HTTPException(status_code=409, detail="Address could not be created due to a constraint violation") from exc
    except Exception as exc:
        db.rollback()
        logger.error("create_address unexpected_error user_id=%s: %s", user_id, exc)
        raise HTTPException(status_code=500, detail="Failed to create address") from exc


def update_address(db: Session, address: Address, updates: dict) -> Address:
    """Apply *updates* to an existing address row and persist them."""
    try:
        for key, value in (updates or {}).items():
            if key == "street":
                key = "address_line1"
            if key == "country":
                setattr(address, "country", value)
                setattr(address, "country_code", (value or "US").upper())
                continue
            if hasattr(address, key):
                setattr(address, key, value)
        db.commit()
        db.refresh(address)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("update_address integrity_error address_id=%s: %s", getattr(address, "id", "?"), exc)
        raise HTTPException(status_code=409, detail="Address could not be updated due to a constraint violation") from exc
    except Exception as exc:
        db.rollback()
        logger.error("update_address unexpected_error address_id=%s: %s", getattr(address, "id", "?"), exc)
        raise HTTPException(status_code=500, detail="Failed to update address") from exc
    return address


def delete_address(db: Session, address: Address) -> None:
    """Hard-delete an address row."""
    try:
        db.delete(address)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        logger.warning("delete_address integrity_error address_id=%s: %s", getattr(address, "id", "?"), exc)
        raise HTTPException(status_code=409, detail="Address could not be deleted due to related records") from exc
    except Exception as exc:
        db.rollback()
        logger.error("delete_address unexpected_error address_id=%s: %s", getattr(address, "id", "?"), exc)
        raise HTTPException(status_code=500, detail="Failed to delete address") from exc


def set_default_address(db: Session, address: Address) -> Address:
    """Mark *address* as the user's default address and persist it."""
    try:
        address.is_default = True
        db.commit()
        db.refresh(address)
    except Exception as exc:
        db.rollback()
        logger.error("set_default_address unexpected_error address_id=%s: %s", getattr(address, "id", "?"), exc)
        raise HTTPException(status_code=500, detail="Failed to set default address") from exc
    return address


# ── Coupon validation ─────────────────────────────────────────────────────────

def _normalize_discount_type(value: object) -> str | None:
    return {'percent': 'percent', 'percentage': 'percent', 'fixed': 'fixed', 'fixed_amount': 'fixed', 'amount': 'fixed'}.get(str(value or '').strip().lower())


def _to_decimal(value: object, default: str = '0') -> Decimal:
    if value is None:
        return Decimal(default)
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if text == '' or text.lower() in {'none', 'null', 'nan'}:
        return Decimal(default)
    try:
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return Decimal(default)


def _require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    if str(current_user.get('role') or '').lower() != 'admin':
        raise HTTPException(status_code=403, detail='Admin access required')
    return current_user


def _to_int(value: object, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).strip()
    if text == '' or text.lower() in {'none', 'null', 'nan'}:
        return default
    try:
        return int(float(text))
    except ValueError:
        return default


def validate_coupon(request: Request, payload: dict | None = Body(default=None), _: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Validate a coupon code for a given order total."""
    try:
        payload = {**dict(request.query_params), **(payload or {})}
        code = str(payload.get('code') or '').strip()
        order_total = payload.get('order_total', payload.get('order_subtotal'))
        if not code or order_total is None:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='code and order_total are required')
        coupon = db.query(Coupon).filter(Coupon.code == code, Coupon.is_active == True).first()
        if coupon is None:
            raise HTTPException(status_code=404, detail='Coupon not found')
        now = utcnow()
        total = _to_decimal(order_total)
        minimum_order_raw = getattr(coupon, 'minimum_order', None)
        if minimum_order_raw is None:
            minimum_order_raw = getattr(coupon, 'min_order', 0)
        minimum_order = _to_decimal(minimum_order_raw)
        usage_limit = getattr(coupon, 'usage_limit', None)
        if usage_limit is None:
            usage_limit = getattr(coupon, 'max_uses', None)
        usage_count = getattr(coupon, 'usage_count', None)
        if usage_count is None:
            usage_count = getattr(coupon, 'uses_count', 0)
        discount_value_raw = getattr(coupon, 'discount_value', None)
        if discount_value_raw is None:
            discount_value_raw = getattr(coupon, 'value', 0)
        if coupon.starts_at and coupon.starts_at > now:
            raise HTTPException(status_code=400, detail='Coupon not active yet')
        if coupon.expires_at and coupon.expires_at < now:
            raise HTTPException(status_code=400, detail='Coupon expired')
        if usage_limit is not None and _to_int(usage_count) >= _to_int(usage_limit):
            raise HTTPException(status_code=400, detail='Usage limit reached')
        if total < minimum_order:
            raise HTTPException(status_code=422, detail=f'Minimum order {minimum_order}')
        discount_type = str(coupon.discount_type or '').lower()
        discount = total * _to_decimal(discount_value_raw) / Decimal('100') if discount_type in {'percent', 'percentage'} else _to_decimal(discount_value_raw)
        if coupon.maximum_discount is not None:
            discount = min(discount, _to_decimal(coupon.maximum_discount))
        new_total = max(Decimal('0'), total - discount)
        return {'valid': True, 'discount_amount': float(discount), 'new_total': float(new_total), 'coupon': coupon}
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("validate_coupon unexpected_error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Coupon validation failed") from exc


def list_coupons(_: dict = Depends(_require_admin), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    total = db.query(Coupon).count()
    coupons = db.query(Coupon).offset((page - 1) * page_size).limit(page_size).all()
    return {'data': coupons, 'total': total, 'page': page, 'page_size': page_size}


def create_coupon(request: Request, payload: dict | None = Body(default=None), _: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    payload = {**dict(request.query_params), **(payload or {})}
    code = str(payload.get('code') or '').strip().upper()
    if not code:
        raise HTTPException(status_code=422, detail='Coupon code is required')
    if db.query(Coupon).filter(Coupon.code == code).first() is not None:
        raise HTTPException(status_code=409, detail='Coupon already exists')
    discount_type = _normalize_discount_type(payload.get('discount_type') or 'percent')
    if discount_type is None:
        raise HTTPException(status_code=422, detail='discount_type must be one of: percent, fixed')
    discount_value = _to_decimal(payload.get('discount_value', payload.get('value')))
    minimum_order = _to_decimal(payload.get('minimum_order', payload.get('min_order', payload.get('min_order_amount', 0))))
    usage_limit_raw = payload.get('usage_limit', payload.get('max_uses'))
    usage_limit = None
    if usage_limit_raw not in (None, '', 'none', 'null', 'nan'):
        usage_limit = _to_int(usage_limit_raw)
    from domains.catalog.ports import create_coupon as _catalog_create_coupon
    try:
        coupon = _catalog_create_coupon(
            db,
            code=code,
            title=payload.get('title'),
            description=payload.get('description'),
            discount_type=discount_type,
            value=str(discount_value),
            discount_value=str(discount_value),
            maximum_discount=payload.get('maximum_discount'),
            min_order=str(minimum_order),
            minimum_order=str(minimum_order),
            max_uses=usage_limit,
            usage_limit=usage_limit,
            per_user_limit=payload.get('per_user_limit'),
            applicable_to=payload.get('applicable_to'),
            is_active=bool(payload.get('is_active', True)),
            starts_at=payload.get('starts_at'),
            expires_at=payload.get('expires_at'),
        )
    except IntegrityError as exc:
        db.rollback()
        logger.warning("create_coupon integrity_error code=%s: %s", code, exc)
        raise HTTPException(status_code=409, detail="Coupon could not be created due to a constraint violation") from exc
    except Exception as exc:
        db.rollback()
        logger.error("create_coupon unexpected_error code=%s: %s", code, exc)
        raise HTTPException(status_code=500, detail="Failed to create coupon") from exc
    db.refresh(coupon)
    return coupon


def delete_coupon(coupon_id: str, _: dict = Depends(_require_admin), db: Session = Depends(get_db)):
    coupon = db.query(Coupon).filter((Coupon.code == coupon_id) | (Coupon.id == int(coupon_id) if coupon_id.isdigit() else False)).first()
    if coupon is None:
        raise HTTPException(status_code=404, detail='Coupon not found')
    if db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).first() is not None:
        raise HTTPException(status_code=409, detail='Archive or disable it instead of deleting a coupon with usage history')
    db.delete(coupon)
    db.commit()
    return {'message': 'Deleted'}


# ── Lazy re-exports ───────────────────────────────────────────────────────────

_REEXPORTS: dict[str, tuple[str, str]] = {
    "clear_wishlist": ("services.commerce.wishlist_write_service", "clear_wishlist"),
    "create_wishlist_item": ("services.commerce.wishlist_write_service", "create_wishlist_item"),
    "delete_wishlist_item": ("services.commerce.wishlist_write_service", "delete_wishlist_item"),
    "create_review": ("controllers.commerce.reviews_controller", "create_review"),
    "update_review": ("controllers.commerce.reviews_controller", "update_review"),
    "delete_review": ("controllers.commerce.reviews_controller", "delete_review"),
    "soft_delete_review": ("services.commerce.reviews_service", "soft_delete_review"),
}


def __getattr__(name: str):
    spec = _REEXPORTS.get(name)
    if spec is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = importlib.import_module(spec[0])
    value = getattr(module, spec[1])
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(_REEXPORTS))
