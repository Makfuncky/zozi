"""Accounts service — relocated to HR (relocated from domains.accounts.services).

This module is HR-domain logic that was previously misplaced in the accounts
domain. It exposes ESS (Employee Self-Service) helpers and the user→employee
lookup. Moved per the cross-domain cleanup initiative (2026-08-27).
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def get_employee_by_user_id(db: Session, user_id: int) -> Optional["Employee"]:
    """Look up the Employee record for a given user ID."""
    from domains.hr.models.employee_models import Employee
    return db.query(Employee).filter(Employee.user_id == user_id).first()


# ESS function wrappers to avoid cross-domain imports in routers (Law 6 compliance)

def get_employee_profile(db: Session, employee_id: int) -> dict:
    """Get employee profile."""
    from domains.hr.services.ess_service import get_employee_profile as _svc
    return _svc(db, employee_id)


def update_employee_profile(
    db: Session, employee_id: int,
    phone: Optional[str] = None, address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None, emergency_contact_phone: Optional[str] = None,
) -> dict:
    """Update employee profile."""
    from domains.hr.services.ess_service import update_employee_profile as _svc
    return _svc(db, employee_id, phone, address, emergency_contact_name, emergency_contact_phone)


def get_leave_balance(db: Session, employee_id: int) -> list:
    """Get leave balance."""
    from domains.hr.services.ess_service import get_leave_balance as _svc
    return _svc(db, employee_id)


def create_leave_request(db: Session, employee_id: int, leave_type: str, start_date: str, end_date: str, reason: str) -> dict:
    """Create leave request."""
    from domains.hr.services.ess_service import create_leave_request as _svc
    return _svc(db, employee_id, leave_type, start_date, end_date, reason)


def get_leave_history(db: Session, employee_id: int) -> list:
    """Get leave history."""
    from domains.hr.services.ess_service import get_leave_history as _svc
    return _svc(db, employee_id)


def get_payslips(db: Session, employee_id: int) -> list:
    """Get payslips."""
    from domains.hr.services.ess_service import get_payslips as _svc
    return _svc(db, employee_id)


def get_attendance(db: Session, employee_id: int) -> dict:
    """Get attendance."""
    from domains.hr.services.ess_service import get_attendance as _svc
    return _svc(db, employee_id)


def get_okrs(db: Session, employee_id: int) -> list:
    """Get OKRs."""
    from domains.hr.services.ess_service import get_okrs as _svc
    return _svc(db, employee_id)


def get_org_chart(db: Session, org_unit_id: Optional[int], employee_id: int) -> dict:
    """Get org chart."""
    from domains.hr.services.ess_service import get_org_chart as _svc
    return _svc(db, org_unit_id, employee_id)


def get_user_by_id(db: Session, user_id: int):
    """Look up a User by ID via the accounts domain's sanctioned read port."""
    from domains.accounts.ports import get_user_by_id as _port
    return _port(db, user_id)
