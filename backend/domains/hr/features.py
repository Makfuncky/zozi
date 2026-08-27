"""HR domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the HR domain. CI must fail on any
``require_feature("hr.*")`` literal not present in this map.

Seeded from the HR-facing service surface: employees, departments, payroll,
attendance, leave, and performance management.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "hr.employee.read": {
        "label": "View Employees",
        "risk": "medium",
        "actions": ["read"],
        "description": "View employee profiles, roles, and assignment details.",
    },
    "hr.employee.manage": {
        "label": "Manage Employees",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and manage employee accounts and roles.",
    },
    "hr.department.read": {
        "label": "View Departments",
        "risk": "low",
        "actions": ["read"],
        "description": "View department structure and department details.",
    },
    "hr.department.manage": {
        "label": "Manage Departments",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Create, update, and manage organizational departments.",
    },
    "hr.payroll.read": {
        "label": "View Payroll",
        "risk": "high",
        "actions": ["read"],
        "description": "View payroll records and compensation details.",
    },
    "hr.payroll.manage": {
        "label": "Manage Payroll",
        "risk": "critical",
        "actions": ["read", "create", "update"],
        "description": "Manage payroll, compensation, and salary adjustments.",
    },
    "hr.attendance.read": {
        "label": "View Attendance",
        "risk": "medium",
        "actions": ["read"],
        "description": "View employee attendance records and time tracking.",
    },
    "hr.attendance.manage": {
        "label": "Manage Attendance",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage attendance policies and correct attendance records.",
    },
    "hr.leave.read": {
        "label": "View Leave Requests",
        "risk": "low",
        "actions": ["read"],
        "description": "View employee leave requests and balances.",
    },
    "hr.leave.manage": {
        "label": "Manage Leave",
        "risk": "medium",
        "actions": ["read", "create", "update", "approve"],
        "description": "Manage leave requests, approvals, and leave policies.",
    },
    "hr.performance.read": {
        "label": "View Performance",
        "risk": "medium",
        "actions": ["read"],
        "description": "View employee performance reviews and goals.",
    },
    "hr.performance.manage": {
        "label": "Manage Performance",
        "risk": "high",
        "actions": ["read", "create", "update"],
        "description": "Manage performance reviews, goals, and evaluations.",
    },
    "hr.profile.read": {
        "label": "View Employee Profile",
        "risk": "low",
        "actions": ["read"],
        "description": "View an employee profile (self or staff).",
    },
    "hr.profile.update": {
        "label": "Update Employee Profile",
        "risk": "medium",
        "actions": ["read", "update"],
        "description": "Update an employee profile (self or staff).",
    },
    "hr.leave.create": {
        "label": "Create Leave Request",
        "risk": "low",
        "actions": ["create"],
        "description": "Submit a new leave / time-off request.",
    },
    "hr.payslip.read": {
        "label": "View Payslips",
        "risk": "medium",
        "actions": ["read"],
        "description": "View employee payslips and compensation statements.",
    },
    "hr.okr.read": {
        "label": "View OKRs",
        "risk": "low",
        "actions": ["read"],
        "description": "View objectives and key results (OKRs).",
    },
    "hr.org.read": {
        "label": "View Org Chart",
        "risk": "low",
        "actions": ["read"],
        "description": "View the organizational chart and reporting structure.",
    },
    # ── Legacy / plural-form atoms (from services/features.py) ────────────────
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
    """Return all HR feature atom identifiers, sorted."""
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    """Return True if ``feature`` is a known HR feature atom (supports wildcard)."""
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known"]
