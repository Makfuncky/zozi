"""governance domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.governance.models`` or ``domains.governance.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
)

# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``)
# so cross-domain consumers are unaffected, but they are now sourced via keyset
# (stable ``id`` order, no OFFSET). The ``*_page`` companions return a ``CursorPage``
# for scale-ready cursor paging (the 100Ks-concurrent-user path).

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page over ``model`` (scale-ready, no OFFSET)."""
    return cursor_paginate_asc(db.query(model), cursor=cursor, page_size=page_size)

from domains.governance.models.admin import APIKey, AdminActivityLog, AdminAnalyticsSnapshot, AdminChangeAuditLog, BadgeBillingRecord, BadgeTier, BadgeTransaction, ChatbotQueryEvent, CommissionBadgeTier, CommissionGlobalConfig, CouponUsage, EmailProviderConfig, EmployeeExpense, FinanceBankAccount, LogisticsCODRemittanceReceipt, LogisticsPartnerBankAccount, LogisticsPartnerDocument, LogisticsSettlement, NormalizedWebhookEvent, PaymentProviderConfig, ProcessedWebhookEvent, ProductVerification, PromotionEngineConfig, PromotionLedgerEntry, PromotionOrderTier, PushNotificationToken, RetentionJobRun, RolePermissionSetting, ShipmentConfirmation, ShippingCarrier, ShippingZone, SupplierBankAccount, SupplierCountryCommission, SupplierDispute, SystemAlert, SystemSetting, TicketReply
from domains.accounts.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RevokedToken,
    User,
)
from domains.customers.models.customer_schema_models import ReferralPointEvent
from domains.security.models.fraud import CreditCardBin, DLPViolation, DeviceFingerprint, FraudAlert, FraudBlacklist, FraudCase, FraudCaseAssignment, FraudEvent, FraudRule, FraudScoringLog, IPAccountLinkage, IPReputation, LogisticsFraudIndicator, ManualReviewQueue, MeetingActionItem, MeetingTranscript, ReturnAbusePattern, SupplierFraudIndicator, VelocityCounter
from domains.comms.models.fraud import MeetingRecording
from domains.comms.models.incident import IncidentActionItem, IncidentThread, IncidentWarRoom, WarRoomTemplate


def get_admin_analytics_snapshot_by_id(db: Session, id_: int) -> Optional[AdminAnalyticsSnapshot]:
    """Return AdminAnalyticsSnapshot by primary key (or None)."""
    return db.get(AdminAnalyticsSnapshot, id_)

def list_admin_analytics_snapshots(db: Session, limit: int = 100) -> List[AdminAnalyticsSnapshot]:
    """Return up to ``limit`` AdminAnalyticsSnapshot rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AdminAnalyticsSnapshot, db, limit)

def list_admin_analytics_snapshots_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AdminAnalyticsSnapshot rows (scale-ready)."""
    return _keyset_page(AdminAnalyticsSnapshot, db, cursor, page_size)

def get_role_permission_setting_by_id(db: Session, id_: int) -> Optional[RolePermissionSetting]:
    """Return RolePermissionSetting by primary key (or None)."""
    return db.get(RolePermissionSetting, id_)

def list_role_permission_settings(db: Session, limit: int = 100) -> List[RolePermissionSetting]:
    """Return up to ``limit`` RolePermissionSetting rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RolePermissionSetting, db, limit)

def list_role_permission_settings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of RolePermissionSetting rows (scale-ready)."""
    return _keyset_page(RolePermissionSetting, db, cursor, page_size)

def get_system_alert_by_id(db: Session, id_: int) -> Optional[SystemAlert]:
    """Return SystemAlert by primary key (or None)."""
    return db.get(SystemAlert, id_)

def list_system_alerts(db: Session, limit: int = 100) -> List[SystemAlert]:
    """Return up to ``limit`` SystemAlert rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SystemAlert, db, limit)

def list_system_alerts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SystemAlert rows (scale-ready)."""
    return _keyset_page(SystemAlert, db, cursor, page_size)

def get_admin_change_audit_log_by_id(db: Session, id_: int) -> Optional[AdminChangeAuditLog]:
    """Return AdminChangeAuditLog by primary key (or None)."""
    return db.get(AdminChangeAuditLog, id_)

def list_admin_change_audit_logs(db: Session, limit: int = 100) -> List[AdminChangeAuditLog]:
    """Return up to ``limit`` AdminChangeAuditLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AdminChangeAuditLog, db, limit)

def list_admin_change_audit_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AdminChangeAuditLog rows (scale-ready)."""
    return _keyset_page(AdminChangeAuditLog, db, cursor, page_size)

def get_admin_activity_log_by_id(db: Session, id_: int) -> Optional[AdminActivityLog]:
    """Return AdminActivityLog by primary key (or None)."""
    return db.get(AdminActivityLog, id_)

def list_admin_activity_logs(db: Session, limit: int = 100) -> List[AdminActivityLog]:
    """Return up to ``limit`` AdminActivityLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(AdminActivityLog, db, limit)

def list_admin_activity_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of AdminActivityLog rows (scale-ready)."""
    return _keyset_page(AdminActivityLog, db, cursor, page_size)

def get_system_setting_by_id(db: Session, id_: int) -> Optional[SystemSetting]:
    """Return SystemSetting by primary key (or None)."""
    return db.get(SystemSetting, id_)

def list_system_settings(db: Session, limit: int = 100) -> List[SystemSetting]:
    """Return up to ``limit`` SystemSetting rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SystemSetting, db, limit)

def list_system_settings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SystemSetting rows (scale-ready)."""
    return _keyset_page(SystemSetting, db, cursor, page_size)

