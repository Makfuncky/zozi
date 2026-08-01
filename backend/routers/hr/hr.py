"""HR and Compliance Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.employee_models import Employee, AlumniNetwork
from controllers.hr.hr_controller import (
    register_address, register_dependent, check_coi_conflict,
    create_coi_report, validate_gcc_compliance, get_employee_graph,
    create_disciplinary_case, get_disciplinary_cases,
    create_offboarding_case, get_offboarding_cases
)
from db.database import get_db
from dependencies.auth import get_current_user

from services.write_helpers import commit_only
router = APIRouter()


@router.post("/{employee_id}/addresses")
def add_address(employee_id: int, address_data: dict, db: Session = Depends(get_db)):
    return register_address(employee_id, address_data, db)


@router.post("/{employee_id}/dependents")
def add_dependent(employee_id: int, dependent_data: dict, db: Session = Depends(get_db)):
    return register_dependent(employee_id, dependent_data, db)


@router.get("/{employee_id}/coi-check")
def check_coi(employee_id: int, db: Session = Depends(get_db)):
    return {"conflicts": check_coi_conflict(employee_id, db)}


@router.post("/{employee_id}/coi-report")
def create_coi(employee_id: int, report_data: dict, db: Session = Depends(get_db)):
    return create_coi_report(employee_id, report_data, db)


@router.get("/{employee_id}/compliance")
def check_compliance(employee_id: int, db: Session = Depends(get_db)):
    return validate_gcc_compliance(employee_id, db)


@router.get("/{employee_id}/graph")
def get_graph(employee_id: int, db: Session = Depends(get_db)):
    return get_employee_graph(employee_id, db)

@router.get("/disciplinary")
def list_disciplinary(db: Session = Depends(get_db)):
    return get_disciplinary_cases(db)


@router.post("/disciplinary")
def add_disciplinary(case_data: dict, db: Session = Depends(get_db)):
    employee_id = case_data.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    return create_disciplinary_case(employee_id, case_data, db)


@router.get("/offboarding")
def list_offboarding(db: Session = Depends(get_db)):
    return get_offboarding_cases(db)


@router.post("/offboarding")
def add_offboarding(case_data: dict, db: Session = Depends(get_db)):
    employee_id = case_data.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    return create_offboarding_case(employee_id, case_data, db)


@router.get("/alumni")
def list_alumni(db: Session = Depends(get_db)):
    """Return the alumni network records (employee offboarding rehire pool)."""
    rows = (
        db.query(AlumniNetwork, Employee)
        .join(Employee, Employee.id == AlumniNetwork.employee_id)
        .all()
    )
    return [
        {
            "id": a.id,
            "employee_id": a.employee_id,
            "full_name": getattr(emp, "full_name", None) or getattr(emp, "name", None)
            or getattr(emp, "employee_code", None),
            "reason": a.notes or a.status,
            "end_date": (a.eligibility_expires_at or a.granted_at).isoformat()
            if (a.eligibility_expires_at or a.granted_at)
            else None,
            "status": a.status,
        }
        for a, emp in rows
    ]


@router.get("/hse/incidents")
def list_hse_incidents(db: Session = Depends(get_db)):
    rows = db.execute(
        text("""
            SELECT i.id, i.employee_id, e.employee_code, i.incident_type,
                   i.description, i.date_occurred, i.severity, i.status
            FROM hse_incidents i
            LEFT JOIN employees e ON e.id = i.employee_id
            ORDER BY i.created_at DESC
        """)
    ).fetchall()
    return [
        {
            "id": r[0],
            "employee_id": r[1],
            "employee_name": r[2],
            "incident_type": r[3],
            "description": r[4],
            "date_occurred": r[5],
            "severity": r[6],
            "status": r[7],
        }
        for r in rows
    ]


@router.post("/hse/incidents")
def create_hse_incident(incident: dict, db: Session = Depends(get_db)):
    employee_id = incident.get("employee_id")
    if not employee_id:
        raise HTTPException(status_code=400, detail="employee_id required")
    db.execute(
        text("""
            INSERT INTO hse_incidents
                (employee_id, incident_type, description, date_occurred, severity, status, created_at)
            VALUES (:eid, :itype, :desc, :docc, :sev, :status, :created)
        """),
        {
            "eid": employee_id,
            "itype": incident.get("incident_type", "near_miss"),
            "desc": incident.get("description", ""),
            "docc": incident.get("date_occurred"),
            "sev": incident.get("severity", "low"),
            "status": incident.get("status", "open"),
            "created": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).replace(tzinfo=None),
        },
    )
    commit_only(db)
    return {"message": "HSE incident recorded", "employee_id": employee_id}


