"""HR and Compliance Controller for GCC labor law adherence."""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeRelation
from domains.hr.models.employee_models import EmployeeAddress
from domains.hr.models.employee_models import EmployeeDependent
from domains.hr.models.employee_models import COIReport
from domains.governance.models.user import User


def register_address(employee_id: int, address_data: dict, db: Session) -> dict:
    """Register a multi-dimensional address for an employee."""
    from domains.hr.models.employee_models import EmployeeAddress
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    addr = EmployeeAddress(employee_id=employee_id, **address_data)
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return {"id": addr.id, "address_type": addr.address_type, "is_primary": addr.is_primary}


def register_dependent(employee_id: int, dependent_data: dict, db: Session) -> dict:
    """Register a dependent for an employee."""
    from domains.hr.models.employee_models import EmployeeDependent
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    dep = EmployeeDependent(employee_id=employee_id, **dependent_data)
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return {"id": dep.id, "name": dep.name, "relation": dep.relation}


def check_coi_conflict(employee_id: int, db: Session) -> list[dict]:
    """Check for conflicts of interest in the employee's relationship graph."""
    conflicts = []
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        return conflicts
    
    relations = db.query(EmployeeRelation).filter(
        ((EmployeeRelation.employee_id == employee_id) | (EmployeeRelation.internal_employee_id == employee_id))
    ).all()
    
    for rel in relations:
        other_id = rel.internal_employee_id if rel.employee_id == employee_id else rel.employee_id
        other = db.query(Employee).filter(Employee.id == other_id).first()
        if other:
            if rel.is_internal_employee and other.employment_status == "active":
                conflicts.append({
                    "internal_employee_id": other_id,
                    "relation_type": rel.relation_type,
                    "risk": "internal_conflict",
                })
    return conflicts


def create_coi_report(employee_id: int, report_data: dict, db: Session) -> dict:
    """Create a COI report for an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    report = COIReport(
        employee_id=employee_id,
        related_person_name=report_data.get("related_person_name"),
        relation_type=report_data.get("relation_type"),
        is_internal=report_data.get("is_internal", False),
        internal_employee_id=report_data.get("internal_employee_id"),
        risk_level=report_data.get("risk_level", "low"),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "risk_level": report.risk_level, "is_approved": report.is_approved}


def validate_gcc_compliance(employee_id: int, db: Session) -> dict:
    """Validate GCC compliance for an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    issues = []
    if not emp.gender:
        issues.append({"type": "missing_gender", "severity": "warning"})
    if not emp.hire_date:
        issues.append({"type": "missing_hire_date", "severity": "error"})
    
    return {"compliant": len(issues) == 0, "issues": issues}


def get_employee_graph(employee_id: int, db: Session) -> dict:
    """Get the full relationship graph for an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    nodes = [{"id": emp.id, "name": emp.employee_code, "type": "employee"}]
    edges = []
    
    relations = db.query(EmployeeRelation).filter(
        (EmployeeRelation.employee_id == employee_id) | (EmployeeRelation.internal_employee_id == employee_id)
    ).all()
    
    for rel in relations:
        other_id = rel.internal_employee_id if rel.employee_id == employee_id else rel.employee_id
        nodes.append({"id": other_id, "type": "employee", "relation": rel.relation_type})
        edges.append({"source": employee_id, "target": other_id, "type": rel.relation_type})
    
    return {"nodes": nodes, "edges": edges}

def create_disciplinary_case(employee_id: int, case_data: dict, db: Session) -> dict:
    """Create a disciplinary case for an employee."""
    from domains.hr.models.employee_models import DisciplinaryCase
    from domains.hr.models.employee_models import Employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    case = DisciplinaryCase(
        employee_id=employee_id,
        employee_name=emp.employee_code,
        stage=case_data.get("stage", "verbal_warning"),
        description=case_data.get("description", ""),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"id": case.id, "stage": case.stage, "status": case.status}


def get_disciplinary_cases(db: Session) -> list[dict]:
    """Get all disciplinary cases."""
    from domains.hr.models.employee_models import DisciplinaryCase
    cases = db.query(DisciplinaryCase).all()
    return [{"id": c.id, "employee_id": c.employee_id, "employee_name": c.employee_name, "stage": c.stage, "description": c.description, "issued_at": str(c.issued_at), "status": c.status} for c in cases]


def create_offboarding_case(employee_id: int, case_data: dict, db: Session) -> dict:
    """Initiate offboarding for an employee."""
    from domains.hr.models.employee_models import OffboardingCase
    from domains.hr.models.employee_models import Employee
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    case = OffboardingCase(
        employee_id=employee_id,
        employee_name=emp.employee_code,
        reason=case_data.get("reason", "resignation"),
        notes=case_data.get("notes"),
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"id": case.id, "reason": case.reason, "status": case.status}


def get_offboarding_cases(db: Session) -> list[dict]:
    """Get all offboarding cases."""
    from domains.hr.models.employee_models import OffboardingCase
    cases = db.query(OffboardingCase).all()
    return [{"id": c.id, "employee_id": c.employee_id, "employee_name": c.employee_name, "reason": c.reason, "status": c.status, "initiated_at": str(c.initiated_at), "completed_at": str(c.completed_at) if c.completed_at else None} for c in cases]

# === Merged from accounts/services/hr_service.py ===

def add_address(employee_id: int, address_data: dict, db: Session):

    return register_address(employee_id, address_data, db)




def add_dependent(employee_id: int, dependent_data: dict, db: Session):

    return register_dependent(employee_id, dependent_data, db)




def add_disciplinary(case_data: dict, db: Session):

    employee_id = case_data.get("employee_id")

    if not employee_id:

        raise HTTPException(status_code=400, detail="employee_id required")

    return create_disciplinary_case(employee_id, case_data, db)




def add_offboarding(case_data: dict, db: Session):

    employee_id = case_data.get("employee_id")

    if not employee_id:

        raise HTTPException(status_code=400, detail="employee_id required")

    return create_offboarding_case(employee_id, case_data, db)




def check_coi(employee_id: int, db: Session):

    return {"conflicts": check_coi_conflict(employee_id, db)}




def check_compliance(employee_id: int, db: Session):

    return validate_gcc_compliance(employee_id, db)




def create_coi(employee_id: int, report_data: dict, db: Session):

    return create_coi_report(employee_id, report_data, db)




def create_hse_incident(incident: dict, db: Session):

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

    db.commit()

    return {"message": "HSE incident recorded", "employee_id": employee_id}




def get_graph(employee_id: int, db: Session):

    return get_employee_graph(employee_id, db)




def list_alumni(db: Session):

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




def list_disciplinary(db: Session):

    return get_disciplinary_cases(db)




def list_hse_incidents(db: Session):

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




def list_offboarding(db: Session):

    return get_offboarding_cases(db)



