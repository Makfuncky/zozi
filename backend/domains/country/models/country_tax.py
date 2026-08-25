from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from infrastructure.utils.datetime_utils import utcnow as utcnow
from . import Base
__all__ = ['CountryTax']

class CountryTax(Base):
    __tablename__ = 'country_tax'
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    __table_args__ = (Index('ix_country_tax_code', 'country_code', unique=True), Index('ix_country_tax_active', 'is_active', 'is_deleted'), Index('ix_country_tax_country_created', 'country_code', 'created_at'), {'schema': 'country'})
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    tax_type = Column(String(20), default='VAT')
    tax_rate = Column(Numeric(5, 4), default=Decimal('0.0000'))
    tax_name = Column(String(50), default='VAT')
    tax_inclusive = Column(Boolean, default=False)
    tax_exempt_categories_json = Column(Text, default='[]')
    tax_reduced_rates_json = Column(Text, default='{}')
    country = relationship('CountryConfig', back_populates='tax', foreign_keys=[country_code])
