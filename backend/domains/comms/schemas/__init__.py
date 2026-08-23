"""comms domain — request/response DTOs."""
from .channel import (
    ChannelCreate,
    ChannelMemberAdd,
    ChannelResponse,
)
from .chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatReactionAdd,
    ChatThreadCreate,
    ChatTypingIndicator,
)
from .email import (
    EmailCampaignCreate,
    EmailCampaignResponse,
    EmailSend,
    EmailSuppressionUpdate,
    EmailTemplateCreate,
    EmailTemplateResponse,
)
from .notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    PushTokenRegister,
    PushTokenUnregister,
)
from .ticket import (
    TicketCreate,
    TicketReply,
    TicketResponse,
    TicketUpdate,
)

__all__ = [
    "ChannelCreate",
    "ChannelMemberAdd",
    "ChannelResponse",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "ChatReactionAdd",
    "ChatThreadCreate",
    "ChatTypingIndicator",
    "EmailCampaignCreate",
    "EmailCampaignResponse",
    "EmailSend",
    "EmailSuppressionUpdate",
    "EmailTemplateCreate",
    "EmailTemplateResponse",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationUpdate",
    "PushTokenRegister",
    "PushTokenUnregister",
    "TicketCreate",
    "TicketReply",
    "TicketResponse",
    "TicketUpdate",
]
