from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["CommissionAgreement", "ProductCommissionOverride", "CommissionLedgerEntry", "CommissionCategoryRate"]


class CommissionAgreement(Base):
    __tablename__ = "commission_agreements"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    country_code = Column(String(10), nullable=True)
    tier = Column(String(20), nullable=False)
    rate = Column(Numeric(5, 4), nullable=False)
    set_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    effective_from = Column(DateTime, default=_utcnow)
    effective_to = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class ProductCommissionOverride(Base):
    __tablename__ = "product_commission_overrides"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rate_percent = Column(Numeric(5, 2), nullable=False)
    set_by_admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class CommissionLedgerEntry(Base):
    __tablename__ = "commission_ledger_entries"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    order_item_id = Column(Integer, ForeignKey("order_items.id"), nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)
    category_slug = Column(String(100), nullable=True)
    badge_level = Column(String(20), nullable=True)
    global_default_rate = Column(Numeric(5, 4), nullable=True)
    category_rate = Column(Numeric(5, 4), nullable=True)
    badge_rate = Column(Numeric(5, 4), nullable=True)
    override_rate = Column(Numeric(5, 4), nullable=True)
    applied_rate = Column(Numeric(5, 4), nullable=True)
    calculation_method = Column(String(20), nullable=True)
    order_value = Column(Numeric(12, 2), nullable=True)
    commission_pct = Column(Numeric(12, 2), nullable=True)
    cap_applied = Column(Boolean, default=False)
    commission_amount = Column(Numeric(12, 2), nullable=True)
    low_value_threshold_used = Column(Boolean, default=False)
    fixed_cap_used = Column(Boolean, default=False)
    override_flag = Column(Boolean, default=False)
    is_adjusted = Column(Boolean, default=False)
    currency = Column(String(3), default="OMR")
    amount = Column(Numeric(12, 2), nullable=True)
    adjusted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="pending")
    credited_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)


class CommissionCategoryRate(Base):
    __tablename__ = 'commission_category_rates'
    __table_args__ = (
        UniqueConstraint('category_id', 'category_slug', name='uq_commission_category_rate'), {"schema": "commerce"})
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    category_slug = Column(String(100), nullable=True)
    category_display_name = Column(String(100), nullable=True)
    country_code = Column(String(10), ForeignKey('country_configs.code'), nullable=True)
    rate_percent = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])
