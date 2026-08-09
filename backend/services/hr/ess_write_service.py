"""ESS (Employee Self-Service) write operations.

Owns the DB writes for employee profile updates and leave requests. These
use raw SQL on the ``employees`` / ``leave_requests`` tables and are moved
here from the ESS router so the router stays a read-only orchestration
surface.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from data.models_employee_models import Employee
from data.services_employee_activity_logger import log_activity
import structlog
logger = structlog.get_logger(__name__)


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
