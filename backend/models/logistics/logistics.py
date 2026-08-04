from __future__ import annotations
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin

__all__ = [
    "LogisticsPartner", "LogisticsPartnerProfile", "LogisticsPartnerServiceArea", "LogisticsPricingProfile",
    "LogisticsVehicleRule", "Shipment", "ShipmentEvent", "LogisticsCategoryPricingRule"
]

class LogisticsPartner(Base, TenantMixin):
    __tablename__ = "logistics_partners"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    contact_name = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    coverage_regions = Column(JSON, nullable=True)
    service_types = Column(JSON, nullable=True)
    status = Column(String, default="active")
    verification_status = Column(String, default="pending")
    verification_note = Column(String, nullable=True)
    verified_by = Column(Integer, nullable=True)
    verified_at = Column(DateTime, nullable=True)

    business_type = Column(String, nullable=True)
    region = Column(String, nullable=True)
    city = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    bio = Column(Text, nullable=True)
    about_us = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    banner_url = Column(String, nullable=True)
    latitude = Column(Numeric(10, 7), nullable=True)
    longitude = Column(Numeric(10, 7), nullable=True)
    social_links = Column(JSON, nullable=True)
    notes = Column(Text, nullable=True)
    is_terms_accepted = Column(Boolean, default=False)
    terms_version = Column(String, nullable=True)
    terms_accepted_at = Column(DateTime, nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True)
    profile = relationship("LogisticsPartnerProfile", back_populates="partner", cascade="all, delete-orphan")
    service_areas = relationship("LogisticsPartnerServiceArea", back_populates="partner")
    pricing_profiles = relationship("LogisticsPricingProfile", back_populates="partner")
    vehicle_rules = relationship("LogisticsVehicleRule", back_populates="partner")
    category_pricing_rules = relationship("LogisticsCategoryPricingRule", back_populates="partner")
    payouts = relationship("LogisticsPartnerPayout", back_populates="partner")
    country = relationship("CountryConfig", foreign_keys="LogisticsPartner.country_code")

class LogisticsPartnerProfile(Base, TenantMixin):
    __tablename__ = "logistics_partner_profiles"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False, unique=True)
    tax_id = Column(String, nullable=True)
    registration_number = Column(String, nullable=True)
    business_type = Column(String, nullable=True)
    years_in_business = Column(Integer, nullable=True)
    insurance_provider = Column(String, nullable=True)
    insurance_policy_number = Column(String, nullable=True)
    insurance_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="profile")

class LogisticsPartnerServiceArea(Base, TenantMixin):
    __tablename__ = "logistics_partner_service_areas"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)

    origin_city = Column(String, nullable=False)
    city_name = Column(String, nullable=False)
    country_name = Column(String, nullable=True)
    zone_label = Column(String, nullable=True)
    charge_amount = Column(Numeric(10, 2), nullable=True)
    minimum_charge = Column(Numeric(10, 2), nullable=True)
    per_kg_rate = Column(Numeric(10, 2), nullable=True)
    pickup_charge = Column(Numeric(10, 2), nullable=True)
    dropoff_charge = Column(Numeric(10, 2), nullable=True)
    per_km_rate = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")
    delivery_days_min = Column(Integer, nullable=True)
    delivery_days_max = Column(Integer, nullable=True)

    review_note = Column(String, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    partner = relationship("LogisticsPartner", back_populates="service_areas")
    pricing_profiles = relationship("LogisticsPricingProfile", back_populates="service_area", cascade="all, delete-orphan")
    vehicle_rules = relationship("LogisticsVehicleRule", back_populates="service_area", cascade="all, delete-orphan")
    category_pricing_rules = relationship("LogisticsCategoryPricingRule", back_populates="service_area", cascade="all, delete-orphan")

class LogisticsPricingProfile(Base, TenantMixin):
    __tablename__ = "logistics_pricing_profiles"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    service_area_id = Column(Integer, ForeignKey("logistics.logistics_partner_service_areas.id"), nullable=False)
    profile_name = Column(String, nullable=False)
    base_in_city_fee = Column(Numeric(10, 2), nullable=True)
    per_kg_rate = Column(Numeric(10, 2), nullable=True)
    minimum_charge = Column(Numeric(10, 2), nullable=True)
    maximum_charge = Column(Numeric(10, 2), nullable=True)
    fuel_multiplier = Column(Numeric(5, 4), default=1.0)
    base_inter_city_fee = Column(Numeric(10, 2), nullable=True)
    per_km_rate = Column(Numeric(10, 2), nullable=True)
    bulk_discount_threshold_kg = Column(Numeric(10, 2), nullable=True)
    bulk_discount_percent = Column(Numeric(5, 4), nullable=True)
    currency = Column(String(3), default="USD")

    review_note = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="pricing_profiles")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="pricing_profiles")

