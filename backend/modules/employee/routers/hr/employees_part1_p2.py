# === From employees.py ===

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

# from modules.employee.routers import employees_controller as ctrl  # FIXME: circular import
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.models.employee_models import Employee
from domains.country.utils.country_rls import enforce_country_access
from infrastructure.utils.datetime_utils import utcnow as _utcnow
from hr.router import router  # noqa: F401



def create_employee_role(
    code: str = Path(...),
    body: EmployeeRoleCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_employee_role(code, body.model_dump(exclude_none=True), db)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db)):
    return ctrl.get_employee(employee_id, db)


@router.patch("/admin/{code}/employees/{employee_id}")
def update_employee(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: EmployeeUpdate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.update_employee(employee_id, body.model_dump(exclude_none=True), current_user, db)


@router.delete("/admin/{code}/employees/{employee_id}")
def delete_employee(
    code: str = Path(...),
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    ctrl.delete_employee(employee_id, current_user, db)
    return {"message": "Employee deleted"}


@router.get("/admin/{code}/employees/leave-requests")
def list_leave_requests(
    code: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from domains.hr.models.employee_models import EmployeeLeaveRequest
    from sqlalchemy.orm import selectinload, joinedload
    query = (
        db.query(EmployeeLeaveRequest)
        .options(
            joinedload(EmployeeLeaveRequest.employee, innerjoin=False).joinedload(
                "user", innerjoin=False
            )
        )
        .order_by(EmployeeLeaveRequest.created_at.desc())
    )
    page_data = paginated_response(query, page=page, size=limit, max_size=100)
    items = []
    for r in page_data["items"]:
        employee_name = None
        if r.employee:
            user = r.employee.user
            employee_name = (user.full_name or user.username) if user else r.employee.employee_code
        items.append({
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": employee_name,
            "leave_type": r.leave_type,
            "start_date": r.start_date.isoformat() if r.start_date else None,
            "end_date": r.end_date.isoformat() if r.end_date else None,
            "days_requested": r.days_requested,
            "status": r.status,
            "approved_by": r.approved_by,
            "notes": r.rejection_reason or "",
        })
    page_data["items"] = items
    return page_data


@router.post("/admin/{code}/employees/leave-requests")