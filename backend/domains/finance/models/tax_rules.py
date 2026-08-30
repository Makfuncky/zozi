"""finance domain — tax and payout rules previously housed under country.

These models were originally defined in ``domains/country/models/countries.py``.
They describe finance-domain concepts (tax rules, payout rules) and have been
relocated here to remove cross-domain pollution.

The ``__tablename__`` is preserved unchanged. The schema has been corrected to
``finance`` (was ``country``) to comply with Law 6 (schema discipline).
"""
from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from infrastructure.database.types import GUID
from . import Base
# CountryConfig relationship resolved lazily via string reference
from infrastructure.utils.datetime_utils import utcnow as utcnow

__all__ = ["PayoutRule", "TaxRule", "PayoutRuleCategory", "PayoutRuleProduct"]


class PayoutRule(Base):
    __tablename__ = 'payout_rules'
    __table_args__ = (Index('ix_payout_rules_country_created', 'country_code', 'created_at'), {'schema': 'finance'})
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    fixed_fee = Column(Numeric(12, 2), default=0)
    percent_fee = Column(Numeric(5, 4), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    country = relationship('CountryConfig', back_populates='payout_rules')


class TaxRule(Base):
    __tablename__ = 'tax_rules'
    __table_args__ = {"schema": "finance"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_tax_rules_country_created', 'country_code', 'created_at'), {'schema': 'finance'})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False, index=True)
    tax_name = Column(String(100), nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    country = relationship('CountryConfig', back_populates='tax_rules')


class PayoutRuleCategory(Base):
    __tablename__ = 'payout_rule_categories'
    __table_args__ = {"schema": "finance"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (UniqueConstraint('country_code', 'category_slug', name='uq_payout_rule_category'), Index('ix_payout_rule_categories_country_created', 'country_code', 'created_at'), {'schema': 'finance'})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False, index=True)
    category_slug = Column(String(100), nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class PayoutRuleProduct(Base):
    __tablename__ = 'payout_rule_products'
    __table_args__ = {"schema": "finance"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (UniqueConstraint('country_code', 'product_id', name='uq_payout_rule_product'), Index('ix_payout_rule_products_country_created', 'country_code', 'created_at'), {'schema': 'finance'})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False, index=True)
    product_id = Column(Integer, nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
