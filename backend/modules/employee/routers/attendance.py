"""Employee HR — Attendance domain router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from infrastructure.utils.country_rls import enforce_country_access
from rbac.dependencies import require_feature

from domains.hr.services.hr_employee_service import get_hr_employee_service

router = APIRouter()


@router.get("/admin/{code}/employees/{employee_id}/attendance")
def list_attendance(
    code: str,
    employee_id: int,
    from_date: str = Query(None),
    to_date: str = Query(None),
    limit: int = Query(50, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read")),
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_attendance(
        employee_id, db, from_date=from_date, to_date=to_date, limit=limit
    )


@router.post("/admin/{code}/employees/{employee_id}/check-in")
def check_in(
    code: str,
    employee_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create")),
):
    return get_hr_employee_service(db).check_in_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/check-out")
def check_out(
    code: str,
    employee_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create")),
):
    return get_hr_employee_service(db).check_out_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/geo-check-in")
def geo_check_in(
    code: str,
    employee_id: int,
    body: dict = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create")),
):
    return get_hr_employee_service(db).check_in_with_geo(employee_id, body or {}, db)
