"""LMS read service — DB read operations for training modules."""

from sqlalchemy.orm import Session
from sqlalchemy import text

from models.hr.employee_models import Employee, EmployeeTraining, TrainingModule


def check_permission_lock(db: Session, employee_id: int, permission: str) -> dict:
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


def get_training_progress(db: Session, employee_id: int) -> dict:
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


def get_training_module(db: Session, employee_id: int) -> dict:
    """Get training module by employee and permission."""
    query = db.query(TrainingModule).join(EmployeeTraining).filter(
        EmployeeTraining.employee_id == employee_id,
        TrainingModule.permission_key != None
    )
    modules = query.all()

    return {
        "modules": [
            {
                "module_id": m.module_id,
                "title": m.title,
                "required_for_role": m.required_for_role,
                "duration_minutes": m.duration_minutes,
                "is_active": m.is_active,
            }
            for m in modules
        ]
    }