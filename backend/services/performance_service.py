"""Performance Management Service — OKR/KPI cascade, 360° reviews, performance health scoring.
Leverages the gap-table migration: okr_objectives, kpi_metrics, performance_reviews.
"""
from __future__ import annotations

__all__ = [
    "create_objective",
    "get_objective_tree",
    "update_objective_progress",
    "create_kpi_metric",
    "record_kpi_value",
    "get_kpi_dashboard",
    "submit_performance_review",
    "get_employee_reviews",
    "compute_performance_health",
    "get_performance_health_board",
]

import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text, func, desc

from models import Employee, User
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
#  OKR Service
# ════════════════════════════════════════════════════════════════

OKR_CASCADE_LEVELS = ["company", "department", "team", "individual"]


def create_objective(
    db: Session,
    title: str,
    cascade_level: str,
    owner_employee_id: int,
    quarter: str = None,
    year: int = None,
    parent_objective_id: Optional[int] = None,
    org_unit_id: Optional[int] = None,
    description: Optional[str] = None,
    key_results: Optional[List[Dict[str, Any]]] = None,
    weight: float = 1.0,
) -> Dict[str, Any]:
    """Create an OKR objective at any cascade level (company → individual).
    If parent_objective_id is provided, validates alignment with parent.
    """
    now = _utcnow()
    q = quarter or f"Q{(now.month - 1) // 3 + 1}"
    y = year or now.year

    # Validate cascade level
    if cascade_level not in OKR_CASCADE_LEVELS:
        raise ValueError(f"Invalid cascade level: {cascade_level}. Must be one of {OKR_CASCADE_LEVELS}")

    # If parent provided, ensure valid cascade hierarchy
    if parent_objective_id:
        parent = db.execute(
            text("SELECT objective_type as cascade_level FROM okr_objectives WHERE id = :id"),
            {"id": parent_objective_id},
        ).mappings().first()
        if parent:
            parent_idx = OKR_CASCADE_LEVELS.index(parent["cascade_level"])
            child_idx = OKR_CASCADE_LEVELS.index(cascade_level)
            if child_idx <= parent_idx:
                raise ValueError(
                    f"Cascade level '{cascade_level}' must be deeper than parent '{parent['cascade_level']}'"
                )

    quarter_value = f"{y}-{q}"
    result = db.execute(
        text("""
            INSERT INTO okr_objectives
                (title, description, objective_type, employee_id, parent_objective_id,
                 org_unit_id, quarter, year, progress_pct, status, created_by, created_at)
            VALUES
                (:title, :description, :objective_type, :employee_id, :parent_objective_id,
                 :org_unit_id, :quarter, :year, 0, 'active', :created_by, :now)
            RETURNING id
        """),
        {
            "title": title,
            "description": description,
            "objective_type": cascade_level,
            "employee_id": owner_employee_id,
            "parent_objective_id": parent_objective_id,
            "org_unit_id": org_unit_id,
            "quarter": quarter_value,
            "year": y,
            "created_by": owner_employee_id,
            "now": now,
        },
    )
    objective_id = result.scalar()

    # Add key results if provided
    if key_results:
        for kr in key_results:
            kr_weight_pct = int(kr.get("weight", 1.0) * 100)
            db.execute(
                text("""
                    INSERT INTO kpi_metrics
                        (objective_id, employee_id, metric_name, metric_type, target_value, current_value, weight_pct, auto_source_query)
                    VALUES
                        (:objective_id, :employee_id, :metric_name, :metric_type, :target_value, 0, :weight_pct, :auto_source)
                """),
                {
                    "objective_id": objective_id,
                    "employee_id": owner_employee_id,
                    "metric_name": kr.get("name", "Key Result"),
                    "metric_type": kr.get("unit", "percent"),
                    "target_value": kr.get("target", 100),
                    "weight_pct": kr_weight_pct,
                    "auto_source": kr.get("auto_source_query"),
                },
            )

    db.commit()
    logger.info("Objective %s created: %s (level=%s)", objective_id, title, cascade_level)

    # Log activity for the HR dashboard feed
    try:
        from services.employee_activity_logger import log_activity
        log_activity(
            db=db,
            actor_employee_id=owner_employee_id,
            action="created_objective",
            entity_type="okr_objective",
            entity_id=str(objective_id),
            country_code=None,
            metadata_json={"title": title, "cascade_level": cascade_level, "quarter": quarter_value},
        )
    except Exception:
        pass  # Best-effort

    return {"id": objective_id, "title": title, "cascade_level": cascade_level, "quarter": quarter_value}


