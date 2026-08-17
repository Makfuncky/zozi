"""controllers.hr.okr_controller (CONTROLLERS layer).

Wraps ``services.hr.okr_engine`` and exposes the OKR endpoints. The HTTP
contract is declared with ``core.route_contract`` decorators so
``routers/generated/auto_router.py`` can auto-generate the thin router — the
previous hand-written ``routers/okr.py`` only instantiated the engine and
passed request bodies through, which is controller-level orchestration that
now lives here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.route_contract import get, post

from domains.hr.services.okr_engine import get_okr_engine

class ObjectiveCreate(BaseModel):
    employee_id: int
    title: str
    description: str
    key_results: List[Dict[str, Any]] = []
    period_start: str
    period_end: str

class KpiEvaluate(BaseModel):
    employee_id: int
    metric_query_hash: str
    target_value: float
    current_value: float

@post("/objectives", deps=["user", "db"], response_model=dict)
def create_objective(payload: ObjectiveCreate, current_user: dict, db: Session):
    """Create an OKR objective for an employee."""
    engine = get_okr_engine(db)
    return engine.create_objective(
        employee_id=payload.employee_id,
        title=payload.title,
        description=payload.description,
        key_results=payload.key_results,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )

@post("/evaluate", deps=["user", "db"], response_model=dict)
def evaluate_kpi(payload: KpiEvaluate, current_user: dict, db: Session):
    """Evaluate a KPI for an employee."""
    engine = get_okr_engine(db)
    return engine.evaluate_kpi(
        employee_id=payload.employee_id,
        metric_query_hash=payload.metric_query_hash,
        target_value=payload.target_value,
        current_value=payload.current_value,
    )

@get("/employee/{employee_id}", deps=["user", "db"], response_model=List[dict])
def get_employee_okrs(employee_id: int, current_user: dict, db: Session):
    """Return the OKRs for an employee."""
    engine = get_okr_engine(db)
    return engine.get_employee_okrs(employee_id)

__all__ = ["ObjectiveCreate", "KpiEvaluate", "create_objective", "evaluate_kpi", "get_employee_okrs"]
