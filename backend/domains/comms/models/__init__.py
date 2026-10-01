"""comms domain - models package.

Re-exports all comms-domain models for convenient importing.
"""
from infrastructure.database.base import Base  # noqa: F401

from domains.comms.models.chat import (  # noqa: F401
    DirectChatRoom,
    DirectChatMessage,
    EntityChatThread,
    EntityChatMessage,
    EscalationSLALog,
    GroupChatMember,
    GroupChatRoom,
    GroupChatMessage,
    VideoRoom,
    VideoRoomParticipant,
)
from domains.comms.models.communication import (  # noqa: F401
    Notification,
    Announcement,
    FAQ,
    HelpCategory,
    TicketMessage,
    ProxyChannel,
    ProxySession,
    ProxyMessage,
    ProxyCallLog,
    EmployeeCommunicationThread,
    ExternalContactMasking,
    CommunicationAuditTrail,
    InternalChannel,
    InternalChannelMember,
    InternalMessage,
    InternalEmail,
    EmailFolder,
    MaskedMessage,
)
from domains.comms.models.marketing import (  # noqa: F401
    FlashSaleItem,
    EmailCampaign,
    EmailTemplate,
    NewsletterSubscriber,
    EmailCampaignLog,
    CampaignRecipient,
    EmailDeliveryEvent,
    EmailSuppression,
    EmailRuntimeConfig,
)
from domains.comms.models.news import NewsArticle  # noqa: F401
from domains.comms.models.communication_schema_models import (  # noqa: F401
    SupportTicket,
    SupportTicketReply,
    TicketAttachment,
    NewsSource,
    InternalNotice,
    EscalationSLARule,
)
from domains.comms.models.suppliers import (  # noqa: F401
    SupplierBadge,
    SupplierBadgeBillingHistory,
    SupplierBadgeCatalog,
    SupplierDocument,
    SupplierNotificationPreference,
    SupplierProfile,
)

__all__ = [
    "Base",
    # chat
    "DirectChatRoom",
    "DirectChatMessage",
    "EntityChatThread",
    "EntityChatMessage",
    "EscalationSLALog",
    "GroupChatMember",
    "GroupChatRoom",
    "GroupChatMessage",
    "VideoRoom",
    "VideoRoomParticipant",
    # communication
    "Notification",
    "Announcement",
    "FAQ",
    "HelpCategory",
    "TicketMessage",
    "ProxyChannel",
    "ProxySession",
    "ProxyMessage",
    "ProxyCallLog",
    "EmployeeCommunicationThread",
    "ExternalContactMasking",
    "CommunicationAuditTrail",
    "InternalChannel",
    "InternalChannelMember",
    "InternalMessage",
    "InternalEmail",
    "EmailFolder",
    "MaskedMessage",
    # marketing
    "FlashSaleItem",
    "EmailCampaign",
    "EmailTemplate",
    "NewsletterSubscriber",
    "EmailCampaignLog",
    "CampaignRecipient",
    "EmailDeliveryEvent",
    "EmailSuppression",
    "EmailRuntimeConfig",
    # news
    "NewsArticle",
    # schema models
    "SupportTicket",
    "SupportTicketReply",
    "TicketAttachment",
    "NewsSource",
    "InternalNotice",
    "EscalationSLARule",
    # suppliers
    "SupplierBadge",
    "SupplierBadgeBillingHistory",
    "SupplierBadgeCatalog",
    "SupplierDocument",
    "SupplierNotificationPreference",
    "SupplierProfile",
]
