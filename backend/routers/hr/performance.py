"""Performance Management Router — OKRs, KPIs, 360° reviews, health board.
Wraps the performance_service functions as REST endpoints under the /hr prefix.
"""
from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from data.db import get_db
from utils.country_rls import enforce_country_access

logger = logging.getLogger(__name__)

router = APIRouter()


# ══════════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ══════════════════════════════════════════════════════════════════


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


class ReviewSubmit(BaseModel):
    employee_id: int
    reviewer_id: int
    review_type: str = Field(..., description="One of: self, manager, peer, subordinate")
    score: float = Field(..., ge=0, le=5, description="Score 0-5")
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None


class ObjectiveProgressUpdate(BaseModel):
    progress_pct: Optional[float] = None
    status: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
#  OKR Endpoints
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/okr", summary="Create an OKR objective")
def create_objective_endpoint(
    body: ObjectiveCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create an OKR objective at any cascade level (company → individual).
    Optionally accepts key_results to create KPIs in the same call.
    """
    from services.performance_service import create_objective
    try:
        result = create_objective(
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
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hr/okr/{objective_id}", summary="Get objective tree with children")
def get_objective_tree_endpoint(
    objective_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get an objective with all its child objectives (aligned cascade)."""
    from services.performance_service import get_objective_tree
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result


@router.patch("/hr/okr/{objective_id}/progress", summary="Update objective progress")
def update_objective_progress_endpoint(
    objective_id: int = Path(...),
    body: ObjectiveProgressUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update objective progress. Auto-computes from child KPIs if progress_pct not provided."""
    from services.performance_service import update_objective_progress
    return update_objective_progress(
        db, objective_id,
        progress_pct=body.progress_pct if body else None,
        status=body.status if body else None,
    )


# ══════════════════════════════════════════════════════════════════
#  KPI Endpoints
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/kpi", summary="Create a KPI metric under an objective")
def create_kpi_endpoint(
    body: KpiCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a KPI metric tied to an objective."""
    from services.performance_service import create_kpi_metric
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


@router.put("/hr/kpi/{kpi_id}/value", summary="Record a KPI value")
def record_kpi_value_endpoint(
    kpi_id: int = Path(...),
    body: KpiValueUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a new current value for a KPI metric and recalc objective progress."""
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    from services.performance_service import record_kpi_value
    return record_kpi_value(db, kpi_id, value=body.value, source=body.source)


@router.get("/hr/kpi/employee/{employee_id}", summary="Get KPI dashboard for an employee")
def get_kpi_dashboard_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all KPIs and objectives for an employee."""
    from services.performance_service import get_kpi_dashboard
    return get_kpi_dashboard(db, employee_id)


# ══════════════════════════════════════════════════════════════════
#  Performance Review Endpoints (360°)
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/reviews", summary="Submit a 360° performance review")
def submit_review_endpoint(
    body: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a 360° performance review entry (self, manager, peer, subordinate)."""
    from services.performance_service import submit_performance_review
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


@router.get("/hr/reviews/{employee_id}", summary="Get reviews for an employee")
def get_employee_reviews_endpoint(
    employee_id: int = Path(...),
    review_cycle: Optional[str] = Query(None, description="e.g. 2026-H1"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all reviews for an employee, grouped by review type."""
    from services.performance_service import get_employee_reviews
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)


# ══════════════════════════════════════════════════════════════════
#  Performance Health Endpoints
# ══════════════════════════════════════════════════════════════════


@router.get("/hr/health/{employee_id}", summary="Compute performance health for an employee")
def compute_health_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    from services.performance_service import compute_performance_health
    result = compute_performance_health(db, employee_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hr/{employee_id}/coi-check", summary="Run a conflict-of-interest check for an employee")
def coi_check_endpoint(
    employee_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Run a simple conflict-of-interest check by examining employee relations
    and shared departments. Returns any detected conflicts."""
    try:
        from data.models_employee_models import Employee, EmployeeRelation
    except Exception as exc:
        logger.warning("EmployeeRelation model not available: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    from sqlalchemy import or_

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    conflicts = []

    # Check employee relations for potential conflicts
    try:
        relations = (
            db.query(EmployeeRelation)
            .filter(
                or_(
                    EmployeeRelation.employee_id == employee_id,
                    EmployeeRelation.internal_employee_id == employee_id,
                )
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    except Exception as exc:
        logger.warning("EmployeeRelation query failed (table may not exist): %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    for rel in relations:
        other_id = (
            rel.internal_employee_id
            if rel.employee_id == employee_id
            else rel.employee_id
        )
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

    # Check if employee's manager is a relative
    if employee.reporting_manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.reporting_manager_id).first()
        if manager:
            for rel in relations:
                other_id = (
                    rel.internal_employee_id
                    if rel.employee_id == employee_id
                    else rel.employee_id
                )
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


@router.get("/hr/health-board", summary="Get performance health board for a manager's team")
def health_board_endpoint(
    manager_employee_id: int = Query(..., description="Manager's employee ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a performance health board for all subordinates of a manager."""
    from services.performance_service import get_performance_health_board
    return get_performance_health_board(db, manager_employee_id, department=department)
