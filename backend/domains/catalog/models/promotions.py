"""Promotion ORM models (BOGO / Buy-X-Get-Y-Free and related promotion types)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["BOGOPromotion"]


class BOGOPromotion(Base):
    """Buy-One-Get-One (and Buy-X-Get-Y-Free) promotion definition.

    Consumed by ``services.commerce.promotion_bogo_service.find_eligible_bogo_promotions``.
    """

    __tablename__ = "bogo_promotions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    buy_quantity = Column(Integer, default=1, nullable=False)
    free_quantity = Column(Integer, default=1, nullable=False)
    free_discount_pct = Column(Integer, default=100, nullable=False)
    apply_to = Column(String(20), default="all", nullable=False)  # "product" | "category" | "all"
    target_id = Column(Integer, nullable=True)
    max_uses_per_customer = Column(Integer, nullable=True)
    stacking_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

