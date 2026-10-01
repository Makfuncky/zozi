"""Security domain read models (CQRS-lite projections)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class SecurityDashboardSummary(BaseModel):
    """Aggregated security dashboard summary."""
    open_threats: int
    resolved_threats_today: int
    pending_verifications: int
    fraud_alerts_active: int
    recent_alerts: List[Dict[str, Any]]


class VerificationStatus(BaseModel):
    """Document/KYC verification status projection."""
    total_verifications: int
    pending: int
    approved: int
    rejected: int
    by_country: Dict[str, int]
    last_updated: Optional[datetime] = None