def get_a_p_i_key_by_id(db: Session, id_: int) -> Optional[APIKey]:
    """Return APIKey by primary key (or None)."""
    return db.get(APIKey, id_)

def list_api_keys(db: Session, limit: int = 100) -> List[APIKey]:
    """Return up to ``limit`` APIKey rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(APIKey, db, limit)

def list_api_keys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of APIKey rows (scale-ready)."""
    return _keyset_page(APIKey, db, cursor, page_size)

def get_badge_billing_record_by_id(db: Session, id_: int) -> Optional[BadgeBillingRecord]:
    """Return BadgeBillingRecord by primary key (or None)."""
    return db.get(BadgeBillingRecord, id_)

def list_badge_billing_records(db: Session, limit: int = 100) -> List[BadgeBillingRecord]:
    """Return up to ``limit`` BadgeBillingRecord rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BadgeBillingRecord, db, limit)

def list_badge_billing_records_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BadgeBillingRecord rows (scale-ready)."""
    return _keyset_page(BadgeBillingRecord, db, cursor, page_size)

def get_badge_transaction_by_id(db: Session, id_: int) -> Optional[BadgeTransaction]:
    """Return BadgeTransaction by primary key (or None)."""
    return db.get(BadgeTransaction, id_)

def list_badge_transactions(db: Session, limit: int = 100) -> List[BadgeTransaction]:
    """Return up to ``limit`` BadgeTransaction rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BadgeTransaction, db, limit)

def list_badge_transactions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BadgeTransaction rows (scale-ready)."""
    return _keyset_page(BadgeTransaction, db, cursor, page_size)

def get_badge_tier_by_id(db: Session, id_: int) -> Optional[BadgeTier]:
    """Return BadgeTier by primary key (or None)."""
    return db.get(BadgeTier, id_)

def list_badge_tiers(db: Session, limit: int = 100) -> List[BadgeTier]:
    """Return up to ``limit`` BadgeTier rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BadgeTier, db, limit)

def list_badge_tiers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of BadgeTier rows (scale-ready)."""
    return _keyset_page(BadgeTier, db, cursor, page_size)

def get_commission_badge_tier_by_id(db: Session, id_: int) -> Optional[CommissionBadgeTier]:
    """Return CommissionBadgeTier by primary key (or None)."""
    return db.get(CommissionBadgeTier, id_)

def list_commission_badge_tiers(db: Session, limit: int = 100) -> List[CommissionBadgeTier]:
    """Return up to ``limit`` CommissionBadgeTier rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommissionBadgeTier, db, limit)

def list_commission_badge_tiers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommissionBadgeTier rows (scale-ready)."""
    return _keyset_page(CommissionBadgeTier, db, cursor, page_size)

def get_commission_global_config_by_id(db: Session, id_: int) -> Optional[CommissionGlobalConfig]:
    """Return CommissionGlobalConfig by primary key (or None)."""
    return db.get(CommissionGlobalConfig, id_)

def list_commission_global_configs(db: Session, limit: int = 100) -> List[CommissionGlobalConfig]:
    """Return up to ``limit`` CommissionGlobalConfig rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CommissionGlobalConfig, db, limit)

def list_commission_global_configs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CommissionGlobalConfig rows (scale-ready)."""
    return _keyset_page(CommissionGlobalConfig, db, cursor, page_size)

def get_ticket_reply_by_id(db: Session, id_: int) -> Optional[TicketReply]:
    """Return TicketReply by primary key (or None)."""
    return db.get(TicketReply, id_)

def list_ticket_replies(db: Session, limit: int = 100) -> List[TicketReply]:
    """Return up to ``limit`` TicketReply rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(TicketReply, db, limit)

def list_ticket_replies_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of TicketReply rows (scale-ready)."""
    return _keyset_page(TicketReply, db, cursor, page_size)

def get_coupon_usage_by_id(db: Session, id_: int) -> Optional[CouponUsage]:
    """Return CouponUsage by primary key (or None)."""
    return db.get(CouponUsage, id_)

def list_coupon_usages(db: Session, limit: int = 100) -> List[CouponUsage]:
    """Return up to ``limit`` CouponUsage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CouponUsage, db, limit)

def list_coupon_usages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CouponUsage rows (scale-ready)."""
    return _keyset_page(CouponUsage, db, cursor, page_size)

def get_payment_provider_config_by_id(db: Session, id_: int) -> Optional[PaymentProviderConfig]:
    """Return PaymentProviderConfig by primary key (or None)."""
    return db.get(PaymentProviderConfig, id_)

def list_payment_provider_configs(db: Session, limit: int = 100) -> List[PaymentProviderConfig]:
    """Return up to ``limit`` PaymentProviderConfig rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PaymentProviderConfig, db, limit)

def list_payment_provider_configs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PaymentProviderConfig rows (scale-ready)."""
    return _keyset_page(PaymentProviderConfig, db, cursor, page_size)

def get_email_provider_config_by_id(db: Session, id_: int) -> Optional[EmailProviderConfig]:
    """Return EmailProviderConfig by primary key (or None)."""
    return db.get(EmailProviderConfig, id_)

def list_email_provider_configs(db: Session, limit: int = 100) -> List[EmailProviderConfig]:
    """Return up to ``limit`` EmailProviderConfig rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmailProviderConfig, db, limit)

def list_email_provider_configs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmailProviderConfig rows (scale-ready)."""
    return _keyset_page(EmailProviderConfig, db, cursor, page_size)

