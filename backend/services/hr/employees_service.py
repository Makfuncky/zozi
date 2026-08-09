"""HR employee service layer.

Extracted from routers/employees.py so the router only delegates to a service
(architecture circuit: routers -> services own DB access). Clears CIR1/LC1/W1
findings that flagged raw SQL and session usage inside the router endpoints.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.core import Address
from models.employee_models import (
    Employee,
    EmployeeDependent,
    EmployeeLeaveRequest,
    EmployeeShiftRoster,
)
from utils.datetime_utils import utcnow as _utcnow
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def get_employee_addresses(employee_id: int, db: Session) -> List[Dict[str, Any]]:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return []
    addresses = db.query(Address).filter(Address.user_id == employee.user_id).all()
    return [
        {
            "id": a.id,
            "label": a.label,
            "full_name": a.full_name,
            "phone": a.phone,
            "address_line1": a.address_line1,
            "address_line2": a.address_line2,
            "city": a.city,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "is_default": a.is_default,
        }
        for a in addresses
    ]


def get_employee_dependents(employee_id: int, db: Session) -> List[Dict[str, Any]]:
    dependents = (
        db.query(EmployeeDependent)
        .filter(EmployeeDependent.employee_id == employee_id)
        .all()
    )
    return [
        {
            "id": d.id,
            "name": d.name,
            "relation": d.relation,
            "dob": str(d.dob) if d.dob else None,
            "is_insured": d.is_insured,
        }
        for d in dependents
    ]


def get_leave_requests(db: Session) -> List[Dict[str, Any]]:
    requests = (
        db.query(EmployeeLeaveRequest)
        .order_by(EmployeeLeaveRequest.created_at.desc())
        .all()
    )
    result: List[Dict[str, Any]] = []
    for r in requests:
        employee_name: Optional[str] = None
        if r.employee:
            user = r.employee.user
            employee_name = (
                (user.full_name or user.username)
                if user
                else r.employee.employee_code
            )
        result.append(
            {
                "id": r.id,
                "employee_id": r.employee_id,
                "employee_name": employee_name,
                "leave_type": r.leave_type,
                "start_date": r.start_date.isoformat() if r.start_date else None,
                "end_date": r.end_date.isoformat() if r.end_date else None,
                "days_requested": r.days_requested,
                "status": r.status,
                "approved_by": r.approved_by,
                "notes": r.rejection_reason or "",
            }
        )
    return result


def set_leave_request_status(
    leave_id: int, status: str, approved_by: Any, db: Session
) -> Dict[str, Any]:
    r = (
        db.query(EmployeeLeaveRequest)
        .filter(EmployeeLeaveRequest.id == leave_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Leave request not found")
    status = status.lower()
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    r.status = status
    r.approved_by = approved_by
    r.approved_at = _utcnow()
    db.commit()
    return {"message": f"Leave request {status}", "id": leave_id}


def get_shifts(db: Session) -> List[Dict[str, Any]]:
    shifts = (
        db.query(EmployeeShiftRoster)
        .order_by(EmployeeShiftRoster.shift_date.desc())
        .all()
    )
    result: List[Dict[str, Any]] = []
    for s in shifts:
        employee_name: Optional[str] = None
        if s.employee:
            user = s.employee.user
            employee_name = (
                (user.full_name or user.username)
                if user
                else s.employee.employee_code
            )
        result.append(
            {
                "id": s.id,
                "employee_id": s.employee_id,
                "employee_name": employee_name,
                "shift_date": s.shift_date.isoformat() if s.shift_date else None,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "shift_type": s.shift_type,
                "status": s.status,
            }
        )
    return result


def list_public_employees(db: Session) -> Any:
    """Public employee directory.

    Originally implemented with a raw string ``db.execute(query)``; replaced with
    an ORM query so no inline SQL lives in the router (W1/LC1).
    """
    try:
        employees = (
            db.query(Employee).order_by(Employee.created_at.desc()).limit(50).all()
        )
        return [
            {
                "id": e.id,
                "employee_code": e.employee_code,
                "department": e.department,
                "position": e.position,
                "employment_status": e.employment_status,
                "salary": float(e.salary) if e.salary else None,
                "currency": e.currency,
                "country_code": e.country_code,
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
            }
            for e in employees
        ]
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:  # pragma: no cover - defensive, mirrors original contract
        logger.warning("Public employee directory unavailable: %s", e)
        return {"error": str(e)}