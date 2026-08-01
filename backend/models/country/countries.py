from __future__ import annotations

from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["CountryConfig", "CountryCommunication", "CountryGatewayCredentials", "PayoutRule", "TaxRule", "ShippingRule", "Message", "PayoutRuleCategory", "PayoutRuleProduct"]


class CountryConfig(Base):
    __tablename__ = "country_configs"
    __table_args__ = ({"schema": "country"},)
    id = Column(Integer, primary_key=True, index=True)
    basics_id = Column(Integer, ForeignKey("country.country_basics.id"), nullable=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    currency = Column(String(3), default="USD")
    currency_symbol = Column(String(10), nullable=True)
    phone_code = Column(String(10), nullable=True)
    language = Column(String(10), default="en")
    timezone = Column(String(60), nullable=True)
    date_format = Column(String(20), default="DD/MM/YYYY")
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    official_name = Column(String(200), nullable=True)
    alpha3 = Column(String(3), nullable=True)
    flag_url = Column(String(500), nullable=True)
    currency_name = Column(String(50), nullable=True)
    exchange_rate_to_usd = Column(Numeric(12, 6), nullable=True)
    capital = Column(String(100), nullable=True)
    region = Column(String(60), nullable=True)
    subregion = Column(String(60), nullable=True)
    
    population = Column(Integer, nullable=True)
    internet_penetration_pct = Column(Numeric(5, 2), nullable=True)
    gdp_per_capita_usd = Column(Numeric(12, 2), nullable=True)
    urbanization_pct = Column(Numeric(5, 2), nullable=True)
    mobile_subs_per_100 = Column(Numeric(5, 2), nullable=True)
    public_holidays_json = Column(Text, nullable=True)
    macro_indicators_json = Column(Text, nullable=True)
    
    tax_type = Column(String(20), default="VAT")
    tax_rate = Column(Numeric(5, 4), default=Decimal("0.0000"))
    tax_name = Column(String(50), default="VAT")
    tax_inclusive = Column(Boolean, default=False)
    tax_exempt_categories_json = Column(Text, default="[]")
    tax_reduced_rates_json = Column(Text, default="{}")
    
    logistics_model = Column(String(30), default="fixed")
    default_vehicle_type = Column(String(30), nullable=True)
    base_rate = Column(Numeric(10, 2), nullable=True)
    per_km_rate = Column(Numeric(10, 2), nullable=True)
    minimum_charge = Column(Numeric(10, 2), nullable=True)
    weight_surcharge_rate = Column(Numeric(5, 4), nullable=True)
    weight_surcharge_threshold_kg = Column(Numeric(10, 2), nullable=True)
    
    payment_methods_json = Column(Text, default="[]")
    payment_gateways_json = Column(Text, nullable=True)
    logistics_providers_json = Column(Text, nullable=True)
    
    legal_rules_json = Column(Text, nullable=True)
    product_restrictions_json = Column(Text, default="[]")
    address_format_json = Column(Text, default='{"fields":["street","city","postal_code"],"required":["street","city"]}')
    regions_json = Column(Text, default="[]")
    
    supplier_requirements_json = Column(Text, nullable=True)
    payout_settings_json = Column(Text, nullable=True)
    commission_tiers_json = Column(Text, nullable=True)
    
    suggested_gateway_rankings_json = Column(Text, nullable=True)
    suggested_commission_ranges_json = Column(Text, nullable=True)
    consumer_behavior_profile_json = Column(Text, nullable=True)
    
    economic_tier = Column(String(20), nullable=True)
    fraud_risk_tier = Column(String(10), nullable=True)
    suggested_logistics_model = Column(String(30), nullable=True)
    data_residency_tier = Column(String(20), default="standard")
    data_residency_encrypted = Column(Text, nullable=True)
    confidence_score = Column(Numeric(5, 4), default=Decimal("0.0000"))
    audit_trail_json = Column(Text, nullable=True)
    
    cod_enabled = Column(Boolean, nullable=True)
    cod_max_amount = Column(Numeric(12, 2), nullable=True)
    cod_verification_required = Column(Boolean, nullable=True)
    cod_remittance_days = Column(Integer, nullable=True)
    settlement_hold_days = Column(Integer, default=3)
    minimum_payout_amount = Column(Numeric(12, 2), nullable=True)
    payout_currency = Column(String(10), nullable=True)
    
    supplier_kyc_tier = Column(String(20), nullable=True)
    supplier_onboarding_fee = Column(Numeric(12, 2), nullable=True)
    supplier_monthly_fee = Column(Numeric(12, 2), nullable=True)
    supplier_rating_threshold = Column(Numeric(5, 2), nullable=True)
    
    legal_entity_required = Column(Boolean, default=False)
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

    communications = relationship("CountryCommunication", back_populates="country")
    gateway_credentials = relationship("CountryGatewayCredentials", back_populates="country")
    tax_rules = relationship("TaxRule", back_populates="country")
    shipping_rules = relationship("ShippingRule", back_populates="country")
    payout_rules = relationship("PayoutRule", back_populates="country")
    category_tax_rates = relationship("CountryCategoryTaxRate", back_populates="country")
    feature_flags = relationship("CountryFeatureFlag", back_populates="country")
    staff_assignments = relationship("CountryStaffAssignment", back_populates="country")
    config_versions = relationship("CountryConfigVersion", back_populates="country")
    commission_rates = relationship("CountryCommissionRate", back_populates="country")
    kyc_requirements = relationship("SupplierKYCRequirement", back_populates="country", uselist=False)
    logistics_kyc_requirements = relationship("LogisticsPartnerKYCRequirement", back_populates="country", uselist=False)
    cities = relationship("CountryCity", back_populates="country")
    basics = relationship("CountryBasics", back_populates="country", uselist=False)
    economics = relationship("CountryEconomics", back_populates="country", uselist=False)
    legal = relationship("CountryLegal", back_populates="country", uselist=False)
    tax = relationship("CountryTax", back_populates="country", uselist=False)


class CountryCommunication(Base):
    __tablename__ = "country_communications"
    __table_args__ = (
        Index("ix_country_communications_recipient", "to_user_id", "status"), {"schema": "country"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    to_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    priority = Column(String(20), default="normal")
    category = Column(String(50), nullable=True)
    status = Column(String(20), default="sent")
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(Integer, nullable=True)
    read_at = Column(DateTime, nullable=True)
    attachments_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    
    country = relationship("CountryConfig", back_populates="communications")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class CountryGatewayCredentials(Base):
    __tablename__ = "country_gateway_credentials"
    __table_args__ = ({"schema": "country"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    gateway_name = Column(String(100), nullable=False)
    environment = Column(String(20), default="test")
    credentials = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    country = relationship("CountryConfig", back_populates="gateway_credentials")


class PayoutRule(Base):
    __tablename__ = "payout_rules"
    __table_args__ = ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    fixed_fee = Column(Numeric(12, 2), default=0)
    percent_fee = Column(Numeric(5, 4), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    country = relationship("CountryConfig", back_populates="payout_rules")


class TaxRule(Base):
    __tablename__ = "tax_rules"
    __table_args__ = ({"schema": "country"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    tax_name = Column(String(100), nullable=False)
    tax_rate = Column(Numeric(5, 4), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    country = relationship("CountryConfig", back_populates="tax_rules")


class ShippingRule(Base):
    __tablename__ = "shipping_rules"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    method = Column(String, nullable=False)
    base_rate = Column(Numeric(10, 2), nullable=False)
    per_kg_rate = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    country = relationship("CountryConfig", back_populates="shipping_rules")


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_message_recipient", "to_user_id", "created_at"),
        Index("ix_message_sender", "from_user_id", "created_at"), {"schema": "country"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    from_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    priority = Column(String(20), default="normal")
    category = Column(String(50), nullable=True)
    status = Column(String(20), default="sent")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig")
    from_user = relationship("User", foreign_keys=[from_user_id])
    to_user = relationship("User", foreign_keys=[to_user_id])


class PayoutRuleCategory(Base):
    __tablename__ = "payout_rule_categories"
    __table_args__ = (
        UniqueConstraint("country_code", "category_slug", name="uq_payout_rule_category"), {"schema": "country"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    category_slug = Column(String, nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig")


class PayoutRuleProduct(Base):
    __tablename__ = "payout_rule_products"
    __table_args__ = (
        UniqueConstraint("country_code", "product_id", name="uq_payout_rule_product"), {"schema": "country"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    payout_rate = Column(Numeric(5, 4), nullable=False)
    min_amount = Column(Numeric(12, 2), nullable=True)
    max_amount = Column(Numeric(12, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig")
    product = relationship("Product")