def get_shipping_carrier_by_id(db: Session, id_: int) -> Optional[ShippingCarrier]:
    """Return ShippingCarrier by primary key (or None)."""
    return db.get(ShippingCarrier, id_)

def list_shipping_carriers(db: Session, limit: int = 100) -> List[ShippingCarrier]:
    """Return up to ``limit`` ShippingCarrier rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShippingCarrier, db, limit)

def list_shipping_carriers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ShippingCarrier rows (scale-ready)."""
    return _keyset_page(ShippingCarrier, db, cursor, page_size)

def get_shipping_zone_by_id(db: Session, id_: int) -> Optional[ShippingZone]:
    """Return ShippingZone by primary key (or None)."""
    return db.get(ShippingZone, id_)

def list_shipping_zones(db: Session, limit: int = 100) -> List[ShippingZone]:
    """Return up to ``limit`` ShippingZone rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShippingZone, db, limit)

def list_shipping_zones_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ShippingZone rows (scale-ready)."""
    return _keyset_page(ShippingZone, db, cursor, page_size)

def get_finance_bank_account_by_id(db: Session, id_: int) -> Optional[FinanceBankAccount]:
    """Return FinanceBankAccount by primary key (or None)."""
    return db.get(FinanceBankAccount, id_)

def list_finance_bank_accounts(db: Session, limit: int = 100) -> List[FinanceBankAccount]:
    """Return up to ``limit`` FinanceBankAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FinanceBankAccount, db, limit)

def list_finance_bank_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FinanceBankAccount rows (scale-ready)."""
    return _keyset_page(FinanceBankAccount, db, cursor, page_size)

def get_promotion_engine_config_by_id(db: Session, id_: int) -> Optional[PromotionEngineConfig]:
    """Return PromotionEngineConfig by primary key (or None)."""
    return db.get(PromotionEngineConfig, id_)


def get_latest_promotion_engine_config(db: Session) -> Optional[PromotionEngineConfig]:
    """Return the most-recent PromotionEngineConfig row (or None)."""
    return db.query(PromotionEngineConfig).order_by(PromotionEngineConfig.id.desc()).first()


def list_promotion_engine_configs(db: Session, limit: int = 100) -> List[PromotionEngineConfig]:
    """Return up to ``limit`` PromotionEngineConfig rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PromotionEngineConfig, db, limit)

def list_promotion_engine_configs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PromotionEngineConfig rows (scale-ready)."""
    return _keyset_page(PromotionEngineConfig, db, cursor, page_size)

def get_promotion_ledger_entry_by_id(db: Session, id_: int) -> Optional[PromotionLedgerEntry]:
    """Return PromotionLedgerEntry by primary key (or None)."""
    return db.get(PromotionLedgerEntry, id_)

def list_promotion_ledger_entries(db: Session, limit: int = 100) -> List[PromotionLedgerEntry]:
    """Return up to ``limit`` PromotionLedgerEntry rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PromotionLedgerEntry, db, limit)

def list_promotion_ledger_entries_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PromotionLedgerEntry rows (scale-ready)."""
    return _keyset_page(PromotionLedgerEntry, db, cursor, page_size)

def get_promotion_order_tier_by_id(db: Session, id_: int) -> Optional[PromotionOrderTier]:
    """Return PromotionOrderTier by primary key (or None)."""
    return db.get(PromotionOrderTier, id_)

def list_promotion_order_tiers(db: Session, limit: int = 100) -> List[PromotionOrderTier]:
    """Return up to ``limit`` PromotionOrderTier rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PromotionOrderTier, db, limit)

def list_promotion_order_tiers_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PromotionOrderTier rows (scale-ready)."""
    return _keyset_page(PromotionOrderTier, db, cursor, page_size)

def get_logistics_c_o_d_remittance_receipt_by_id(db: Session, id_: int) -> Optional[LogisticsCODRemittanceReceipt]:
    """Return LogisticsCODRemittanceReceipt by primary key (or None)."""
    return db.get(LogisticsCODRemittanceReceipt, id_)

def list_logistics_c_o_d_remittance_receipts(db: Session, limit: int = 100) -> List[LogisticsCODRemittanceReceipt]:
    """Return up to ``limit`` LogisticsCODRemittanceReceipt rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsCODRemittanceReceipt, db, limit)

def list_logistics_c_o_d_remittance_receipts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsCODRemittanceReceipt rows (scale-ready)."""
    return _keyset_page(LogisticsCODRemittanceReceipt, db, cursor, page_size)

def get_logistics_partner_bank_account_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerBankAccount]:
    """Return LogisticsPartnerBankAccount by primary key (or None)."""
    return db.get(LogisticsPartnerBankAccount, id_)

def list_logistics_partner_bank_accounts(db: Session, limit: int = 100) -> List[LogisticsPartnerBankAccount]:
    """Return up to ``limit`` LogisticsPartnerBankAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartnerBankAccount, db, limit)

def list_logistics_partner_bank_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartnerBankAccount rows (scale-ready)."""
    return _keyset_page(LogisticsPartnerBankAccount, db, cursor, page_size)

def get_logistics_partner_document_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerDocument]:
    """Return LogisticsPartnerDocument by primary key (or None)."""
    return db.get(LogisticsPartnerDocument, id_)

def list_logistics_partner_documents(db: Session, limit: int = 100) -> List[LogisticsPartnerDocument]:
    """Return up to ``limit`` LogisticsPartnerDocument rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsPartnerDocument, db, limit)

def list_logistics_partner_documents_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsPartnerDocument rows (scale-ready)."""
    return _keyset_page(LogisticsPartnerDocument, db, cursor, page_size)

