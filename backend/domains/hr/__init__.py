"""HR domain — public facade.

Exports the public API for the HR domain. Uses lazy imports to avoid
circular dependency issues at module load time.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # services
    "EmployeeService": ("domains.hr.services.employees.employee_service", "EmployeeService"),
    "HRService": ("domains.hr.services.employees.hr_service", "HRService"),
    "COIService": ("domains.hr.services.employees.coi_service", "COIService"),
    "RiskService": ("domains.hr.services.employees.risk_service", "RiskService"),
    "HSEManager": ("domains.hr.services.employees.hse_manager", "HSEManager"),
    "ESSService": ("domains.hr.services.ess.ess_service", "ESSService"),
    "HierarchyService": ("domains.hr.services.hierarchy.hierarchy_service", "HierarchyService"),
    "LMSService": ("domains.hr.services.learning.lms_service", "LMSService"),
    "PayrollService": ("domains.hr.services.payroll.payroll_service", "PayrollService"),
    "PayrollEngine": ("domains.hr.services.payroll.payroll_engine", "PayrollEngine"),
    "ShiftRosterService": ("domains.hr.services.shift.shift_roster_service", "ShiftRosterService"),
    "SuccessionService": ("domains.hr.services.succession.succession_service", "SuccessionService"),
    "TravelService": ("domains.hr.services.travel.travel_service", "TravelService"),
    # models
    "Employee": ("domains.hr.models.employee_models", "Employee"),
    "HRSchema": ("domains.hr.models.hr_schema_models", "HRSchema"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.hr' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
