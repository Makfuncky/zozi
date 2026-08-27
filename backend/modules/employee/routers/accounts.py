"""Employee accounts router — thin HTTP surface delegating to HR/ESS services."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from rbac import get_current_user
from rbac.dependencies import require_feature
from infrastructure.database.database import get_db
from domains.governance.ports import User
from domains.hr.ports import (
    get_employee_profile,
    update_employee_profile,
    get_leave_balance,
    create_leave_request,
    get_leave_history,
    get_payslips,
    get_attendance,
    get_okrs,
    get_org_chart,
    HREmployeeService,
)

router = APIRouter(prefix="/api/v1/employee/accounts", tags=["employee", "accounts"])


def _paginate(items, page: int, page_size: int):
    """Apply page/page_size slicing to a list. Non-invasive post-slice."""
    if not isinstance(items, list):
        return items
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]


def _get_employee_id(user: User, db=Depends(get_db)) -> int:
    """Get the Employee record ID for the current user."""
    svc = HREmployeeService(db)
    emp_row = svc.get_employee_by_user_id(user.id)
    if not emp_row:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp_row["id"]


def _get_employee_org_unit_id(user: User, db=Depends(get_db)) -> Optional[int]:
    """Get the Employee's org_unit_id for the current user."""
    svc = HREmployeeService(db)
    emp_row = svc.get_employee_by_user_id(user.id)
    if not emp_row:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp_row.get("org_unit_id")


# ── Profile ──────────────────────────────────────────────────────


@router.get("/profile")
def ess_get_profile(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.profile.read")
    emp_id = _get_employee_id(current_user, db)
    try:
        return get_employee_profile(db, emp_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Profile not found")


@router.put("/profile")
def ess_update_profile(
    phone: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.profile.update")
    emp_id = _get_employee_id(current_user, db)
    try:
        return update_employee_profile(
            db, emp_id,
            phone=phone, address=address,
            emergency_contact_name=emergency_contact_name,
            emergency_contact_phone=emergency_contact_phone,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Leave ────────────────────────────────────────────────────────


@router.get("/leave/balance")
def ess_leave_balance(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.leave.read")
    emp_id = _get_employee_id(current_user, db)
    return get_leave_balance(db, emp_id)


@router.post("/leave/request")
def ess_request_leave(
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.leave.create")
    emp_id = _get_employee_id(current_user, db)
    return create_leave_request(db, emp_id, leave_type, start_date, end_date, reason)


@router.get("/leave/history")
def ess_leave_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.leave.read")
    emp_id = _get_employee_id(current_user, db)
    items = get_leave_history(db, emp_id)
    return _paginate(items, page, page_size)


# ── Payslips ─────────────────────────────────────────────────────


@router.get("/payslips")
def ess_payslips(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.payslip.read")
    emp_id = _get_employee_id(current_user, db)
    items = get_payslips(db, emp_id)
    return _paginate(items, page, page_size)


# ── Attendance ───────────────────────────────────────────────────


@router.get("/attendance")
def ess_attendance(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.attendance.read")
    emp_id = _get_employee_id(current_user, db)
    items = get_attendance(db, emp_id)
    return _paginate(items, page, page_size)


# ── OKRs ─────────────────────────────────────────────────────────


@router.get("/okrs")
def ess_okrs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.okr.read")
    emp_id = _get_employee_id(current_user, db)
    items = get_okrs(db, emp_id)
    return _paginate(items, page, page_size)


# ── Org Chart (self) ─────────────────────────────────────────────


@router.get("/org-chart")
def ess_org_chart(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    require_feature("hr.org.read")
    emp_id = _get_employee_id(current_user, db)
    org_unit_id = _get_employee_org_unit_id(current_user, db)
    return get_org_chart(db, org_unit_id, emp_id)
