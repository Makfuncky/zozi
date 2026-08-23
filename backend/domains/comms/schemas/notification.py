"""Notification request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class NotificationCreate(BaseModel):
    """Request DTO for creating a notification."""
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
    """Response DTO for a notification."""
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
    """Request DTO for updating a notification."""
    is_read: Optional[bool] = None
    read_at: Optional[str] = None


class PushTokenRegister(BaseModel):
    """Request DTO for registering a push token."""
    token: str
    platform: str = "android"


class PushTokenUnregister(BaseModel):
    """Request DTO for unregistering a push token."""
    token: str
