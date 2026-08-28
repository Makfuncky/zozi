"""Segmentation service — RFM analysis, lifetime value, and free-form tags.

Segments are computed deterministically from the user's order history (read
via ``orders.ports`` per Law 3). LTV is the sum of completed/delivered order
totals expressed as ``Decimal`` to avoid float drift. Free-form tags are
persisted in ``CustomerTag`` (schema ``customer``).
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.customers.models import CustomerTag
from domains.orders.ports import Order
from infrastructure.utils.datetime_utils import utcnow
import structlog

logger = structlog.get_logger(__name__)


_LOYALTY_THRESHOLDS = (
    ("vip", Decimal("2000")),
    ("gold", Decimal("1000")),
    ("silver", Decimal("500")),
    ("bronze", Decimal("0")),
)


def _classify_segment(lifetime_value: Decimal, recency_days: Optional[int], frequency: int) -> str:
    """Return the RFM-derived segment label for a customer."""
    if lifetime_value <= Decimal("0") and frequency == 0:
        return "new"
    if recency_days is not None and recency_days > 180:
        return "at_risk"
    for label, threshold in _LOYALTY_THRESHOLDS:
        if lifetime_value >= threshold:
            return label
    return "bronze"


def _serialize_tag(row: CustomerTag) -> Dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "tag": row.tag,
        "created_at": row.created_at,
    }


class SegmentationService:
    """Service facade for RFM, LTV, and free-form tags."""

    def __init__(self, db: Session):
        self.db = db

    def get_customer_segment(self, user_id: int) -> Dict[str, Any]:
        """Compute the RFM segment for a customer from their order history."""
        orders = (
            self.db.query(Order)
            .filter(Order.user_id == int(user_id), Order.is_deleted.is_(False))
            .order_by(Order.created_at.desc())
            .all()
        )
        if not orders:
            return {
                "user_id": int(user_id),
                "segment": "new",
                "lifetime_value": Decimal("0.00"),
                "order_count": 0,
                "last_order_at": None,
                "recency_days": None,
            }
        lifetime = sum(
            (o.total_amount for o in orders if o.total_amount is not None),
            Decimal("0.00"),
        )
        now = utcnow()
        last_order = orders[0]
        last_at = getattr(last_order, "created_at", None)
        recency = None
        if last_at is not None:
            recency = (now - last_at).days
        segment = _classify_segment(lifetime, recency, len(orders))
        return {
            "user_id": int(user_id),
            "segment": segment,
            "lifetime_value": lifetime,
            "order_count": len(orders),
            "last_order_at": last_at,
            "recency_days": recency,
        }

    def get_ltv(self, user_id: int) -> Dict[str, Any]:
        """Return the lifetime value and supporting order stats."""
        segment = self.get_customer_segment(user_id)
        return {
            "user_id": int(user_id),
            "lifetime_value": segment["lifetime_value"],
            "order_count": segment["order_count"],
            "last_order_at": segment["last_order_at"],
            "segment": segment["segment"],
        }

    def tag_customer(self, user_id: int, tag: str) -> Dict[str, Any]:
        """Add a free-form tag to a customer. Idempotent on (user_id, tag)."""
        tag = (tag or "").strip()
        if not tag:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tag must be a non-empty string.",
            )
        if len(tag) > 64:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tag must be 64 characters or fewer.",
            )
        existing = (
            self.db.query(CustomerTag)
            .filter(
                CustomerTag.user_id == int(user_id),
                CustomerTag.tag == tag,
            )
            .first()
        )
        if existing is not None:
            existing.is_deleted = False
            row = existing
        else:
            row = CustomerTag(user_id=int(user_id), tag=tag)
            self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            logger.warning(
                "segmentation.tag_conflict", user_id=user_id, tag=tag, error=str(exc)
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag already exists.",
            ) from exc
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "segmentation.tag_failed", user_id=user_id, tag=tag, error=str(exc)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add tag.",
            ) from exc
        self.db.refresh(row)
        return _serialize_tag(row)
