from __future__ import annotations

import hashlib
from decimal import Decimal
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index, JSON, CheckConstraint
from sqlalchemy import event
from sqlalchemy.orm import relationship
from . import Base
from utils.datetime_utils import utcnow as _utcnow

__all__ = [
    "AdminAnalyticsSnapshot", "RolePermissionSetting", "SystemAlert", "AdminChangeAuditLog",
    "AdminActivityLog", "SystemSetting", "APIKey",
    "BadgeBillingRecord", "BadgeTransaction", "BadgeTier",
    "CommissionBadgeTier", "CommissionGlobalConfig",
    "TicketReply", "CouponUsage", "PaymentProviderConfig",
    "EmailProviderConfig", "ShippingCarrier", "ShippingZone", "FinanceBankAccount",
    "PromotionEngineConfig", "PromotionLedgerEntry", "PromotionOrderTier",
    "LogisticsCODRemittanceReceipt", "LogisticsPartnerBankAccount",
    "LogisticsPartnerDocument", "LogisticsSettlement", "ShipmentConfirmation",
    "ChatbotQueryEvent", "PushNotificationToken",
    "ProductVerification", "SupplierBankAccount",
    "ProcessedWebhookEvent", "NormalizedWebhookEvent", "SupplierDispute", "SupplierCountryCommission",
    "EmployeeExpense", "RetentionJobRun"
]


