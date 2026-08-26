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



def create_leave_request(
    code: str = Path(...),
    body: LeaveCreate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    return ctrl.create_leave_request(body.employee_id or 0, body.model_dump(exclude_none=True), current_user, db)


@router.patch("/admin/{code}/employees/leave-requests/{leave_id}")
def update_leave_request_status(
    code: str = Path(...),
    leave_id: int = Path(...),
    body: LeaveStatusUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from domains.hr.models.employee_models import EmployeeLeaveRequest
    r = db.query(EmployeeLeaveRequest).filter(EmployeeLeaveRequest.id == leave_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Leave request not found")
    status = body.status.lower()
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    r.status = status
    r.approved_by = current_user.get("id")
    r.approved_at = _utcnow()
    db.commit()
    return {"message": f"Leave request {status}", "id": leave_id}


@router.get("/admin/{code}/employees/shifts")
def list_shifts(
    code: str = Path(...),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from domains.hr.models.employee_models import EmployeeShiftRoster
    from sqlalchemy.orm import joinedload
    query = (
        db.query(EmployeeShiftRoster)
        .options(
            joinedload(EmployeeShiftRoster.employee, innerjoin=False).joinedload(
                "user", innerjoin=False
            )
        )
        .order_by(EmployeeShiftRoster.shift_date.desc())
    )
    page_data = paginated_response(query, page=page, size=limit, max_size=100)
    items = []
    for s in page_data["items"]:
        employee_name = None
        if s.employee:
            user = s.employee.user
            employee_name = (user.full_name or user.username) if user else s.employee.employee_code
        items.append({
            "id": s.id,
            "employee_id": s.employee_id,
            "employee_name": employee_name,
            "shift_date": s.shift_date.isoformat() if s.shift_date else None,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "shift_type": s.shift_type,
            "status": s.status,
        })
    page_data["items"] = items
    return page_data


@router.post("/admin/{code}/employees/shifts")
def create_shift_roster(
    code: str = Path(...),
    body: ShiftCreate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    return ctrl.create_shift_roster(body.employee_id, body.model_dump(exclude_none=True), current_user, db)


@router.get("/public")
def list_employees_public(db: Session = Depends(get_db)):
    try:
        query = "SELECT id, employee_code, department, position, employment_status, salary, currency, country_code, hire_date, created_at FROM employees ORDER BY created_at DESC LIMIT 50"
        result = db.execute(query)
        employees = []
        for row in result:
            employees.append({
                "id": row[0],
                "employee_code": row[1],
                "department": row[2],
                "position": row[3],
                "employment_status": row[4],
                "salary": float(row[5]) if row[5] else None,
                "currency": row[6],
                "country_code": row[7],
                "hire_date": row[8].isoformat() if row[8] else None,
            })
        return employees
    except Exception as e:
        return {"error": str(e)}


@router.post("/employees/{employee_id}/kill-switch")
def kill_switch_employee(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl.kill_switch(employee_id, current_user, db)

