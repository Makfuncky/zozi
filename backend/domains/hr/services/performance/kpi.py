"""KPI Service — metrics, values, dashboards."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from infrastructure.utils.datetime_utils import utcnow as _utcnow
from domains.hr.services.performance.okr import update_objective_progress

logger = logging.getLogger(__name__)


def create_kpi_metric(
    db: Session,
    objective_id: int,
    employee_id: int,
    metric_name: str,
    target_value: float,
    unit: str = "number",
    weight: float = 1.0,
    auto_source_query: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a KPI metric tied to an objective."""
    metric_type = unit
    weight_pct = int(weight * 100)

    result = db.execute(
        text("""
            INSERT INTO kpi_metrics
                (objective_id, employee_id, metric_name, metric_type, target_value, current_value, weight_pct, auto_source_query)
            VALUES
                (:objective_id, :employee_id, :metric_name, :metric_type, :target_value, 0, :weight_pct, :auto_source)
            RETURNING id
        """),
        {
            "objective_id": objective_id,
            "employee_id": employee_id,
            "metric_name": metric_name,
            "metric_type": metric_type,
            "target_value": target_value,
            "weight_pct": weight_pct,
            "auto_source": auto_source_query,
        },
    )

    kpi_id = result.scalar()
    db.commit()
    return {"id": kpi_id, "metric_name": metric_name, "target_value": target_value}


def record_kpi_value(
    db: Session,
    kpi_id: int,
    value: float,
    source: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a new current value for a KPI metric and recalc objective progress."""
    db.execute(
        text("""
            UPDATE kpi_metrics
            SET current_value = :value,
                last_recorded_at = :now,
                source = COALESCE(:source, source)
            WHERE id = :id
        """),
        {"value": value, "now": _utcnow(), "source": source, "id": kpi_id},
    )

    kpi = db.execute(
        text("SELECT objective_id FROM kpi_metrics WHERE id = :id"),
        {"id": kpi_id},
    ).mappings().first()

    if kpi:
        update_objective_progress(db, kpi["objective_id"])

    db.commit()
    return {"kpi_id": kpi_id, "current_value": value}


def get_kpi_dashboard(db: Session, employee_id: int) -> Dict[str, Any]:
    """Get all KPIs and objectives for an employee."""
    objectives = db.execute(
        text("""
            SELECT id, title, objective_type as cascade_level, progress_pct, status, quarter, year
            FROM okr_objectives
            WHERE employee_id = :eid AND status = 'active'
            ORDER BY year DESC, quarter DESC
        """),
        {"eid": employee_id},
    ).mappings().all()

    objective_ids = [o["id"] for o in objectives]
    kpis_by_obj = {}

    if objective_ids:
        placeholders = ", ".join(f":oid{i}" for i in range(len(objective_ids)))
        params = {f"oid{i}": oid for i, oid in enumerate(objective_ids)}
        kpi_rows = db.execute(
            text(f"""
                SELECT objective_id, id, metric_name, target_value, current_value, metric_type as unit, weight_pct as weight, last_recorded_at
                FROM kpi_metrics
                WHERE objective_id IN ({placeholders})
                ORDER BY weight_pct DESC
            """),
            params,
        ).mappings().all()

        for k in kpi_rows:
            kpis_by_obj.setdefault(k["objective_id"], []).append(dict(k))

    result = []
    for obj in objectives:
        result.append({
            "objective": dict(obj),
            "kpis": kpis_by_obj.get(obj["id"], []),
        })

    return {"employee_id": employee_id, "objectives": result}
