"""CouponUsage model for promotions domain."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class CouponUsage(Base):
    __tablename__ = "coupon_usages"
    __table_args__ = ({"schema": "promotions"},)
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    order_id = Column(Integer, nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
