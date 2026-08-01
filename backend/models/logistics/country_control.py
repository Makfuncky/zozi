"""Country control models."""
from __future__ import annotations

from decimal import Decimal
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Float, ForeignKey, Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, BigInteger
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow


class ShiftHandoverLog(Base):
    __tablename__ = "shift_handover_logs"
    __table_args__ = (
        Index("ix_handover_user_created", "user_id", "created_at"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    shift_start = Column(DateTime, nullable=False)
    shift_end = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    handover_to_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    handover_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    user = relationship("User", foreign_keys=[user_id])
    country = relationship("CountryConfig")
    handover_to = relationship("User", foreign_keys=[handover_to_user_id])


class PaymentOrchestratorSync(Base):
    __tablename__ = "payment_orchestrator_sync"
    __table_args__ = (
        UniqueConstraint("country_code", "gateway_id", name="uq_pos_country_gateway"),
        Index("ix_pos_status", "status"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    gateway_id = Column(String(60), nullable=False)
    gateway_name = Column(String(100), nullable=True)
    environment = Column(String(20), default="test")
    is_active = Column(Boolean, default=True)
    fee_percent = Column(Numeric(8, 4), nullable=True)
    fee_fixed = Column(Numeric(12, 2), nullable=True)
    supported_payment_methods = Column(Text, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class SupplierOnboardingSync(Base):
    __tablename__ = "supplier_onboarding_sync"
    __table_args__ = (
        UniqueConstraint("country_code", "supplier_id", name="uq_sos_country_supplier"),
        Index("ix_sos_status", "status"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False, index=True)
    kyc_status = Column(String(30), default="pending")
    kyc_documents = Column(Text, nullable=True)
    onboarding_fee_paid = Column(Boolean, default=False)
    monthly_fee_status = Column(String(20), default="pending")
    status = Column(String(20), default="pending")
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")
    supplier = relationship("User")


class LegalContractTemplate(Base):
    __tablename__ = "legal_contract_templates"
    __table_args__ = (
        UniqueConstraint("country_code", "template_type", name="uq_lct_country_type"),
        Index("ix_lct_type", "template_type"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    template_type = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0")
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class DataResidencyRecord(Base):
    __tablename__ = "data_residency_records"
    __table_args__ = (
        UniqueConstraint("country_code", "data_type", name="uq_drr_country_type"),
        Index("ix_drr_compliance", "compliance_status"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)
    storage_location = Column(String(100), nullable=True)
    cross_border_allowed = Column(Boolean, default=False)
    compliance_status = Column(String(30), default="pending")
    last_audit_at = Column(DateTime, nullable=True)
    next_audit_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class CountryMapConfig(Base):
    __tablename__ = "country_map_configs"
    __table_args__ = (
        UniqueConstraint("country_code", name="uq_cmc_country"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, unique=True, index=True)
    map_provider = Column(String(30), default="google")
    api_key_ref = Column(String(100), nullable=True)
    default_zoom = Column(Integer, default=5)
    show_regions = Column(Boolean, default=True)
    show_cities = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig")


class ShopWarehouseLocation(Base):
    __tablename__ = "shop_warehouse_locations"
    __table_args__ = (
        Index("ix_swl_active", "is_active"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    warehouse_code = Column(String(30), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig")


class LogisticsPartnerLocation(Base):
    __tablename__ = "logistics_partner_locations"
    __table_args__ = (
        Index("ix_lpl_partner", "partner_id"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    location_type = Column(String(30), default="warehouse")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    partner = relationship("LogisticsPartner")
    country = relationship("CountryConfig")


class ParcelLocationTracker(Base):
    __tablename__ = "parcel_location_trackers"
    __table_args__ = (
        Index("ixplt_parcel", "parcel_id"),
        Index("ixplt_created", "created_at"), {"schema": "hr"})

    id = Column(Integer, primary_key=True, index=True)
    parcel_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=False, index=True)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=False, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_name = Column(String(200), nullable=True)
    timestamp = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)

    parcel = relationship("Shipment")
    country = relationship("CountryConfig")
