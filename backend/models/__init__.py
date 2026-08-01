from __future__ import annotations

import os

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


class _GuardedMetaData(MetaData):
    """MetaData that forbids ``create_all`` / ``drop_all`` outside dev/test.

    Implements Constitution §2.7 / ADR-012: ``Base.metadata.create_all()`` is
    for development and test only.  Production schema changes MUST go through
    reviewed Alembic migrations.

    The guard passes through when:
      * ``ALEMBIC_MODE=true`` (sanctioned migration context), **or**
      * the target bind is SQLite (dev / in-memory test), **or**
      * ``APP_ENV`` is not ``production``.

    Every other combination raises ``RuntimeError`` so there is no code path
    that can accidentally ``create_all`` against a PostgreSQL production
    database.
    """

    def _guard(self, operation: str, bind) -> None:
        if os.getenv("ALEMBIC_MODE") == "true":
            return
        env = os.getenv("APP_ENV", "development").lower()
        if env == "production":
            raise RuntimeError(
                f"{operation} is forbidden in production (APP_ENV=production). "
                f"Use a reviewed Alembic migration instead of Base.metadata."
                f"{operation}."
            )
        if bind is not None and bind.dialect.name == "postgresql":
            raise RuntimeError(
                f"{operation} is disabled on PostgreSQL. "
                f"Use a reviewed Alembic migration instead of Base.metadata."
                f"{operation}."
            )

    def create_all(self, *args, **kwargs):
        bind = kwargs.get("bind")
        if bind is None and args:
            bind = args[0]
        self._guard("create_all", bind)
        return super().create_all(*args, **kwargs)

    def drop_all(self, *args, **kwargs):
        bind = kwargs.get("bind")
        if bind is None and args:
            bind = args[0]
        self._guard("drop_all", bind)
        return super().drop_all(*args, **kwargs)


class Base(DeclarativeBase):
    metadata = _GuardedMetaData()

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
from .country.country_basics import *
from .country.country_economics import *
from .country.country_legal import *
from .country_tax import *
from .events import *
from .analytics.analytics import *
from .media.upload_job import *
from .audit.platform import *

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
    "AIUploadJob", "AIStagingProduct", "AIStagingVariant", "AIGenerationLog",
    "CountryBasics", "CountryEconomics", "CountryLegal", "CountryTax",
    "ChatAttachment", "InternalEmail", "EmailFolder",
    "OutboxEvent", "InboxEvent", "EventRetryQueue", "EventDeadLetter",
    "DailySalesSnapshot", "MonthlySalesSnapshot", "KPICustomer", "KPISupplier", "KPICountry", "KPIRevenue", "KPIOrders", "KPIRetention", "KPIConversion", "CashPositionSnapshotMV", "FacetCountsSnapshot",
    "UploadJob",
    "FeatureFlag", "WormAudit",
]
