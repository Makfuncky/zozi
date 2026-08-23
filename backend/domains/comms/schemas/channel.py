"""Channel request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class ChannelCreate(BaseModel):
    """Request DTO for creating an internal channel."""
    name: str
    channel_type: str = "public"


class ChannelResponse(BaseModel):
    """Response DTO for an internal channel."""
    id: int
    name: str
    channel_type: str
    member_count: int = 0


class ChannelMemberAdd(BaseModel):
    """Request DTO for adding a member to a channel."""
    channel_id: int
    user_id: int
