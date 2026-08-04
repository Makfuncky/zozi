"""Learning Management System Controller with Permission Locking."""
from __future__ import annotations

from fastapi import HTTPException

from services.hr.lms_write_service import (
    create_training_module as create_training_module_svc,
    assign_training as assign_training_svc,
    update_training_completion,
    get_training_by_employee_module,
)
from services.hr.lms_read_service import (
    check_permission_lock as check_permission_lock_svc,
    get_training_progress as get_training_progress_svc,
)


def create_training_module(module_data: dict, db) -> dict:
    """Create a training module."""
    module = create_training_module_svc(
        db=db,
        title=module_data.get("title"),
        description=module_data.get("description"),
        required_for_role=module_data.get("required_role"),
        duration_minutes=module_data.get("duration_minutes", 30),
        is_active=module_data.get("is_active", True),
        permission_key=module_data.get("permission_key"),
    )

    return {"module_id": module.module_id, "title": module.title}


def assign_training(employee_id: int, module_id: str, db) -> dict:
    """Assign a training module to an employee."""
    try:
        training = assign_training_svc(db=db, employee_id=employee_id, module_id=module_id)
        return {"employee_id": employee_id, "module_id": module_id, "status": "assigned"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


def verify_training_completion(employee_id: int, module_id: str, quiz_score: float, db) -> dict:
    """Verify training completion and unlock permissions."""
    if quiz_score < 70:
        return {"status": "failed", "reason": "score_below_threshold", "score": quiz_score}

    training = get_training_by_employee_module(db, employee_id, module_id)

    if not training:
        raise HTTPException(status_code=404, detail="Training not found")

    training = update_training_completion(db, training, quiz_score)

    return {"employee_id": employee_id, "module_id": module_id, "status": "completed", "unlocked": True}


def check_permission_lock(employee_id: int, permission: str, db) -> dict:
    """Check if a permission is locked for an employee."""
    return check_permission_lock_svc(db=db, employee_id=employee_id, permission=permission)


def get_training_progress(employee_id: int, db) -> dict:
    """Get training progress for an employee."""
    return get_training_progress_svc(db=db, employee_id=employee_id)