class LogisticsVehicleRule(Base, TenantMixin):
    __tablename__ = "logistics_vehicle_rules"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    service_area_id = Column(Integer, ForeignKey("logistics.logistics_partner_service_areas.id"), nullable=False)
    vehicle_type = Column(String, nullable=False)
    max_weight_kg = Column(Numeric(10, 2), nullable=True)
    cost_multiplier = Column(Numeric(5, 4), nullable=True)
    priority_rank = Column(Integer, default=0)
    route_scope = Column(String, nullable=True)
    max_volume_cm3 = Column(Numeric(12, 2), nullable=True)

    review_note = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="vehicle_rules")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="vehicle_rules")

class LogisticsCategoryPricingRule(Base, TenantMixin):
    __tablename__ = "logistics_category_pricing_rules"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    service_area_id = Column(Integer, ForeignKey("logistics.logistics_partner_service_areas.id"), nullable=True)
    category_name = Column(String, nullable=False)
    flat_fee_override = Column(Numeric(10, 2), nullable=True)
    special_handling_fee = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="USD")

    review_note = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    partner = relationship("LogisticsPartner", back_populates="category_pricing_rules")
    service_area = relationship("LogisticsPartnerServiceArea", back_populates="category_pricing_rules")

class Shipment(Base, TenantMixin):
    __tablename__ = "shipments"
    __table_args__ = (
        Index("ix_shipments_order_id", "order_id"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    assigned_partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=True)
    carrier_id = Column(Integer, ForeignKey("logistics.shipping_carriers.id"), nullable=True)
    tracking_number = Column(String, unique=True, nullable=True)
    carrier_name = Column(String, nullable=True)
    status = Column(String, default="processing")
    distribution_channel = Column(String, nullable=True)
    current_hub = Column(String, nullable=True)
    scan_code = Column(String, nullable=True)
    package_count = Column(Integer, default=1)
    package_weight_kg = Column(Numeric(5, 2), nullable=True)
    package_dimensions = Column(String, nullable=True)
    packaged_at = Column(DateTime, nullable=True)
    packaged_by_user_id = Column(Integer, nullable=True)
    packaged_notes = Column(String, nullable=True)
    packaging_notes = Column(String, nullable=True)
    shipped_at = Column(DateTime, nullable=True)
    estimated_delivery = Column(DateTime, nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    delivery_signature_name = Column(String, nullable=True)
    delivery_signature_data_url = Column(String, nullable=True)
    delivery_signature_captured_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    accepted_vehicle_type = Column(String, nullable=True)
    accepted_vehicle_multiplier = Column(Numeric(5, 4), nullable=True)
    accepted_vehicle_selected_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    order = relationship("Order", back_populates="shipments")
    supplier = relationship("User", backref="shipments")
    assigned_partner = relationship("LogisticsPartner", backref="shipments")
    carrier = relationship("ShippingCarrier", backref="shipments")

class ShipmentEvent(Base, TenantMixin):
    __tablename__ = "shipment_events"
    __partition_by__ = "range"
    __partition_key__ = "created_at"
    __table_args__ = (
        Index("ix_shipment_events_shipment_id", "shipment_id"),
        Index("ix_shipment_events_order_id", "order_id"), {"schema": "logistics"})
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    actor_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    actor_role = Column(String, nullable=True)
    event_type = Column(String, nullable=False)
    status_after = Column(String, nullable=True)
    distribution_channel = Column(String, nullable=True)
    location = Column(String, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    scan_code = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

