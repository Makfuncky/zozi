from __future__ import annotations

import hashlib
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint, func
from sqlalchemy import event
from sqlalchemy.orm import relationship
from . import Base
from domains.country.models.countries import CountryConfig  # noqa: F401
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Supplier/LP bank accounts relocated to the accounts domain
# (domains/accounts/models/banking.py). Re-exported here so governance.ports
# import sites remain unchanged (Law 3 sanctioned re-export).
from domains.accounts.models.banking import (  # noqa: E402,F401
    SupplierBankAccount,
    LogisticsPartnerBankAccount,
)

__all__ = [
    "AdminAnalyticsSnapshot", "RolePermissionSetting", "SystemAlert", "AdminChangeAuditLog",
    "AdminActivityLog", "SystemSetting", "APIKey",
    "BadgeBillingRecord", "BadgeTransaction", "BadgeTier",
    "CommissionBadgeTier", "CommissionGlobalConfig",
    "TicketReply", "PaymentProviderConfig",
    "EmailProviderConfig", "ShippingCarrier", "ShippingZone", "FinanceBankAccount",
    "PromotionOrderTier",
    "LogisticsCODRemittanceReceipt",
    "LogisticsPartnerDocument", "LogisticsSettlement", "ShipmentConfirmation",
    "ChatbotQueryEvent", "PushNotificationToken",
    "ProductVerification",
    "ProcessedWebhookEvent", "NormalizedWebhookEvent", "SupplierCountryCommission",
    "EmployeeExpense", "RetentionJobRun"
]


class AdminAnalyticsSnapshot(Base):
    __tablename__ = "admin_analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_key", name="uq_admin_analytics_snapshots_key"),
        Index("ix_admin_analytics_snapshots_group_computed", "snapshot_group", "computed_at"),
        Index("ix_admin_analytics_snapshots_expires", "expires_at"), {"schema": "governance"})
    id = Column(Integer, primary_key=True, index=True)
    snapshot_key = Column(String(120), nullable=False, index=True)
    snapshot_group = Column(String(80), nullable=False, index=True)
    period = Column(String(40), nullable=True)
    payload_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)


