"""comms domain — request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Channel DTOs (from channel.py) ───

class ChannelCreate(BaseModel):
    name: str
    channel_type: str = "public"


class ChannelResponse(BaseModel):
    id: int
    name: str
    channel_type: str
    member_count: int = 0


class ChannelMemberAdd(BaseModel):
    channel_id: int
    user_id: int


# ── Chat DTOs (from chat.py) ───

class ChatMessageCreate(BaseModel):
    thread_id: int
    content: str
    message_type: str = "text"


class ChatMessageResponse(BaseModel):
    id: int
    thread_id: int
    sender_id: int
    content: str
    message_type: str
    created_at: str


class ChatThreadCreate(BaseModel):
    entity_type: str
    entity_id: int
    title: Optional[str] = None
    participants: list[int] = []


class ChatReactionAdd(BaseModel):
    message_id: int
    reaction: str


class ChatTypingIndicator(BaseModel):
    thread_id: int
    is_typing: bool = True


# ── Email DTOs (from email.py) ───

class EmailSend(BaseModel):
    to: str
    subject: str
    html: str
    from_address: Optional[str] = None
    purpose: str = "default"


class EmailCampaignCreate(BaseModel):
    name: str
    subject: str
    html_content: str
    recipient_list: str = "all"


class EmailCampaignResponse(BaseModel):
    id: int
    name: str
    subject: str
    status: str
    created_at: str


class EmailTemplateCreate(BaseModel):
    name: str
    subject: str
    html_content: str


class EmailTemplateResponse(BaseModel):
    id: int
    name: str
    subject: str
    is_active: bool


class EmailSuppressionUpdate(BaseModel):
    email: str
    action: str = "suppress"


# ── Notification DTOs (from notification.py) ───

class NotificationCreate(BaseModel):
    user_id: int
    type: Optional[str] = None
    title: str
    message: str
    channel: str = "in_app"
    priority: str = "medium"
    link: Optional[str] = None
    template: Optional[str] = None
    scheduled_at: Optional[str] = None


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: Optional[str]
    title: str
    message: str
    channel: str
    priority: str
    is_read: bool
    created_at: str
    read_at: Optional[str] = None


class NotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[str] = None


class PushTokenRegister(BaseModel):
    token: str
    platform: str = "android"


class PushTokenUnregister(BaseModel):
    token: str


# ── Ticket DTOs (from ticket.py) ───

class TicketCreate(BaseModel):
    subject: str
    message: str
    priority: str = "medium"


class TicketResponse(BaseModel):
    id: int
    user_id: int
    subject: str
    priority: str
    status: str
    created_at: str


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None


class TicketReply(BaseModel):
    ticket_id: int
    message: str


__all__ = [
    "ChannelCreate", "ChannelMemberAdd", "ChannelResponse",
    "ChatMessageCreate", "ChatMessageResponse", "ChatReactionAdd",
    "ChatThreadCreate", "ChatTypingIndicator",
    "EmailCampaignCreate", "EmailCampaignResponse", "EmailSend",
    "EmailSuppressionUpdate", "EmailTemplateCreate", "EmailTemplateResponse",
    "NotificationCreate", "NotificationResponse", "NotificationUpdate",
    "PushTokenRegister", "PushTokenUnregister",
    "TicketCreate", "TicketReply", "TicketResponse", "TicketUpdate",
]
