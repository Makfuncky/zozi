"""Admin coupon management controller."""
from __future__ import annotations

from typing import Optional, cast

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from data.models import Coupon
from services.commerce.coupons_write_service import (
    create_coupon as _create_coupon,
    delete_coupon as _delete_coupon,
    get_coupon_usage_count as _get_coupon_usage_count,
    update_coupon as _update_coupon,
)
from services.common.db_read import all_rows, exists, first, scalar_with_filters
from utils.audit import audit_log
from utils.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE
import structlog
logger = structlog.get_logger(__name__)


def _build_list_page_payload(items: list, total: int, *, offset: int = 0, page_size: int = 20) -> dict:
    return {
        "data": items,
        "total": total,
        "offset": offset,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 0,
    }


def list_coupons(db: Session, *, skip: int = 0, limit: int | None = None, search: Optional[str] = None) -> dict:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    filters: list = []
    if search and search.strip():
        filters.append(Coupon.code.ilike(f"%{search.strip()}%"))
    total = scalar_with_filters(db, func.count(Coupon.id), filters) or 0
    coupons = all_rows(
        db,
        Coupon,
        filters,
        order_by=[Coupon.created_at.desc(), Coupon.id.desc()],
        offset=skip,
        limit=resolved_limit,
    )
    return _build_list_page_payload([
            {
                "id": c.id,
                "code": c.code,
                "discount_type": c.discount_type,
                "value": c.discount_value,
                "discount_value": c.discount_value,
                "min_order": c.minimum_order,
                "min_order_amount": c.minimum_order,
                "max_uses": c.usage_limit,
                "uses_count": c.usage_count,
                "used_count": c.usage_count,
                "expires_at": c.expires_at,
                "is_active": c.is_active,
                "created_at": c.created_at,
            }
            for c in coupons
        ], total, offset=skip, page_size=resolved_limit)


def create_coupon(data: dict, acting_user: dict, db: Session) -> dict:
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Coupon code is required")
    if exists(db, Coupon, [Coupon.code == code]):
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    from datetime import datetime as _dt
    expires_raw = data.get("expires_at")
    expires_at = None
    if expires_raw:
        try:
            expires_at = _dt.fromisoformat(str(expires_raw).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError as e:
            logger.exception("create_coupon_failed", error=str(e))
            expires_at = None

    coupon_data = {
        "code": code,
        "discount_type": data.get("discount_type", "percent"),
        "discount_value": float(data.get("value", 10)),
        "minimum_order": float(data.get("min_order", 0)),
        "usage_limit": int(data["max_uses"]) if data.get("max_uses") else None,
        "expires_at": expires_at,
        "is_active": bool(data.get("is_active", True)),
    }
    coupon = _create_coupon(db, **coupon_data)
    audit_log(
        db=db,
        action="COUPON_CREATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="coupon",
        resource_id=cast(int, coupon.id),
        details={"code": coupon.code, "value": coupon.discount_value},
        status="success",
    )
    return {"message": "Coupon created", "id": coupon.id, "code": coupon.code}


def update_coupon(coupon_id: int, data: dict, acting_user: dict, db: Session) -> dict:
    coupon = first(db, Coupon, [Coupon.id == coupon_id])
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    
    updates = {}
    for field in ("discount_type", "discount_value", "minimum_order", "usage_limit", "is_active"):
        api_field = field
        if field == "discount_value":
            api_field = "value"
        elif field == "minimum_order":
            api_field = "min_order"
        elif field == "usage_limit":
            api_field = "max_uses"
        if api_field in data:
            updates[field] = data[api_field]
    
    if "expires_at" in data and data["expires_at"]:
        from datetime import datetime as _dt
        try:
            updates["expires_at"] = _dt.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError as e:
            logger.exception("update_coupon_failed", error=str(e))
    
    _update_coupon(db, coupon, updates)
    return {"message": "Coupon updated", "id": coupon_id}


def delete_coupon(coupon_id: int, acting_user: dict, db: Session) -> dict:
    coupon = first(db, Coupon, [Coupon.id == coupon_id])
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    usage_count = _get_coupon_usage_count(db, coupon_id)
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} recorded usage(s). Archive or disable it instead of deleting.",
        )

    try:
        _delete_coupon(db, coupon)
    except IntegrityError as e:
        logger.exception("delete_coupon_failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Coupon has related records that must be archived or removed before deletion.",
        )
    return {"message": "Coupon deleted"}


# â”€â”€ Support Tickets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

