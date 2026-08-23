"""LMS write operations: training modules and employee training assignments."""
from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from infrastructure.utils.datetime_utils import utcnow as _utcnow
from domains.hr.models.employee_models import EmployeeTraining
from domains.hr.models.employee_models import TrainingModule
import structlog
logger = structlog.get_logger(__name__)


def create_training_module(
    db: Session,
    *,
    title: str,
    description: Optional[str] = None,
    required_for_role: Optional[str] = None,
    duration_minutes: int = 30,
    is_active: bool = True,
) -> TrainingModule:
    module = TrainingModule(
        module_id=str(uuid.uuid4()),
        title=title,
        description=description,
        required_for_role=required_for_role,
        duration_minutes=duration_minutes,
        is_active=is_active,
    )
    db.add(module)
    db.commit()
    db.refresh(module)
    return module


def assign_training(db: Session, *, employee_id: int, module_id: str) -> EmployeeTraining:
    training = EmployeeTraining(
        employee_id=employee_id,
        module_id=module_id,
        status="assigned",
    )
    db.add(training)
    db.commit()
    db.refresh(training)
    return training


def update_training_completion(
    db: Session, *, employee_training: EmployeeTraining, quiz_score: float
) -> EmployeeTraining:
    employee_training.completed_at = _utcnow()
    employee_training.score = quiz_score
    employee_training.status = "completed"
    db.commit()
    db.refresh(employee_training)
    return employee_training
