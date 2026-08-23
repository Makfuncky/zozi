"""Chat request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ChatMessageCreate(BaseModel):
    """Request DTO for creating a chat message."""
    thread_id: int
    content: str
    message_type: str = "text"


class ChatMessageResponse(BaseModel):
    """Response DTO for a chat message."""
    id: int
    thread_id: int
    sender_id: int
    content: str
    message_type: str
    created_at: str


class ChatThreadCreate(BaseModel):
    """Request DTO for creating a chat thread."""
    entity_type: str
    entity_id: int
    title: Optional[str] = None
    participants: list[int] = []


class ChatReactionAdd(BaseModel):
    """Request DTO for adding a reaction to a message."""
    message_id: int
    reaction: str


class ChatTypingIndicator(BaseModel):
    """Request DTO for sending a typing indicator."""
    thread_id: int
    is_typing: bool = True
