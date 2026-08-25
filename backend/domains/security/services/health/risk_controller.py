"""controllers.security.risk_controller (CONTROLLERS layer).

Wraps ``services.security.risk_service`` and exposes the risk-management
endpoints under both ``/api/v1/admin`` (admin) and ``/api/v1`` (public).

HTTP contract declared with ``infrastructure.routing.route_contract`` decorators
(stacked for the admin + public surfaces). The thin hand-written routers
(``admin_security_health.py`` / ``public_security_health.py``) are retained as
the authoritative routers and the auto-generator collision-skips these paths.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get, post

from domains.governance.services.risk.risk_service import detect_ghost_employees as _detect_ghost_employees
from domains.governance.services.risk.risk_service import detect_impossible_travel as _detect_impossible_travel
from domains.governance.services.risk.risk_service import get_audit_timeline as _get_audit_timeline
from domains.governance.services.risk.risk_service import get_team_health_radar as _get_team_health_radar
from domains.governance.services.risk.risk_service import update_flight_risk_score as _update_flight_risk_score

@get("/api/v1/admin/ghost-employees", deps=["db"], query=["threshold_days"], tags=["security-risk"])
@get("/api/v1/ghost-employees", deps=["db"], query=["threshold_days"], tags=["security-risk"])
def detect_ghost_employees(db: Session = None, threshold_days: int = 30):
    return _detect_ghost_employees(db, threshold_days)


@get("/api/v1/admin/impossible-travel", deps=["db"], query=["threshold_hours"], tags=["security-risk"])
@get("/api/v1/impossible-travel", deps=["db"], query=["threshold_hours"], tags=["security-risk"])
def detect_impossible_travel(db: Session = None, threshold_hours: int = 24):
    return _detect_impossible_travel(db, threshold_hours)


@post(
    "/api/v1/admin/{employee_id}/risk-score",
    deps=["db"],
    query=["metric", "score"],
    tags=["security-risk"],
)
@post(
    "/api/v1/{employee_id}/risk-score",
    deps=["db"],
    query=["metric", "score"],
    tags=["security-risk"],
)
def update_flight_risk_score(employee_id: int, metric: str = None, score: float = None, db: Session = None):
    return _update_flight_risk_score(employee_id, metric, score, db)


@get("/api/v1/admin/team-health/{manager_id}", deps=["db"], tags=["security-risk"])
@get("/api/v1/team-health/{manager_id}", deps=["db"], tags=["security-risk"])
def get_team_health_radar(manager_id: int, db: Session = None):
    return _get_team_health_radar(manager_id, db)


@get("/api/v1/admin/{employee_id}/audit-timeline", deps=["db"], query=["limit"], tags=["security-risk"])
@get("/api/v1/{employee_id}/audit-timeline", deps=["db"], query=["limit"], tags=["security-risk"])
def get_audit_timeline(employee_id: int, limit: int = 100, db: Session = None):
    return _get_audit_timeline(employee_id, db, limit)


__all__ = [
    "detect_ghost_employees",
    "detect_impossible_travel",
    "get_audit_timeline",
    "get_team_health_radar",
    "update_flight_risk_score",
]
