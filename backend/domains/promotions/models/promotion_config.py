"""PromotionEngineConfig model for promotions domain."""
from __future__ import annotations

from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class PromotionEngineConfig(Base):
    __tablename__ = "promotion_engine_configs"
    __table_args__ = ({"schema": "promotions"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True, index=True)
    engine_enabled = Column(Boolean, default=False)
    allow_product_coupons = Column(Boolean, default=True)
    allow_category_coupons = Column(Boolean, default=True)
    allow_order_tier_discounts = Column(Boolean, default=True)
    allow_referral_rewards = Column(Boolean, default=True)
    allow_supplier_promotions = Column(Boolean, default=True)
    allow_global_coupons = Column(Boolean, default=True)
    stacking_mode = Column(String, default="best_only")
    max_combined_discount_percent = Column(Numeric(5, 2), default=Decimal("50.00"))
    max_combined_discount_amount = Column(Numeric(12, 3), default=Decimal("0.000"))
    show_savings_line_item = Column(Boolean, default=True)
    tier_discount_visible = Column(Boolean, default=True)
    points_per_omr = Column(Integer, default=1000)
    referral_referrer_points = Column(Integer, default=100)
    referral_referee_points = Column(Integer, default=100)
    points_expiry_months = Column(Integer, default=12)
    referral_monthly_cap = Column(Integer, default=20)
    referral_verification_delay_days = Column(Integer, default=7)
    min_points_redeem = Column(Integer, default=1000)
    allow_partial_points_redemption = Column(Boolean, default=True)
    updated_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True, index=True)

    country = relationship("CountryConfig", foreign_keys=[country_code])
