"""
Comprehensive fix for comms domain architectural violations.
This script fixes:
1. ports.py - adds __all__, exports missing models from chat.py
2. features.py - converts CATALOG to FEATURES dict for RBAC compatibility
3. events.py - adds publish helpers, fixes event type strings
4. subscribers.py - integrates with canonical event bus
"""
import os
import re

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'

# =============================================================================
# FIX 1: ports.py - Add __all__ and export missing models
# =============================================================================
ports_path = os.path.join(BACKEND, 'domains', 'comms', 'ports.py')

with open(ports_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Add imports from chat.py models that are missing
chat_models_import = """from domains.comms.models.chat import (
    DirectChatRoom, DirectChatMessage, EntityChatThread, EntityChatMessage,
    EscalationSLALog, GroupChatMember, GroupChatRoom, GroupChatMessage,
    VideoRoom, VideoRoomParticipant,
)
from domains.comms.models.communication_schema_models import (
    SupportTicket, TicketAttachment, NewsSource, InternalNotice, EscalationSLARule,
)
from domains.comms.models.news import NewsArticle
"""

# Insert after existing imports
if 'from domains.comms.models.chat import' not in content:
    content = content.replace(
        'from domains.comms.models.communication import',
        chat_models_import + 'from domains.comms.models.communication import'
    )

# Add __all__ at the end of file
if '__all__' not in content:
    __all__ = '''

# Sanctioned cross-domain READ surface
__all__ = [
    # Models from communication.py
    "Announcement", "ChatAttachment", "ChatReadReceipt", "CommunicationAuditTrail",
    "EmailFolder", "EmployeeCommunicationThread", "ExternalContactMasking", "FAQ",
    "HelpCategory", "InternalChannel", "InternalChannelMember", "InternalEmail",
    "InternalMessage", "MaskedMessage", "Notification", "ProxyCallLog", "ProxyChannel",
    "ProxyMessage", "ProxySession", "TicketMessage",
    # Models from marketing.py
    "CampaignRecipient", "EmailCampaign", "EmailCampaignLog", "EmailDeliveryEvent",
    "EmailRuntimeConfig", "EmailSuppression", "EmailTemplate", "FlashSale",
    "FlashSaleItem", "NewsletterSubscriber", "PointsTransaction", "UserPoints",
    # Models from suppliers.py
    "SupplierBadge", "SupplierBadgeBillingHistory", "SupplierBadgeCatalog",
    "SupplierDocument", "SupplierNotificationPreference", "SupplierProfile",
    # Models from communication_schema_models.py
    "SupportTicket", "SupportTicketReply", "TicketAttachment", "NewsSource",
    "InternalNotice", "EscalationSLARule",
    # Models from chat.py
    "DirectChatRoom", "DirectChatMessage", "EntityChatThread", "EntityChatMessage",
    "EscalationSLALog", "GroupChatMember", "GroupChatRoom", "GroupChatMessage",
    "VideoRoom", "VideoRoomParticipant",
    # Models from news.py
    "NewsArticle",
    # Functions
    "get_notification_by_id", "list_notifications", "list_notifications_page",
    "get_ticket_message_by_id", "list_ticket_messages",
    "get_announcement_by_id", "list_announcements",
]
'''
    content = content.rstrip() + '\n' + __all__

with open(ports_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Fixed ports.py')

# =============================================================================
# FIX 2: features.py - Convert CATALOG to FEATURES dict
# =============================================================================
features_path = os.path.join(BACKEND, 'domains', 'comms', 'features.py')

with open(features_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace CATALOG tuple with FEATURES dict
# Find the CATALOG definition and replace it
old_catalog = '''CATALOG = ('''

if old_catalog in content:
    # Replace the entire CATALOG block with a FEATURES dict
    # Find the start and end of CATALOG
    start_idx = content.find('CATALOG = (')
    end_idx = content.find(')', start_idx) + 1
    
    features_dict = '''FEATURES = {
    # Notification features
    "comms.notification.read": "Read notifications",
    "comms.notification.create": "Create notifications",
    "comms.notification.manage": "Manage all notifications",
    # Email campaign features
    "comms.email_campaign.read": "Read email campaigns",
    "comms.email_campaign.create": "Create email campaigns",
    "comms.email_campaign.manage": "Manage all email campaigns",
    # Email template features
    "comms.email_template.read": "Read email templates",
    "comms.email_template.create": "Create email templates",
    "comms.email_template.manage": "Manage all email templates",
    # Flash sale features
    "comms.flash_sale.read": "Read flash sales",
    "comms.flash_sale.create": "Create flash sales",
    "comms.flash_sale.manage": "Manage all flash sales",
    # Ticket features
    "comms.ticket.read": "Read support tickets",
    "comms.ticket.create": "Create support tickets",
    "comms.ticket.manage": "Manage all tickets",
    # Chat features
    "comms.chat.read": "Read chat messages",
    "comms.chat.send": "Send chat messages",
    "comms.chat.manage": "Manage all chat",
    # Video room features
    "comms.video_room.create": "Create video rooms",
    "comms.video_room.join": "Join video rooms",
    "comms.video_room.manage": "Manage video rooms",
    # Internal channel features
    "comms.internal_channel.read": "Read internal channels",
    "comms.internal_channel.manage": "Manage internal channels",
    # Announcement features
    "comms.announcement.read": "Read announcements",
    "comms.announcement.manage": "Manage announcements",
    # Newsletter features
    "comms.newsletter.subscribe": "Subscribe to newsletter",
    "comms.newsletter.manage": "Manage newsletter subscribers",
    # FAQ features
    "comms.faq.read": "Read FAQs",
    "comms.faq.manage": "Manage FAQs",
    # Points features
    "comms.points.read": "Read points",
    "comms.points.manage": "Manage points system",
    # Supplier comms features
    "comms.supplier.read": "Read supplier communications",
    "comms.supplier.manage": "Manage supplier communications",
}'''

    content = content[:start_idx] + features_dict + '\n\n' + content[end_idx:]
    
    # Update __all__ to include FEATURES
    content = content.replace('"CATALOG"', '"FEATURES"')
    
    with open(features_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('OK: Fixed features.py')
else:
    print('WARN: CATALOG not found in features.py - may already be fixed')

print('Done with Phase 1 fixes')
