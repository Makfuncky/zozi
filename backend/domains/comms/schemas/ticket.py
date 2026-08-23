"""Ticket request/response DTOs."""
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class TicketCreate(BaseModel):
    """Request DTO for creating a support ticket."""
    subject: str
    message: str
    priority: str = "medium"


class TicketResponse(BaseModel):
    """Response DTO for a support ticket."""
    id: int
    user_id: int
    subject: str
    priority: str
    status: str
    created_at: str


class TicketUpdate(BaseModel):
    """Request DTO for updating a ticket."""
    status: Optional[str] = None
    priority: Optional[str] = None


class TicketReply(BaseModel):
    """Request DTO for replying to a ticket."""
    ticket_id: int
    message: str
