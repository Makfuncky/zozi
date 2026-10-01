"""Employee module serializers (per-actor view models).

Per ARCHITECTURE_DIAGRAM.md §3, modules/{actor}/serializers/ holds
response shaping helpers that transform domain service output into
employee-facing API responses.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EmployeeDashboardSummary(BaseModel):
    """Employee-facing dashboard summary."""
    total_tasks: int
    pending_reviews: int
    team_size: int
    alerts_count: int


class EmployeeProfileResponse(BaseModel):
    """Employee-facing profile response."""
    id: int
    email: str
    username: str
    role: str
    department: Optional[str] = None
    country_code: Optional[str] = None
    created_at: Optional[datetime] = None


class PayrollSummary(BaseModel):
    """Employee-facing payroll summary."""
    period: str
    gross_amount: float
    net_amount: float
    currency: str = "USD"
    status: str


def shape_employee_profile(user: Dict[str, Any]) -> EmployeeProfileResponse:
    """Shape a domain user dict into an employee-facing profile."""
    return EmployeeProfileResponse(
        id=user.get("id", 0),
        email=user.get("email", ""),
        username=user.get("username", ""),
        role=user.get("role", "employee"),
        department=user.get("department"),
        country_code=user.get("country_code"),
        created_at=user.get("created_at"),
    )


__all__ = [
    "EmployeeDashboardSummary",
    "EmployeeProfileResponse",
    "PayrollSummary",
    "shape_employee_profile",
]
