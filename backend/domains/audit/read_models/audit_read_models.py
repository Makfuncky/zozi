"""Audit domain read models (CQRS-lite projections)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class AuditTrailSummary(BaseModel):
    """Aggregated audit trail summary for dashboards."""
    total_entries: int
    entries_today: int
    entries_by_action: Dict[str, int]
    recent_entries: List[Dict[str, Any]]


class ComplianceStatus(BaseModel):
    """Data residency compliance status projection."""
    domain: str
    country_code: str
    compliant: bool
    violations_count: int
    last_check: Optional[datetime] = None
