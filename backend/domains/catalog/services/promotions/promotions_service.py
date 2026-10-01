"""Catalog domain — promotions service (coupons, banners, BOGO)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import structlog

from domains.promotions.models.promotions import Coupon

logger = structlog.get_logger(__name__)


def create_coupon(
    db: Session,
    *,
    code: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    discount_type: str = "percent",
    value: str = "0",
    discount_value: Optional[str] = None,
    maximum_discount=None,
    min_order: str = "0",
    minimum_order: Optional[str] = None,
    max_uses: Optional[int] = None,
    usage_limit: Optional[int] = None,
    per_user_limit=None,
    applicable_to=None,
    is_active: bool = True,
    starts_at=None,
    expires_at=None,
) -> Coupon:
    """Persist a new coupon (sanctioned cross-domain write)."""
    coupon = Coupon(
        code=code,
        title=title,
        description=description,
        discount_type=discount_type,
        value=value,
        discount_value=discount_value if discount_value is not None else value,
        maximum_discount=maximum_discount,
        min_order=min_order,
        minimum_order=minimum_order if minimum_order is not None else min_order,
        max_uses=max_uses,
        usage_limit=usage_limit,
        per_user_limit=per_user_limit,
        applicable_to=applicable_to,
        is_active=is_active,
        starts_at=starts_at,
        expires_at=expires_at,
    )
    try:
        db.add(coupon)
        db.commit()
        db.refresh(coupon)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("create_coupon integrity_error code=%s: %s", code, exc)
        raise
    return coupon
