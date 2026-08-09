"""Coupon read service (SERVICES layer).

Owns all read access for ``coupons``. Routers and controllers must not query
the ORM directly for coupon reads. Pagination uses keyset (cursor) semantics
over a stable ``id DESC`` sort so concurrent inserts never cause the drift
that skip-based pagination suffers from.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from data.models import Coupon, CouponUsage
from utils.pagination import SAFE_QUERY_LIMIT
import structlog
logger = structlog.get_logger(__name__)


def get_coupon_by_code_active(db: Session, code: str) -> Optional[Coupon]:
    """Return the active coupon for ``code`` (case-insensitive, trimmed)."""
    normalized = (code or "").strip().upper()
    return (
        db.query(Coupon)
        .filter(Coupon.code == normalized, Coupon.is_active.is_(True), Coupon.is_deleted.is_(False))
        .first()
    )


def get_coupon_by_id(db: Session, coupon_id: int) -> Optional[Coupon]:
    return db.query(Coupon).filter(Coupon.id == coupon_id).first()


def get_coupon_usage_count(db: Session, coupon_id: int) -> int:
    return int(
        db.query(func.count(CouponUsage.id))
        .filter(CouponUsage.coupon_id == coupon_id)
        .scalar()
        or 0
    )


def list_coupons(
    db: Session,
    limit: int = SAFE_QUERY_LIMIT,
    cursor: Optional[int] = None,
) -> List[Coupon]:
    """Keyset (cursor) pagination over active, non-deleted coupons.

    ``cursor`` is the ``id`` of the last coupon the caller saw; the next page
    returns coupons with a strictly smaller ``id`` under a stable ``id DESC``
    sort. This avoids position-based scanning and the drift it causes when rows
    are inserted concurrently.
    """
    query = db.query(Coupon).filter(Coupon.is_deleted.is_(False))
    if cursor is not None:
        query = query.filter(Coupon.id < int(cursor))
    return query.order_by(Coupon.id.desc()).limit(min(max(1, limit), SAFE_QUERY_LIMIT)).all()
