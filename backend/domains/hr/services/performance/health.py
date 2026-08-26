"""Performance Health Scoring — composite health scores and boards."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional, Dict, Any, List

from sqlalchemy.orm import Session
from sqlalchemy import text

from domains.hr.models.employee_models import Employee
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


def compute_performance_health(
    db: Session,
    employee_id: int,
) -> Dict[str, Any]:
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return {"error": "Employee not found"}

    review_score = employee.performance_score or 0.0
    review_health = min(review_score / 5.0, 1.0)

    kpis = db.execute(
        text("""
            SELECT target_value, current_value FROM kpi_metrics
            WHERE employee_id = :eid
        """),
        {"eid": employee_id},
    ).mappings().all()

    kpi_attainment = 0.0
    if kpis:
        kpi_attainment = sum(
            min(k["current_value"] / k["target_value"], 1.0) if k["target_value"] > 0 else 0
            for k in kpis
        ) / len(kpis)

    recent_attendance = db.execute(
        text("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalies
            FROM employee_attendance
            WHERE employee_id = :eid
              AND date >= :since
        """),
        {"eid": employee_id, "since": date.today().replace(day=1)},
    ).mappings().first()

    attendance_health = 1.0
    if recent_attendance and recent_attendance["total"] > 0:
        anomaly_rate = recent_attendance["anomalies"] / recent_attendance["total"]
        attendance_health = max(0, 1.0 - anomaly_rate)

    objectives = db.execute(
        text("""
            SELECT progress_pct FROM okr_objectives
            WHERE employee_id = :eid AND status = 'active'
        """),
        {"eid": employee_id},
    ).mappings().all()

    obj_health = 0.0
    if objectives:
        obj_health = sum(o["progress_pct"] for o in objectives) / (len(objectives) * 100)

    composite = (
        review_health * 0.40 +
        kpi_attainment * 0.30 +
        attendance_health * 0.15 +
        obj_health * 0.15
    )

    if composite >= 0.80:
        color = "green"
        label = "High Performer"
    elif composite >= 0.55:
        color = "amber"
        label = "Meeting Expectations"
    else:
        color = "red"
        label = "Needs Improvement"

    return {
        "employee_id": employee_id,
        "composite_score": round(composite * 100, 1),
        "color": color,
        "label": label,
        "signals": {
            "review_score": round(review_health * 100, 1),
            "kpi_attainment": round(kpi_attainment * 100, 1),
            "attendance_health": round(attendance_health * 100, 1),
            "objective_progress": round(obj_health * 100, 1),
        },
    }


def get_performance_health_board(
    db: Session,
    manager_employee_id: int,
    department: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get a performance health board for all subordinates of a manager."""
    from domains.hr.hierarchy_service import get_all_subordinates as get_subs

    user = db.query(Employee).filter(Employee.id == manager_employee_id).first()
    if not user:
        return []

    subs = get_subs(db, user.user_id)
    result = []

    for sub in subs:
        if department and sub.get("department") != department:
            continue
        health = compute_performance_health(db, sub["id"])
        health["employee_code"] = sub["employee_code"]
        health["department"] = sub["department"]
        health["position"] = sub["position"]
        result.append(health)

    result.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return result
