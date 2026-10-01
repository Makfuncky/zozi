"""promotions domain â€" promotion models (Coupon, Banner, BOGOPromotion, FlashSale).

Moved from domains/catalog/models/promotions.py: these are promotion concepts,
not catalog. Now properly owned by the promotions domain with schema
"promotions".

Coupon: discount codes for products/orders
Banner: promotional banners on the storefront
BOGOPromotion: Buy-One-Get-One / Buy-X-Get-Y-Free promotions
FlashSale: time-limited promotional sales
"""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow
# CountryConfig relationship resolved lazily via string reference

__all__ = ["Coupon", "Banner", "BOGOPromotion", "FlashSale"]


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(100), unique=True, index=True, nullable=False)
    discount_type = Column(String(20), default="percentage")
    discount_value = Column(Numeric(5, 2))
    minimum_order = Column(Numeric(10, 2), default=0)
    maximum_discount = Column(Numeric(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class Banner(Base):
    __tablename__ = "banners"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    subtitle = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    link = Column(String(500), nullable=True)
    banner_type = Column(String(30), default="hero")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    sort_order = Column(Integer, default=0)
    bg_color = Column(String(10), nullable=True)
    text_color = Column(String(10), nullable=True)
    subtitle_color = Column(String(10), nullable=True)
    btn_bg_color = Column(String(10), nullable=True)
    btn_text_color = Column(String(10), nullable=True)
    badge_text = Column(String(50), nullable=True)
    badge_color = Column(String(10), nullable=True)
    effect = Column(String(30), nullable=True)
    video_url = Column(String(500), nullable=True)
    cta_label = Column(String(100), nullable=True)
    cta_url = Column(String(500), nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class BOGOPromotion(Base):
    """Buy-One-Get-One (and Buy-X-Get-Y-Free) promotion definition."""
    __tablename__ = "bogo_promotions"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    buy_quantity = Column(Integer, default=1, nullable=False)
    free_quantity = Column(Integer, default=1, nullable=False)
    free_discount_pct = Column(Integer, default=100, nullable=False)
    apply_to = Column(String(20), default="all", nullable=False)
    target_id = Column(Integer, nullable=True)
    max_uses_per_customer = Column(Integer, nullable=True)
    stacking_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='RESTRICT'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)


class FlashSale(Base):
    """Time-limited promotional sale."""
    __tablename__ = "flash_sales"
    __table_args__ = ({"schema": "promotions", "extend_existing": True},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])
    items = relationship("FlashSaleItem", back_populates="flash_sale", cascade="all, delete-orphan")
