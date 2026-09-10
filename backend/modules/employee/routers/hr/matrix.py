"""Matrix / dotted-line management sub-router — thin delegators (Law 2)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.hierarchy.hierarchy_service import (
    assign_matrix_manager,
    remove_matrix_manager,
    get_matrix_managers,
    get_matrix_subordinates,
    detect_circular_reporting,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.post("/matrix/assign")
def assign_matrix(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return assign_matrix_manager(db, employee_id=payload.get("employee_id", 0), matrix_manager_id=payload.get("matrix_manager_id", 0), relation_type=payload.get("relation_type", "matrix_manager"), notes=payload.get("notes"))


@router.delete("/matrix/{relation_id}")
def remove_matrix(relation_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.delete"))
):
    return remove_matrix_manager(db, relation_id)


@router.get("/employee/{employee_id}/matrix-managers")
def matrix_managers(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"matrix_managers": get_matrix_managers(db, employee_id)}


@router.get("/employee/{manager_id}/matrix-subordinates")
def matrix_subordinates(manager_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}


@router.get("/detect-circular")
def detect_circular(employee_id: int = Query(...), proposed_manager_id: int = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)
    return {"is_circular": is_circular, "message": "Circular reporting detected" if is_circular else "No circular relationship"}