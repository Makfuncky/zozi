"""Employee security router — thin HTTP surface delegating to security services."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from rbac.dependencies import require_feature
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from domains.security.services.health.flat_risk_service import (
    detect_ghost_employees,
    detect_impossible_travel,
    get_audit_timeline,
    get_team_health_radar,
    update_flight_risk_score,
)
from domains.security.services.risk_service import get_risk_scores


router = APIRouter(prefix="/api/v1/employee/security", tags=["employee", "security"])


@router.get("/{employee_id}/risk-score")
def get_risk_score(employee_id: int, db: Session = Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    require_feature("security.events.read")
    return get_risk_scores(db, employee_id)


@router.get("/ghost-employees")
def ghost_employees(threshold_days: int = Query(30), db: Session = Depends(get_db)):
    require_feature("security.events.read")
    return {"ghost_employees": detect_ghost_employees(db, threshold_days)}


@router.get("/impossible-travel")
def impossible_travel(threshold_hours: int = Query(24), db: Session = Depends(get_db)):
    require_feature("security.events.read")
    return {"impossible_travels": detect_impossible_travel(db, threshold_hours)}


@router.post("/{employee_id}/risk-score")
def update_risk(employee_id: int, metric: str = Query(...), score: float = Query(...), db: Session = Depends(get_db)):
    require_feature("security.events.manage")
    return update_flight_risk_score(employee_id, metric, score, db)


@router.get("/team-health/{manager_id}")
def team_health(manager_id: int, db: Session = Depends(get_db)):
    require_feature("security.events.read")
    return get_team_health_radar(manager_id, db)


@router.get("/{employee_id}/audit-timeline")
def audit_timeline(employee_id: int, limit: int = Query(100), db: Session = Depends(get_db)):
    require_feature("security.events.read")
    return get_audit_timeline(employee_id, db, limit)


# ── Public surface (migrated from domains/security/services/health/risk_controller) ──
public_router = APIRouter(prefix="/api/v1", tags=["public", "security-risk"])


@public_router.get("/ghost-employees")
def public_ghost_employees(
    threshold_days: int = Query(30, ge=1, le=365),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("security.events.read")
    return detect_ghost_employees(db, threshold_days)


@public_router.get("/impossible-travel")
def public_impossible_travel(
    threshold_hours: int = Query(24, ge=1, le=168),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("security.events.read")
    return detect_impossible_travel(db, threshold_hours)


@public_router.post("/{employee_id}/risk-score")
def public_update_flight_risk_score(
    employee_id: int,
    metric: str = Query(...),
    score: float = Query(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("security.events.manage")
    return update_flight_risk_score(employee_id, metric, score, db)


@public_router.get("/team-health/{manager_id}")
def public_team_health(
    manager_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("security.events.read")
    return get_team_health_radar(manager_id, db)


@public_router.get("/{employee_id}/audit-timeline")
def public_audit_timeline(
    employee_id: int,
    limit: int = Query(100, ge=1, le=500),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    require_feature("security.events.read")
    return get_audit_timeline(employee_id, db, limit)
