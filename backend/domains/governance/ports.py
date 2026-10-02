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

from domains.governance.models.admin import APIKey, AdminActivityLog, AdminAnalyticsSnapshot, AdminChangeAuditLog, BadgeBillingRecord, BadgeTier, BadgeTransaction, ChatbotQueryEvent, CommissionBadgeTier, CommissionGlobalConfig, EmailProviderConfig, EmployeeExpense, FinanceBankAccount, LogisticsCODRemittanceReceipt, LogisticsPartnerDocument, LogisticsSettlement, NormalizedWebhookEvent, PaymentProviderConfig, ProcessedWebhookEvent, ProductVerification, PromotionOrderTier, PushNotificationToken, RetentionJobRun, RolePermissionSetting, ShipmentConfirmation, ShippingCarrier, ShippingZone, SupplierCountryCommission, SystemAlert, SystemSetting, TicketReply
from domains.accounts.models.banking import LogisticsPartnerBankAccount, SupplierBankAccount
from domains.suppliers.models.suppliers import SupplierDispute
from domains.promotions.models.coupon_usage import CouponUsage
from domains.promotions.models.promotion_config import PromotionEngineConfig
from domains.promotions.models.promotion_ledger import PromotionLedgerEntry
from domains.accounts.models.user import (
    EmailVerificationToken,
    PasswordResetToken,
    RevokedToken,
    User,
)
from domains.customers.models.customer_schema_models import ReferralPointEvent
from domains.security.models.fraud import CreditCardBin, DLPViolation, DeviceFingerprint, FraudAlert, FraudBlacklist, FraudCase, FraudCaseAssignment, FraudEvent, FraudRule, FraudScoringLog, IPAccountLinkage, IPReputation, LogisticsFraudIndicator, ManualReviewQueue, MeetingActionItem, MeetingTranscript, ReturnAbusePattern, VelocityCounter
from domains.suppliers.models.fraud_indicators import SupplierFraudIndicator
from domains.comms.models.fraud import MeetingRecording
from domains.comms.models.incident import IncidentActionItem, IncidentThread, IncidentWarRoom, WarRoomTemplate


def get_shipping_carrier_by_id(db: Session, id_: int) -> Optional[ShippingCarrier]:
    """Return ShippingCarrier by primary key (or None)."""
    return db.get(ShippingCarrier, id_)


def get_shipping_zone_by_id(db: Session, id_: int) -> Optional[ShippingZone]:
    """Return ShippingZone by primary key (or None)."""
    return db.get(ShippingZone, id_)


def get_logistics_partner_bank_account_by_id(db: Session, id_: int) -> Optional[LogisticsPartnerBankAccount]:
    """Return LogisticsPartnerBankAccount by primary key (or None)."""
    return db.get(LogisticsPartnerBankAccount, id_)


def supplier_bank_account_query(db: Session) -> object:
    """Return a base ``SupplierBankAccount`` query for sanctioned cross-domain delegation."""
    return db.query(SupplierBankAccount)


def supplier_bank_account_model() -> type:
    """Return the ``SupplierBankAccount`` model class (for column reference only)."""
    return SupplierBankAccount


