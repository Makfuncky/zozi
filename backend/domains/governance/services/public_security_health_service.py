"""Risk Management Router."""
from __future__ import annotations
from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from rbac import detect_ghost_employees
from rbac import detect_impossible_travel
from rbac import update_flight_risk_score
from rbac import get_team_health_radar
from rbac import get_audit_timeline
from infrastructure.database.database import get_db

def get_risk_score(employee_id: int, db: Session=Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db.execute(text('\n                SELECT employee_id, metric_name, score, recorded_at\n                FROM employee_risk_scores\n                WHERE employee_id = :eid\n                ORDER BY recorded_at DESC\n            '), {'eid': employee_id}).fetchall()
    else:
        rows = db.execute(text('\n                SELECT employee_id, metric_name, score, recorded_at\n                FROM employee_risk_scores\n                ORDER BY recorded_at DESC\n                LIMIT 200\n            ')).fetchall()
    return [{'employee_id': r[0], 'metric_name': r[1], 'score': float(r[2]) if r[2] is not None else None, 'recorded_at': (r[3].isoformat() if not isinstance(r[3], str) else r[3]) if r[3] else None} for r in rows]