class RolePermissionSetting(Base):
    __tablename__ = "role_permission_settings"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String(255), nullable=False)
    permissions_json = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class SystemAlert(Base):
    __tablename__ = "system_alerts"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String(255), nullable=False)
    severity = Column(String(255), default="info")
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class AdminChangeAuditLog(Base):
    __tablename__ = "admin_change_audit_logs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    action = Column(String(255), nullable=False)
    entity = Column(String(255), nullable=False)
    entity_key = Column(String(255), nullable=True)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    
    admin = relationship("User", foreign_keys=[admin_id], backref="admin_change_logs")


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    action = Column(String(255), nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String(255), default="string")
    description = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class BadgeBillingRecord(Base):
    __tablename__ = "badge_billing_records"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    billing_reference = Column(String(255), unique=True, nullable=True)
    badge_level = Column(String(50), nullable=True)
    charge_type = Column(String(255), nullable=True)
    charge_source = Column(String(255), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(255), default="pending")
    reference_id = Column(String(255), nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    billed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("finance.bank_transactions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    supplier = relationship("User", foreign_keys=[supplier_id], backref="badge_billing_records")
    bank_transaction = relationship("BankTransaction", backref="badge_billing_records")
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)


class BadgeTransaction(Base):
    __tablename__ = "badge_transactions"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String(255), nullable=False)
    reference_id = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class BadgeTier(Base):
    __tablename__ = "badge_tiers"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    min_points = Column(Integer, nullable=False)
    benefits = Column(JSON, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class CommissionBadgeTier(Base):
    __tablename__ = "commission_badge_tiers"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    badge_level = Column(String(50), unique=True, nullable=False)
    commission_rate = Column(Numeric(5, 4), nullable=False)
    setup_fee = Column(Numeric(12, 2), default=Decimal("0.00"))
    recurring_fee = Column(Numeric(12, 2), default=Decimal("0.00"))
    recurring_interval = Column(String(20), nullable=True)
    benefits_json = Column(Text, nullable=True)
    min_fulfilled_orders = Column(Integer, nullable=True)
    min_monthly_revenue = Column(Numeric(15, 2), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class CommissionGlobalConfig(Base):
    __tablename__ = "commission_global_configs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    default_rate = Column(Numeric(5, 4), default=Decimal("0.1500"))
    low_value_threshold = Column(Numeric(10, 2), default=Decimal("5.00"))
    fixed_cap_amount = Column(Numeric(10, 2), default=Decimal("0.50"))
    fixed_cap_enabled = Column(Boolean, default=True)
    margin_protection_enabled = Column(Boolean, default=False)
    margin_threshold = Column(Numeric(5, 4), default=Decimal("0.10"))
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    country_code = Column(String(2), nullable=True, index=True)


class TicketReply(Base):
    __tablename__ = "ticket_replies"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("comms.support_tickets.id", ondelete="SET NULL"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    message = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class PaymentProviderConfig(Base):
    __tablename__ = "payment_provider_configs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(255), nullable=False)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class EmailProviderConfig(Base):
    __tablename__ = "email_provider_configs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    email_from_default = Column(String(255), nullable=True)
    email_from_promotional = Column(String(255), nullable=True)
    email_from_transactional = Column(String(255), nullable=True)
    email_from_notification = Column(String(255), nullable=True)
    email_from_alert = Column(String(255), nullable=True)
    email_from_verification = Column(String(255), nullable=True)
    email_from_login_verification = Column(String(255), nullable=True)
    email_from_password_reset = Column(String(255), nullable=True)
    resend_api_key = Column(String(255), nullable=True)
    resend_webhook_secret = Column(String(255), nullable=True)
    smtp_host = Column(String(255), nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String(255), nullable=True)
    smtp_password = Column(String(255), nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    smtp_timeout_seconds = Column(Integer, default=10)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)


class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    code = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class ShippingZone(Base):
    __tablename__ = "shipping_zones"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    countries = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class FinanceBankAccount(Base):
    __tablename__ = "finance_bank_accounts"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String(255), nullable=True)
    account_number = Column(String(255), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_label = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    iban = Column(String(255), nullable=True)
    swift_code = Column(String(255), nullable=True)
    routing_number = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=True)
    support_email = Column(String(255), nullable=True)
    support_phone = Column(String(255), nullable=True)
    remittance_reference_prefix = Column(String(255), nullable=True)
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    scope = Column(String(255), nullable=True, default="zozi_primary")
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class PromotionOrderTier(Base):
    __tablename__ = "promotion_order_tiers"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, nullable=True)
    tier_name = Column(String(255), nullable=True)
    min_order_amount = Column(Numeric(10, 2), nullable=False)
    max_order_amount = Column(Numeric(10, 2), nullable=True)
    discount_type = Column(String(255), nullable=False, default="fixed")
    discount_amount = Column(Numeric(10, 2), nullable=True)
    discount_value = Column(Numeric(10, 2), nullable=True)
    stacking_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class LogisticsCODRemittanceReceipt(Base):
    __tablename__ = "logistics_cod_remittance_receipts"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete="SET NULL"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id", ondelete="SET NULL"), nullable=True)
    settlement_id = Column(Integer, ForeignKey("governance.logistics_settlements.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    bank_reference = Column(String(255), nullable=True)
    receipt_file_url = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(255), default="pending")
    currency = Column(String(3), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    settlement = relationship("LogisticsSettlement", foreign_keys=[settlement_id])
    partner = relationship("LogisticsPartner", foreign_keys=[partner_id])


class LogisticsPartnerDocument(Base):
    __tablename__ = "logistics_partner_documents"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete="SET NULL"), nullable=False)
    doc_type = Column(String(255), nullable=False)
    file_url = Column(String(255), nullable=False)
    reviewed_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class LogisticsSettlement(Base):
    __tablename__ = "logistics_settlements"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete="SET NULL"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete="SET NULL"), nullable=True)
    ledger_id = Column(Integer, nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    pickup_charge = Column(Numeric(12, 2), nullable=True)
    dropoff_charge = Column(Numeric(12, 2), nullable=True)
    total_delivery_fee = Column(Numeric(12, 2), nullable=True)
    cod_collected = Column(Numeric(12, 2), nullable=True)
    cod_remitted = Column(Numeric(12, 2), nullable=True)
    cod_retained = Column(Numeric(12, 2), nullable=True)
    cod_remittance_status = Column(String(255), nullable=True)
    eligible_at = Column(DateTime, nullable=True)
    status = Column(String(255), default="pending")
    currency = Column(String(3), nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    payout_id = Column(Integer, ForeignKey("finance.payouts.id", ondelete="SET NULL"), nullable=True)
    bank_transaction_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class ShipmentConfirmation(Base):
    __tablename__ = "shipment_confirmations"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id", ondelete="SET NULL"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete="SET NULL"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    requester_user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    requester_role = Column(String(255), nullable=True)
    target_user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    target_role = Column(String(255), nullable=True)
    confirmation_type = Column(String(255), nullable=True)
    status = Column(String(255), default="pending")
    requested_status = Column(String(255), nullable=True)
    requested_event_type = Column(String(255), nullable=True)
    current_hub = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    confirmation_code = Column(String(255), nullable=True)
    confirmed_at = Column(DateTime, default=_utcnow)
    responded_at = Column(DateTime, nullable=True)
    tracking_number = Column(String(255), nullable=True)
    delivery_signature_name = Column(String(255), nullable=True)
    delivery_signature_data_url = Column(String(255), nullable=True)
    delivery_signature_captured_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class ChatbotQueryEvent(Base):
    __tablename__ = "chatbot_query_events"
    __table_args__ = {"schema": "governance"}
    __table_args__ = (
        Index("ix_chatbot_events_user_created", "user_id", "created_at"),
        Index("ix_chatbot_events_session_created", "session_id", "created_at"),
        Index("ix_chatbot_events_type_created", "event_type", "created_at"),
        Index("ix_chatbot_events_intent_created", "intent", "created_at"),
        Index("ix_chatbot_events_clicked_product_id", "clicked_product_id"),
        Index("ix_chatbot_events_created_at", "created_at"),
        Index("ix_chatbot_events_normalized_query", "normalized_query"),
        Index("ix_chatbot_events_session_id", "session_id"), {"schema": "governance"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    session_id = Column(String(64), nullable=False)
    event_type = Column(String(30), nullable=False, server_default="query")
    message = Column(Text, nullable=True)
    normalized_query = Column(String(500), nullable=True)
    intent = Column(String(100), nullable=True)
    filters_json = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=False, server_default="0")
    product_ids_json = Column(Text, nullable=True)
    clicked_product_id = Column(Integer, ForeignKey("catalog.products.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)

    __constraints__ = (
        CheckConstraint("result_count >= 0", name="ck_chatbot_events_result_count_nonnegative"),
    )


class PushNotificationToken(Base):
    __tablename__ = "push_notification_tokens"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    token = Column(String(255), nullable=False)
    device_type = Column(String(255), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class ProductVerification(Base):
    __tablename__ = "product_verifications"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("catalog.products.id", ondelete="SET NULL"), nullable=False)
    status = Column(String(255), default="pending")
    verified_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id", ondelete="SET NULL"), nullable=True)
    verification_type = Column(String(255), nullable=True)
    result = Column(String(255), nullable=True)
    expected_specs = Column(Text, nullable=True)
    actual_specs = Column(Text, nullable=True)
    discrepancies = Column(Text, nullable=True)
    scan_code = Column(String(255), nullable=True)
    image_urls = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    order_id = Column(Integer, ForeignKey("orders.orders.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    processor = Column(String(255), nullable=False)
    event_id = Column(String(255), nullable=False)
    payload_hash = Column(String(255), nullable=False)
    processed_at = Column(DateTime, default=_utcnow)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


@event.listens_for(ProcessedWebhookEvent, "before_insert")
def _populate_processed_webhook_payload_hash(mapper, connection, target):
    # payload_hash is NOT NULL. Several call sites (legacy webhook handlers)
    # insert without it. Derive a stable hash from the row's own identity so the
    # insert never violates the constraint (and remains meaningful for dedup).
    if not target.payload_hash:
        seed = f"{target.processor}:{target.event_id}".encode("utf-8")
        target.payload_hash = hashlib.sha256(seed).hexdigest()


class NormalizedWebhookEvent(Base):
    __tablename__ = "normalized_webhook_events"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String(255), nullable=False, index=True)
    gateway_event_id = Column(String(255), nullable=False)
    event_type = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)
    environment = Column(String(255), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    zozi_order_id = Column(Integer, nullable=True)
    gateway_transaction_id = Column(String(255), nullable=True)
    gateway_customer_id = Column(String(255), nullable=True)
    gross_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), nullable=True)
    gateway_fee = Column(Numeric(12, 2), nullable=True)
    net_settlement = Column(Numeric(12, 2), nullable=True)
    fraud_score = Column(Numeric(5, 2), nullable=True)
    three_ds_status = Column(String(255), nullable=True)
    avs_result = Column(String(255), nullable=True)
    raw_payload = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class EmployeeExpense(Base):
    __tablename__ = "employee_expenses"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("hr.employees.id", ondelete="SET NULL"), nullable=False, index=True)
    expense_type = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    approved_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
    employee = relationship("Employee", backref="expenses")
    approver = relationship("User", foreign_keys=[approved_by_id], backref="employee_expense_approvals")


class SupplierCountryCommission(Base):
    __tablename__ = "supplier_country_commissions"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False)
    country_code = Column(String(2), nullable=False)
    commission_rate = Column(Numeric(5, 2), nullable=False)
    category_slug = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class RetentionJobRun(Base):
    __tablename__ = "retention_job_runs"
    __table_args__ = ({"schema": "governance"},)
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=True)
    target_table = Column(String(100), nullable=True)
    target_name = Column(String(100), nullable=True)
    cutoff_days = Column(Integer, nullable=True)
    records_deleted = Column(Integer, default=0)
    archived_count = Column(Integer, default=0)
    deleted_count = Column(Integer, default=0)
    artifact_path = Column(String(255), nullable=True)
    result_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

