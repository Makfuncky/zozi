"""HR write service — DB write operations for HR-specific entities."""
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from data.models_employee_models import (
    COIReport,
    DisciplinaryCase,
    EmployeeAddress,
    EmployeeDependent,
    EmployeeRiskScore,
    OffboardingCase,
)


def create_employee_address(
    db: Session,
    employee_id: int,
    address_type: str,
    street: str,
    city: str,
    country_code: str,
    state: Optional[str] = None,
    postal_code: Optional[str] = None,
    is_primary: bool = False,
) -> EmployeeAddress:
    addr = EmployeeAddress(
        employee_id=employee_id,
        address_type=address_type,
        street=street,
        city=city,
        country_code=country_code,
        state=state,
        postal_code=postal_code,
        is_primary=is_primary,
    )
    db.add(addr)
    db.commit()
    db.refresh(addr)
    return addr


def create_employee_dependent(
    db: Session,
    employee_id: int,
    name: str,
    relation: str,
    is_insured: bool = False,
    dob: Optional[datetime] = None,
) -> EmployeeDependent:
    dep = EmployeeDependent(
        employee_id=employee_id,
        name=name,
        relation=relation,
        is_insured=is_insured,
        dob=dob,
    )
    db.add(dep)
    db.commit()
    db.refresh(dep)
    return dep


def create_coi_report(
    db: Session,
    employee_id: int,
    related_person_name: str,
    relation_type: str,
    is_internal: bool = False,
    internal_employee_id: Optional[int] = None,
    risk_level: str = "low",
) -> COIReport:
    report = COIReport(
        employee_id=employee_id,
        related_person_name=related_person_name,
        relation_type=relation_type,
        is_internal=is_internal,
        internal_employee_id=internal_employee_id,
        risk_level=risk_level,
        is_approved=False,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def create_disciplinary_case(
    db: Session,
    employee_id: int,
    employee_name: str,
    stage: str = "verbal_warning",
    description: str = "",
) -> DisciplinaryCase:
    case = DisciplinaryCase(
        employee_id=employee_id,
        employee_name=employee_name,
        stage=stage,
        description=description,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def create_offboarding_case(
    db: Session,
    employee_id: int,
    employee_name: str,
    reason: str = "resignation",
    notes: Optional[str] = None,
) -> OffboardingCase:
    case = OffboardingCase(
        employee_id=employee_id,
        employee_name=employee_name,
        reason=reason,
        notes=notes,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def upsert_employee_risk_score(
    db: Session,
    employee_id: int,
    metric_name: str,
    score: float,
    recorded_at: Optional[datetime] = None,
) -> EmployeeRiskScore:
    from utils.datetime_utils import utcnow as _utcnow
    
    if recorded_at is None:
        recorded_at = _utcnow()
    
    db.execute(text("""
        INSERT INTO employee_risk_scores (employee_id, metric_name, score, recorded_at)
        VALUES (:emp_id, :metric, :score, :recorded_at)
        ON CONFLICT (employee_id, metric_name)
        DO UPDATE SET score = :score, recorded_at = :recorded_at
    """), {
        "emp_id": employee_id,
        "metric": metric_name,
        "score": score,
        "recorded_at": recorded_at,
    })
    db.commit()
    
    risk_score = db.query(EmployeeRiskScore).filter(
        EmployeeRiskScore.employee_id == employee_id,
        EmployeeRiskScore.metric_name == metric_name,
    ).first()
    return risk_score