"""OKR Service — objectives, cascade, progress tracking."""

from __future__ import annotations

import logging
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from domains.accounts.models.user import User
from domains.hr.models.employee_models import Employee
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

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
    """Create an OKR objective at any cascade level (company to individual)."""
    now = _utcnow()
    q = quarter or f"Q{(now.month - 1) // 3 + 1}"
    y = year or now.year

    if cascade_level not in OKR_CASCADE_LEVELS:
        raise ValueError(f"Invalid cascade level: {cascade_level}. Must be one of {OKR_CASCADE_LEVELS}")

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

    if key_results:
        kpi_params = [
            {
                "objective_id": objective_id,
                "employee_id": owner_employee_id,
                "metric_name": kr.get("name", "Key Result"),
                "metric_type": kr.get("unit", "percent"),
                "target_value": kr.get("target", 100),
                "weight_pct": int(kr.get("weight", 1.0) * 100),
                "auto_source": kr.get("auto_source_query"),
            }
            for kr in key_results
        ]

        db.execute(
            text("""
                INSERT INTO kpi_metrics
                    (objective_id, employee_id, metric_name, metric_type, target_value, current_value, weight_pct, auto_source_query)
                VALUES
                    (:objective_id, :employee_id, :metric_name, :metric_type, :target_value, 0, :weight_pct, :auto_source)
            """),
            kpi_params,
        )

    db.commit()
    logger.info("Objective %s created: %s (level=%s)", objective_id, title, cascade_level)

    try:
        from domains.hr.services.employee_activity_logger import log_activity
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
        pass

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

    tree = dict(objective)
    tree["children"] = []

    owner_ids = [c["owner_employee_id"] for c in children]
    emp_by_id = {}

    if owner_ids:
        emp_rows = db.query(Employee).filter(Employee.id.in_(owner_ids)).all()
        for e in emp_rows:
            emp_by_id[e.id] = e

    for child in children:
        emp = emp_by_id.get(child["owner_employee_id"])
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

    obj = db.execute(
        text("SELECT parent_objective_id FROM okr_objectives WHERE id = :id"),
        {"id": objective_id},
    ).mappings().first()

    if obj and obj["parent_objective_id"]:
        update_objective_progress(db, obj["parent_objective_id"])

    db.commit()
    return {"id": objective_id, "progress_pct": progress_pct, "status": status or "active"}
