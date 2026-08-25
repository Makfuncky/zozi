"""Auto-migrated service logic from routers/ess.py."""
from __future__ import annotations

from __future__ import annotations

import logging

from typing import Optional

from fastapi import Depends, HTTPException

from sqlalchemy import text

from sqlalchemy.orm import Session

from domains.accounts.services.auth.auth_service import get_current_user

from infrastructure.database.database import get_db

from domains.governance.models.user import User

from domains.hr.models.employee_models import Employee

from domains.hr.services.employee_activity_logger import log_activity

logger = logging.getLogger(__name__)

def _get_employee(user: User, db: Session) -> Employee:
    """Get the Employee record for the current user."""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp

def ess_get_profile(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    row = db.execute(
        text("""
            SELECT e.*, u.email, u.full_name, u.role,
                   ou.name as unit_name, ou.path as unit_path
            FROM employees e
            JOIN users u ON u.id = e.user_id
            LEFT JOIN org_units ou ON ou.id = e.org_unit_id
            WHERE e.id = :eid
        """),
        {"eid": emp.id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return dict(row)

def ess_update_profile(phone: Optional[str], address: Optional[str], emergency_contact_name: Optional[str], emergency_contact_phone: Optional[str], current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    updates = []
    params: dict = {"eid": emp.id}
    if phone is not None:
        updates.append("phone = :phone")
        params["phone"] = phone
    if address is not None:
        updates.append("address = :address")
        params["address"] = address
    if emergency_contact_name is not None:
        updates.append("emergency_contact_name = :ec_name")
        params["ec_name"] = emergency_contact_name
    if emergency_contact_phone is not None:
        updates.append("emergency_contact_phone = :ec_phone")
        params["ec_phone"] = emergency_contact_phone
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    db.execute(
        text(f"UPDATE employees SET {', '.join(updates)} WHERE id = :eid"),
        params,
    )
    db.commit()
    log_activity(db, emp.id, "profile_updated", "employee_profile", str(emp.id))
    return {"status": "updated", "fields": [u.split(" =")[0] for u in updates]}

def ess_leave_balance(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT leave_type, year, allocated_days, used_days,
                   carried_forward_days, pending_days,
                   (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
            FROM employee_leave_ledgers
            WHERE employee_id = :eid
            ORDER BY year DESC, leave_type
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]

def ess_request_leave(leave_type: str, start_date: str, end_date: str, reason: str, current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    result = db.execute(
        text("""
            INSERT INTO leave_requests
                (employee_id, leave_type, start_date, end_date, reason, status, created_at)
            VALUES
                (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
            RETURNING id
        """),
        {
            "eid": emp.id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "now": text("NOW()"),
        },
    )
    leave_id = result.scalar()
    db.commit()
    log_activity(db, emp.id, "leave_requested", "leave_request", str(leave_id))
    return {"id": leave_id, "status": "pending"}

def ess_leave_history(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, leave_type, start_date, end_date, reason, status, created_at
            FROM leave_requests
            WHERE employee_id = :eid
            ORDER BY created_at DESC
            LIMIT 50
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]

def ess_payslips(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, payroll_date, gross_amount, net_amount, deductions, status, created_at
            FROM payroll_records
            WHERE employee_id = :eid
            ORDER BY payroll_date DESC
            LIMIT 24
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]

def ess_attendance(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, clock_in, clock_out, status, created_at
            FROM attendance_records
            WHERE employee_id = :eid
            ORDER BY clock_in DESC
            LIMIT 60
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]

def ess_okrs(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, title, description, objective_type, quarter, year,
                   status, progress_pct, confidence_level, created_at
            FROM okr_objectives
            WHERE employee_id = :eid
            ORDER BY year DESC, quarter DESC
        """),
        {"eid": emp.id},
    ).mappings().all()
    objectives = []
    for obj in rows:
        obj_dict = dict(obj)
        kpis = db.execute(
            text("""
                SELECT id, metric_name, metric_type, target_value, current_value, weight_pct
                FROM kpi_metrics
                WHERE objective_id = :oid
            """),
            {"oid": obj_dict["id"]},
        ).mappings().all()
        obj_dict["kpis"] = [dict(k) for k in kpis]
        objectives.append(obj_dict)
    return objectives

def ess_org_chart(current_user: User, db: Session):
    emp = _get_employee(current_user, db)
    row = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.path, ou.depth, ou.parent_unit_id,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.id = :ouid
        """),
        {"ouid": emp.org_unit_id},
    ).mappings().first()

    if not row:
        return {"org_unit": None, "colleagues": [], "sub_units": []}

    org_unit = dict(row)

    # Colleagues in the same unit
    colleagues = db.execute(
        text("""
            SELECT e.id, u.full_name, e.employee_code, e.job_title
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.org_unit_id = :ouid AND e.id != :eid AND e.employment_status = 'active'
            ORDER BY u.full_name
        """),
        {"ouid": emp.org_unit_id, "eid": emp.id},
    ).mappings().all()

    # Sub-units
    sub_units = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.depth,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.parent_unit_id = :ouid
            ORDER BY ou.name
        """),
        {"ouid": emp.org_unit_id},
    ).mappings().all()

    return {
        "org_unit": org_unit,
        "colleagues": [dict(c) for c in colleagues],
        "sub_units": [dict(s) for s in sub_units],
    }


# ── ESS Write Operations (merged from ess_write_service.py) ───────────────────

def update_employee_profile(
    db: Session,
    emp: Employee,
    *,
    phone: str | None = None,
    address: str | None = None,
    emergency_contact_name: str | None = None,
    emergency_contact_phone: str | None = None,
) -> dict:
    updates: list[str] = []
    params: dict = {"eid": emp.id}
    if phone is not None:
        updates.append("phone = :phone")
        params["phone"] = phone
    if address is not None:
        updates.append("address = :address")
        params["address"] = address
    if emergency_contact_name is not None:
        updates.append("emergency_contact_name = :ec_name")
        params["ec_name"] = emergency_contact_name
    if emergency_contact_phone is not None:
        updates.append("emergency_contact_phone = :ec_phone")
        params["ec_phone"] = emergency_contact_phone
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    # Column names come from a fixed allowlist, never from user input.
    db.execute(
        text(f"UPDATE employees SET {', '.join(updates)} WHERE id = :eid"),
        params,
    )
    db.commit()
    log_activity(db, emp.id, "profile_updated", "employee_profile", str(emp.id))
    return {"status": "updated", "fields": [u.split(" =")[0] for u in updates]}


def create_leave_request(
    db: Session,
    emp: Employee,
    *,
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
) -> dict:
    result = db.execute(
        text(
            """
            INSERT INTO leave_requests
                (employee_id, leave_type, start_date, end_date, reason, status, created_at)
            VALUES
                (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
            RETURNING id
            """
        ),
        {
            "eid": emp.id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "now": text("NOW()"),
        },
    )
    leave_id = result.scalar()
    db.commit()
    log_activity(db, emp.id, "leave_requested", "leave_request", str(leave_id))
    return {"id": leave_id, "status": "pending"}

