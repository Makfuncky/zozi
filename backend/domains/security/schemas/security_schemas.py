"""Security domain Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class DocumentVerificationResponse(BaseModel):
    """Schema for document verification response."""
    id: int
    user_id: int
    document_type: str
    status: str
    verified_at: Optional[datetime] = None
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class KYCVerificationResponse(BaseModel):
    """Schema for KYC verification response."""
    id: int
    user_id: int
    status: str
    provider: Optional[str] = None
    verified_at: Optional[datetime] = None
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AlertEscalationRuleResponse(BaseModel):
    """Schema for alert escalation rule response."""
    id: int
    alert_type: str
    severity: str
    threshold_value: Optional[float] = None
    current_tier: int
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ThreatDetectionRequest(BaseModel):
    """Schema for threat detection request."""
    actor_id: Optional[int] = None
    activity_type: str
    metadata: Optional[Dict[str, Any]] = None
