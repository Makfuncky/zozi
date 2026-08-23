from __future__ import annotations

# Canonical home for customer-schema tables that do not live in any other
# domain's models. The following tables were relocated OUT of this file to
# their owning domains; they are re-exported below so legacy imports resolve:
#   - NewsArticle, EntityChatThread, VideoRoom, VideoRoomParticipant,
#     DirectChatRoom, GroupChatMember, EscalationSLALog -> domains.comms.models
#   - ShiftHandoverSession -> domains.hr.models
#   - Address, Cart, CartItem, SystemHealthEvent, UserSession -> domains.governance.models.core (legacy home)
#   - Referral, ReferralPointEvent -> domains.governance.models.user (legacy home)

__all__ = [
    # re-exports (relocated to owning domains / legacy homes)
    "SystemHealthEvent",
    "UserSession",
    "NewsArticle",
    "EntityChatThread",
    "VideoRoom",
    "VideoRoomParticipant",
    "DirectChatRoom",
    "GroupChatMember",
    "ShiftHandoverSession",
    "EscalationSLALog",
]


# ---------------------------------------------------------------------------
# Relocated models: canonical definitions now live in their owning domains.
# These re-exports keep legacy imports resolving until every caller is migrated.
# ---------------------------------------------------------------------------

from domains.governance.models.core import (  # noqa: F401
    SystemHealthEvent as SystemHealthEvent,
    UserSession as UserSession,
)
from domains.comms.models.chat import (  # noqa: F401
    DirectChatRoom as DirectChatRoom,
    EntityChatThread as EntityChatThread,
    EscalationSLALog as EscalationSLALog,
    GroupChatMember as GroupChatMember,
    VideoRoom as VideoRoom,
    VideoRoomParticipant as VideoRoomParticipant,
)
from domains.comms.models.news import NewsArticle as NewsArticle  # noqa: F401,F811
from domains.hr.models.employee_models import ShiftHandoverSession as ShiftHandoverSession  # noqa: F401,F811
