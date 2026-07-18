"""
Enhancements to integrate Supplier, Logistics, and Commission systems with Country Control Plane.

This patch adds country scoping to:
- SupplierProfile: country_code FK, KYC tier
- LogisticsPartner: country_code FK, verification requirements
- CommissionAgreement: country-scoped rates
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Index, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from db.database import Base
from utils.datetime_utils import utcnow as _utcnow


class SupplierKYCRequirement(Base):
    __tablename__ = 'supplier_kyc_requirements'
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey('country_configs.code'), nullable=False, unique=True)
    kyc_tier_required = Column(String(20), nullable=False, default='standard')  # basic | standard | strict
    document_types_required = Column(Text, nullable=True)  # JSON list
    verification_wait_days = Column(Integer, default=3)
    auto_approve_threshold = Column(Numeric(5, 2), default=0.85)  # credibility score
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])


class LogisticsPartnerKYCRequirement(Base):
    __tablename__ = 'logistics_partner_kyc_requirements'
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey('country_configs.code'), nullable=False, unique=True)
    min_experience_months = Column(Integer, default=6)
    required_documents = Column(Text, nullable=True)  # JSON list
    insurance_required = Column(Boolean, default=True)
    insurance_min_coverage = Column(Numeric(15, 2), nullable=True)
    vehicle_requirements = Column(Text, nullable=True)  # JSON
    background_check_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])


class CountryCommissionRate(Base):
    __tablename__ = 'country_commission_rates'
    __table_args__ = (
        UniqueConstraint('country_code', 'supplier_tier', 'name', name='uq_country_commission'),
        Index('ix_country_commission_country', 'country_code'),
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey('country_configs.code'), nullable=False)
    supplier_tier = Column(String(20), nullable=False)  # bronze | silver | gold | platinum
    name = Column(String(50), nullable=False)  # fixed_rate | dynamic_rate | promotional
    rate = Column(Numeric(5, 4), nullable=False)
    min_order_amount = Column(Numeric(12, 2), nullable=True)
    max_commission = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])
