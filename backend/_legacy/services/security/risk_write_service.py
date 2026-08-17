"""Risk management write service.

Owns the DB write operations for risk management (flight-risk / burnout score
updates). Moved out of controllers/risk_controller.py to satisfy the W1 layer
contract (routers/controllers must not write to the DB).
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.datetime_utils import utcnow as _utcnow


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