def get_logistics_settlement_by_id(db: Session, id_: int) -> Optional[LogisticsSettlement]:
    """Return LogisticsSettlement by primary key (or None)."""
    return db.get(LogisticsSettlement, id_)

def list_logistics_settlements(db: Session, limit: int = 100) -> List[LogisticsSettlement]:
    """Return up to ``limit`` LogisticsSettlement rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsSettlement, db, limit)

def list_logistics_settlements_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsSettlement rows (scale-ready)."""
    return _keyset_page(LogisticsSettlement, db, cursor, page_size)

def get_shipment_confirmation_by_id(db: Session, id_: int) -> Optional[ShipmentConfirmation]:
    """Return ShipmentConfirmation by primary key (or None)."""
    return db.get(ShipmentConfirmation, id_)

def list_shipment_confirmations(db: Session, limit: int = 100) -> List[ShipmentConfirmation]:
    """Return up to ``limit`` ShipmentConfirmation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ShipmentConfirmation, db, limit)

def list_shipment_confirmations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ShipmentConfirmation rows (scale-ready)."""
    return _keyset_page(ShipmentConfirmation, db, cursor, page_size)

def get_chatbot_query_event_by_id(db: Session, id_: int) -> Optional[ChatbotQueryEvent]:
    """Return ChatbotQueryEvent by primary key (or None)."""
    return db.get(ChatbotQueryEvent, id_)

def list_chatbot_query_events(db: Session, limit: int = 100) -> List[ChatbotQueryEvent]:
    """Return up to ``limit`` ChatbotQueryEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ChatbotQueryEvent, db, limit)

def list_chatbot_query_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ChatbotQueryEvent rows (scale-ready)."""
    return _keyset_page(ChatbotQueryEvent, db, cursor, page_size)

def get_push_notification_token_by_id(db: Session, id_: int) -> Optional[PushNotificationToken]:
    """Return PushNotificationToken by primary key (or None)."""
    return db.get(PushNotificationToken, id_)

def list_push_notification_tokens(db: Session, limit: int = 100) -> List[PushNotificationToken]:
    """Return up to ``limit`` PushNotificationToken rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(PushNotificationToken, db, limit)

def list_push_notification_tokens_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of PushNotificationToken rows (scale-ready)."""
    return _keyset_page(PushNotificationToken, db, cursor, page_size)

def get_product_verification_by_id(db: Session, id_: int) -> Optional[ProductVerification]:
    """Return ProductVerification by primary key (or None)."""
    return db.get(ProductVerification, id_)

def list_product_verifications(db: Session, limit: int = 100) -> List[ProductVerification]:
    """Return up to ``limit`` ProductVerification rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductVerification, db, limit)

def list_product_verifications_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProductVerification rows (scale-ready)."""
    return _keyset_page(ProductVerification, db, cursor, page_size)

def get_supplier_bank_account_by_id(db: Session, id_: int) -> Optional[SupplierBankAccount]:
    """Return SupplierBankAccount by primary key (or None)."""
    return db.get(SupplierBankAccount, id_)

def list_supplier_bank_accounts(db: Session, limit: int = 100) -> List[SupplierBankAccount]:
    """Return up to ``limit`` SupplierBankAccount rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierBankAccount, db, limit)

def list_supplier_bank_accounts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierBankAccount rows (scale-ready)."""
    return _keyset_page(SupplierBankAccount, db, cursor, page_size)

def get_processed_webhook_event_by_id(db: Session, id_: int) -> Optional[ProcessedWebhookEvent]:
    """Return ProcessedWebhookEvent by primary key (or None)."""
    return db.get(ProcessedWebhookEvent, id_)

def list_processed_webhook_events(db: Session, limit: int = 100) -> List[ProcessedWebhookEvent]:
    """Return up to ``limit`` ProcessedWebhookEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProcessedWebhookEvent, db, limit)

def list_processed_webhook_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ProcessedWebhookEvent rows (scale-ready)."""
    return _keyset_page(ProcessedWebhookEvent, db, cursor, page_size)

def get_normalized_webhook_event_by_id(db: Session, id_: int) -> Optional[NormalizedWebhookEvent]:
    """Return NormalizedWebhookEvent by primary key (or None)."""
    return db.get(NormalizedWebhookEvent, id_)

def list_normalized_webhook_events(db: Session, limit: int = 100) -> List[NormalizedWebhookEvent]:
    """Return up to ``limit`` NormalizedWebhookEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(NormalizedWebhookEvent, db, limit)

def list_normalized_webhook_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of NormalizedWebhookEvent rows (scale-ready)."""
    return _keyset_page(NormalizedWebhookEvent, db, cursor, page_size)

def get_employee_expense_by_id(db: Session, id_: int) -> Optional[EmployeeExpense]:
    """Return EmployeeExpense by primary key (or None)."""
    return db.get(EmployeeExpense, id_)

def list_employee_expenses(db: Session, limit: int = 100) -> List[EmployeeExpense]:
    """Return up to ``limit`` EmployeeExpense rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(EmployeeExpense, db, limit)

def list_employee_expenses_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of EmployeeExpense rows (scale-ready)."""
    return _keyset_page(EmployeeExpense, db, cursor, page_size)

def get_supplier_dispute_by_id(db: Session, id_: int) -> Optional[SupplierDispute]:
    """Return SupplierDispute by primary key (or None)."""
    return db.get(SupplierDispute, id_)

