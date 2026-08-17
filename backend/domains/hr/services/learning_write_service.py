"""Learning Management System write service.

Owns the DB write operations for the LMS (training module creation, training
assignment, completion verification). Moved out of controllers/lms_controller.py
to satisfy the W1 layer contract (routers/controllers must not write to the DB).
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from _legacy.models.employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow


def create_training_module(module_data: dict, db: Session) -> dict:
    """Create a training module."""
    module_id = str(hash(module_data.get("title")))

    db.execute(text("""
        INSERT INTO training_modules (module_id, title, description, required_for_role, duration_minutes, is_active)
        VALUES (:mid, :title, :desc, :role, :dur, :active)
    """), {
        "mid": module_id,
        "title": module_data.get("title"),
        "desc": module_data.get("description"),
        "role": module_data.get("required_role"),
        "dur": module_data.get("duration_minutes", 30),
        "active": module_data.get("is_active", True),
    })
    db.commit()

    return {"module_id": module_id, "title": module_data.get("title")}


def assign_training(employee_id: int, module_id: str, db: Session) -> dict:
    """Assign a training module to an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    db.execute(text("""
        INSERT INTO employee_trainings (employee_id, module_id, assigned_at, status)
        VALUES (:eid, :mid, :now, 'assigned')
    """), {"eid": employee_id, "mid": module_id, "now": _utcnow()})
    db.commit()

    return {"employee_id": employee_id, "module_id": module_id, "status": "assigned"}


def verify_training_completion(employee_id: int, module_id: str, quiz_score: float, db: Session) -> dict:
    """Verify training completion and unlock permissions."""
    if quiz_score < 70:
        return {"status": "failed", "reason": "score_below_threshold", "score": quiz_score}

    db.execute(text("""
        UPDATE employee_trainings
        SET status = 'completed', score = :score, completed_at = :now
        WHERE employee_id = :eid AND module_id = :mid
    """), {"score": quiz_score, "now": _utcnow(), "eid": employee_id, "mid": module_id})
    db.commit()

    return {"employee_id": employee_id, "module_id": module_id, "status": "completed", "unlocked": True}