class AdminAnalyticsSnapshot(Base):
    __tablename__ = "admin_analytics_snapshots"
    __table_args__ = (
        UniqueConstraint("snapshot_key", name="uq_admin_analytics_snapshots_key"),
        Index("ix_admin_analytics_snapshots_group_computed", "snapshot_group", "computed_at"),
        Index("ix_admin_analytics_snapshots_expires", "expires_at"), {"schema": "audit"})
    id = Column(Integer, primary_key=True, index=True)
    snapshot_key = Column(String(120), nullable=False, index=True)
    snapshot_group = Column(String(80), nullable=False, index=True)
    period = Column(String(40), nullable=True)
    payload_json = Column(Text, nullable=False)
    computed_at = Column(DateTime, default=_utcnow, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    country_code = Column(String(3), nullable=True, index=True)


class RolePermissionSetting(Base):
    __tablename__ = "role_permission_settings"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, nullable=False)
    permissions_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class SystemAlert(Base):
    __tablename__ = "system_alerts"
    __table_args__ = ({"schema": "configuration"},)
    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(String, nullable=False)
    severity = Column(String, default="info")
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class AdminChangeAuditLog(Base):
    __tablename__ = "admin_change_audit_logs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_key = Column(String, nullable=True)
    before_json = Column(Text, nullable=True)
    after_json = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    
    admin = relationship("User", foreign_keys=[admin_id])


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    action = Column(String, nullable=False)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = ({"schema": "configuration"},)
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False)
    value = Column(Text, nullable=True)
    value_type = Column(String, default="string")
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class APIKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = ({"schema": "core"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key_hash = Column(String, nullable=False)
    permissions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class BadgeBillingRecord(Base):
    __tablename__ = "badge_billing_records"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    billing_reference = Column(String, unique=True, nullable=True)
    badge_level = Column(String(50), nullable=True)
    charge_type = Column(String, nullable=True)
    charge_source = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String, default="pending")
    reference_id = Column(String, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    due_at = Column(DateTime, nullable=True)
    billed_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    payment_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, nullable=True)
    bank_transaction_id = Column(Integer, ForeignKey("finance.bank_transactions.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    supplier = relationship("User", foreign_keys=[supplier_id])
    bank_transaction = relationship("BankTransaction")


class BadgeTransaction(Base):
    __tablename__ = "badge_transactions"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    transaction_type = Column(String, nullable=False)
    reference_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class BadgeTier(Base):
    __tablename__ = "badge_tiers"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    min_points = Column(Integer, nullable=False)
    benefits = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class CommissionBadgeTier(Base):
    __tablename__ = "commission_badge_tiers"
    __table_args__ = ({"schema": "commerce"},)
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
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class CommissionGlobalConfig(Base):
    __tablename__ = "commission_global_configs"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    default_rate = Column(Numeric(5, 4), default=Decimal("0.1500"))
    low_value_threshold = Column(Numeric(10, 2), default=Decimal("5.00"))
    fixed_cap_amount = Column(Numeric(10, 2), default=Decimal("0.50"))
    fixed_cap_enabled = Column(Boolean, default=True)
    margin_protection_enabled = Column(Boolean, default=False)
    margin_threshold = Column(Numeric(5, 4), default=Decimal("0.10"))
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class TicketReply(Base):
    __tablename__ = "ticket_replies"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class CouponUsage(Base):
    __tablename__ = "coupon_usage"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    coupon_id = Column(Integer, ForeignKey("commerce.coupons.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    coupon = relationship("Coupon", backref="usages")
    user = relationship("User", foreign_keys=[user_id])
    order = relationship("Order", foreign_keys=[order_id])
    country = relationship("CountryConfig", foreign_keys=[country_code])


class PaymentProviderConfig(Base):
    __tablename__ = "payment_provider_configs"
    __table_args__ = ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String, nullable=False)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class EmailProviderConfig(Base):
    __tablename__ = "email_provider_configs"
    __table_args__ = ({"schema": "configuration"},)
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    email_from_default = Column(String, nullable=True)
    email_from_promotional = Column(String, nullable=True)
    email_from_transactional = Column(String, nullable=True)
    email_from_notification = Column(String, nullable=True)
    email_from_alert = Column(String, nullable=True)
    email_from_verification = Column(String, nullable=True)
    email_from_login_verification = Column(String, nullable=True)
    email_from_password_reset = Column(String, nullable=True)
    resend_api_key = Column(String, nullable=True)
    resend_webhook_secret = Column(String, nullable=True)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, nullable=True)
    smtp_username = Column(String, nullable=True)
    smtp_password = Column(String, nullable=True)
    smtp_use_tls = Column(Boolean, default=True)
    smtp_use_ssl = Column(Boolean, default=False)
    smtp_timeout_seconds = Column(Integer, default=10)
    country_code = Column(String(3), nullable=True, index=True)


class ShippingCarrier(Base):
    __tablename__ = "shipping_carriers"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class ShippingZone(Base):
    __tablename__ = "shipping_zones"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    name = Column(String, nullable=False)
    countries = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class FinanceBankAccount(Base):
    __tablename__ = "finance_bank_accounts"
    __table_args__ = ({"schema": "treasury"},)
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String, nullable=True)
    account_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    account_label = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    swift_code = Column(String, nullable=True)
    routing_number = Column(String, nullable=True)
    currency = Column(String(3), nullable=True)
    support_email = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)
    remittance_reference_prefix = Column(String, nullable=True)
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    scope = Column(String, nullable=True, default="zozi_primary")
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class PromotionEngineConfig(Base):
    __tablename__ = "promotion_engine_configs"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    engine_enabled = Column(Boolean, default=False)
    allow_product_coupons = Column(Boolean, default=True)
    allow_category_coupons = Column(Boolean, default=True)
    allow_order_tier_discounts = Column(Boolean, default=True)
    allow_referral_rewards = Column(Boolean, default=True)
    allow_supplier_promotions = Column(Boolean, default=True)
    allow_global_coupons = Column(Boolean, default=True)
    stacking_mode = Column(String, default="best_only")
    max_combined_discount_percent = Column(Numeric(5, 2), default=Decimal("50.00"))
    max_combined_discount_amount = Column(Numeric(12, 3), default=Decimal("0.000"))
    show_savings_line_item = Column(Boolean, default=True)
    tier_discount_visible = Column(Boolean, default=True)
    points_per_omr = Column(Integer, default=1000)
    referral_referrer_points = Column(Integer, default=100)
    referral_referee_points = Column(Integer, default=100)
    points_expiry_months = Column(Integer, default=12)
    referral_monthly_cap = Column(Integer, default=20)
    referral_verification_delay_days = Column(Integer, default=7)
    min_points_redeem = Column(Integer, default=1000)
    allow_partial_points_redemption = Column(Boolean, default=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class PromotionLedgerEntry(Base):
    __tablename__ = "promotion_ledger_entries"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    entry_type = Column(String, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class PromotionOrderTier(Base):
    __tablename__ = "promotion_order_tiers"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, nullable=True)
    tier_name = Column(String, nullable=True)
    min_order_amount = Column(Numeric(10, 2), nullable=False)
    max_order_amount = Column(Numeric(10, 2), nullable=True)
    discount_type = Column(String, nullable=False, default="fixed")
    discount_amount = Column(Numeric(10, 2), nullable=True)
    discount_value = Column(Numeric(10, 2), nullable=True)
    stacking_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=True)
    updated_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)

    country = relationship("CountryConfig", foreign_keys=[country_code])


