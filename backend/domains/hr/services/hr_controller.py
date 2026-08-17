"""HR & compliance controller.

Delegates to ``services.hr.hr_service`` which implements employee addresses,
dependents, conflict-of-interest (COI) reporting, GCC labor-law compliance
validation, disciplinary and offboarding case management, and the employee
relationship graph. The controller is the stable boundary the router imports.

Routes are declared with the metadata-only decorators from ``core.route_contract``
so ``routers/generated/auto_router.py`` can auto-generate the FastAPI surface.
A controller never imports FastAPI directly.

HR endpoints are currently unauthenticated (they mirror the legacy hand-written
router); only ``db`` is injected. Move them under ``deps=["admin"]`` once an
admin gate exists for the HR surface.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from core.route_contract import get, post

from domains.hr.services.hr_service import (
    check_coi_conflict as _check_coi_conflict,
)
from domains.hr.services.hr_service import (
    create_coi_report as _create_coi_report,
)
from domains.hr.services.hr_service import (
    create_disciplinary_case as _create_disciplinary_case,
)
from domains.hr.services.hr_service import (
    create_offboarding_case as _create_offboarding_case,
)
from domains.hr.services.hr_service import (
    get_disciplinary_cases as _get_disciplinary_cases,
)
from domains.hr.services.hr_service import (
    get_employee_graph as _get_employee_graph,
)
from domains.hr.services.hr_service import (
    get_offboarding_cases as _get_offboarding_cases,
)
from domains.hr.services.hr_service import (
    register_address as _register_address,
)
from domains.hr.services.hr_service import (
    register_dependent as _register_dependent,
)
from domains.hr.services.hr_service import (
    validate_gcc_compliance as _validate_gcc_compliance,
)

@post("/api/v1/hr/{employee_id}/addresses", deps=["db"], body=dict, tags=["hr"])
def register_address(employee_id: int, address_data: dict, db: Session) -> dict:
    """Register a postal address for an employee."""
    return _register_address(employee_id, address_data, db)

@post("/api/v1/hr/{employee_id}/dependents", deps=["db"], body=dict, tags=["hr"])
def register_dependent(employee_id: int, dependent_data: dict, db: Session) -> dict:
    """Register a dependent (family member) for an employee."""
    return _register_dependent(employee_id, dependent_data, db)

@get("/api/v1/hr/{employee_id}/coi-check", deps=["db"], tags=["hr"])
def check_coi_conflict(employee_id: int, db: Session) -> list[dict]:
    """Check an employee for conflict-of-interest relationships."""
    return _check_coi_conflict(employee_id, db)

@post("/api/v1/hr/{employee_id}/coi-report", deps=["db"], body=dict, tags=["hr"])
def create_coi_report(employee_id: int, report_data: dict, db: Session) -> dict:
    """File a conflict-of-interest report for an employee."""
    return _create_coi_report(employee_id, report_data, db)

@get("/api/v1/hr/{employee_id}/compliance", deps=["db"], tags=["hr"])
def validate_gcc_compliance(employee_id: int, db: Session) -> dict:
    """Validate an employee against GCC labor-law compliance rules."""
    return _validate_gcc_compliance(employee_id, db)

@get("/api/v1/hr/{employee_id}/graph", deps=["db"], tags=["hr"])
def get_employee_graph(employee_id: int, db: Session) -> dict:
    """Return the employee relationship/Reporting graph."""
    return _get_employee_graph(employee_id, db)

@get("/api/v1/hr/disciplinary", deps=["db"], tags=["hr"])
def get_disciplinary_cases(db: Session) -> list[dict]:
    """List all disciplinary cases."""
    return _get_disciplinary_cases(db)

@post("/api/v1/hr/{employee_id}/disciplinary", deps=["db"], body=dict, tags=["hr"])
def create_disciplinary_case(employee_id: int, case_data: dict, db: Session) -> dict:
    """Open a disciplinary case for an employee."""
    return _create_disciplinary_case(employee_id, case_data, db)

@get("/api/v1/hr/offboarding", deps=["db"], tags=["hr"])
def get_offboarding_cases(db: Session) -> list[dict]:
    """List all offboarding cases."""
    return _get_offboarding_cases(db)

@post("/api/v1/hr/{employee_id}/offboarding", deps=["db"], body=dict, tags=["hr"])
def create_offboarding_case(employee_id: int, case_data: dict, db: Session) -> dict:
    """Open an offboarding case for an employee."""
    return _create_offboarding_case(employee_id, case_data, db)
