"""Employee Self-Service (ESS) Service — encapsulates ESS data access."""

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_employee_profile(db: Session, employee_id: int) -> dict:
    row = db.execute(
        text("""
            SELECT e.*, u.email, u.full_name, u.role,
                   ou.name as unit_name, ou.path as unit_path
            FROM employees e
            JOIN users u ON u.id = e.user_id
            LEFT JOIN org_units ou ON ou.id = e.org_unit_id
            WHERE e.id = :eid
        """),
        {"eid": employee_id},
    ).mappings().first()
    if not row:
        raise Exception("Profile not found")
    return dict(row)


def update_employee_profile(
    db: Session, employee_id: int,
    phone: Optional[str] = None, address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None, emergency_contact_phone: Optional[str] = None,
) -> dict:
    updates = []
    params: dict = {"eid": employee_id}
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
        raise Exception("No fields to update")
    set_clause = ", ".join(updates)
    db.execute(
        text(f"UPDATE employees SET {set_clause} WHERE id = :eid"),
        params,
    )
    db.commit()
    return {"status": "updated", "fields": [u.split(" =")[0] for u in updates]}


def get_leave_balance(db: Session, employee_id: int) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT leave_type, year, allocated_days, used_days,
                   carried_forward_days, pending_days,
                   (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
            FROM employee_leave_ledgers
            WHERE employee_id = :eid
            ORDER BY year DESC, leave_type
            LIMIT 1000
        """),
        {"eid": employee_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def create_leave_request(db: Session, employee_id: int, leave_type: str, start_date: str, end_date: str, reason: str) -> dict:
    result = db.execute(
        text("""
            INSERT INTO leave_requests
                (employee_id, leave_type, start_date, end_date, reason, status, created_at)
            VALUES
                (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
            RETURNING id
        """),
        {
            "eid": employee_id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "now": text("NOW()"),
        },
    )
    leave_id = result.scalar()
    db.commit()
    return {"id": leave_id, "status": "pending"}


def get_leave_history(db: Session, employee_id: int) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT id, leave_type, start_date, end_date, reason, status, created_at
            FROM leave_requests
            WHERE employee_id = :eid
            ORDER BY created_at DESC
            LIMIT 50
        """),
        {"eid": employee_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_payslips(db: Session, employee_id: int) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT id, payroll_date, gross_amount, net_amount, deductions, status, created_at
            FROM payroll_records
            WHERE employee_id = :eid
            ORDER BY payroll_date DESC
            LIMIT 24
        """),
        {"eid": employee_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_attendance(db: Session, employee_id: int) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT id, clock_in, clock_out, status, created_at
            FROM attendance_records
            WHERE employee_id = :eid
            ORDER BY clock_in DESC
            LIMIT 60
        """),
        {"eid": employee_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_okrs(db: Session, employee_id: int) -> List[dict]:
    rows = db.execute(
        text("""
            SELECT id, title, description, objective_type, quarter, year,
                   status, progress_pct, confidence_level, created_at
            FROM okr_objectives
            WHERE employee_id = :eid
            ORDER BY year DESC, quarter DESC
            LIMIT 1000
        """),
        {"eid": employee_id},
    ).mappings().all()
    objectives = []
    for obj in rows:
        obj_dict = dict(obj)
        kpis = db.execute(
            text("""
                SELECT id, metric_name, metric_type, target_value, current_value, weight_pct
                FROM kpi_metrics
                WHERE objective_id = :oid
                LIMIT 1000
            """),
            {"oid": obj_dict["id"]},
        ).mappings().all()
        obj_dict["kpis"] = [dict(k) for k in kpis]
        objectives.append(obj_dict)
    return objectives


def get_org_chart(db: Session, org_unit_id: Optional[int], employee_id: int) -> dict:
    row = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.path, ou.depth, ou.parent_unit_id,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.id = :ouid
        """),
        {"ouid": org_unit_id},
    ).mappings().first()

    if not row:
        return {"org_unit": None, "colleagues": [], "sub_units": []}

    org_unit = dict(row)

    colleagues = db.execute(
        text("""
            SELECT e.id, u.full_name, e.employee_code, e.job_title
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.org_unit_id = :ouid AND e.id != :eid AND e.employment_status = 'active'
            ORDER BY u.full_name
            LIMIT 1000
        """),
        {"ouid": org_unit_id, "eid": employee_id},
    ).mappings().all()

    sub_units = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.depth,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.parent_unit_id = :ouid
            ORDER BY ou.name
            LIMIT 1000
        """),
        {"ouid": org_unit_id},
    ).mappings().all()

    return {
        "org_unit": org_unit,
        "colleagues": [dict(c) for c in colleagues],
        "sub_units": [dict(s) for s in sub_units],
    }
