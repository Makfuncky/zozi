"""ESS Portal — Employee Self-Service endpoints for profile, leave, attendance, payslips."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from data.dependencies_auth import get_current_user
from data.db import get_db
from data.models import User
from data.models_employee_models import Employee
from services.employee_activity_logger import log_activity

from services.write_helpers import commit_only
logger = logging.getLogger(__name__)
router = APIRouter()


def _get_employee(user: User, db: Session) -> Employee:
    """Get the Employee record for the current user."""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp


# ── Profile ──────────────────────────────────────────────────────


@router.get("/profile")
def ess_get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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


@router.put("/profile")
def ess_update_profile(
    phone: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    update_data = {}
    if phone is not None:
        update_data["phone"] = phone
    if address is not None:
        update_data["address"] = address
    if emergency_contact_name is not None:
        update_data["emergency_contact_name"] = emergency_contact_name
    if emergency_contact_phone is not None:
        update_data["emergency_contact_phone"] = emergency_contact_phone
    db.query(Employee).filter(Employee.id == emp.id).update(update_data)
    commit_only(db)
    log_activity(db, emp.id, "profile_updated", "employee_profile", str(emp.id))
    return {"status": "updated", "fields": [u.split(" =")[0] for u in updates]}


# ── Leave ────────────────────────────────────────────────────────


@router.get("/leave/balance")
def ess_leave_balance(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT leave_type, year, allocated_days, used_days,
                   carried_forward_days, pending_days,
                   (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
            FROM employee_leave_ledgers
            WHERE employee_id = :eid
            ORDER BY year DESC, leave_type
            OFFSET :skip LIMIT :limit
        """),
        {"eid": emp.id, "skip": skip, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/leave/request")
def ess_request_leave(
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
    commit_only(db)
    log_activity(db, emp.id, "leave_requested", "leave_request", str(leave_id))
    return {"id": leave_id, "status": "pending"}


@router.get("/leave/history")
def ess_leave_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, leave_type, start_date, end_date, reason, status, created_at
            FROM leave_requests
            WHERE employee_id = :eid
            ORDER BY created_at DESC
            OFFSET :skip LIMIT :limit
        """),
        {"eid": emp.id, "skip": skip, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Payslips ─────────────────────────────────────────────────────


@router.get("/payslips")
def ess_payslips(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, payroll_date, gross_amount, net_amount, deductions, status, created_at
            FROM payroll_records
            WHERE employee_id = :eid
            ORDER BY payroll_date DESC
            OFFSET :skip LIMIT :limit
        """),
        {"eid": emp.id, "skip": skip, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Attendance ───────────────────────────────────────────────────


@router.get("/attendance")
def ess_attendance(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, clock_in, clock_out, status, created_at
            FROM attendance_records
            WHERE employee_id = :eid
            ORDER BY clock_in DESC
            OFFSET :skip LIMIT :limit
        """),
        {"eid": emp.id, "skip": skip, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── OKRs ─────────────────────────────────────────────────────────


@router.get("/okrs")
def ess_okrs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, title, description, objective_type, quarter, year,
                   status, progress_pct, confidence_level, created_at
            FROM okr_objectives
            WHERE employee_id = :eid
            ORDER BY year DESC, quarter DESC
            OFFSET :skip LIMIT :limit
        """),
        {"eid": emp.id, "skip": skip, "limit": limit},
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


# ── Org Chart (self) ─────────────────────────────────────────────


@router.get("/org-chart")
def ess_org_chart(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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
            OFFSET :skip LIMIT :limit
        """),
        {"ouid": emp.org_unit_id, "eid": emp.id, "skip": skip, "limit": limit},
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
            OFFSET :skip LIMIT :limit
        """),
        {"ouid": emp.org_unit_id, "skip": skip, "limit": limit},
    ).mappings().all()

    return {
        "org_unit": org_unit,
        "colleagues": [dict(c) for c in colleagues],
        "sub_units": [dict(s) for s in sub_units],
    }
