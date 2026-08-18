from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from utils.datetime_utils import utcnow as utcnow
from . import Base
__all__ = ['CountryLegal']

class CountryLegal(Base):
    __tablename__ = 'country_legal'
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    __table_args__ = (Index('ix_country_legal_code', 'country_code', unique=True), Index('ix_country_legal_country_created', 'country_code', 'created_at'), {'schema': 'country'})
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=True, unique=True, index=True)
    version = Column(Integer, nullable=False, default=1, server_default='1')
    country_code = Column(String(3), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    legal_entity_required = Column(String(1), default='true')
    consumer_protection_days = Column(Integer, default=14)
    data_privacy_framework = Column(String(20), nullable=True)
    gdpr_compliant = Column(Boolean, default=False)
    local_data_residency = Column(Boolean, default=False)
    compliance_score = Column(Numeric(5, 4), default=Decimal('0.5000'))
    legal_risk_tier = Column(String(10), default='medium')
    contract_templates_json = Column(Text, default='[]')
    regulatory_bodies_json = Column(Text, default='[]')
    country = relationship('CountryConfig', back_populates='legal', foreign_keys=[country_code])