def list_supplier_disputes(db: Session, limit: int = 100) -> List[SupplierDispute]:
    """Return up to ``limit`` SupplierDispute rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierDispute, db, limit)

def list_supplier_disputes_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierDispute rows (scale-ready)."""
    return _keyset_page(SupplierDispute, db, cursor, page_size)

def get_supplier_country_commission_by_id(db: Session, id_: int) -> Optional[SupplierCountryCommission]:
    """Return SupplierCountryCommission by primary key (or None)."""
    return db.get(SupplierCountryCommission, id_)

def list_supplier_country_commissions(db: Session, limit: int = 100) -> List[SupplierCountryCommission]:
    """Return up to ``limit`` SupplierCountryCommission rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierCountryCommission, db, limit)

def list_supplier_country_commissions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierCountryCommission rows (scale-ready)."""
    return _keyset_page(SupplierCountryCommission, db, cursor, page_size)

def get_retention_job_run_by_id(db: Session, id_: int) -> Optional[RetentionJobRun]:
    """Return RetentionJobRun by primary key (or None)."""
    return db.get(RetentionJobRun, id_)

def list_retention_job_runs(db: Session, limit: int = 100) -> List[RetentionJobRun]:
    """Return up to ``limit`` RetentionJobRun rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(RetentionJobRun, db, limit)

def list_retention_job_runs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of RetentionJobRun rows (scale-ready)."""
    return _keyset_page(RetentionJobRun, db, cursor, page_size)

def get_fraud_event_by_id(db: Session, id_: int) -> Optional[FraudEvent]:
    """Return FraudEvent by primary key (or None)."""
    return db.get(FraudEvent, id_)

def list_fraud_events(db: Session, limit: int = 100) -> List[FraudEvent]:
    """Return up to ``limit`` FraudEvent rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudEvent, db, limit)

def list_fraud_events_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudEvent rows (scale-ready)."""
    return _keyset_page(FraudEvent, db, cursor, page_size)

def get_fraud_blacklist_by_id(db: Session, id_: int) -> Optional[FraudBlacklist]:
    """Return FraudBlacklist by primary key (or None)."""
    return db.get(FraudBlacklist, id_)

def list_fraud_blacklists(db: Session, limit: int = 100) -> List[FraudBlacklist]:
    """Return up to ``limit`` FraudBlacklist rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudBlacklist, db, limit)

def list_fraud_blacklists_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudBlacklist rows (scale-ready)."""
    return _keyset_page(FraudBlacklist, db, cursor, page_size)

def get_fraud_rule_by_id(db: Session, id_: int) -> Optional[FraudRule]:
    """Return FraudRule by primary key (or None)."""
    return db.get(FraudRule, id_)

def list_fraud_rules(db: Session, limit: int = 100) -> List[FraudRule]:
    """Return up to ``limit`` FraudRule rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudRule, db, limit)

def list_fraud_rules_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudRule rows (scale-ready)."""
    return _keyset_page(FraudRule, db, cursor, page_size)

def get_manual_review_queue_by_id(db: Session, id_: int) -> Optional[ManualReviewQueue]:
    """Return ManualReviewQueue by primary key (or None)."""
    return db.get(ManualReviewQueue, id_)

def list_manual_review_queues(db: Session, limit: int = 100) -> List[ManualReviewQueue]:
    """Return up to ``limit`` ManualReviewQueue rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ManualReviewQueue, db, limit)

def list_manual_review_queues_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ManualReviewQueue rows (scale-ready)."""
    return _keyset_page(ManualReviewQueue, db, cursor, page_size)

def get_i_p_reputation_by_id(db: Session, id_: int) -> Optional[IPReputation]:
    """Return IPReputation by primary key (or None)."""
    return db.get(IPReputation, id_)

def list_ip_reputations(db: Session, limit: int = 100) -> List[IPReputation]:
    """Return up to ``limit`` IPReputation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(IPReputation, db, limit)

def list_ip_reputations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of IPReputation rows (scale-ready)."""
    return _keyset_page(IPReputation, db, cursor, page_size)

def get_device_fingerprint_by_id(db: Session, id_: int) -> Optional[DeviceFingerprint]:
    """Return DeviceFingerprint by primary key (or None)."""
    return db.get(DeviceFingerprint, id_)

def list_device_fingerprints(db: Session, limit: int = 100) -> List[DeviceFingerprint]:
    """Return up to ``limit`` DeviceFingerprint rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DeviceFingerprint, db, limit)

def list_device_fingerprints_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of DeviceFingerprint rows (scale-ready)."""
    return _keyset_page(DeviceFingerprint, db, cursor, page_size)

def get_credit_card_bin_by_id(db: Session, id_: int) -> Optional[CreditCardBin]:
    """Return CreditCardBin by primary key (or None)."""
    return db.get(CreditCardBin, id_)

def list_credit_card_bins(db: Session, limit: int = 100) -> List[CreditCardBin]:
    """Return up to ``limit`` CreditCardBin rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(CreditCardBin, db, limit)

def list_credit_card_bins_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of CreditCardBin rows (scale-ready)."""
    return _keyset_page(CreditCardBin, db, cursor, page_size)

def get_return_abuse_pattern_by_id(db: Session, id_: int) -> Optional[ReturnAbusePattern]:
    """Return ReturnAbusePattern by primary key (or None)."""
    return db.get(ReturnAbusePattern, id_)

