"""Learning Management System sub-router — thin delegators to lms_service."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.learning.lms_service import (
    assign_training as _assign_training_svc,
    check_permission_lock,
    create_training_module,
    get_training_progress,
    verify_training_completion,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.post("/modules")
def create_module(module_data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return create_training_module(module_data, db)


@router.post("/{employee_id}/assign")
def lms_assign_training(employee_id: int, module_id: str = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return _assign_training_svc(employee_id, module_id, db)


@router.post("/{employee_id}/complete")
def complete_training(employee_id: int, module_id: str = Query(...), quiz_score: float = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return verify_training_completion(employee_id, module_id, quiz_score, db)


@router.get("/{employee_id}/lock/{permission}")
def check_lock(employee_id: int, permission: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return check_permission_lock(employee_id, permission, db)


@router.get("/{employee_id}/progress")
def training_progress(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_training_progress(employee_id, db)