"""Performance Review Service — 360 degree reviews, scoring."""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import text

from domains.hr.models.employee_models import Employee
from infrastructure.utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

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
    """Submit a 360 degree performance review entry."""
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
    _recompute_employee_score(db, employee_id)
    db.commit()

    try:
        from domains.hr.services.employee_activity_logger import log_activity
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
        pass

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
        query += " AND review_cycle = :review_cycle"
        params["review_cycle"] = review_cycle

    reviews = db.execute(text(query + " ORDER BY submitted_at DESC"), params).mappings().all()

    grouped: Dict[str, list] = {"self": [], "manager": [], "peer": [], "subordinate": []}
    for r in reviews:
        rtype = r["review_type"]
        if rtype in grouped:
            grouped[rtype].append(dict(r))

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
