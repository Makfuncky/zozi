"""Risk Management Controller for Fraud Detection and Telemetry."""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from models.employee_models import Employee, EmployeeAttendance, GeoFenceLog, EmployeeRelation, COIReport
from utils.datetime_utils import utcnow as _utcnow


def detect_ghost_employees(db: Session, threshold_days: int = 30) -> list[dict]:
    """Detect employees with no activity for threshold days."""
    cutoff = _utcnow() - timedelta(days=threshold_days)
    
    ghosts = db.execute(text("""
        SELECT e.id, e.employee_code, e.department, e.position, e.employment_status
        FROM employees e
        LEFT JOIN employee_attendance ea ON ea.employee_id = e.id 
            AND ea.date >= :cutoff_date
        WHERE e.employment_status = 'active'
        AND (ea.id IS NULL OR e.updated_at < :cutoff)
        ORDER BY e.created_at DESC
    """), {"cutoff_date": cutoff.date(), "cutoff": cutoff}).fetchall()
    
    return [{"id": g[0], "employee_code": g[1], "department": g[2], "position": g[3], "status": g[4]} for g in ghosts]


def detect_impossible_travel(db: Session, threshold_hours: int = 24) -> list[dict]:
    """Detect employees with impossible travel patterns (SQLite-compatible)."""
    travels = db.execute(text("""
        WITH base AS (
            SELECT
                employee_id,
                latitude,
                longitude,
                scanned_at,
                LAG(scanned_at) OVER (PARTITION BY employee_id ORDER BY scanned_at) as prev_scan
            FROM geo_fence_logs
            WHERE scanned_at >= :since
        ),
        travel AS (
            SELECT
                employee_id,
                latitude,
                longitude,
                scanned_at,
                prev_scan,
                CASE
                    WHEN prev_scan IS NOT NULL
                    THEN (julianday(scanned_at) - julianday(prev_scan)) * 24
                    ELSE 0
                END as hours_diff
            FROM base
        )
        SELECT
            employee_id,
            scanned_at,
            hours_diff,
            latitude,
            longitude
        FROM travel
        WHERE hours_diff < :threshold AND hours_diff > 0
    """), {"since": _utcnow() - timedelta(days=7), "threshold": threshold_hours}).fetchall()

    return [
        {
            "employee_id": t[0],
            "timestamp": (t[1].isoformat() if not isinstance(t[1], str) else t[1]) if t[1] else None,
            "hours_diff": float(t[2]),
            "location": [t[3], t[4]],
        }
        for t in travels
    ]


def update_flight_risk_score(employee_id: int, metric: str, score: float, db: Session) -> dict:
    """Update flight risk/burnout score for an employee."""
    db.execute(text("""
        INSERT INTO employee_risk_scores (employee_id, metric_name, score, recorded_at)
        VALUES (:emp_id, :metric, :score, :now)
        ON CONFLICT (employee_id, metric_name) 
        DO UPDATE SET score = :score, recorded_at = :now
    """), {"emp_id": employee_id, "metric": metric, "score": score, "now": _utcnow()})
    db.commit()
    
    return {"employee_id": employee_id, "metric": metric, "score": score}


def get_team_health_radar(manager_id: int, db: Session) -> dict:
    """Get team health radar for a manager."""
    # Get all subordinates
    subordinates = db.execute(text("""
        SELECT id FROM employees WHERE reporting_manager_id = :mgr_id
    """), {"mgr_id": manager_id}).fetchall()
    
    emp_ids = [s[0] for s in subordinates]
    if not emp_ids:
        return {"burnout_score": 0, "flight_risk_score": 0, "engagement_score": 0}
    
    scores = db.execute(text("""
        SELECT metric_name, AVG(score) as avg_score
        FROM employee_risk_scores
        WHERE employee_id IN :emp_ids
        GROUP BY metric_name
    """), {"emp_ids": tuple(emp_ids)}).fetchall()
    
    result = {"burnout_score": 0, "flight_risk_score": 0, "engagement_score": 0}
    for s in scores:
        if s[0] in result:
            result[s[0]] = float(s[1])
    
    return result


def get_audit_timeline(employee_id: int, db: Session, limit: int = 100) -> list[dict]:
    """Get immutable audit timeline for an employee."""
    events = db.execute(text("""
        SELECT event_type, event_data, actor_id, ip_address, user_agent, created_at
        FROM employee_audit_timeline
        WHERE employee_id = :emp_id
        ORDER BY created_at DESC
        LIMIT :limit
    """), {"emp_id": employee_id, "limit": limit}).fetchall()
    
    return [{
        "event_type": e[0],
        "event_data": e[1],
        "actor_id": e[2],
        "ip_address": e[3],
        "user_agent": e[4],
        "created_at": (e[5].isoformat() if not isinstance(e[5], str) else e[5]) if e[5] else None,
    } for e in events]

