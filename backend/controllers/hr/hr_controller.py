"""controllers.hr.hr_controller controller.

Business logic is delegated to services.hr.hr_service (routers -> controllers -> services)."""

from services.hr.hr_service import (
    check_coi_conflict, create_coi_report, create_disciplinary_case, create_offboarding_case, get_disciplinary_cases, get_employee_graph,
    get_offboarding_cases, register_address, register_dependent, validate_gcc_compliance
)

__all__ = [
    "check_coi_conflict", "create_coi_report", "create_disciplinary_case", "create_offboarding_case", "get_disciplinary_cases", "get_employee_graph",
    "get_offboarding_cases", "register_address", "register_dependent", "validate_gcc_compliance"
]
