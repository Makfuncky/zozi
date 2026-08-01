"""Learning Management System Controller with Permission Locking."""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from models.employee_models import Employee
from utils.datetime_utils import utcnow as _utcnow
from services.write_helpers import (
    commit_only,
)


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
    commit_only(db)
    
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
    commit_only(db)
    
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
    commit_only(db)
    
    return {"employee_id": employee_id, "module_id": module_id, "status": "completed", "unlocked": True}


def check_permission_lock(employee_id: int, permission: str, db: Session) -> dict:
    """Check if a permission is locked for an employee."""
    result = db.execute(text("""
        SELECT m.required_for_role, et.status
        FROM training_modules m
        JOIN employee_trainings et ON et.module_id = m.module_id
        WHERE m.permission_key = :perm AND et.employee_id = :eid
    """), {"perm": permission, "eid": employee_id}).fetchone()
    
    if not result:
        return {"locked": False, "reason": "no_requirement"}
    
    if result[1] != "completed":
        return {"locked": True, "reason": "training_incomplete", "required_role": result[0]}
    
    return {"locked": False, "reason": "training_completed"}


def get_training_progress(employee_id: int, db: Session) -> dict:
    """Get training progress for an employee."""
    progress = db.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
            AVG(score) as avg_score
        FROM employee_trainings et
        JOIN training_modules m ON m.module_id = et.module_id
        WHERE et.employee_id = :eid
    """), {"eid": employee_id}).fetchone()
    
    return {
        "total_modules": progress[0] or 0,
        "completed": progress[1] or 0,
        "completion_rate": round((progress[1] or 0) / (progress[0] or 1) * 100, 2),
        "avg_score": progress[2] or 0,
    }

