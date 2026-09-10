"""OKR / KPI / Performance reviews sub-router — thin delegators."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.perf_service import (
    create_objective as svc_create_objective,
    get_objective_tree,
    update_objective_progress as svc_update_objective_progress,
    create_kpi_metric,
    record_kpi_value,
    get_kpi_dashboard,
    submit_performance_review,
    get_employee_reviews,
    compute_performance_health,
    get_performance_health_board,
)
from domains.hr.services.hr_employee_service import get_hr_employee_service
from rbac.dependencies import require_feature

router = APIRouter()


@router.post("/hr/okr", summary="Create an OKR objective")
def create_objective_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    try:
        return svc_create_objective(db=db, **body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/hr/okr/{objective_id}", summary="Get objective tree with children")
def get_objective_tree_endpoint(objective_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result


@router.patch("/hr/okr/{objective_id}/progress", summary="Update objective progress")
def update_objective_progress_endpoint(objective_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    return svc_update_objective_progress(db, objective_id, **(body or {}))


@router.post("/hr/kpi", summary="Create a KPI metric under an objective")
def create_kpi_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return create_kpi_metric(db=db, **body)


@router.put("/hr/kpi/{kpi_id}/value", summary="Record a KPI value")
def record_kpi_value_endpoint(kpi_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    return record_kpi_value(db, kpi_id, **body)


@router.get("/hr/kpi/employee/{employee_id}", summary="Get KPI dashboard for an employee")
def get_kpi_dashboard_endpoint(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_kpi_dashboard(db, employee_id)


@router.post("/hr/reviews", summary="Submit a 360 performance review")
def submit_review_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    try:
        return submit_performance_review(db=db, **body)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request")


@router.get("/hr/reviews/{employee_id}", summary="Get reviews for an employee")
def get_employee_reviews_endpoint(employee_id: int, review_cycle: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)


@router.get("/hr/health/{employee_id}", summary="Compute performance health for an employee")
def compute_health_endpoint(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    result = compute_performance_health(db, employee_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hr/{employee_id}/coi-check", summary="Run a conflict-of-interest check for an employee")
def coi_check_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read")),
):
    return get_hr_employee_service(db).coi_check(employee_id)


@router.get("/hr/health-board", summary="Get performance health board for a manager's team")
def health_board_endpoint(manager_employee_id: int = Query(...), department: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_performance_health_board(db, manager_employee_id, department=department)