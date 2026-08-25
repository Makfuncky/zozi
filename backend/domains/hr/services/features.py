"""Feature atoms for hr domain.

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the hr domain. CI must fail on any
``require_feature("hr.*")`` literal that is not present in this map.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "hr.employees.read": {
        "label": "View Employees",
        "risk": "low",
        "actions": ["read"],
        "description": "View employee records and profiles.",
    },
    "hr.employees.manage": {
        "label": "Manage Employees",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Full employee lifecycle management including onboarding and offboarding.",
    },
    "hr.attendance.read": {
        "label": "View Attendance",
        "risk": "low",
        "actions": ["read"],
        "description": "View employee attendance records and time tracking.",
    },
    "hr.attendance.manage": {
        "label": "Manage Attendance",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Manage attendance records, shifts, and time corrections.",
    },
    "hr.leave.read": {
        "label": "View Leave Requests",
        "risk": "low",
        "actions": ["read"],
        "description": "View employee leave requests and balances.",
    },
    "hr.leave.manage": {
        "label": "Manage Leave Requests",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Approve, reject, and manage employee leave requests.",
    },
    "hr.payroll.read": {
        "label": "View Payroll",
        "risk": "low",
        "actions": ["read"],
        "description": "View payroll records and compensation data.",
    },
    "hr.payroll.manage": {
        "label": "Manage Payroll",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Process payroll, manage compensation, and configure pay rules.",
    },
    "hr.org_structure.read": {
        "label": "View Org Structure",
        "risk": "low",
        "actions": ["read"],
        "description": "View organizational structure, units, and reporting lines.",
    },
    "hr.org_structure.manage": {
        "label": "Manage Org Structure",
        "risk": "medium",
        "actions": ["read", "create", "update", "delete"],
        "description": "Manage organizational units, departments, and hierarchy.",
    },
    "hr.training.read": {
        "label": "View Training",
        "risk": "low",
        "actions": ["read"],
        "description": "View training modules and employee certification records.",
    },
    "hr.training.manage": {
        "label": "Manage Training",
        "risk": "medium",
        "actions": ["read", "create", "update"],
        "description": "Manage training modules, assign courses, and track certifications.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
