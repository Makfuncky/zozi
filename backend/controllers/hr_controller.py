"""HR and Compliance Controller for GCC labor law adherence."""
from __future__ import annotations
from datetime import datetime, date
from typing import Optional
from collections import defaultdict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeRelation, EmployeeAddress, EmployeeDependent, COIReport
from models import User


def register_address(employee_id: int, address_data: dict, db: Session) -> dict:
    """Register a multi-dimensional address for an employee."""
    from models.employee_models import EmployeeAddress
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
    from models.employee_models import EmployeeDependent
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
    from models.employee_models import DisciplinaryCase, Employee
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
    from models.employee_models import DisciplinaryCase
    cases = db.query(DisciplinaryCase).all()
    return [{"id": c.id, "employee_id": c.employee_id, "employee_name": c.employee_name, "stage": c.stage, "description": c.description, "issued_at": str(c.issued_at), "status": c.status} for c in cases]


def create_offboarding_case(employee_id: int, case_data: dict, db: Session) -> dict:
    """Initiate offboarding for an employee."""
    from models.employee_models import OffboardingCase, Employee
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
    from models.employee_models import OffboardingCase
    cases = db.query(OffboardingCase).all()
    return [{"id": c.id, "employee_id": c.employee_id, "employee_name": c.employee_name, "reason": c.reason, "status": c.status, "initiated_at": str(c.initiated_at), "completed_at": str(c.completed_at) if c.completed_at else None} for c in cases]

