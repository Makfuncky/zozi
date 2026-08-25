"""Audit domain Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class AuditLogCreate(BaseModel):
    """Schema for creating an audit log entry."""
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log response."""
    id: int
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    user_id: Optional[int] = None
    username: Optional[str] = None
    user_role: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
