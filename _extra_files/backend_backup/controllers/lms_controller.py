"""Learning Management System Controller with Permission Locking."""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeTraining

from services.lms_write_service import (
    assign_training as _assign_training,
    create_training_module as _create_training_module,
    update_training_completion as _update_training_completion,
)


def create_training_module(module_data: dict, db: Session) -> dict:
    """Create a training module."""
    module = _create_training_module(
        db=db,
        title=module_data.get("title"),
        description=module_data.get("description"),
        required_for_role=module_data.get("required_role"),
        duration_minutes=module_data.get("duration_minutes", 30),
        is_active=module_data.get("is_active", True),
    )
    return {"module_id": module.module_id, "title": module.title}


def assign_training(employee_id: int, module_id: str, db: Session) -> dict:
    """Assign a training module to an employee."""
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    _assign_training(db=db, employee_id=employee_id, module_id=module_id)
    
    return {"employee_id": employee_id, "module_id": module_id, "status": "assigned"}


def verify_training_completion(
    employee_id: int,
    module_id: str,
    quiz_score: float,
    db: Session,
) -> dict:
    """Verify training completion and unlock permissions."""
    if quiz_score < 70:
        return {
            "status": "failed",
            "reason": "score_below_threshold",
            "score": quiz_score,
        }
    
    training = db.query(EmployeeTraining).filter(
        EmployeeTraining.employee_id == employee_id,
        EmployeeTraining.module_id == module_id
    ).first()
    
    if not training:
        return {
            "status": "failed",
            "reason": "training_not_found",
            "employee_id": employee_id,
            "module_id": module_id,
        }
    
    _update_training_completion(
        db=db,
        employee_training=training,
        quiz_score=quiz_score,
    )
    
    return {
        "employee_id": employee_id,
        "module_id": module_id,
        "status": "completed",
        "unlocked": True,
    }


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
        return {
            "locked": True,
            "reason": "training_incomplete",
            "required_role": result[0],
        }
    
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