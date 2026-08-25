"""HR risk-score read service.

Owns the employee risk-score query previously embedded as raw ``text()`` SQL in
``modules/employee/routers/risk.py``.

The legacy SQL referenced a pre-migration schema (``metric_name`` /
``recorded_at``) that no longer exists. The live ``hr.employee_risk_scores``
table (Alembic ``2026_08_06_0007``) uses ``assessment_date`` + ``risk_level``.
We read through the ORM model so the router stays Law-2 clean and the response
reflects the real columns.
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from domains.hr.models.employee_models import EmployeeRiskScore


def get_employee_risk_scores(db: Session, employee_id: Optional[int] = None) -> List[dict]:
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    stmt = select(EmployeeRiskScore)
    if employee_id and employee_id != 0:
        stmt = stmt.where(EmployeeRiskScore.employee_id == employee_id)
        stmt = stmt.order_by(desc(EmployeeRiskScore.assessment_date))
    else:
        stmt = stmt.order_by(desc(EmployeeRiskScore.assessment_date)).limit(200)

    rows = db.execute(stmt).scalars().all()
    return [
        {
            "employee_id": r.employee_id,
            "assessment_date": r.assessment_date.isoformat() if r.assessment_date else None,
            "score": float(r.score) if r.score is not None else None,
            "risk_level": r.risk_level,
            "country_code": r.country_code,
        }
        for r in rows
    ]


def update_employee_risk_score(employee_id: int, metric: str, score: float, db: Session):
    """Persist a flight-risk score.

    Delegates to the rbac ``update_flight_risk_score`` hook so the router does
    not own the write. (The rbac implementation is currently a ``_noop`` stub;
    behaviour is preserved until the real scorer is wired in.)
    """
    from rbac import update_flight_risk_score

    return update_flight_risk_score(employee_id, metric, score, db)
