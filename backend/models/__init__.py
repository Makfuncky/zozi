from __future__ import annotations

from db.base import Base, _GuardedMetaData


from .core.user import *
from .catalog.products import *
from .orders.orders import *
from .finance.payments import *
from .communication.suppliers import *
from .logistics.logistics import *
from .communication.marketing import *
from .communication.communication import *
from .country.countries import *
from .treasury.finance import *
from .finance.commission import *
from .logistics.admin import *
from .security.fraud import *
from .communication.core import *
from .country.country_enhancements import *
from .logistics.country_control import *
from .hr.employee_models import *
from .media.media_models import *
from .mixins import *
from .supplier.onboarding import *
from .security.incident import *
from .security.permissions import *
from .catalog.ai_upload import *
from .logistics.imports import *
from .country.country_basics import *
from .country.country_economics import *
from .country.country_legal import *
from .country.country_tax import *
from .events import *
from .analytics.analytics import *
from .media.upload_job import *
from .audit.platform import *
from .ai.ai_models import *

__all__ = [
    "User", "UserDevice", "Referral", "ReferralPointEvent", "UserLoginHistory",
    "PasswordResetToken", "EmailVerificationToken", "RevokedToken",
    "Address", "Cart", "CartItem", "Review", "WishlistItem", "Wishlist",
    "AuditLog", "SupportTicket", "SupportTicketReply", "TicketAttachment", "UserBrowsingHistory",
    "ShiftHandoverLog", "PaymentOrchestratorSync", "Office", "CityDistanceMatrix",
    "ExecutiveNews", "SupplierOnboardingSync", "LegalContractTemplate", "DataResidencyRecord",
    "CountryMapConfig", "ShopWarehouseLocation", "LogisticsPartnerLocation", "ParcelLocationTracker",
    "CountryConfig", "CountryCommunication", "CountryGatewayCredentials", "PayoutRule", "TaxRule", "ShippingRule", "Message",
    "CountryCity",
    "Category", "Product", "ProductVariant", "ProductImage", "ProductVideo", "VideoAnalytics",
    "Order", "OrderItem", "OrderLogisticsAllocation",
    "ReturnRequest", "OrderNotification",
    "Warehouse", "StockMovement",
    "PurchaseOrder", "PurchaseOrderLine",
    "GoodsReceiptNote", "GoodsReceiptLine",
    "SalesOrder", "SalesOrderLine",
    "Payment", "Coupon", "Banner", "PaymentGatewayConnection", "Payout", "LogisticsPartnerPayout", "PaymentReconciliationRun",
    "SupplierProfile", "SupplierDocument", "SupplierNotificationPreference", "LogisticsPartnerProfile", "SupplierDispute", "SupplierCountryCommission",
    "LogisticsPartner", "LogisticsPartnerServiceArea", "LogisticsPricingProfile",
    "LogisticsVehicleRule", "LogisticsCategoryPricingRule", "Shipment", "ShipmentEvent",
    "FlashSale", "FlashSaleItem", "EmailCampaign", "EmailTemplate", "NewsletterSubscriber", "EmailCampaignLog",
    "Notification", "Announcement", "FAQ", "HelpCategory", "TicketMessage",
    "ProxyChannel", "ProxySession", "ProxyMessage", "ProxyCallLog",
    "TransactionLedger", "SupplierSettlement", "JournalEntry", "JournalEntryLine", "Account", "AccountGroup", "AccountBalance", "FinancialReport",
    "Invoice", "InvoiceItem", "RefundLedger", "BankTransaction", "VATRemittance",
    "APBill", "ARInvoice", "BankAccount",
    "CommissionAgreement", "ProductCommissionOverride", "CommissionLedgerEntry",
    "AdminAnalyticsSnapshot", "RolePermissionSetting", "SystemAlert", "AdminChangeAuditLog",
    "AdminActivityLog", "SystemSetting", "APIKey",
    "FraudEvent", "FraudBlacklist", "FraudRule", "ManualReviewQueue", "IPReputation", "DeviceFingerprint", "CreditCardBin", "ReturnAbusePattern",
    "SupplierFraudIndicator", "LogisticsFraudIndicator",
    "BadgeBillingRecord", "BadgeTransaction", "BadgeTier",
    "CommissionBadgeTier", "CommissionCategoryRate", "CommissionGlobalConfig",
    "TicketReply", "CouponUsage", "PaymentProviderConfig",
    "EmailProviderConfig", "ShippingCarrier", "ShippingZone", "FinanceBankAccount",
    "PromotionEngineConfig", "PromotionLedgerEntry", "PromotionOrderTier",
    "LogisticsCODRemittanceReceipt", "LogisticsPartnerBankAccount",
    "LogisticsPartnerDocument", "LogisticsSettlement", "ShipmentConfirmation",
    "ChatbotQueryEvent", "PushNotificationToken",
    "ProductVerification", "SupplierBankAccount",
    "ProcessedWebhookEvent", "NormalizedWebhookEvent", "SupplierKYCRequirement", "CountryCommissionRate", "CountryCategoryTaxRate", "LogisticsPartnerKYCRequirement",
    "CountryFeatureFlag", "CountryStaffAssignment", "CrossCountryCustomerSession", "OmanDeliveryZone",
    "CountryGatewayConfig", "CountryCommunicationThread", "CountryCommissionRateHistory", "CountryLogisticsZone", "CountryPayoutRule",
    "CampaignRecipient",
    "EmailDeliveryEvent", "EmailSuppression",
    "PayoutRuleCategory", "PayoutRuleProduct",
    "TreasuryAccount", "TreasuryTransaction", "CashFlowForecast", "CashPositionSnapshot", "GatewaySettlementSchedule",
    "PendingJournalEntry", "PayoutBatch", "PayoutBatchItem",
    "BankStatementImport", "BankStatementLine", "BankMappingRule", "FixedAsset",
    "Accrual", "ScannedExpense", "FinanceAutomationLog",
    "CashAccount", "CashTransaction",
    "PhysicalIDCard", "DynamicQRSession", "EmployeeBiometric",
    "GeoFenceLog", "EmployeeRole", "Employee", "EmployeeAttendance",
    "EmployeeWorkLog", "EmployeeLeaveRequest", "EmployeeLeaveLedger", "EmployeeShiftRoster",
    "EmployeeAddress", "EmployeeDependent", "EmployeeAsset",
    "EmployeeCertification", "EmployeeDocument", "EmployeeRelation",
    "COIReport", "TravelRequest", "AlumniNetwork",
    "MediaAsset", "MediaUploadSession",
    "SystemHealthEvent", "UserSession", "CommandCenterView",
    "AuditMixin", "SoftDeleteMixin",
    "NewsSource", "NewsArticle", "InternalNotice", "PredictiveSimulation", "AlertEscalationRule",
    "EntityChatThread", "EntityChatMessage",
    "CountryConfigVersion", "FraudAlert", "IPAccountLinkage",
    "MeetingTranscript", "MeetingActionItem", "MeetingRecording", "VelocityCounter",
    "FraudScoringLog", "FraudCase", "FraudCaseAssignment",
    "DLPViolation",
    "EmployeeCommunicationThread", "ExternalContactMasking", "InternalChannel", "InternalChannelMember", "InternalMessage", "CommunicationAuditTrail",
    "OnboardingPipeline", "OnboardingStep", "DocumentVerification", "OCRResult", "KYCVerification",
    "IncidentWarRoom", "IncidentThread", "IncidentActionItem", "WarRoomTemplate",
    "RetentionJobRun",
    "CountryHolidayCalendar", "CountryLegalContract", "CountryLocalization", "CountryPaymentAlias",
    "DirectChatMessage", "DirectChatRoom",
    "DisciplinaryCase", "EmployeeExpense",
    "EscalationSLARule", "EscalationSLALog",
    "GroupChatMember", "GroupChatMessage", "GroupChatRoom",
    "OffboardingCase",
    "ShiftHandoverSession", "ShiftHandoverTask",
    "VideoRoom", "VideoRoomParticipant", "VideoRoomRecording",
    "PermissionCategory", "Permission", "RolePermissionAssignment", "UserPermissionOverride", "PermissionAuditLog",
    "AIUploadJob", "AIStagingProduct", "AIStagingVariant", "AIGenerationLog", "AIStagingImage", "AIAuditLog", "AIEmbedding", "AIRequest", "AIResult",
    "CountryBasics", "CountryEconomics", "CountryLegal", "CountryTax",
    "ChatAttachment", "InternalEmail", "EmailFolder",
    "OutboxEvent", "InboxEvent", "EventRetryQueue", "EventDeadLetter",
    "DailySalesSnapshot", "MonthlySalesSnapshot", "KPICustomer", "KPISupplier", "KPICountry", "KPIRevenue", "KPIOrders", "KPIRetention", "KPIConversion", "CashPositionSnapshotMV", "FacetCountsSnapshot",
    "UploadJob",
    "FeatureFlag", "WormAudit",
]