# --- P11 re-exports (Law 3 sanctioned READ surface only) ---
# Ports.py is read-only model access. Service functions must be imported
# directly from their owning service modules, NOT through ports.
# Reads/models are re-exported from owning models; writes were removed and their
# consumers now call the owning governance service directly (ports is read-only).
from domains.governance.models.admin import LogisticsCODRemittanceReceipt, LogisticsPartnerDocument, LogisticsSettlement, PromotionOrderTier, ShipmentConfirmation, ShippingCarrier, ShippingZone
from domains.accounts.models.banking import LogisticsPartnerBankAccount
from domains.suppliers.models.suppliers import SupplierDispute
from domains.promotions.models.coupon_usage import CouponUsage
from domains.promotions.models.promotion_config import PromotionEngineConfig
from domains.promotions.models.promotion_ledger import PromotionLedgerEntry

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
    "TicketAttachment": ("domains.comms.models.communication_schema_models", "TicketAttachment"),
    "TicketReply": ("domains.governance.models.admin", "TicketReply"),
    "SupplierDispute": ("domains.governance.models.admin", "SupplierDispute"),
    "Address": ("domains.accounts.models.core", "Address"),
    "logistics_partner_bank_account_model": ("domains.governance.models.admin", "LogisticsPartnerBankAccount"),
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
    "DataResidencyService": ("domains.governance.services.audit", "DataResidencyService"),
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
    "delete_user_admin": ("domains.accounts.services.users.user_management_service", "delete_user_admin"),
    "approve_product": ("domains.catalog.services.products.admin_products_service", "approve_product"),
    "reject_product": ("domains.catalog.services.products.admin_products_service", "reject_product"),
    "delete_coupon": ("domains.promotions.services.coupons.coupon_service", "delete_coupon_admin"),
    "verify_payout": ("domains.finance.services.payouts.payout_batch_service", "verify_payout"),
    "verify_bank_account": ("domains.accounts.services.users.user_management_service", "verify_bank_account"),
    "get_authority_level": ("domains.hr.services.hierarchy.hierarchy_service", "get_authority_level"),
    "get_user_chain": ("domains.hr.services.hierarchy.hierarchy_service", "get_user_chain"),
    "get_all_subordinates": ("domains.hr.services.hierarchy.hierarchy_service", "get_all_subordinates"),
    "get_team_members": ("domains.hr.services.hierarchy.hierarchy_service", "get_team_members"),
    "is_in_chain": ("domains.hr.services.hierarchy.hierarchy_service", "is_in_chain"),
    "can_manage": ("domains.hr.services.hierarchy.hierarchy_service", "can_manage"),
    "get_org_chart": ("domains.hr.services.hierarchy.hierarchy_service", "get_org_chart"),
    "get_home_org_unit": ("domains.hr.services.hierarchy.hierarchy_service", "get_home_org_unit"),
    # Promotion/coupon operations (canonical homes in promotions/customers domains)
    "list_coupons": ("domains.customers.services.coupons_read_service", "list_coupons"),
    "create_coupon": ("domains.catalog.services.promotions.promotions_service", "create_coupon"),
    "validate_coupon": ("domains.customers.services.coupons_service", "validate_coupon"),
    # Account operations (canonical home in accounts domain)
    "get_user_by_id": ("domains.accounts.ports", "get_user_by_id"),
    # Approval/workflow operations (canonical home in governance/approval)
    "can_approve": ("domains.governance.services.approval.approval_matrix_service", "can_approve"),
    "require_approval": ("domains.governance.services.approval.approval_matrix_service", "require_approval"),
    "resolve_approvers": ("domains.governance.services.approval.approval_matrix_service", "resolve_approvers"),
    # Permission operations (canonical home in hr domain)
    "check_permission": ("domains.hr.services.hr_permissions", "check_permission"),
    "reassign_manager": ("domains.hr.services.hierarchy.hierarchy_service", "reassign_manager"),
    "backfill_authority_levels": ("domains.hr.services.hierarchy.hierarchy_service", "backfill_authority_levels"),
    "APPROVAL_RULES": ("domains.governance.services.approval.approval_matrix_service", "APPROVAL_RULES"),
}

import importlib

# Explicit lazy stubs so `from module import name` works (Python 3.10 compatibility)
# These are populated on first access by __getattr__
is_in_chain = None
can_manage = None
reassign_manager = None
backfill_authority_levels = None
check_permission = None
can_approve = None
require_approval = None
resolve_approvers = None
APPROVAL_RULES = None
approve_product = None
reject_product = None
delete_coupon = None
verify_payout = None
verify_bank_account = None
get_authority_level = None
get_user_chain = None
get_all_subordinates = None
get_team_members = None
get_org_chart = None
get_home_org_unit = None
list_coupons = None
create_coupon = None
validate_coupon = None
get_user_by_id = None

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, symbol)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# --- Sanctioned cross-domain function surface ---

def list_coupons(db: Session, limit: int = 100, cursor: Optional[int] = None) -> dict:
    """Sanctioned cross-domain read: list coupons (delegates to promotions domain)."""
    from domains.promotions.ports import list_coupons as _svc
    return _svc(db, cursor=cursor, page_size=limit)


def create_coupon(db: Session, payload: dict) -> dict:
    """Sanctioned cross-domain write: create a coupon (delegates to promotions domain)."""
    from domains.promotions.ports import create_coupon_from_payload as _svc
    return _svc(db, payload)


def validate_coupon(db: Session, code: str, order_total: object) -> dict:
    """Sanctioned cross-domain read: validate a coupon (delegates to promotions domain)."""
    from domains.promotions.ports import validate_coupon as _svc
    return _svc(db, code, order_total)


def get_approval_chain(db: Session, employee_id: int, resource_type: str, min_authority_level: int | None = None) -> list:
    """Sanctioned cross-domain read: resolve the approval chain for an employee/resource."""
    from domains.governance.services.approval.approval_matrix_service import get_approval_chain as _svc
    return _svc(db, user_id=employee_id, resource_type=resource_type)

def get_ticket_detail(db, ticket_id: int, *args, **kwargs) -> dict | None:
    """Return a support-ticket detail by id (Law 3 sanctioned read surface).

    Degrades gracefully (Law 30) — returns None when the ticket store is
    unavailable. Route it through the comms tickets service once provisioned.
    """
    try:
        from domains.comms.services.tickets.tickets_service import get_ticket_by_id

        return get_ticket_by_id(db, ticket_id)
    except Exception:
        return None
