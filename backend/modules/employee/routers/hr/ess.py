"""Employee Self-Service (ESS) portal sub-router — thin delegators (Law 2)."""
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.ess_service import (
    get_employee_profile,
    update_employee_profile,
    get_leave_balance,
    create_leave_request as svc_create_leave_request,
    get_leave_history,
    get_payslips,
    get_attendance as svc_get_attendance,
    get_okrs,
    get_org_chart as svc_get_org_chart,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/profile")
def ess_get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    emp_id = current_user.get("id")
    return get_employee_profile(db, emp_id)


@router.put("/profile")
def ess_update_profile(
    phone: Optional[str] = None, address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None, emergency_contact_phone: Optional[str] = None,
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read")),
    _feature_gate: None = Depends(require_feature("hr.update")),
    _perm_gate: None = Depends(require_feature("hr.create")),
):
    return update_employee_profile(db, current_user.get("id"), phone, address, emergency_contact_name, emergency_contact_phone)


@router.get("/leave/balance")
def ess_leave_balance(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_leave_balance(db, current_user.get("id"))


@router.post("/leave/request")
def ess_request_leave(
    leave_type: str, start_date: str, end_date: str, reason: str,
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create")),
    _feature_gate: None = Depends(require_feature("hr.read")),
):
    return svc_create_leave_request(db, current_user.get("id"), leave_type, start_date, end_date, reason)


@router.get("/leave/history")
def ess_leave_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_leave_history(db, current_user.get("id"))


@router.get("/payslips")
def ess_payslips(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_payslips(db, current_user.get("id"))


@router.get("/attendance")
def ess_attendance(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return svc_get_attendance(db, current_user.get("id"))


@router.get("/okrs")
def ess_okrs(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return get_okrs(db, current_user.get("id"))


@router.get("/org-chart")
def ess_org_chart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    return svc_get_org_chart(db, None, current_user.get("id"))