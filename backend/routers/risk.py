"""Risk Management Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from controllers.risk_controller import (
    detect_ghost_employees, detect_impossible_travel,
    update_flight_risk_score, get_team_health_radar, get_audit_timeline
)
from services.security.risk_service import get_risk_score
from data.db import get_db

router = APIRouter()


@router.get("/{employee_id}/risk-score")
def get_risk_score_route(employee_id: int, db: Session = Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    return get_risk_score(employee_id, db)


@router.get("/ghost-employees")
def ghost_employees(threshold_days: int = Query(30), db: Session = Depends(get_db)):
    return {"ghost_employees": detect_ghost_employees(db, threshold_days)}


@router.get("/impossible-travel")
def impossible_travel(threshold_hours: int = Query(24), db: Session = Depends(get_db)):
    return {"impossible_travels": detect_impossible_travel(db, threshold_hours)}


@router.post("/{employee_id}/risk-score")
def update_risk(employee_id: int, metric: str = Query(...), score: float = Query(...), db: Session = Depends(get_db)):
    return update_flight_risk_score(employee_id, metric, score, db)


@router.get("/team-health/{manager_id}")
def team_health(manager_id: int, db: Session = Depends(get_db)):
    return get_team_health_radar(manager_id, db)


@router.get("/{employee_id}/audit-timeline")
def audit_timeline(employee_id: int, limit: int = Query(100), db: Session = Depends(get_db)):
    return get_audit_timeline(employee_id, db, limit)

