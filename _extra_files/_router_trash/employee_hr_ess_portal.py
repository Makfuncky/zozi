"""ESS Portal — Employee Self-Service endpoints for profile, leave, attendance, payslips."""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from controllers.auth_controller import get_current_user
from db.database import get_db
from data.models import User
from data.models_employee_models import Employee
from data.services_employee_activity_logger import log_activity
from services.db_read import first, first_row, rows
from services.hr.ess_write_service import update_employee_profile, create_leave_request
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_employee(user: User, db: Session) -> Employee:
    """Get the Employee record for the current user."""
    emp = first(db, Employee, [Employee.user_id == user.id])
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp


# ── Profile ──────────────────────────────────────────────────────


@router.get("/profile", response_model=dict)
def ess_get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    row = first_row(
        db,
        sql="""
            SELECT e.*, u.email, u.full_name, u.role,
                   ou.name as unit_name, ou.path as unit_path
            FROM employees e
            JOIN users u ON u.id = e.user_id
            LEFT JOIN org_units ou ON ou.id = e.org_unit_id
            WHERE e.id = :eid
        """,
        params={"eid": emp.id},
    )
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return dict(row._mapping)


@router.put("/profile", response_model=dict)
def ess_update_profile(
    phone: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    return update_employee_profile(
        db,
        emp,
        phone=phone,
        address=address,
        emergency_contact_name=emergency_contact_name,
        emergency_contact_phone=emergency_contact_phone,
    )


# ── Leave ────────────────────────────────────────────────────────


@router.get("/leave/balance", response_model=dict)
def ess_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    records = rows(
        db,
        sql="""
            SELECT leave_type, year, allocated_days, used_days,
                   carried_forward_days, pending_days,
                   (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
            FROM employee_leave_ledgers
            WHERE employee_id = :eid
            ORDER BY year DESC, leave_type
        """,
        params={"eid": emp.id},
    )
    return [dict(r._mapping) for r in records]


@router.post("/leave/request", response_model=dict)
def ess_request_leave(
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    return create_leave_request(
        db,
        emp,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )


@router.get("/leave/history", response_model=dict)
def ess_leave_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    records = rows(
        db,
        sql="""
            SELECT id, leave_type, start_date, end_date, reason, status, created_at
            FROM leave_requests
            WHERE employee_id = :eid
            ORDER BY created_at DESC
            LIMIT 50
        """,
        params={"eid": emp.id},
    )
    return [dict(r._mapping) for r in records]


# ── Payslips ─────────────────────────────────────────────────────


@router.get("/payslips", response_model=dict)
def ess_payslips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    records = rows(
        db,
        sql="""
            SELECT id, payroll_date, gross_amount, net_amount, deductions, status, created_at
            FROM payroll_records
            WHERE employee_id = :eid
            ORDER BY payroll_date DESC
            LIMIT 24
        """,
        params={"eid": emp.id},
    )
    return [dict(r._mapping) for r in records]


# ── Attendance ───────────────────────────────────────────────────


@router.get("/attendance", response_model=dict)
def ess_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    records = rows(
        db,
        sql="""
            SELECT id, clock_in, clock_out, status, created_at
            FROM attendance_records
            WHERE employee_id = :eid
            ORDER BY clock_in DESC
            LIMIT 60
        """,
        params={"eid": emp.id},
    )
    return [dict(r._mapping) for r in records]


# ── OKRs ─────────────────────────────────────────────────────────


@router.get("/okrs", response_model=dict)
def ess_okrs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    records = rows(
        db,
        sql="""
            SELECT id, title, description, objective_type, quarter, year,
                   status, progress_pct, confidence_level, created_at
            FROM okr_objectives
            WHERE employee_id = :eid
            ORDER BY year DESC, quarter DESC
        """,
        params={"eid": emp.id},
    )
    objectives = []
    for obj in records:
        obj_dict = dict(obj._mapping)
        kpis = rows(
            db,
            sql="""
                SELECT id, metric_name, metric_type, target_value, current_value, weight_pct
                FROM kpi_metrics
                WHERE objective_id = :oid
            """,
            params={"oid": obj_dict["id"]},
        )
        obj_dict["kpis"] = [dict(k._mapping) for k in kpis]
        objectives.append(obj_dict)
    return objectives


# ── Org Chart (self) ─────────────────────────────────────────────


@router.get("/org-chart", response_model=dict)
def ess_org_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    row = first_row(
        db,
        sql="""
            SELECT ou.id, ou.name, ou.path, ou.depth, ou.parent_unit_id,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.id = :ouid
        """,
        params={"ouid": emp.org_unit_id},
    )

    if not row:
        return {"org_unit": None, "colleagues": [], "sub_units": []}

    org_unit = dict(row._mapping)

    # Colleagues in the same unit
    colleagues = rows(
        db,
        sql="""
            SELECT e.id, u.full_name, e.employee_code, e.job_title
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.org_unit_id = :ouid AND e.id != :eid AND e.employment_status = 'active'
            ORDER BY u.full_name
        """,
        params={"ouid": emp.org_unit_id, "eid": emp.id},
    )

    # Sub-units
    sub_units = rows(
        db,
        sql="""
            SELECT ou.id, ou.name, ou.depth,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.parent_unit_id = :ouid
            ORDER BY ou.name
        """,
        params={"ouid": emp.org_unit_id},
    )

    return {
        "org_unit": org_unit,
        "colleagues": [dict(c._mapping) for c in colleagues],
        "sub_units": [dict(s._mapping) for s in sub_units],
    }