def list_return_abuse_patterns(db: Session, limit: int = 100) -> List[ReturnAbusePattern]:
    """Return up to ``limit`` ReturnAbusePattern rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ReturnAbusePattern, db, limit)

def list_return_abuse_patterns_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of ReturnAbusePattern rows (scale-ready)."""
    return _keyset_page(ReturnAbusePattern, db, cursor, page_size)

def get_supplier_fraud_indicator_by_id(db: Session, id_: int) -> Optional[SupplierFraudIndicator]:
    """Return SupplierFraudIndicator by primary key (or None)."""
    return db.get(SupplierFraudIndicator, id_)

def list_supplier_fraud_indicators(db: Session, limit: int = 100) -> List[SupplierFraudIndicator]:
    """Return up to ``limit`` SupplierFraudIndicator rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(SupplierFraudIndicator, db, limit)

def list_supplier_fraud_indicators_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of SupplierFraudIndicator rows (scale-ready)."""
    return _keyset_page(SupplierFraudIndicator, db, cursor, page_size)

def get_logistics_fraud_indicator_by_id(db: Session, id_: int) -> Optional[LogisticsFraudIndicator]:
    """Return LogisticsFraudIndicator by primary key (or None)."""
    return db.get(LogisticsFraudIndicator, id_)

def list_logistics_fraud_indicators(db: Session, limit: int = 100) -> List[LogisticsFraudIndicator]:
    """Return up to ``limit`` LogisticsFraudIndicator rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(LogisticsFraudIndicator, db, limit)

def list_logistics_fraud_indicators_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of LogisticsFraudIndicator rows (scale-ready)."""
    return _keyset_page(LogisticsFraudIndicator, db, cursor, page_size)

def get_fraud_alert_by_id(db: Session, id_: int) -> Optional[FraudAlert]:
    """Return FraudAlert by primary key (or None)."""
    return db.get(FraudAlert, id_)

def list_fraud_alerts(db: Session, limit: int = 100) -> List[FraudAlert]:
    """Return up to ``limit`` FraudAlert rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudAlert, db, limit)

def list_fraud_alerts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudAlert rows (scale-ready)."""
    return _keyset_page(FraudAlert, db, cursor, page_size)

def get_i_p_account_linkage_by_id(db: Session, id_: int) -> Optional[IPAccountLinkage]:
    """Return IPAccountLinkage by primary key (or None)."""
    return db.get(IPAccountLinkage, id_)

def list_ip_account_linkages(db: Session, limit: int = 100) -> List[IPAccountLinkage]:
    """Return up to ``limit`` IPAccountLinkage rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(IPAccountLinkage, db, limit)

def list_ip_account_linkages_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of IPAccountLinkage rows (scale-ready)."""
    return _keyset_page(IPAccountLinkage, db, cursor, page_size)

def get_velocity_counter_by_id(db: Session, id_: int) -> Optional[VelocityCounter]:
    """Return VelocityCounter by primary key (or None)."""
    return db.get(VelocityCounter, id_)

def list_velocity_counters(db: Session, limit: int = 100) -> List[VelocityCounter]:
    """Return up to ``limit`` VelocityCounter rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VelocityCounter, db, limit)

def list_velocity_counters_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of VelocityCounter rows (scale-ready)."""
    return _keyset_page(VelocityCounter, db, cursor, page_size)

def get_fraud_scoring_log_by_id(db: Session, id_: int) -> Optional[FraudScoringLog]:
    """Return FraudScoringLog by primary key (or None)."""
    return db.get(FraudScoringLog, id_)

def list_fraud_scoring_logs(db: Session, limit: int = 100) -> List[FraudScoringLog]:
    """Return up to ``limit`` FraudScoringLog rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudScoringLog, db, limit)

def list_fraud_scoring_logs_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudScoringLog rows (scale-ready)."""
    return _keyset_page(FraudScoringLog, db, cursor, page_size)

def get_fraud_case_by_id(db: Session, id_: int) -> Optional[FraudCase]:
    """Return FraudCase by primary key (or None)."""
    return db.get(FraudCase, id_)

def list_fraud_cases(db: Session, limit: int = 100) -> List[FraudCase]:
    """Return up to ``limit`` FraudCase rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudCase, db, limit)

def list_fraud_cases_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudCase rows (scale-ready)."""
    return _keyset_page(FraudCase, db, cursor, page_size)

def get_fraud_case_assignment_by_id(db: Session, id_: int) -> Optional[FraudCaseAssignment]:
    """Return FraudCaseAssignment by primary key (or None)."""
    return db.get(FraudCaseAssignment, id_)

def list_fraud_case_assignments(db: Session, limit: int = 100) -> List[FraudCaseAssignment]:
    """Return up to ``limit`` FraudCaseAssignment rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(FraudCaseAssignment, db, limit)

def list_fraud_case_assignments_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of FraudCaseAssignment rows (scale-ready)."""
    return _keyset_page(FraudCaseAssignment, db, cursor, page_size)

def get_d_l_p_violation_by_id(db: Session, id_: int) -> Optional[DLPViolation]:
    """Return DLPViolation by primary key (or None)."""
    return db.get(DLPViolation, id_)

def list_dlp_violations(db: Session, limit: int = 100) -> List[DLPViolation]:
    """Return up to ``limit`` DLPViolation rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(DLPViolation, db, limit)

def list_d_l_p_violations_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of DLPViolation rows (scale-ready)."""
    return _keyset_page(DLPViolation, db, cursor, page_size)

def get_meeting_transcript_by_id(db: Session, id_: int) -> Optional[MeetingTranscript]:
    """Return MeetingTranscript by primary key (or None)."""
    return db.get(MeetingTranscript, id_)

