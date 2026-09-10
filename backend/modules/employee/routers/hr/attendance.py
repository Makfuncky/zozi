"""Attendance, work-logs, relations, QR-IAM, geo — thin delegators (Law 2)."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from infrastructure.utils.country_rls import enforce_country_access
from domains.hr.services.hr_employee_service import get_hr_employee_service
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/admin/{code}/employees/{employee_id}/attendance")
def list_attendance(
    code: str, employee_id: int,
    from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=365), db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.delete")),
    _feature_gate: None = Depends(require_feature("hr.update")),
    _perm_gate: None = Depends(require_feature("hr.read")),
    _gate: None = Depends(require_feature("hr.create")),
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_attendance(employee_id, db, from_date=from_date, to_date=to_date, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/check-in")
def check_in(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).check_in_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/check-out")
def check_out(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).check_out_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/geo-check-in")
def geo_check_in(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).check_in_with_geo(employee_id, body or {}, db)


@router.get("/admin/{code}/employees/{employee_id}/relations")
def list_relations(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_relations(employee_id, db)


@router.post("/admin/{code}/employees/{employee_id}/relations")
def create_relation(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_relation(employee_id, body or {}, db)


@router.delete("/admin/{code}/employees/relations/{relation_id}")
def delete_relation(code: str, relation_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.delete"))
):
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).remove_employee_relation(relation_id, db)
    return {"message": "Relation removed"}


@router.get("/admin/{code}/employees/{employee_id}/work-logs")
def list_work_logs(
    code: str, employee_id: int,
    from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=365),
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.read")),
    _feature_gate: None = Depends(require_feature("hr.create")),
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_work_logs(employee_id, db, from_date=from_date, to_date=to_date, status=status, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/work-logs")
def create_work_log(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_work_log(employee_id, body or {}, db)


@router.patch("/admin/{code}/employees/work-logs/{log_id}/approve")
def approve_work_log(code: str, log_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.update"))
):
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).approve_work_log(log_id, body or {}, current_user, db)


@router.post("/employees/{employee_id}/qr-token")
def generate_qr_token(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).generate_qr_login_token(employee_id, db)


@router.post("/employees/qr-login")
def qr_login(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).validate_qr_login(body.get("qr_token", ""), db)


@router.post("/geo/validate")
def validate_geo(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    return get_hr_employee_service(db).validate_geo_location(
        body.get("latitude", 0), body.get("longitude", 0), body.get("office_id", 0), db
    )