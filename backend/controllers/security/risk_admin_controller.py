"""Thin orchestration controller for employee risk / flight-risk admin reads.

The ``routers.admin_security_health`` router delegates to this controller so it
stays within the allowed circuit (routers -> controllers/schemas/auth-deps only).
The raw parameterized SQL read for ``employee_risk_scores`` lives here (the
controller layer owns DB access); the query is fully parameterized.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.db_read import execute as db_read_execute


def get_risk_scores(db: Session, employee_id: int) -> list[dict]:
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db_read_execute(
            db,
            text(
                "SELECT employee_id, metric_name, score, recorded_at "
                "FROM employee_risk_scores "
                "WHERE employee_id = :eid "
                "ORDER BY recorded_at DESC"
            ),
            {"eid": employee_id},
        ).fetchall()
    else:
        rows = db_read_execute(
            db,
            text(
                "SELECT employee_id, metric_name, score, recorded_at "
                "FROM employee_risk_scores "
                "ORDER BY recorded_at DESC "
                "LIMIT 200"
            ),
        ).fetchall()
    return [
        {
            "employee_id": r[0],
            "metric_name": r[1],
            "score": float(r[2]) if r[2] is not None else None,
            "recorded_at": (r[3].isoformat() if not isinstance(r[3], str) else r[3]) if r[3] else None,
        }
        for r in rows
    ]
