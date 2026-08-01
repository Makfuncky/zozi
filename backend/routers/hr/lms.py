"""Learning Management System Router."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from controllers.lms_controller import (
    create_training_module, assign_training, verify_training_completion,
    check_permission_lock, get_training_progress
)
from db.database import get_db

router = APIRouter()


@router.post("/modules")
def create_module(module_data: dict, db: Session = Depends(get_db)):
    return create_training_module(module_data, db)


@router.post("/{employee_id}/assign")
def assign_training(employee_id: int, module_id: str = Query(...), db: Session = Depends(get_db)):
    return assign_training(employee_id, module_id, db)


@router.post("/{employee_id}/complete")
def complete_training(employee_id: int, module_id: str = Query(...), quiz_score: float = Query(...), db: Session = Depends(get_db)):
    return verify_training_completion(employee_id, module_id, quiz_score, db)


@router.get("/{employee_id}/lock/{permission}")
def check_lock(employee_id: int, permission: str, db: Session = Depends(get_db)):
    return check_permission_lock(employee_id, permission, db)


@router.get("/{employee_id}/progress")
def training_progress(employee_id: int, db: Session = Depends(get_db)):
    return get_training_progress(employee_id, db)
