"""finance domain â€” payment, payout, and gateway models.

These models were previously in domains/payments/models/payments.py but belong
to the finance domain because they represent financial operations:
- Payment: customer payment for an order (finance operation)
- Payout: platform payment to a supplier (finance operation)
- LogisticsPartnerPayout: platform payment to a logistics partner (finance operation)
- PaymentGatewayConnection: gateway configuration (finance/treasury)
- PaymentReconciliationRun: reconciliation (finance)

Coupon and Banner were moved to domains/catalog/models/ because they are
promotion/catalog concepts, not finance concepts.
"""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint, func
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

__all__ = ["Payment", "Payout", "LogisticsPartnerPayout", "PaymentGatewayConnection", "PaymentReconciliationRun"]


def _get_table_args():
    import os
    db_url = os.getenv("DATABASE_URL", "sqlite:///")
    is_postgres = db_url.startswith("postgresql") or db_url.startswith("postgres")
    args = ()
    if is_postgres:
        args = (
            Index("idx_pgc_credentials_gin", "credentials"),
            Index("idx_pgc_fee_config_gin", "fee_config"),
            Index("idx_pgc_supported_methods_gin", "supported_methods"),
        )
    return args


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="chk_payment_amount_non_negative"),
        CheckConstraint("status IN ('pending', 'completed', 'failed', 'refunded')", name="chk_payment_status_valid"),
        Index("ix_payments_order_id", "order_id"),
        Index("ix_payments_status_created", "status", "created_at"),
        Index("ix_payments_provider_status", "provider", "status"),
        {"schema": "finance"})
    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id", ondelete='CASCADE'), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)
    provider = Column(String(50), nullable=True)
    status = Column(String(30), default="pending")
    intent_id = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='SET NULL'), nullable=True, index=True)
    layout_json = Column(Text, nullable=True)
    country = relationship("CountryConfig", foreign_keys=[country_code])


class PaymentReconciliationRun(Base):
    __tablename__ = "payment_reconciliation_runs"
    __table_args__ = ({"schema": "finance"},)
    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
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
    status = Column(String(30), default="pending")
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class PaymentGatewayConnection(Base):
    __tablename__ = "payment_gateway_connections"
    __table_args__ = _get_table_args() + ({"schema": "finance"},)
    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    provider_code = Column(String(100), nullable=False)
    gateway_name = Column(String(100), nullable=False)
    country_code = Column(String(2), nullable=False)
    environment = Column(String(20), default="test")
    is_active = Column(Boolean, default=True)
    credentials = Column(JSON, nullable=True)
    fee_config = Column(JSON, nullable=True)
    supported_methods = Column(JSON, nullable=True)
    last_sync_at = Column(DateTime, nullable=True)
    provider_kind = Column(String(20), nullable=False, default="custom")
    display_name = Column(String(120), nullable=False)
    is_enabled = Column(Boolean, nullable=True, default=True)
    supports_customer_checkout = Column(Boolean, nullable=True, default=False)
    supports_payouts = Column(Boolean, nullable=True, default=False)
    payment_mode = Column(String(20), nullable=False, default="test")
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
    updated_by_id = Column(Integer, ForeignKey("governance.users.id", ondelete='SET NULL'), nullable=True)
    adapter_supported = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class Payout(Base):
    __tablename__ = "payouts"
    __table_args__ = ({"schema": "finance"},)
    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    batch_number = Column(String(50), nullable=True)
    order_id = Column(Integer, ForeignKey("commerce.orders.id", ondelete='SET NULL'), nullable=True)
    supplier_id = Column(Integer, ForeignKey("governance.users.id", ondelete='RESTRICT'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    method = Column(String(50), nullable=False)
    status = Column(String(30), default="pending")
    reference_id = Column(String(100), nullable=True)
    reference = Column(String(200), nullable=True)
    provider = Column(String(50), nullable=True)
    provider_recipient_id = Column(String(100), nullable=True)
    provider_transfer_id = Column(String(100), nullable=True)
    provider_status = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    supplier = relationship("User", foreign_keys=[supplier_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class LogisticsPartnerPayout(Base):
    __tablename__ = "logistics_partner_payouts"
    __table_args__ = ({"schema": "finance"},)
    id = Column(Integer, primary_key=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete='CASCADE'), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    status = Column(String(30), default="pending")
    reference_id = Column(String(100), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    method = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    partner = relationship("LogisticsPartner", back_populates="payouts")
    country = relationship("CountryConfig", foreign_keys=[country_code])


