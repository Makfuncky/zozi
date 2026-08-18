"""controllers.hr.lms_controller controller.

Coordinates LMS business rules and delegates ALL persistence to
``services.hr.lms_service``. It must not issue ``db.query`` directly
and must not perform commits.

The HTTP contract is declared with ``infrastructure.routing.route_contract`` decorators
so the auto-router emits ``routers/public_hr_lms.py``.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from infrastructure.routing.route_contract import get, post

from domains.hr.services.lms_service import (
    assign_training as service_assign_training,
    check_permission_lock as service_check_permission_lock,
    create_training_module as service_create_training_module,
    get_training_progress as service_get_training_progress,
    verify_training_completion as service_verify_training_completion,
)


@post("/modules", deps=["db"], tags=["lms"])
def create_training_module(module_data: dict, db: Session) -> dict:
    return service_create_training_module(module_data, db)


@post("/{employee_id}/assign", deps=["db"], query=["module_id"], tags=["lms"])
def assign_training(employee_id: int, db: Session, module_id: str = ...) -> dict:
    return service_assign_training(employee_id, module_id, db)


@post("/{employee_id}/complete", deps=["db"], query=["module_id", "quiz_score"], tags=["lms"])
def verify_training_completion(employee_id: int, db: Session, module_id: str = ..., quiz_score: float = ...) -> dict:
    return service_verify_training_completion(employee_id, module_id, quiz_score, db)


@get("/{employee_id}/lock/{permission}", deps=["db"], tags=["lms"])
def check_permission_lock(employee_id: int, permission: str, db: Session) -> dict:
    return service_check_permission_lock(employee_id, permission, db)


@get("/{employee_id}/progress", deps=["db"], tags=["lms"])
def get_training_progress(employee_id: int, db: Session) -> dict:
    return service_get_training_progress(employee_id, db)
