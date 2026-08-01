"""Backward-compatible re-exports from the HR domain package.

All employee-related endpoints live in controllers.hr.hr_controller.
"""
from controllers.hr.hr_controller import (
    register_address, register_dependent, check_coi_conflict,
    create_coi_report, validate_gcc_compliance, get_employee_graph,
    create_disciplinary_case, get_disciplinary_cases,
    create_offboarding_case, get_offboarding_cases,
)
__all__ = [
    "register_address", "register_dependent", "check_coi_conflict",
    "create_coi_report", "validate_gcc_compliance", "get_employee_graph",
    "create_disciplinary_case", "get_disciplinary_cases",
    "create_offboarding_case", "get_offboarding_cases",
]