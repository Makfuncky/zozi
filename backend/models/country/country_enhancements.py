"""Country enhancement models."""
from __future__ import annotations

from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["SupplierKYCRequirement", "LogisticsPartnerKYCRequirement", "CountryCommissionRate", "CountryConfigVersion",
           "CountryFeatureFlag", "CountryStaffAssignment", "CrossCountryCustomerSession", "OmanDeliveryZone",
           "CountryCity", "CountryCategoryTaxRate", "CountryGatewayConfig", "CountryCommunicationThread",
           "CountryCommissionRateHistory", "CountryLogisticsZone", "CountryPayoutRule", "CountryHolidayCalendar",
           "CountryLegalContract", "CountryLocalization", "CountryPaymentAlias"]


class CountryFeatureFlag(Base):
    __tablename__ = "country_feature_flags"
    __table_args__ = (
        UniqueConstraint("country_code", "feature_key", name="uq_country_feature"), {"schema": "configuration"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    feature_key = Column(String(100), nullable=False)
    feature_name = Column(String(200), nullable=True)
    is_enabled = Column(Boolean, default=True)
    config = Column(Text, nullable=True)
    rollout_audience = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class CountryStaffAssignment(Base):
    __tablename__ = "country_staff_assignments"
    __table_args__ = (
        UniqueConstraint("user_id", "country_code", name="uq_staff_country"),
        Index("ix_staff_user", "user_id"), {"schema": "configuration"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    role_in_country = Column(String(40), nullable=False, server_default="country_manager")
    is_active = Column(Boolean, default=True)
    assigned_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    country = relationship("CountryConfig")
    assigned_by_user = relationship("User", foreign_keys=[assigned_by])


class CrossCountryCustomerSession(Base):
    __tablename__ = "cross_country_customer_sessions"
    __table_args__ = (
        Index("ix_cross_country_user", "user_id"), {"schema": "configuration"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    source_country_code = Column(String(10), nullable=False)
    target_country_code = Column(String(10), nullable=False)
    session_data = Column(Text, nullable=True)
    conversion = Column(Boolean, default=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User")
    order = relationship("Order")


class OmanDeliveryZone(Base):
    __tablename__ = "oman_delivery_zones"
    __table_args__ = (
        Index("ix_oman_zone_code", "zone_code"), {"schema": "configuration"})

    id = Column(Integer, primary_key=True, index=True)
    zone_code = Column(String(20), nullable=False, unique=True)
    zone_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    car_rate = Column(Numeric(10, 2), default=0)
    van_rate = Column(Numeric(10, 2), default=0)
    truck_rate = Column(Numeric(10, 2), default=0)
    weight_surcharge_rate = Column(Numeric(5, 4), nullable=True)
    weight_surcharge_threshold_kg = Column(Numeric(10, 2), nullable=True)
    cities_json = Column(Text, default="[]")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class CountryConfigVersion(Base):
    __tablename__ = "country_config_versions"
    __table_args__ = (
        Index("ix_country_config_version_type", "config_type"),
        Index("ix_country_config_version_status", "status"), {"schema": "configuration"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    config_type = Column(String(50), nullable=False)
    version = Column(Integer, nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), default="draft")
    draft_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    published_at = Column(DateTime, nullable=True)
    effective_from = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class SupplierKYCRequirement(Base):
    __tablename__ = 'supplier_kyc_requirements'
    __table_args__ = ({"schema": "country"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
    kyc_tier_required = Column(String(20), nullable=False, default='standard')
    document_types_required = Column(Text, nullable=True)
    verification_wait_days = Column(Integer, default=3)
    auto_approve_threshold = Column(Numeric(5, 2), default=Decimal("0.85"))
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])


class LogisticsPartnerKYCRequirement(Base):
    __tablename__ = 'logistics_partner_kyc_requirements'
    __table_args__ = ({"schema": "country"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
    min_experience_months = Column(Integer, default=6)
    required_documents = Column(Text, nullable=True)
    insurance_required = Column(Boolean, default=True)
    insurance_min_coverage = Column(Numeric(15, 2), nullable=True)
    vehicle_requirements = Column(Text, nullable=True)
    background_check_required = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])


class CountryCommissionRate(Base):
    __tablename__ = 'country_commission_rates'
    __table_args__ = (
        UniqueConstraint('country_code', 'supplier_tier', 'name', name='uq_country_commission'), {"schema": "configuration"})
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    supplier_tier = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    rate_percent = Column(Numeric(5, 2), nullable=False, default=0)
    fixed_fee = Column(Numeric(10, 2), nullable=True, default=0)
    effective_from = Column(DateTime, default=_utcnow)
    effective_to = Column(DateTime, nullable=True)
    
    country = relationship('CountryConfig', foreign_keys=[country_code])


class CountryLocalization(Base):
    __tablename__ = 'country_localization'
    __table_args__ = (
        UniqueConstraint('country_code', name='uq_country_localization'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
    default_numeral_system = Column(String(20), default='western')
    hijri_calendar_enabled = Column(Boolean, default=False)
    rtl_layout_enabled = Column(Boolean, default=False)
    address_format = Column(String(200), default='{street}, {city}, {postal_code}')
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig')


class CountryPaymentAlias(Base):
    __tablename__ = 'country_payment_aliases'
    __table_args__ = (
        UniqueConstraint('country_code', 'alias_type', name='uq_country_payment_alias'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    alias_type = Column(String(50), nullable=False)
    alias_value = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')


class CountryLegalContract(Base):
    __tablename__ = 'country_legal_contracts'
    __table_args__ = (
        UniqueConstraint('country_code', 'contract_type', name='uq_country_legal_contract'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    contract_type = Column(String(50), nullable=False)
    version = Column(String(20), default='1.0')
    content_html = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig')


class CountryCategoryTaxRate(Base):
    __tablename__ = 'country_category_tax_rates'
    __table_args__ = (
        UniqueConstraint('country_code', 'category_id', name='uq_country_category_tax'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    category_id = Column(Integer, ForeignKey("commerce.categories.id"), nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=True)
    tax_name = Column(String(50), nullable=True)
    category_slug = Column(String(100), nullable=True)
    rate = Column(Numeric(5, 4), nullable=True)
    is_exempt = Column(Boolean, default=False)
    is_reduced = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    source = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')
    category = relationship('Category')


class CountryCity(Base):
    """Normalized cities table — extracted from JSON blob for proper relational queries."""
    __tablename__ = "country_cities"
    __table_args__ = ({"schema": "country"},)

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    name = Column(String(200), nullable=False)
    name_local = Column(String(200), nullable=True)
    population = Column(Integer, default=0)
    is_capital = Column(Boolean, default=False)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    postal_code_prefix = Column(String(20), nullable=True)
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)
    region = Column(String(100), nullable=True)
    sort_order = Column(Integer, default=0)
    source = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class CountryHolidayCalendar(Base):
    __tablename__ = 'country_holiday_calendars'
    __table_args__ = (
        Index('ix_country_holiday_date', 'holiday_date'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    holiday_date = Column(DateTime, nullable=False)
    name = Column(String(200), nullable=False)
    local_name = Column(String(200), nullable=True)
    is_observed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')


class CountryGatewayConfig(Base):
    __tablename__ = 'country_gateway_configs'
    __table_args__ = (
        UniqueConstraint('country_code', 'gateway_id', name='uq_country_gateway'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    gateway_id = Column(String(50), nullable=False)
    gateway_name = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    priority = Column(Integer, default=0)
    credentials = Column(Text, nullable=True)
    environment = Column(String(20), default='test')
    settings = Column(Text, nullable=True)
    last_tested_at = Column(DateTime, nullable=True)
    last_test_result = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    
    country = relationship('CountryConfig')


class CountryCommunicationThread(Base):
    __tablename__ = 'country_communication_threads'
    __table_args__ = (
        Index('ix_comm_thread_entity', 'entity_type', 'entity_id'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    participants = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    last_message_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')


class CountryCommissionRateHistory(Base):
    __tablename__ = 'country_commission_rate_history'
    __table_args__ = (
        Index('ix_comm_rate_effective', 'effective_from'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    category_id = Column(Integer, ForeignKey("commerce.categories.id"), nullable=True)
    supplier_tier = Column(String(20), nullable=False)
    rate_percent = Column(Numeric(5, 4), nullable=False)
    effective_from = Column(DateTime, nullable=False)
    effective_to = Column(DateTime, nullable=True)
    changed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    change_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')
    category = relationship('Category')


class CountryLogisticsZone(Base):
    __tablename__ = 'country_logistics_zones'
    __table_args__ = (
        UniqueConstraint('country_code', 'zone_code', name='uq_zone_code'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    zone_code = Column(String(50), nullable=False)
    zone_name = Column(String(200), nullable=False)
    zone_type = Column(String(20), default='local')
    cities = Column(Text, nullable=True)
    pricing_config = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')


class CountryPayoutRule(Base):
    __tablename__ = 'country_payout_rules'
    __table_args__ = (
        Index('ix_payout_supplier', 'supplier_tier'), {"schema": "configuration"})
    
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    supplier_tier = Column(String(20), nullable=True)
    min_amount = Column(Numeric(15, 3), nullable=True)
    max_amount = Column(Numeric(15, 3), nullable=True)
    fixed_fee = Column(Numeric(15, 3), default=0)
    percent_fee = Column(Numeric(5, 4), default=0)
    settlement_days = Column(Integer, default=3)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship('CountryConfig')