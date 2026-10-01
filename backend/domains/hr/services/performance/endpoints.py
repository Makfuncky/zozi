"""Performance endpoint wrappers — Pydantic models and endpoint adapters."""

from __future__ import annotations

from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException


class KpiCreate(BaseModel):
    objective_id: int
    employee_id: int
    metric_name: str = Field(..., min_length=1, max_length=200)
    target_value: float
    unit: str = "number"
    weight: float = 1.0
    auto_source_query: Optional[str] = None


class KpiValueUpdate(BaseModel):
    value: float
    source: Optional[str] = None


class ObjectiveCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300, description="OKR objective title")
    cascade_level: str = Field(..., description="One of: company, department, team, individual")
    owner_employee_id: int = Field(..., description="Employee ID who owns this objective")
    quarter: Optional[str] = Field(None, description="e.g. Q1, Q2, Q3, Q4")
    year: Optional[int] = None
    parent_objective_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    description: Optional[str] = None
    key_results: Optional[List[Dict[str, Any]]] = None
    weight: float = 1.0


class ObjectiveProgressUpdate(BaseModel):
    progress_pct: Optional[float] = None
    status: Optional[str] = None


class ReviewSubmit(BaseModel):
    employee_id: int
    reviewer_id: int
    review_type: str = Field(..., description="One of: self, manager, peer, subordinate")
    score: float = Field(..., ge=0, le=5, description="Score 0-5")
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None


def coi_check_endpoint(employee_id: int, db: Session, current_user: dict):
    """Run a simple conflict-of-interest check."""
    try:
        from domains.hr.models.employee_models import Employee, EmployeeRelation
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("EmployeeRelation model not available: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    from sqlalchemy import or_
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    conflicts = []
    try:
        relations = (
            db.query(EmployeeRelation)
            .filter(or_(
                EmployeeRelation.employee_id == employee_id,
                EmployeeRelation.internal_employee_id == employee_id,
            ))
            .all()
        )
    except Exception as exc:
        logging.getLogger(__name__).warning("EmployeeRelation query failed: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    for rel in relations:
        other_id = rel.internal_employee_id if rel.employee_id == employee_id else rel.employee_id
        other = db.query(Employee).filter(Employee.id == other_id).first()
        if other and other.department and employee.department:
            if other.department == employee.department:
                conflicts.append({
                    "type": "same_department",
                    "employee_id": other.id,
                    "employee_code": other.employee_code,
                    "relation_type": rel.relation_type,
                    "description": f"{employee.employee_code} and {other.employee_code} are in the same department ({employee.department}) with a {rel.relation_type} relation",
                    "severity": "medium",
                })

    if employee.reporting_manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.reporting_manager_id).first()
        if manager:
            for rel in relations:
                other_id = rel.internal_employee_id if rel.employee_id == employee_id else rel.employee_id
                if other_id == manager.id:
                    conflicts.append({
                        "type": "manager_relation",
                        "employee_id": manager.id,
                        "employee_code": manager.employee_code,
                        "relation_type": rel.relation_type,
                        "description": f"{employee.employee_code}'s {rel.relation_type} ({manager.employee_code}) is their direct manager",
                        "severity": "high",
                    })

    return {
        "employee_id": employee_id,
        "employee_code": employee.employee_code,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
    }


def compute_health_endpoint(employee_id: int, db: Session, current_user: dict):
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    from domains.hr.services.performance.health import compute_performance_health
    result = compute_performance_health(db, employee_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


def create_kpi_endpoint(body: KpiCreate, db: Session, current_user: dict):
    """Create a KPI metric tied to an objective."""
    from domains.hr.services.performance.kpi import create_kpi_metric
    return create_kpi_metric(
        db=db,
        objective_id=body.objective_id,
        employee_id=body.employee_id,
        metric_name=body.metric_name,
        target_value=body.target_value,
        unit=body.unit,
        weight=body.weight,
        auto_source_query=body.auto_source_query,
    )


def create_objective_endpoint(body: ObjectiveCreate, db: Session, current_user: dict):
    """Create an OKR objective at any cascade level (company to individual)."""
    from domains.hr.services.performance.okr import create_objective
    try:
        return create_objective(
            db=db,
            title=body.title,
            cascade_level=body.cascade_level,
            owner_employee_id=body.owner_employee_id,
            quarter=body.quarter,
            year=body.year,
            parent_objective_id=body.parent_objective_id,
            org_unit_id=body.org_unit_id,
            description=body.description,
            key_results=body.key_results,
            weight=body.weight,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def get_employee_reviews_endpoint(employee_id: int, review_cycle: Optional[str], db: Session, current_user: dict):
    """Get all reviews for an employee, grouped by review type."""
    from domains.hr.services.performance.reviews import get_employee_reviews
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)


def get_kpi_dashboard_endpoint(employee_id: int, db: Session, current_user: dict):
    """Get all KPIs and objectives for an employee."""
    from domains.hr.services.performance.kpi import get_kpi_dashboard
    return get_kpi_dashboard(db, employee_id)


def get_objective_tree_endpoint(objective_id: int, db: Session, current_user: dict):
    """Get an objective with all its child objectives (aligned cascade)."""
    from domains.hr.services.performance.okr import get_objective_tree
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result


def health_board_endpoint(manager_employee_id: int, department: Optional[str], db: Session, current_user: dict):
    """Get a performance health board for all subordinates of a manager."""
    from domains.hr.services.performance.health import get_performance_health_board
    return get_performance_health_board(db, manager_employee_id, department=department)


def record_kpi_value_endpoint(kpi_id: int, body: KpiValueUpdate, db: Session, current_user: dict):
    """Record a new current value for a KPI metric and recalc objective progress."""
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    from domains.hr.services.performance.kpi import record_kpi_value
    return record_kpi_value(db, kpi_id, value=body.value, source=body.source)


def submit_review_endpoint(body: ReviewSubmit, db: Session, current_user: dict):
    """Submit a 360 degree performance review entry."""
    from domains.hr.services.performance.reviews import submit_performance_review
    try:
        return submit_performance_review(
            db=db,
            employee_id=body.employee_id,
            reviewer_id=body.reviewer_id,
            review_type=body.review_type,
            score=body.score,
            strengths=body.strengths,
            areas_for_improvement=body.areas_for_improvement,
            comments=body.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def update_objective_progress_endpoint(objective_id: int, body: ObjectiveProgressUpdate, db: Session, current_user: dict):
    """Update objective progress. Auto-computes from child KPIs if not provided."""
    from domains.hr.services.performance.okr import update_objective_progress
    return update_objective_progress(
        db, objective_id,
        progress_pct=body.progress_pct if body else None,
        status=body.status if body else None,
    )
