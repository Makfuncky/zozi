"""Admin coupon management controller."""
from __future__ import annotations

from typing import Any, Optional
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from data.models import Coupon
from utils.audit import audit_log, AuditAction
from utils.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE

from services.write_helpers import add_and_flush, commit_and_refresh, commit_only, delete_only, rollback_only

def list_coupons(db: Session, *, skip: int = 0, limit: int | None = None, search: Optional[str] = None) -> dict:
    resolved_limit = _ADMIN_DEFAULT_PAGE_SIZE if limit is None else max(1, min(limit, _ADMIN_MAX_PAGE_SIZE))
    query = db.query(Coupon)
    if search and search.strip():
        query = query.filter(Coupon.code.ilike(f"%{search.strip()}%"))
    total = query.with_entities(func.count(Coupon.id)).scalar() or 0
    coupons = (
        query.order_by(Coupon.created_at.desc(), Coupon.id.desc())
        .offset(skip)
        .limit(resolved_limit)
        .all()
    )
    return _build_list_page_payload([
            {
                "id": c.id,
                "code": c.code,
                "discount_type": c.discount_type,
                "value": c.value,
                "discount_value": c.value,
                "min_order": c.min_order,
                "min_order_amount": c.min_order,
                "max_uses": c.max_uses,
                "uses_count": c.uses_count,
                "used_count": c.uses_count,
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
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")

    from datetime import datetime as _dt
    expires_raw = data.get("expires_at")
    expires_at = None
    if expires_raw:
        try:
            expires_at = _dt.fromisoformat(str(expires_raw).replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            expires_at = None

    coupon = Coupon(
        code=code,
        discount_type=data.get("discount_type", "percent"),
        value=float(data.get("value", 10)),
        min_order=float(data.get("min_order", 0)),
        max_uses=int(data["max_uses"]) if data.get("max_uses") else None,
        expires_at=expires_at,
        is_active=bool(data.get("is_active", True)),
    )
    add_and_flush(db, coupon)
    commit_and_refresh(db, coupon)
    audit_log(
        db=db,
        action="COUPON_CREATED",
        user_id=acting_user["id"],
        username=acting_user.get("username"),
        user_role=acting_user.get("role"),
        resource_type="coupon",
        resource_id=cast(int, getattr(coupon, "id")),
        details={"code": coupon.code, "value": coupon.value},
        status="success",
    )
    return {"message": "Coupon created", "id": coupon.id, "code": coupon.code}


def update_coupon(coupon_id: int, data: dict, acting_user: dict, db: Session) -> dict:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    for field in ("discount_type", "value", "min_order", "max_uses", "is_active"):
        if field in data:
            setattr(coupon, field, data[field])
    if "expires_at" in data and data["expires_at"]:
        from datetime import datetime as _dt
        try:
            setattr(coupon, "expires_at", _dt.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00")).replace(tzinfo=None))
        except ValueError:
            pass
    commit_only(db)
    return {"message": "Coupon updated", "id": coupon_id}


def delete_coupon(coupon_id: int, acting_user: dict, db: Session) -> dict:
    coupon = db.query(Coupon).filter(Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    usage_count = db.query(func.count(CouponUsage.id)).filter(CouponUsage.coupon_id == coupon_id).scalar() or 0
    if usage_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} recorded usage(s). Archive or disable it instead of deleting.",
        )

    try:
        delete_only(db, coupon)
        commit_only(db)
    except IntegrityError:
        rollback_only(db)
        raise HTTPException(
            status_code=409,
            detail="Coupon has related records that must be archived or removed before deletion.",
        )
    return {"message": "Coupon deleted"}


# â”€â”€ Support Tickets â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