def get_objective_tree(db: Session, objective_id: int) -> Dict[str, Any]:
    """Get an objective with all its child objectives (aligned cascade)."""
    objective = db.execute(
        text("""
            SELECT id, title, description, objective_type as cascade_level, employee_id as owner_employee_id,
                   parent_objective_id, org_unit_id, quarter, year, progress_pct, status
            FROM okr_objectives WHERE id = :id
        """),
        {"id": objective_id},
    ).mappings().first()

    if not objective:
        return {}

    children = db.execute(
        text("""
            SELECT id, title, objective_type as cascade_level, employee_id as owner_employee_id, progress_pct, status
            FROM okr_objectives WHERE parent_objective_id = :parent_id AND status = 'active'
            ORDER BY created_at ASC
        """),
        {"parent_id": objective_id},
    ).mappings().all()

    # Recursively build tree
    tree = dict(objective)
    tree["children"] = []
    for child in children:
        # Get employee name
        emp = db.query(Employee).filter(Employee.id == child["owner_employee_id"]).first()
        child_dict = dict(child)
        child_dict["owner_name"] = emp.employee_code if emp else None
        tree["children"].append(get_objective_tree(db, child["id"]))

    return tree


def update_objective_progress(
    db: Session,
    objective_id: int,
    progress_pct: Optional[float] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Update objective progress. Auto-computes from child KPIs if not provided."""
    if progress_pct is None:
        # Auto-compute from KPI metrics
        kpis = db.execute(
            text("""            SELECT target_value, current_value, weight_pct FROM kpi_metrics
                WHERE objective_id = :oid
        """),
        {"oid": objective_id},
    ).mappings().all()

        if kpis and sum(k["weight_pct"] for k in kpis) > 0:
            total_weight = sum(k["weight_pct"] for k in kpis)
            weighted_progress = sum(
                (min(k["current_value"] / k["target_value"], 1.0) if k["target_value"] > 0 else 0) * k["weight_pct"]
                for k in kpis
            )
            progress_pct = round((weighted_progress / total_weight) * 100, 1)
        else:
            progress_pct = 0

    updates = {"progress_pct": progress_pct}
    if status:
        updates["status"] = status

    db.execute(
        text("""
            UPDATE okr_objectives
            SET progress_pct = :progress,
                status = COALESCE(:status, status),
                updated_at = :now
            WHERE id = :id
        """),
        {"progress": progress_pct, "status": status, "now": _utcnow(), "id": objective_id},
    )

    # Cascade progress up to parent
    obj = db.execute(
        text("SELECT parent_objective_id FROM okr_objectives WHERE id = :id"),
        {"id": objective_id},
    ).mappings().first()
    if obj and obj["parent_objective_id"]:
        update_objective_progress(db, obj["parent_objective_id"])

    db.commit()
    return {"id": objective_id, "progress_pct": progress_pct, "status": status or "active"}


# ════════════════════════════════════════════════════════════════
#  KPI Service
# ════════════════════════════════════════════════════════════════

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
    # Map unit to metric_type for DB schema compatibility
    metric_type = unit  # 'number', 'percentage', 'currency', 'boolean', 'rating'
    weight_pct = int(weight * 100)  # Convert 0-1 weight to 0-100 pct for DB

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

    # Get the objective ID for this KPI and recalculate progress
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

    result = []
    for obj in objectives:
        kpis = db.execute(
            text("""
                SELECT id, metric_name, target_value, current_value, metric_type as unit, weight_pct as weight, last_recorded_at
                FROM kpi_metrics
                WHERE objective_id = :oid
                ORDER BY weight_pct DESC
            """),
            {"oid": obj["id"]},
        ).mappings().all()

        result.append({
            "objective": dict(obj),
            "kpis": [dict(k) for k in kpis],
        })

    return {"employee_id": employee_id, "objectives": result}


# ════════════════════════════════════════════════════════════════
#  Performance Review Service (360°)
# ════════════════════════════════════════════════════════════════

REVIEW_TYPES = ["self", "manager", "peer", "subordinate"]
REVIEW_RATING_LABELS = {
    1: "Needs Improvement",
    2: "Below Expectations",
    3: "Meets Expectations",
    4: "Exceeds Expectations",
    5: "Outstanding",
}


def submit_performance_review(
    db: Session,
    employee_id: int,
    reviewer_id: int,
    review_type: str,
    score: float,
    strengths: Optional[str] = None,
    areas_for_improvement: Optional[str] = None,
    comments: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a 360° performance review entry."""
    if review_type not in REVIEW_TYPES:
        raise ValueError(f"Invalid review type: {review_type}. Must be one of {REVIEW_TYPES}")
    if score < 0 or score > 5:
        raise ValueError("Score must be between 0 and 5")

    review_cycle = f"{_utcnow().year}-H{1 if _utcnow().month <= 6 else 2}"

    result = db.execute(
        text("""
            INSERT INTO performance_reviews
                (employee_id, reviewer_id, review_type, overall_score, strengths,
                 areas_for_improvement, comments, review_cycle, status, submitted_at)
            VALUES
                (:employee_id, :reviewer_id, :review_type, :score, :strengths,
                 :areas, :comments, :review_cycle, 'submitted', :now)
            RETURNING id
        """),
        {
            "employee_id": employee_id,
            "reviewer_id": reviewer_id,
            "review_type": review_type,
            "score": score,
            "strengths": strengths,
            "areas": areas_for_improvement,
            "comments": comments,
            "review_cycle": review_cycle,
            "now": _utcnow(),
        },
    )
    review_id = result.scalar()

    # Auto-update employee performance_score
    _recompute_employee_score(db, employee_id)

    db.commit()

    # Log activity for the HR dashboard feed
    try:
        from services.employee_activity_logger import log_activity
        log_activity(
            db=db,
            actor_employee_id=reviewer_id,
            action="submitted_review",
            entity_type="performance_review",
            entity_id=str(review_id),
            target_employee_id=employee_id,
            country_code=None,
            metadata_json={"score": score, "review_type": review_type},
        )
    except Exception:
        pass  # Best-effort

    return {"id": review_id, "score": score, "type": review_type}


def get_employee_reviews(
    db: Session,
    employee_id: int,
    review_cycle: Optional[str] = None,
) -> Dict[str, Any]:
    """Get all reviews for an employee, grouped by review type."""
    query = """
        SELECT id, employee_id, reviewer_id, review_type,
               overall_score as score, strengths, areas_for_improvement,
               comments, review_cycle, status, submitted_at, acknowledged_at
        FROM performance_reviews WHERE employee_id = :eid
    """
    params = {"eid": employee_id}
    if review_cycle:
        query += " AND review_cycle = :cycle"
        params["cycle"] = review_cycle

    reviews = db.execute(text(query + " ORDER BY submitted_at DESC"), params).mappings().all()

    grouped: Dict[str, list] = {"self": [], "manager": [], "peer": [], "subordinate": []}
    for r in reviews:
        rtype = r["review_type"]
        if rtype in grouped:
            grouped[rtype].append(dict(r))

    # Compute average
    all_scores = [r["score"] for r in reviews if r["score"] is not None]
    avg_score = round(sum(all_scores) / len(all_scores), 2) if all_scores else None

    return {
        "employee_id": employee_id,
        "avg_score": avg_score,
        "review_count": len(reviews),
        "reviews": grouped,
    }


def _recompute_employee_score(db: Session, employee_id: int) -> None:
    """Recompute the employee's overall performance_score from all reviews."""
    result = db.execute(
        text("""
            SELECT
                AVG(CASE WHEN review_type = 'self' THEN overall_score ELSE NULL END) as self_score,
                AVG(CASE WHEN review_type = 'manager' THEN overall_score ELSE NULL END) as manager_score,
                AVG(CASE WHEN review_type = 'peer' THEN overall_score ELSE NULL END) as peer_score,
                AVG(CASE WHEN review_type = 'subordinate' THEN overall_score ELSE NULL END) as sub_score
            FROM performance_reviews
            WHERE employee_id = :eid AND status = 'submitted'
        """),
        {"eid": employee_id},
    ).mappings().first()

    if not result:
        return

    # Weighted average: manager 40%, self 20%, peer 25%, subordinate 15%
    weights = {"self_score": 0.20, "manager_score": 0.40, "peer_score": 0.25, "subordinate_score": 0.15}
    weighted_sum = 0.0
    total_weight = 0.0
    for field, weight in weights.items():
        val = result[field]
        if val is not None:
            weighted_sum += val * weight
            total_weight += weight

    if total_weight > 0:
        final_score = round(weighted_sum / total_weight, 2)
        db.execute(
            text("UPDATE employees SET performance_score = :score WHERE id = :eid"),
            {"score": final_score, "eid": employee_id},
        )


# ════════════════════════════════════════════════════════════════
#  Performance Health Scoring
# ════════════════════════════════════════════════════════════════

def compute_performance_health(
    db: Session,
    employee_id: int,
) -> Dict[str, Any]:
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return {"error": "Employee not found"}

    # 1. Review score (weight: 40%)
    review_score = employee.performance_score or 0.0
    review_health = min(review_score / 5.0, 1.0)  # Normalize to 0-1

    # 2. KPI attainment (weight: 30%)
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

    # 3. Attendance (weight: 15%)
    recent_attendance = db.execute(
        text("""
            SELECT COUNT(*) as total, SUM(CASE WHEN is_anomaly THEN 1 ELSE 0 END) as anomalies
            FROM employee_attendance
            WHERE employee_id = :eid
              AND date >= :since
        """),
        {"eid": employee_id, "since": date.today().replace(day=1)},  # Current month
    ).mappings().first()
    attendance_health = 1.0
    if recent_attendance and recent_attendance["total"] > 0:
        anomaly_rate = recent_attendance["anomalies"] / recent_attendance["total"]
        attendance_health = max(0, 1.0 - anomaly_rate)

    # 4. Objective progress (weight: 15%)
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

    # Weighted composite
    composite = (
        review_health * 0.40 +
        kpi_attainment * 0.30 +
        attendance_health * 0.15 +
        obj_health * 0.15
    )

    # Determine color band
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
    from services.hierarchy_service import get_all_subordinates as get_subs
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

    # Sort by composite score descending
    result.sort(key=lambda x: x.get("composite_score", 0), reverse=True)
    return result
