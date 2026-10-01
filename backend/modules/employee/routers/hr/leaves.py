"""Leave and shifts sub-router — thin delegators (Law 2)."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from infrastructure.utils.country_rls import enforce_country_access
from domains.hr.services.hr_employee_service import get_hr_employee_service
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/admin/{code}/employees/leave-requests")
def list_leave_requests(code: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
                        db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_leave_requests(db, code, page=page, limit=limit)


@router.post("/admin/{code}/employees/leave-requests")
def create_leave_request(code: str, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    data = body or {}
    return get_hr_employee_service(db).create_leave_request(data.get("employee_id", 0), data, current_user, db)


@router.patch("/admin/{code}/employees/leave-requests/{leave_id}")
def update_leave_request_status(code: str, leave_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    enforce_country_access(code, db=db)
    status = (body or {}).get("status", "").lower()
    return get_hr_employee_service(db).update_leave_request_status(db, leave_id, status, current_user)


@router.get("/admin/{code}/employees/shifts")
def list_shifts(code: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_shifts(db, code, page=page, limit=limit)


@router.post("/admin/{code}/employees/shifts")
def create_shift_roster(code: str, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    data = body or {}
    return get_hr_employee_service(db).create_shift_roster(data.get("employee_id", 0), data, current_user, db)