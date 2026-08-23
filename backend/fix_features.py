"""
Fix features.py - convert CATALOG to FEATURES dict for RBAC compatibility.
"""
import os

features_path = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\comms\features.py'

with open(features_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace CATALOG tuple with FEATURES dict
old_catalog = '''# ── catalog (exported for rbac/catalog.py scan) ────────────────────────────

CATALOG: tuple[CommsFeature, ...] = (
    NOTIFICATION_READ,
    NOTIFICATION_MANAGE,
    NOTIFICATION_PUSH_REGISTER,
    TICKET_CREATE,
    TICKET_READ,
    TICKET_MANAGE,
    TICKET_ESCALATE,
    CHAT_SEND,
    CHAT_READ,
    CHAT_MODERATE,
    INTERNAL_CHANNEL_MANAGE,
    CAMPAIGN_CREATE,
    CAMPAIGN_SEND,
    CAMPAIGN_READ,
    TEMPLATE_MANAGE,
    NEWSLETTER_MANAGE,
    PROXY_COMMUNICATION_USE,
    PROXY_CALL,
    VIDEO_ROOM_CREATE,
    VIDEO_ROOM_JOIN,
    VIDEO_ROOM_MANAGE,
    ANNOUNCEMENT_CREATE,
    ANNOUNCEMENT_READ,
    FAQ_MANAGE,
    SLA_MANAGE,
)'''

new_features = '''# ── features catalog (exported for rbac/catalog.py scan) ───────────────────
# rbac/catalog.py aggregates via: FEATURE_CATALOG.update(getattr(feat, "FEATURES", {}))

FEATURES = {
    # Notification features
    "comms.notification.read": "Read own notifications",
    "comms.notification.manage": "Create, update, dispatch notifications (admin)",
    "comms.notification.push.register": "Register push notification tokens",
    # Ticket features
    "comms.ticket.create": "Create support tickets",
    "comms.ticket.read": "Read support tickets",
    "comms.ticket.manage": "Manage all tickets",
    "comms.ticket.escalate": "Escalate tickets",
    # Chat features
    "comms.chat.send": "Send chat messages",
    "comms.chat.read": "Read chat messages",
    "comms.chat.moderate": "Moderate chat",
    # Internal channel features
    "comms.internal_channel.manage": "Manage internal channels",
    # Campaign features
    "comms.campaign.create": "Create email campaigns",
    "comms.campaign.send": "Send email campaigns",
    "comms.campaign.read": "Read email campaigns",
    # Template features
    "comms.template.manage": "Manage email templates",
    # Newsletter features
    "comms.newsletter.manage": "Manage newsletter subscribers",
    # Proxy communication features
    "comms.proxy.communication.use": "Use proxy communications",
    "comms.proxy.call": "Make proxy calls",
    # Video room features
    "comms.video_room.create": "Create video rooms",
    "comms.video_room.join": "Join video rooms",
    "comms.video_room.manage": "Manage video rooms",
    # Announcement features
    "comms.announcement.create": "Create announcements",
    "comms.announcement.read": "Read announcements",
    # FAQ features
    "comms.faq.manage": "Manage FAQs",
    # SLA features
    "comms.sla.manage": "Configure escalation SLA rules",
}'''

if old_catalog in content:
    content = content.replace(old_catalog, new_features)
    
    # Update __all__ to include FEATURES instead of CATALOG
    content = content.replace('"CATALOG"', '"FEATURES"')
    
    with open(features_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('OK: Fixed features.py - CATALOG -> FEATURES dict')
else:
    print('WARN: CATALOG pattern not found - checking if already fixed')
    if 'FEATURES' in content:
        print('Already has FEATURES dict')
    else:
        print('ERROR: Could not find CATALOG or FEATURES')
