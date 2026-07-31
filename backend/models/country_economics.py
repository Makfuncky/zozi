from __future__ import annotations

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from utils.datetime_utils import utcnow as _utcnow

from . import Base

__all__ = ["CountryEconomics"]


class CountryEconomics(Base):
    __tablename__ = "country_economics"
    __table_args__ = (
        Index("ix_country_economics_code", "country_code", unique=True), {"schema": "country"}
    )
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    economic_tier = Column(String(20), nullable=True)
    fraud_risk_tier = Column(String(10), nullable=True)
    suggested_logistics_model = Column(String(30), nullable=True)
    data_residency_tier = Column(String(20), default="standard")
    data_residency_encrypted = Column(Text, nullable=True)
    confidence_score = Column(Numeric(5, 4), default=Decimal("0.0000"))
    audit_trail_json = Column(Text, nullable=True)
    cod_enabled = Column(String(1), nullable=True)
    cod_max_amount = Column(Numeric(12, 2), nullable=True)
    cod_verification_required = Column(String(1), nullable=True)
    cod_remittance_days = Column(Integer, nullable=True)
    settlement_hold_days = Column(Integer, default=3)
    minimum_payout_amount = Column(Numeric(12, 2), nullable=True)
    payout_currency = Column(String(10), nullable=True)
    supplier_kyc_tier = Column(String(20), nullable=True)
    supplier_onboarding_fee = Column(Numeric(12, 2), nullable=True)
    supplier_monthly_fee = Column(Numeric(12, 2), nullable=True)
    supplier_rating_threshold = Column(Numeric(5, 2), nullable=True)
    legal_entity_required = Column(String(1), default="false")
    consumer_protection_days = Column(Integer, default=14)
    data_privacy_framework = Column(String(20), nullable=True)
    max_package_weight_kg = Column(Numeric(8, 2), nullable=True)
    max_package_dimensions_cm = Column(String(200), nullable=True)
    signature_required_threshold = Column(Numeric(10, 2), nullable=True)
    measurement_system = Column(String(10), default="metric")
    working_days_json = Column(Text, default="[]")
    supported_languages_json = Column(Text, default="[]")
    payout_methods_json = Column(Text, default="[]")
    logistics_zones_json = Column(Text, default="[]")

    country = relationship("CountryConfig", back_populates="economics", foreign_keys=[country_code])