def _apply_legacy_import_shims() -> None:
    """Transitional compat for pre-domain reorganisation model imports.

    The models/ package was split into domain sub-packages, but many call
    sites still import via legacy flat paths (``from models.employee_models
    import Employee``) or legacy package paths (``from data.models_core import
    AuditLog``) that never existed after the reorg.  This registers
    ``models.<leaf>`` aliases for the real ``models.<domain>.<leaf>`` modules
    and copies each submodule's public names onto its domain package so
    those imports resolve.  Canonical style remains ``from data.models import X``
    or ``models/<domain>/<module>.py``.
    """
    import sys as _sys
    _ns = __name__
    _leaf_aliases = {
        "employee_models": "hr.employee_models",
        "user": "core.user",
        "products": "catalog.products",
        "fraud": "security.fraud",
        "countries": "country.countries",
        "country_tax": "country.country_tax",
        "country_enhancements": "country.country_enhancements",
        "country_control": "logistics.country_control",
        "payments": "finance.payments",
        "upload_job": "media.upload_job",
        "media_models": "media.media_models",
        "admin": "logistics.admin",
    }
    for _flat, _dotted in _leaf_aliases.items():
        _real = _sys.modules.get(f"{_ns}.{_dotted}")
        if _real is None:
            continue
        _sys.modules[f"{_ns}.{_flat}"] = _real
        globals()[_flat] = _real
    _pkg_subs = (
        ("core", ("user",)),
        ("catalog", ("products", "ai_upload")),
        ("orders", ("orders",)),
        ("finance", ("payments", "commission")),
        ("security", ("permissions", "incident", "fraud")),
        ("logistics", ("logistics", "admin", "imports", "country_control")),
        ("communication", ("suppliers", "core", "marketing", "communication")),
        ("country", ("countries", "country_basics", "country_economics", "country_enhancements", "country_legal", "country_tax")),
        ("media", ("upload_job", "media_models")),
        ("hr", ("employee_models",)),
        ("treasury", ("finance",)),
        ("supplier", ("onboarding",)),
        ("analytics", ("analytics",)),
         ("audit", ("platform",)),
     )
    for _pkg, _subs in _pkg_subs:
        _pkgmod = _sys.modules.get(f"{_ns}.{_pkg}")
        if _pkgmod is None:
            continue
        for _sub in _subs:
            _submod = _sys.modules.get(f"{_ns}.{_pkg}.{_sub}")
            if _submod is None:
                continue
            _exported = getattr(_submod, "__all__", None)
            if _exported is None:
                _exported = [n for n in dir(_submod) if not n.startswith("_")]
            for _n in _exported:
                setattr(_pkgmod, _n, getattr(_submod, _n))
    _cross_exports = (
        ("core", ("communication.core",)),
    )
    for _dest_pkg, _src_pkgs in _cross_exports:
        _pkgmod = _sys.modules.get(f"{_ns}.{_dest_pkg}")
        if _pkgmod is None:
            continue
        for _src in _src_pkgs:
            _submod = _sys.modules.get(f"{_ns}.{_src}")
            if _submod is None:
                continue
            _exported = getattr(_submod, "__all__", None)
            if _exported is None:
                _exported = [n for n in dir(_submod) if not n.startswith("_")]
            for _n in _exported:
                setattr(_pkgmod, _n, getattr(_submod, _n))


_apply_legacy_import_shims()