def list_meeting_transcripts(db: Session, limit: int = 100) -> List[MeetingTranscript]:
    """Return up to ``limit`` MeetingTranscript rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MeetingTranscript, db, limit)

def list_meeting_transcripts_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MeetingTranscript rows (scale-ready)."""
    return _keyset_page(MeetingTranscript, db, cursor, page_size)

def get_meeting_action_item_by_id(db: Session, id_: int) -> Optional[MeetingActionItem]:
    """Return MeetingActionItem by primary key (or None)."""
    return db.get(MeetingActionItem, id_)

def list_meeting_action_items(db: Session, limit: int = 100) -> List[MeetingActionItem]:
    """Return up to ``limit`` MeetingActionItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MeetingActionItem, db, limit)

def list_meeting_action_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MeetingActionItem rows (scale-ready)."""
    return _keyset_page(MeetingActionItem, db, cursor, page_size)

def get_meeting_recording_by_id(db: Session, id_: int) -> Optional[MeetingRecording]:
    """Return MeetingRecording by primary key (or None)."""
    return db.get(MeetingRecording, id_)

def list_meeting_recordings(db: Session, limit: int = 100) -> List[MeetingRecording]:
    """Return up to ``limit`` MeetingRecording rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(MeetingRecording, db, limit)

def list_meeting_recordings_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of MeetingRecording rows (scale-ready)."""
    return _keyset_page(MeetingRecording, db, cursor, page_size)

def get_incident_war_room_by_id(db: Session, id_: int) -> Optional[IncidentWarRoom]:
    """Return IncidentWarRoom by primary key (or None)."""
    return db.get(IncidentWarRoom, id_)

def list_incident_war_rooms(db: Session, limit: int = 100) -> List[IncidentWarRoom]:
    """Return up to ``limit`` IncidentWarRoom rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(IncidentWarRoom, db, limit)

def list_incident_war_rooms_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of IncidentWarRoom rows (scale-ready)."""
    return _keyset_page(IncidentWarRoom, db, cursor, page_size)

def get_incident_thread_by_id(db: Session, id_: int) -> Optional[IncidentThread]:
    """Return IncidentThread by primary key (or None)."""
    return db.get(IncidentThread, id_)

def list_incident_threads(db: Session, limit: int = 100) -> List[IncidentThread]:
    """Return up to ``limit`` IncidentThread rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(IncidentThread, db, limit)

def list_incident_threads_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of IncidentThread rows (scale-ready)."""
    return _keyset_page(IncidentThread, db, cursor, page_size)

def get_incident_action_item_by_id(db: Session, id_: int) -> Optional[IncidentActionItem]:
    """Return IncidentActionItem by primary key (or None)."""
    return db.get(IncidentActionItem, id_)

def list_incident_action_items(db: Session, limit: int = 100) -> List[IncidentActionItem]:
    """Return up to ``limit`` IncidentActionItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(IncidentActionItem, db, limit)

def list_incident_action_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of IncidentActionItem rows (scale-ready)."""
    return _keyset_page(IncidentActionItem, db, cursor, page_size)

def get_war_room_template_by_id(db: Session, id_: int) -> Optional[WarRoomTemplate]:
    """Return WarRoomTemplate by primary key (or None)."""
    return db.get(WarRoomTemplate, id_)

