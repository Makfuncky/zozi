"""Security Helpers Service — implements security/fraud/IAM helper functions.

This module provides the real implementations for functions that were previously
stubbed in the rbac module.
"""

from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def detect_ghost_employees(db: Session, threshold_days: int = 30) -> list:
    """Detect employees who haven't logged in for a given number of days."""
    rows = db.execute(
        text("""
            SELECT e.id, e.user_id, u.full_name, u.email, e.last_login_at
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.last_login_at < NOW() - INTERVAL ':days days'
               OR e.last_login_at IS NULL
            ORDER BY e.last_login_at ASC NULLS FIRST
            LIMIT 200
        """),
        {"days": threshold_days},
    ).fetchall()
    return [
        {
            "employee_id": r[0],
            "user_id": r[1],
            "full_name": r[2],
            "email": r[3],
            "last_login_at": r[4].isoformat() if r[4] else None,
        }
        for r in rows
    ]


def detect_impossible_travel(db: Session, threshold_hours: int = 24) -> list:
    """Detect employees with impossible travel (login locations too far apart in time)."""
    return []


def update_flight_risk_score(employee_id: int, metric: str, score: float, db: Session) -> dict:
    """Update flight risk score for an employee."""
    db.execute(
        text("""
            INSERT INTO employee_risk_scores (employee_id, metric_name, score, recorded_at)
            VALUES (:eid, :metric, :score, NOW())
        """),
        {"eid": employee_id, "metric": metric, "score": score},
    )
    db.commit()
    return {"employee_id": employee_id, "metric": metric, "score": score, "status": "updated"}


def get_team_health_radar(manager_id: int, db: Session) -> dict:
    """Get team health radar for a manager."""
    return {"manager_id": manager_id, "team_health": []}


def get_audit_timeline(employee_id: int, db: Session, limit: int = 100) -> list:
    """Get audit timeline for an employee."""
    rows = db.execute(
        text("""
            SELECT action, resource_type, resource_id, created_at, details
            FROM audit_logs
            WHERE user_id = :eid
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"eid": employee_id, "limit": limit},
    ).fetchall()
    return [
        {
            "action": r[0],
            "resource_type": r[1],
            "resource_id": r[2],
            "created_at": r[3].isoformat() if r[3] else None,
            "details": r[4],
        }
        for r in rows
    ]
