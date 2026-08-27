# ARCHIVED MODULE - DO NOT IMPORT FROM `domains/_parked`.
# Historical leftover from the ORD-SLICE god-domain decomposition.
# Resolution / live owner documented in RESOLVER.md PART 5 (Sec 37) and _parked_report.txt.
# Retained for reference only; this file is NOT part of the running application.
"""Legacy coupon write service.

Holds the DB write operations originally defined in
controllers/coupons_controller.py so that module can stay read-only and
satisfy the W1 layer contract (routers/controllers must not write to the DB).

Field names here intentionally match the legacy ``models.Coupon`` shape used
by that controller (``value`` / ``min_order`` / ``max_uses`` / ``is_active``).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.audit.services.logs.audit_service import audit_log, AuditAction
from domains.governance.ports import CouponUsage
from domains.finance.ports import Coupon
from kernel.money import round_money


def create_coupon(
    code: str,
    discount_type: str,
    value: Decimal,
    min_order: Decimal,
    max_uses: Optional[int],
    is_active: bool,
    current_user: dict,
    db: Session,
) -> Coupon:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    code = code.strip().upper()
    if db.query(Coupon).filter(Coupon.code == code).first():
        raise HTTPException(status_code=409, detail="Coupon code already exists")
    if discount_type not in ("percent", "fixed"):
        raise HTTPException(status_code=422, detail="discount_type must be 'percent' or 'fixed'")
    coupon = Coupon(
        code=code,
        discount_type=discount_type,
        value=round_money(value),
        min_order=round_money(min_order),
        max_uses=max_uses,
        is_active=True,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    audit_log(
        db,
        action=AuditAction.COUPON_CREATED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="coupon",
        resource_id=coupon.id,
        details={"code": coupon.code, "discount_type": coupon.discount_type},
    )
    return coupon


def _delete_coupon_record(coupon: Coupon, current_user: dict, db: Session) -> dict:
    usage_count = db.query(CouponUsage).filter(CouponUsage.coupon_id == coupon.id).count()
    if usage_count:
        raise HTTPException(
            status_code=409,
            detail=f"Coupon has {usage_count} usage record(s). Archive or disable it instead of deleting.",
        )

    coupon_id = coupon.id
    coupon_code = coupon.code
    try:
        db.delete(coupon)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Coupon is still referenced by other records. Archive or disable it instead of deleting.",
        ) from None

    audit_log(
        db,
        action=AuditAction.COUPON_DELETED,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="coupon",
        resource_id=coupon_id,
        details={"code": coupon_code},
    )
    return {"detail": "Coupon deleted"}