def list_war_room_templates(db: Session, limit: int = 100) -> List[WarRoomTemplate]:
    """Return up to ``limit`` WarRoomTemplate rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(WarRoomTemplate, db, limit)

def list_war_room_templates_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    """Keyset-cursor page of WarRoomTemplate rows (scale-ready)."""
    return _keyset_page(WarRoomTemplate, db, cursor, page_size)

# --- P11 re-exports (Law 3 sanctioned READ surface only) ---
# Ports.py is read-only model access. Service functions must be imported
# directly from their owning service modules, NOT through ports.
# Reads/models are re-exported from owning models; writes were removed and their
# consumers now call the owning governance service directly (ports is read-only).
from domains.governance.models.admin import CouponUsage, LogisticsCODRemittanceReceipt, LogisticsPartnerBankAccount, LogisticsPartnerDocument, LogisticsSettlement, PromotionEngineConfig, PromotionLedgerEntry, PromotionOrderTier, ShipmentConfirmation, ShippingCarrier, ShippingZone, SupplierDispute

# Model re-exports only (Law 3: ports should be read-only model access).
# Service functions were removed from this module and must be imported
# directly from their owning service modules.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    # Model re-exports (canonical homes in other domains)
    "User": ("domains.accounts.models.user", "User"),
    "UserDevice": ("domains.accounts.models.user", "UserDevice"),
    "UserLoginHistory": ("domains.accounts.models.user", "UserLoginHistory"),
    "SystemHealthEvent": ("domains.governance.models.core", "SystemHealthEvent"),
    "AuditLog": ("domains.audit.models.audit_schema_models", "AuditLog"),
    "SupportTicket": ("domains.comms.models.communication_schema_models", "SupportTicket"),
    "TicketReply": ("domains.governance.models.admin", "TicketReply"),
    "SupplierDispute": ("domains.governance.models.admin", "SupplierDispute"),
    "DirectChatMessage": ("domains.comms.models.chat", "DirectChatMessage"),
    "DirectChatRoom": ("domains.comms.models.chat", "DirectChatRoom"),
    "GroupChatRoom": ("domains.comms.models.chat", "GroupChatRoom"),
    "GroupChatMember": ("domains.comms.models.chat", "GroupChatMember"),
    "GroupChatMessage": ("domains.comms.models.chat", "GroupChatMessage"),
    "EntityChatThread": ("domains.comms.models.chat", "EntityChatThread"),
    "EntityChatMessage": ("domains.comms.models.chat", "EntityChatMessage"),
    "EscalationSLALog": ("domains.comms.models.chat", "EscalationSLALog"),
    "VideoRoom": ("domains.comms.models.chat", "VideoRoom"),
    "VideoRoomParticipant": ("domains.comms.models.chat", "VideoRoomParticipant"),
    "VideoRoomRecording": ("domains.comms.models.chat", "VideoRoomRecording"),
    # Service function exports (Law 3 sanctioned cross-domain surface)
    "bulk_archive_entities": ("domains.governance.services.admin.bulk_ops_service", "bulk_archive_entities"),
    "bulk_restore_entities": ("domains.governance.services.admin.bulk_ops_service", "bulk_restore_entities"),
    "DataResidencyService": ("domains.governance.services.audit.audit_trail_service", "DataResidencyService"),
    "download_export_job_result": ("domains.governance.services.operations", "download_export_job_result"),
    "export_audit_logs_csv": ("domains.governance.services.operations", "export_audit_logs_csv"),
    "export_coupons_csv": ("domains.governance.services.operations", "export_coupons_csv"),
    "export_orders_csv": ("domains.governance.services.operations", "export_orders_csv"),
    "export_products_csv": ("domains.governance.services.operations", "export_products_csv"),
    "export_transfer_csv": ("domains.governance.services.operations", "export_transfer_csv"),
    "export_users_csv": ("domains.governance.services.operations", "export_users_csv"),
    "queue_export_job": ("domains.governance.services.operations", "queue_export_job"),
    "update_flight_risk_score": ("domains.governance.services.risk.risk_write_service", "update_flight_risk_score"),
    "get_current_admin": ("domains.governance.services.settings.admin_service", "get_current_admin"),
    "get_ticket_detail": ("domains.governance.services.settings.admin_service", "get_ticket_detail"),
    "require_admin_2fa_enabled": ("domains.governance.services.settings.admin_service", "require_admin_2fa_enabled"),
    "require_admin_2fa_verified": ("domains.governance.services.settings.admin_service", "require_admin_2fa_verified"),
    "archive_entity": ("domains.governance.services.settings.misc_service", "archive_entity"),
    "restore_entity": ("domains.governance.services.settings.misc_service", "restore_entity"),
    "hard_delete_entity": ("domains.governance.services.settings.misc_service", "hard_delete_entity"),
    "create_processed_webhook_event": ("domains.governance.services.settings.misc_service", "create_processed_webhook_event"),
    "create_address": ("domains.governance.services.settings.misc_service", "create_address"),
    "get_audit_log_page": ("domains.governance.services.settings.misc_service", "get_audit_log_page"),
    "get_available_audit_actions": ("domains.governance.services.settings.misc_service", "get_available_audit_actions"),
}

import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# --- Query delegation (Law 3 sanctioned cross-domain query surface) ---

def badge_billing_record_query(db: Session) -> object:
    """Return a base ``BadgeBillingRecord`` query for sanctioned cross-domain delegation."""
    return db.query(BadgeBillingRecord)

def finance_bank_account_query(db: Session) -> object:
    """Return a base ``FinanceBankAccount`` query for sanctioned cross-domain delegation."""
    return db.query(FinanceBankAccount)

def logistics_cod_remittance_receipt_query(db: Session) -> object:
    """Return a base ``LogisticsCODRemittanceReceipt`` query for sanctioned cross-domain delegation."""
    return db.query(LogisticsCODRemittanceReceipt)

def logistics_settlement_query(db: Session) -> object:
    """Return a base ``LogisticsSettlement`` query for sanctioned cross-domain delegation."""
    return db.query(LogisticsSettlement)

def processed_webhook_event_query(db: Session) -> object:
    """Return a base ``ProcessedWebhookEvent`` query for sanctioned cross-domain delegation."""
    return db.query(ProcessedWebhookEvent)


def supplier_bank_account_query(db: Session) -> object:
    """Return a base ``SupplierBankAccount`` query for sanctioned cross-domain delegation."""
    return db.query(SupplierBankAccount)


def user_device_query(db: Session) -> object:
    """Return a base ``UserDevice`` query for sanctioned cross-domain delegation."""
    from domains.accounts.models.user import UserDevice
    return db.query(UserDevice)


def user_login_history_query(db: Session) -> object:
    """Return a base ``UserLoginHistory`` query for sanctioned cross-domain delegation."""
    from domains.accounts.models.user import UserLoginHistory
    return db.query(UserLoginHistory)


def supplier_bank_account_model() -> type:
    """Return the ``SupplierBankAccount`` model class (for column reference only)."""
    return SupplierBankAccount


def user_device_model() -> type:
    """Return the ``UserDevice`` model class (for column reference only)."""
    from domains.accounts.models.user import UserDevice
    return UserDevice


def user_login_history_model() -> type:
    """Return the ``UserLoginHistory`` model class (for column reference only)."""
    from domains.accounts.models.user import UserLoginHistory
    return UserLoginHistory


def get_approval_chain(db: Session, employee_id: int, resource_type: str, min_authority_level: int | None = None) -> list:
    """Sanctioned cross-domain read: resolve the approval chain for an employee/resource."""
    from domains.governance.services.approval.approval_matrix_service import get_approval_chain as _svc
    return _svc(db, user_id=employee_id, resource_type=resource_type)
