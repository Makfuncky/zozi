"""comms domain — permission atoms (AXIS 3 seed).

Feature atoms are defined **once** per domain in ``features.py`` and
aggregated by ``rbac/catalog.py`` (Law 4). Every atom used in a
``require_feature("comms.…")`` call across ``modules/*/routers`` must be
declared here.

The comms domain covers: notifications, tickets, chat/messaging, email
marketing campaigns, proxy communications, video conferencing, internal
channels, announcements, and escalation/SLA management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class CommsFeature:
    """A single permission atom within the comms domain."""

    atom: str
    description: str
    default_roles: FrozenSet[str] = frozenset()


# ── notification features ─────────────────────────────────────────────────

NOTIFICATION_READ = CommsFeature(
    atom="comms.notification.read",
    description="Read own notifications",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

NOTIFICATION_MANAGE = CommsFeature(
    atom="comms.notification.manage",
    description="Create, update, dispatch notifications (admin)",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

NOTIFICATION_PUSH_REGISTER = CommsFeature(
    atom="comms.notification.push_register",
    description="Register/unregister push notification tokens",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

# ── ticket features ────────────────────────────────────────────────────────

TICKET_CREATE = CommsFeature(
    atom="comms.ticket.create",
    description="Create support tickets",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

TICKET_READ = CommsFeature(
    atom="comms.ticket.read",
    description="Read support tickets",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

TICKET_MANAGE = CommsFeature(
    atom="comms.ticket.manage",
    description="Reply to, update status, and manage tickets (staff)",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

TICKET_ESCALATE = CommsFeature(
    atom="comms.ticket.escalate",
    description="Escalate tickets and manage SLA rules",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

# ── chat / messaging features ──────────────────────────────────────────────

CHAT_SEND = CommsFeature(
    atom="comms.chat.send",
    description="Send chat messages (direct/group/internal)",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

CHAT_READ = CommsFeature(
    atom="comms.chat.read",
    description="Read chat messages",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

CHAT_MODERATE = CommsFeature(
    atom="comms.chat.moderate",
    description="Moderate chat (delete messages, apply legal hold)",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

INTERNAL_CHANNEL_MANAGE = CommsFeature(
    atom="comms.internal_channel.manage",
    description="Create and manage internal communication channels",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

# ── email marketing features ───────────────────────────────────────────────

CAMPAIGN_CREATE = CommsFeature(
    atom="comms.campaign.create",
    description="Create email marketing campaigns",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

CAMPAIGN_SEND = CommsFeature(
    atom="comms.campaign.send",
    description="Send email campaigns to subscribers",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

CAMPAIGN_READ = CommsFeature(
    atom="comms.campaign.read",
    description="Read campaign metrics and logs",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

TEMPLATE_MANAGE = CommsFeature(
    atom="comms.template.manage",
    description="Manage email templates",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

NEWSLETTER_MANAGE = CommsFeature(
    atom="comms.newsletter.manage",
    description="Manage newsletter subscribers",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

# ── proxy communication features ──────────────────────────────────────────

PROXY_COMMUNICATION_USE = CommsFeature(
    atom="comms.proxy.use",
    description="Use proxy phone/email for anonymized communication",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

PROXY_CALL = CommsFeature(
    atom="comms.proxy.call",
    description="Initiate proxy voice calls",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

# ── video conferencing features ────────────────────────────────────────────

VIDEO_ROOM_CREATE = CommsFeature(
    atom="comms.video.create",
    description="Create video conference rooms",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

VIDEO_ROOM_JOIN = CommsFeature(
    atom="comms.video.join",
    description="Join video conference rooms",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

VIDEO_ROOM_MANAGE = CommsFeature(
    atom="comms.video.manage",
    description="Manage video rooms (recordings, participants)",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

# ── announcement features ──────────────────────────────────────────────────

ANNOUNCEMENT_CREATE = CommsFeature(
    atom="comms.announcement.create",
    description="Create platform announcements",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

ANNOUNCEMENT_READ = CommsFeature(
    atom="comms.announcement.read",
    description="Read active announcements",
    default_roles=frozenset({"customer", "supplier", "employee", "admin", "super_admin"}),
)

# ── FAQ / help-center features ────────────────────────────────────────────

FAQ_MANAGE = CommsFeature(
    atom="comms.faq.manage",
    description="Manage FAQ entries and help categories",
    default_roles=frozenset({"employee", "admin", "super_admin"}),
)

# ── escalation / SLA features ──────────────────────────────────────────────

SLA_MANAGE = CommsFeature(
    atom="comms.sla.manage",
    description="Configure escalation SLA rules",
    default_roles=frozenset({"admin", "super_admin"}),
)

# ── features catalog (exported for rbac/catalog.py scan) ───────────────────
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
    # Broadcast features
    "comms.broadcast": "Send broadcast messages and notifications to user segments",
}

__all__ = [
    "CommsFeature",
    "FEATURES",
    "NOTIFICATION_READ",
    "NOTIFICATION_MANAGE",
    "NOTIFICATION_PUSH_REGISTER",
    "TICKET_CREATE",
    "TICKET_READ",
    "TICKET_MANAGE",
    "TICKET_ESCALATE",
    "CHAT_SEND",
    "CHAT_READ",
    "CHAT_MODERATE",
    "INTERNAL_CHANNEL_MANAGE",
    "CAMPAIGN_CREATE",
    "CAMPAIGN_SEND",
    "CAMPAIGN_READ",
    "TEMPLATE_MANAGE",
    "NEWSLETTER_MANAGE",
    "PROXY_COMMUNICATION_USE",
    "PROXY_CALL",
    "VIDEO_ROOM_CREATE",
    "VIDEO_ROOM_JOIN",
    "VIDEO_ROOM_MANAGE",
    "ANNOUNCEMENT_CREATE",
    "ANNOUNCEMENT_READ",
    "FAQ_MANAGE",
    "SLA_MANAGE",
]
