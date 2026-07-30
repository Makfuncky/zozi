from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = ["Payment", "Coupon", "Banner", "PaymentGatewayConnection", "Payout", "LogisticsPartnerPayout", "PaymentReconciliationRun"]


def _get_table_args():
    import os
    db_url = os.getenv("DATABASE_URL", "sqlite:///")
    is_postgres = db_url.startswith("postgresql") or db_url.startswith("postgres")
    args = ()
    if is_postgres:
        args = (
            Index("idx_pgc_credentials_gin", "credentials", postgresql_using="gin"),
            Index("idx_pgc_fee_config_gin", "fee_config", postgresql_using="gin"),
            Index("idx_pgc_supported_methods_gin", "supported_methods", postgresql_using="gin"),
        )
    return args


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_non_negative"),
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name="chk_payment_status_valid"),
        Index("ix_payments_order_id", "order_id"), {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    status = Column(String, default="pending")
    intent_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    # Free-form canvas layout (shapes, colors, images, video, buttons) stored as
    # a JSON-encoded string. Drives the complete admin/employee banner editor.
    layout_json = Column(Text, nullable=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class PaymentReconciliationRun(Base):
    __tablename__ = "payment_reconciliation_runs"
    __table_args__ = ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=True)
    reconciled_count = Column(Integer, default=0)
    unmatched_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    stale_pending_orders = Column(Integer, default=0)
    recent_webhook_count = Column(Integer, default=0)
    result_json = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    country_code = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, default="percentage")
    discount_value = Column(Numeric(5, 2))
    minimum_order = Column(Numeric(10, 2), default=0)
    maximum_discount = Column(Numeric(10, 2), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    usage_count = Column(Integer, default=0)
    starts_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class Banner(Base):
    __tablename__ = "banners"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(String, nullable=True)
    image_url = Column(String, nullable=True)
    link = Column(String, nullable=True)
    banner_type = Column(String, default="hero")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    bg_color = Column(String, nullable=True)
    text_color = Column(String, nullable=True)
    subtitle_color = Column(String, nullable=True)
    btn_bg_color = Column(String, nullable=True)
    btn_text_color = Column(String, nullable=True)
    badge_text = Column(String, nullable=True)
    badge_color = Column(String, nullable=True)
    effect = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    cta_label = Column(String, nullable=True)
    cta_url = Column(String, nullable=True)
    starts_at = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class PaymentGatewayConnection(Base):
    __tablename__ = "payment_gateway_connections"
    __table_args__ = _get_table_args() + ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String(100), nullable=False)
    gateway_name = Column(String(100), nullable=False)
    country_code = Column(String(10), nullable=False)
    environment = Column(String(20), default="test")
    is_active = Column(Boolean, default=True)
    credentials = Column(JSON, nullable=True)
    fee_config = Column(JSON, nullable=True)
    supported_methods = Column(JSON, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    # Extended gateway configuration (matches migration e7f8a9b0c1d2)
    provider_kind = Column(String(20), nullable=False, default="custom")
    display_name = Column(String(120), nullable=False)
    is_enabled = Column(Boolean, nullable=True, default=True)
    supports_customer_checkout = Column(Boolean, nullable=True, default=False)
    supports_payouts = Column(Boolean, nullable=True, default=False)
    mode = Column(String(20), nullable=False, default="test")
    public_key = Column(String(500), nullable=True)
    secret_key = Column(String(1000), nullable=True)
    webhook_secret = Column(String(1000), nullable=True)
    merchant_id = Column(String(255), nullable=True)
    api_base_url = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    test_url = Column(String(500), nullable=True)
    settlement_cycle = Column(String(50), nullable=True)
    supported_currencies_json = Column(Text, nullable=True)
    extra_config_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    fee_percent = Column(Numeric(8, 4), nullable=False, default=0)
    fixed_fee_amount = Column(Numeric(12, 2), nullable=False, default=0)
    payout_fee_percent = Column(Numeric(8, 4), nullable=False, default=0)
    payout_fixed_fee_amount = Column(Numeric(12, 2), nullable=False, default=0)
    pass_fee_to_customer = Column(Boolean, nullable=True, default=False)
    test_status = Column(String(20), nullable=False, default="untested")
    test_message = Column(String(500), nullable=True)
    last_tested_at = Column(DateTime, nullable=True)
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    adapter_supported = Column(Boolean, default=False)


class Payout(Base):
    __tablename__ = "payouts"
    __table_args__ = ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    batch_number = Column(String(50), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    method = Column(String, nullable=False)
    status = Column(String, default="pending")
    reference_id = Column(String, nullable=True)
    reference = Column(String, nullable=True)
    provider = Column(String, nullable=True)
    provider_recipient_id = Column(String, nullable=True)
    provider_transfer_id = Column(String, nullable=True)
    provider_status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    supplier = relationship("User", foreign_keys=[supplier_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class LogisticsPartnerPayout(Base):
    __tablename__ = "logistics_partner_payouts"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics_partners.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    reference_id = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    country_code = Column(String(10), ForeignKey("country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    partner = relationship("LogisticsPartner", back_populates="payouts")
    country = relationship("CountryConfig", foreign_keys=[country_code])
