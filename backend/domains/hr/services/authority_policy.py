"""HR domain — Authority level policy service.

Defines resource-type to authority-level thresholds for approval workflows.
"""
from __future__ import annotations

from typing import Dict

# Authority level thresholds by resource type
AUTHORITY_THRESHOLDS: Dict[str, int] = {
    "leave": 1,
    "expense_500": 2,
    "expense_2000": 3,
    "expense_10000": 4,
    "payroll_release": 4,
    "offboarding_approve": 3,
    "disciplinary_final": 4,
    "hiring_approve": 3,
}


def get_required_authority(resource_type: str) -> int:
    """Get the required authority level for a resource type."""
    return AUTHORITY_THRESHOLDS.get(resource_type, 1)


def can_approve(employee_authority_level: int, resource_type: str) -> bool:
    """Check if an employee has sufficient authority to approve a resource."""
    return employee_authority_level >= get_required_authority(resource_type)


__all__ = [
    "AUTHORITY_THRESHOLDS",
    "get_required_authority",
    "can_approve",
]
