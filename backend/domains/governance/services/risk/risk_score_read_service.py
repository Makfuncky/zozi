"""Employee risk-score read service.

Owns the raw ``employee_risk_scores`` read query previously embedded (as
``text()`` SQL) in the admin/public security-health routers. Relocating the
raw SQL here keeps ``modules/*/routers`` Law-2 clean (no raw SQL in the HTTP
layer) while preserving the exact query semantics.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_employee_risk_scores(db: Session, employee_id: int) -> List[dict]:
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db.execute(
            text(
                """
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                WHERE employee_id = :eid
                ORDER BY recorded_at DESC
                """
            ),
            {"eid": employee_id},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                """
                SELECT employee_id, metric_name, score, recorded_at
                FROM employee_risk_scores
                ORDER BY recorded_at DESC
                LIMIT 200
                """
            )
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
