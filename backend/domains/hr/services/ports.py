"""HR domain — sanctioned cross-domain READ surface (ports).

Per ARCHITECTURE_DIAGRAM.md Law 3, cross-domain reads may ONLY happen through a
publishing domain's ports.py. Other domains import these functions instead of
importing domains.hr.models or domains.hr.services directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via rbac).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

from .events import HREvent  # noqa: F401 — re-export for type hints


def _get_models():
    from domains.hr.models.employee_models import Employee
    from domains.hr.models.employee_models import EmployeeAttendance
    from domains.hr.models.employee_models import EmployeeLeaveRequest
    from domains.hr.models.employee_models import EmployeeDocument
    from domains.hr.models.employee_models import OrgUnit
    from domains.hr.models.employee_models import Office
    return Employee, EmployeeAttendance, EmployeeLeaveRequest, EmployeeDocument, OrgUnit, Office


def get_employee_by_id(db: Session, id_: int) -> Optional[object]:
    """Return Employee by primary key (or None)."""
    Employee, *_ = _get_models()
    return db.get(Employee, id_)


def get_employee_by_user_id(db: Session, user_id: int) -> Optional[object]:
    """Return the Employee whose ``user_id`` matches (or None)."""
    Employee, *_ = _get_models()
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def list_employees(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` Employee rows."""
    Employee, *_ = _get_models()
    return db.query(Employee).limit(limit).all()


def get_employee_attendance_by_id(db: Session, id_: int) -> Optional[object]:
    """Return EmployeeAttendance by primary key (or None)."""
    _, EmployeeAttendance, *_ = _get_models()
    return db.get(EmployeeAttendance, id_)


def list_employee_attendances(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` EmployeeAttendance rows."""
    _, EmployeeAttendance, *_ = _get_models()
    return db.query(EmployeeAttendance).limit(limit).all()


def get_employee_leave_request_by_id(db: Session, id_: int) -> Optional[object]:
    """Return EmployeeLeaveRequest by primary key (or None)."""
    *_, EmployeeLeaveRequest, *_ = _get_models()
    return db.get(EmployeeLeaveRequest, id_)


def list_employee_leave_requests(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` EmployeeLeaveRequest rows."""
    *_, EmployeeLeaveRequest, __, __ = _get_models() if False else (None, None, None, None, None, None)
    from domains.hr.models.employee_models import EmployeeLeaveRequest as _ELR
    return db.query(_ELR).limit(limit).all()


def list_employee_documents(db: Session, employee_id: int) -> List[object]:
    """Return EmployeeDocuments for an employee."""
    from domains.hr.models.employee_models import EmployeeDocument as _ED
    return db.query(_ED).filter(_ED.employee_id == employee_id).all()


def get_org_unit_by_id(db: Session, id_: int) -> Optional[object]:
    """Return OrgUnit by primary key (or None)."""
    *_, OrgUnit, _ = _get_models()
    return db.get(OrgUnit, id_)


def list_active_org_units(db: Session, country_code: Optional[str] = None) -> List[object]:
    """Return active OrgUnits (optionally country-scoped)."""
    *_, OrgUnit, __ = _get_models()
    query = db.query(OrgUnit).filter(OrgUnit.is_active == True)  # noqa: E712
    if country_code:
        query = query.filter(OrgUnit.country_code == country_code)
    return query.order_by(OrgUnit.path, OrgUnit.name).all()


def get_office_by_id(db: Session, id_: int) -> Optional[object]:
    """Return Office by primary key (or None)."""
    *_, Office = _get_models()
    return db.get(Office, id_)


def list_offices(db: Session, limit: int = 100) -> List[object]:
    """Return up to ``limit`` Office rows."""
    *_, Office = _get_models()
    return db.query(Office).limit(limit).all()


__all__ = [
    "get_employee_by_id",
    "get_employee_by_user_id",
    "list_employees",
    "get_employee_attendance_by_id",
    "list_employee_attendances",
    "get_employee_leave_request_by_id",
    "list_employee_leave_requests",
    "list_employee_documents",
    "get_org_unit_by_id",
    "list_active_org_units",
    "get_office_by_id",
    "list_offices",
]
