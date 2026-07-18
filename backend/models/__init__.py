from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

from .user import *
from .products import *
from .orders import *
from .payments import *
from .suppliers import *
from .logistics import *
from .marketing import *
from .communication import *
from .countries import *
from .finance import *
from .commission import *
from .admin import *
from .fraud import *
from .core import *
from .country_enhancements import *
from .country_control import *
from .employee_models import *
from .media_models import *
from .mixins import *
from .onboarding import *
from .incident import *
from .permissions import *
from .ai_upload import *

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
    "Category", "Product", "ProductVariant", "ProductVideo", "VideoAnalytics",
    "Order", "OrderItem", "OrderLogisticsAllocation",
    "ReturnRequest",
    "Payment", "Coupon", "Banner", "PaymentGatewayConnection", "Payout", "LogisticsPartnerPayout", "PaymentReconciliationRun",
    "SupplierProfile", "SupplierDocument", "SupplierNotificationPreference", "LogisticsPartnerProfile", "SupplierDispute", "SupplierCountryCommission",
    "LogisticsPartner", "LogisticsPartnerServiceArea", "LogisticsPricingProfile",
    "LogisticsVehicleRule", "LogisticsCategoryPricingRule", "Shipment", "ShipmentEvent",
    "FlashSale", "FlashSaleItem", "EmailCampaign", "EmailTemplate", "NewsletterSubscriber", "EmailCampaignLog",
    "Notification", "Announcement", "FAQ", "HelpCategory", "TicketMessage",
    "ProxyChannel", "ProxySession", "ProxyMessage", "ProxyCallLog",
    "TransactionLedger", "SupplierSettlement", "JournalEntry", "JournalEntryLine", "Account", "AccountGroup", "AccountBalance", "FinancialReport",
    "Invoice", "InvoiceItem", "RefundLedger", "BankTransaction", "VATRemittance",
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
]
