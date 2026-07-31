"""LMS write service — DB write operations for training modules."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from models.employee_models import Employee, EmployeeTraining, TrainingModule


def create_training_module(
    db: Session,
    title: str,
    description: Optional[str] = None,
    required_for_role: Optional[str] = None,
    duration_minutes: int = 30,
    is_active: bool = True,
    permission_key: Optional[str] = None,
) -> TrainingModule:
    module_id = str(hash(title))
    module = TrainingModule(
        module_id=module_id,
        title=title,
        description=description,
        required_for_role=required_for_role,
        duration_minutes=duration_minutes,
        is_active=is_active,
        permission_key=permission_key,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def assign_training(
    db: Session,
    employee_id: int,
    module_id: str,
) -> EmployeeTraining:
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise ValueError("Employee not found")
    
    training = EmployeeTraining(
        employee_id=employee_id,
        module_id=module_id,
        status="assigned",
        assigned_at=datetime.now(timezone.utc),
    )
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


def update_training_completion(
    db: Session,
    employee_training: EmployeeTraining,
    quiz_score: float,
) -> EmployeeTraining:
    if quiz_score < 70:
        employee_training.status = "failed"
        employee_training.score = quiz_score
        db.commit()
        db.refresh(employee_training)
        return employee_training
    
    employee_training.status = "completed"
    employee_training.score = quiz_score
    employee_training.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(employee_training)
    return employee_training


def delete_training_module(db: Session, module: TrainingModule) -> None:
    db.delete(module)
    db.commit()