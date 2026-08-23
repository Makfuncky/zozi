"""Email request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class EmailSend(BaseModel):
    """Request DTO for sending an email."""
    to: str
    subject: str
    html: str
    from_address: Optional[str] = None
    purpose: str = "default"


class EmailCampaignCreate(BaseModel):
    """Request DTO for creating an email campaign."""
    name: str
    subject: str
    html_content: str
    recipient_list: str = "all"


class EmailCampaignResponse(BaseModel):
    """Response DTO for an email campaign."""
    id: int
    name: str
    subject: str
    status: str
    created_at: str


class EmailTemplateCreate(BaseModel):
    """Request DTO for creating an email template."""
    name: str
    subject: str
    html_content: str


class EmailTemplateResponse(BaseModel):
    """Response DTO for an email template."""
    id: int
    name: str
    subject: str
    is_active: bool


class EmailSuppressionUpdate(BaseModel):
    """Request DTO for updating email suppression."""
    email: str
    action: str = "suppress"
