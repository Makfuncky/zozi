from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["CommissionAgreement", "ProductCommissionOverride", "CommissionLedgerEntry", "CommissionCategoryRate"]


class CommissionAgreement(Base):
    __tablename__ = "commission_agreements"
    uuid = Column(String(36), unique=True, nullable=False)
    version = Column(Integer, nullable=False, server_default='1')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_commission_agreements_country', 'country_code'), Index('ix_commission_agreements_supplier', 'supplier_id'), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=False, index=True)
    country_code = Column(String(2), nullable=False, index=True)
    tier = Column(String(20), nullable=False)
    rate = Column(Numeric(5, 4), nullable=False)
    set_by_admin_id = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(DateTime, default=_utcnow)
    effective_to = Column(DateTime, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class ProductCommissionOverride(Base):
    __tablename__ = "product_commission_overrides"
    uuid = Column(String(36), unique=True, nullable=False)
    version = Column(Integer, nullable=False, server_default='1')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_product_commission_overrides_country', 'country_code'), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id", ondelete="SET NULL"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=False, index=True)
    rate_percent = Column(Numeric(5, 2), nullable=False)
    set_by_admin_id = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)


class CommissionLedgerEntry(Base):
    __tablename__ = "commission_ledger_entries"
    uuid = Column(String(36), unique=True, nullable=False)
    version = Column(Integer, nullable=False, server_default='1')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_commission_ledger_country', 'country_code'), Index('ix_commission_ledger_supplier', 'supplier_id'), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id", ondelete="SET NULL"), nullable=True, index=True)
    order_item_id = Column(Integer, ForeignKey("commerce.order_items.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id", ondelete="SET NULL"), nullable=True, index=True)
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
    adjusted_by = Column(Integer, ForeignKey("governance.users.id", ondelete="SET NULL"), nullable=True, index=True)
    status = Column(String(30), default="pending")
    credited_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(2), nullable=True, index=True)


class CommissionCategoryRate(Base):
    __tablename__ = 'commission_category_rates'
    uuid = Column(String(36), unique=True, nullable=False)
    version = Column(Integer, nullable=False, server_default='1')
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (
        UniqueConstraint('category_id', 'category_slug', name='uq_commission_category_rate'),
        Index('ix_commission_category_rates_country', 'country_code'),
        {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('commerce.categories.id', ondelete="SET NULL"), nullable=True, index=True)
    category_slug = Column(String(100), nullable=True)
    category_display_name = Column(String(100), nullable=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete="SET NULL"), nullable=True, index=True)
    rate_percent = Column(Numeric(5, 2), nullable=False, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