class LogisticsCODRemittanceReceipt(Base):
    __tablename__ = "logistics_cod_remittance_receipts"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=True)
    settlement_id = Column(Integer, ForeignKey("logistics.logistics_settlements.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    bank_reference = Column(String, nullable=True)
    receipt_file_url = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    status = Column(String, default="pending")
    currency = Column(String(3), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    settlement = relationship("LogisticsSettlement", foreign_keys=[settlement_id])
    partner = relationship("LogisticsPartner", foreign_keys=[partner_id])


class LogisticsPartnerBankAccount(Base):
    __tablename__ = "logistics_partner_bank_accounts"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    account_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    beneficiary_name = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    swift_code = Column(String, nullable=True)
    routing_number = Column(String, nullable=True)
    currency = Column(String(3), nullable=True)
    bank_country = Column(String(3), nullable=True)
    verification_status = Column(String, default="pending")
    verification_note = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    provider_recipient_id = Column(String, nullable=True)
    provider_status = Column(String, nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class LogisticsPartnerDocument(Base):
    __tablename__ = "logistics_partner_documents"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    doc_type = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    reviewed_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class LogisticsSettlement(Base):
    __tablename__ = "logistics_settlements"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    ledger_id = Column(Integer, nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    pickup_charge = Column(Numeric(12, 2), nullable=True)
    dropoff_charge = Column(Numeric(12, 2), nullable=True)
    total_delivery_fee = Column(Numeric(12, 2), nullable=True)
    cod_collected = Column(Numeric(12, 2), nullable=True)
    cod_remitted = Column(Numeric(12, 2), nullable=True)
    cod_retained = Column(Numeric(12, 2), nullable=True)
    cod_remittance_status = Column(String, nullable=True)
    eligible_at = Column(DateTime, nullable=True)
    status = Column(String, default="pending")
    currency = Column(String(3), nullable=True)
    payout_id = Column(Integer, ForeignKey("treasury.payouts.id"), nullable=True)
    bank_transaction_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class ShipmentConfirmation(Base):
    __tablename__ = "shipment_confirmations"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    requester_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    requester_role = Column(String, nullable=True)
    target_user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    target_role = Column(String, nullable=True)
    confirmation_type = Column(String, nullable=True)
    status = Column(String, default="pending")
    requested_status = Column(String, nullable=True)
    requested_event_type = Column(String, nullable=True)
    current_hub = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    confirmation_code = Column(String, nullable=True)
    confirmed_at = Column(DateTime, default=_utcnow)
    responded_at = Column(DateTime, nullable=True)
    tracking_number = Column(String, nullable=True)
    delivery_signature_name = Column(String, nullable=True)
    delivery_signature_data_url = Column(String, nullable=True)
    delivery_signature_captured_at = Column(DateTime, nullable=True)
    response_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class ChatbotQueryEvent(Base):
    __tablename__ = "chatbot_query_events"
    __table_args__ = (
        Index("ix_chatbot_events_user_created", "user_id", "created_at"),
        Index("ix_chatbot_events_session_created", "session_id", "created_at"),
        Index("ix_chatbot_events_type_created", "event_type", "created_at"),
        Index("ix_chatbot_events_intent_created", "intent", "created_at"),
        Index("ix_chatbot_events_clicked_product_id", "clicked_product_id"),
        Index("ix_chatbot_events_created_at", "created_at"),
        Index("ix_chatbot_events_normalized_query", "normalized_query"),
        Index("ix_chatbot_events_session_id", "session_id"), {"schema": "audit"})

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    session_id = Column(String(64), nullable=False)
    event_type = Column(String(30), nullable=False, server_default="query")
    message = Column(Text, nullable=True)
    normalized_query = Column(String(500), nullable=True)
    intent = Column(String(100), nullable=True)
    filters_json = Column(Text, nullable=True)
    result_count = Column(Integer, nullable=False, server_default="0")
    product_ids_json = Column(Text, nullable=True)
    clicked_product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    country_code = Column(String(3), nullable=True, index=True)

    __constraints__ = (
        CheckConstraint("result_count >= 0", name="ck_chatbot_events_result_count_nonnegative"),
    )


class PushNotificationToken(Base):
    __tablename__ = "push_notification_tokens"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    token = Column(String, nullable=False)
    device_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class ProductVerification(Base):
    __tablename__ = "product_verifications"
    __table_args__ = ({"schema": "commerce"},)
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("commerce.products.id"), nullable=False)
    status = Column(String, default="pending")
    verified_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    shipment_id = Column(Integer, ForeignKey("logistics.shipments.id"), nullable=True)
    verification_type = Column(String, nullable=True)
    result = Column(String, nullable=True)
    expected_specs = Column(Text, nullable=True)
    actual_specs = Column(Text, nullable=True)
    discrepancies = Column(Text, nullable=True)
    scan_code = Column(String, nullable=True)
    image_urls = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    country_code = Column(String(3), nullable=True, index=True)


class SupplierBankAccount(Base):
    __tablename__ = "supplier_bank_accounts"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    account_number = Column(String, nullable=True)
    bank_name = Column(String, nullable=False)
    beneficiary_name = Column(String, nullable=True)
    branch_name = Column(String, nullable=True)
    iban = Column(String, nullable=True)
    swift_code = Column(String, nullable=True)
    routing_number = Column(String, nullable=True)
    currency = Column(String(3), nullable=True)
    bank_country = Column(String(3), nullable=True)
    verification_status = Column(String, default="pending")
    verification_note = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    provider_recipient_id = Column(String, nullable=True)
    provider_status = Column(String, nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"
    __table_args__ = ({"schema": "analytics"},)
    id = Column(Integer, primary_key=True, index=True)
    processor = Column(String, nullable=False)
    event_id = Column(String, nullable=False)
    payload_hash = Column(String, nullable=False)
    processed_at = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


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
    __table_args__ = ({"schema": "analytics"},)
    id = Column(Integer, primary_key=True, index=True)
    provider_code = Column(String, nullable=False, index=True)
    gateway_event_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    environment = Column(String, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    zozi_order_id = Column(Integer, nullable=True)
    gateway_transaction_id = Column(String, nullable=True)
    gateway_customer_id = Column(String, nullable=True)
    gross_amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(3), nullable=True)
    gateway_fee = Column(Numeric(12, 2), nullable=True)
    net_settlement = Column(Numeric(12, 2), nullable=True)
    fraud_score = Column(Numeric(5, 2), nullable=True)
    three_ds_status = Column(String, nullable=True)
    avs_result = Column(String, nullable=True)
    raw_payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class EmployeeExpense(Base):
    __tablename__ = "employee_expenses"
    __table_args__ = ({"schema": "hr"},)
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("logistics.employees.id"), nullable=False, index=True)
    expense_type = Column(String(50), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")
    approved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    receipt_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)
    employee = relationship("Employee", backref="expenses")
    approver = relationship("User", foreign_keys=[approved_by])


class SupplierDispute(Base):
    __tablename__ = "supplier_disputes"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("commerce.orders.id"), nullable=True)
    dispute_type = Column(String(40), default="other")
    priority = Column(String(20), default="medium")
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    return_request_id = Column(Integer, ForeignKey("commerce.return_requests.id"), nullable=True)
    verification_id = Column(Integer, nullable=True)
    invoice_id = Column(Integer, nullable=True)
    related_order_id = Column(Integer, nullable=True)
    evidence_urls = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    supplier_notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    reason = Column(Text, nullable=True)
    status = Column(String, default="open")
    resolved_by = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(3), nullable=True, index=True)


class SupplierCountryCommission(Base):
    __tablename__ = "supplier_country_commissions"
    __table_args__ = ({"schema": "supplier"},)
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    country_code = Column(String(3), nullable=False)
    commission_rate = Column(Numeric(5, 2), nullable=False)
    category_slug = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)


class RetentionJobRun(Base):
    __tablename__ = "retention_job_runs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=True)
    target_table = Column(String(100), nullable=True)
    target_name = Column(String(100), nullable=True)
    cutoff_days = Column(Integer, nullable=True)
    records_deleted = Column(Integer, default=0)
    archived_count = Column(Integer, default=0)
    deleted_count = Column(Integer, default=0)
    artifact_path = Column(String, nullable=True)
    result_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=_utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="pending")
    error_message = Column(Text, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
