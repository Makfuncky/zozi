from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from data.dependencies_auth import get_current_user
from controllers import employees_controller as ctrl
from data.db import get_db
from data.models_employee_models import Employee
from utils.country_rls import enforce_country_access, get_country_or_404
from utils.datetime_utils import utcnow as _utcnow
from services.hr.employee_write_service import list_employees_public

from services.write_helpers import commit_only
router = APIRouter()

EMPLOYEE_SCOPES = ("employees",)


class OfficeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = True


class OfficeUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None


class EmployeeCreate(BaseModel):
    user_id: Optional[int] = None
    employee_code: Optional[str] = None
    office_id: Optional[int] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: str = "full_time"
    employment_status: str = "active"
    salary: Optional[float] = None
    currency: Optional[str] = None
    hire_date: Optional[str] = None
    notes: Optional[str] = None


class EmployeeUpdate(BaseModel):
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    employment_status: Optional[str] = None
    salary: Optional[float] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    office_id: Optional[int] = None
    user_id: Optional[int] = None
    is_verified: Optional[bool] = None


class EmployeeDocumentCreate(BaseModel):
    document_type: str = Field(..., max_length=80)
    document_name: str = Field(..., max_length=200)
    file_url: str = Field(..., max_length=500)
    expires_at: Optional[str] = None
    notes: Optional[str] = None


class EmployeeDocumentUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[str] = None


class CheckInBody(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    notes: Optional[str] = None


class CheckOutBody(BaseModel):
    notes: Optional[str] = None


class GeoCheckInBody(BaseModel):
    latitude: float
    longitude: float
    office_id: int
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    notes: Optional[str] = None


class RelationCreate(BaseModel):
    related_employee_id: int
    relation_type: str = "peer"
    notes: Optional[str] = None


class WorkLogCreate(BaseModel):
    date: Optional[str] = None
    hours_worked: float = 0
    description: Optional[str] = None


class WorkLogApprove(BaseModel):
    status: str = "approved"


class QrLoginBody(BaseModel):
    qr_token: str


class GeoValidateBody(BaseModel):
    latitude: float
    longitude: float
    office_id: int


class EmployeeRoleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = None
    permissions: Optional[dict] = None


class LeaveStatusUpdate(BaseModel):
    status: str = Field(..., description="approved or rejected")


class LeaveCreate(BaseModel):
    employee_id: Optional[int] = None
    leave_type: str = 'annual'
    start_date: str
    end_date: str
    notes: Optional[str] = None


class ShiftCreate(BaseModel):
    employee_id: int
    shift_date: str
    start_time: str
    end_time: str
    shift_type: str = 'scheduled'
    status: str = 'scheduled'


# ── Offices ───────────────────────────────────────────────────────

@router.get("/admin/{code}/offices")
def list_offices(
    code: str = Path(..., description="Country code"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.list_offices(code, db)


@router.post("/admin/{code}/offices")
def create_office(
    code: str = Path(..., description="Country code"),
    body: OfficeCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_office(code, body.model_dump(exclude_none=True), db)


@router.put("/admin/{code}/offices/{office_id}")
def update_office(
    code: str = Path(..., description="Country code"),
    office_id: int = Path(...),
    body: OfficeUpdate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.update_office(office_id, body.model_dump(exclude_none=True), db)


@router.delete("/admin/{code}/offices/{office_id}")
def delete_office(
    code: str = Path(..., description="Country code"),
    office_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    ctrl.delete_office(office_id, db)
    return {"message": "Office deleted"}


# ── Employee CRUD ─────────────────────────────────────────────────

@router.get("/admin/{code}/employees")
def list_employees(
    code: str = Path(..., description="Country code"),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None, alias="employment_status"),
    q: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.list_employees(code, db, department=department, status=status, query=q, limit=limit)


@router.post("/admin/{code}/employees")
def create_employee(
    code: str = Path(..., description="Country code"),
    body: EmployeeCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_employee(code, body.model_dump(exclude_none=True), current_user, db)


# ── Employee Documents ────────────────────────────────────────────

@router.get("/admin/{code}/employees/{employee_id}/documents")
def list_employee_documents(
    code: str = Path(...),
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.list_employee_documents(employee_id, db)


@router.get("/employees/{employee_id}/addresses")
def list_employee_addresses(
    employee_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from data.models_core import Address
    from data.models_employee_models import Employee

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return []
    addresses = db.query(Address).filter(Address.user_id == employee.user_id).offset(skip).limit(limit).all()
    return [
        {
            "id": a.id,
            "label": a.label,
            "full_name": a.full_name,
            "phone": a.phone,
            "address_line1": a.address_line1,
            "address_line2": a.address_line2,
            "city": a.city,
            "state": a.state,
            "postal_code": a.postal_code,
            "country": a.country,
            "is_default": a.is_default,
        }
        for a in addresses
    ]


@router.get("/employees/{employee_id}/dependents")
def list_employee_dependents(
    employee_id: int = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from data.models_employee_models import EmployeeDependent

    dependents = (
        db.query(EmployeeDependent).filter(EmployeeDependent.employee_id == employee_id).offset(skip).limit(limit).all()
    )
    return [
        {
            "id": d.id,
            "name": d.name,
            "relation": d.relation,
            "dob": str(d.dob) if d.dob else None,
            "is_insured": d.is_insured,
        }
        for d in dependents
    ]


@router.post("/admin/{code}/employees/{employee_id}/documents")
def create_employee_document(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: EmployeeDocumentCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_employee_document(employee_id, body.model_dump(exclude_none=True), db)


@router.patch("/admin/{code}/employees/documents/{doc_id}")
def update_employee_document_status(
    code: str = Path(...),
    doc_id: int = Path(...),
    body: EmployeeDocumentUpdate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.update_employee_document_status(doc_id, body.model_dump(exclude_none=True), db)


# ── Attendance ────────────────────────────────────────────────────

@router.get("/admin/{code}/employees/{employee_id}/attendance")
def list_attendance(
    code: str = Path(...),
    employee_id: int = Path(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    return ctrl.list_attendance(employee_id, db, from_date=from_date, to_date=to_date, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/check-in")
def check_in(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: CheckInBody = None,
    db: Session = Depends(get_db),
):
    return ctrl.check_in_employee(employee_id, body.model_dump(exclude_none=True), db)


@router.post("/admin/{code}/employees/{employee_id}/check-out")
def check_out(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: CheckOutBody = None,
    db: Session = Depends(get_db),
):
    return ctrl.check_out_employee(employee_id, body.model_dump(exclude_none=True), db)


# ── Geo-Fenced Check-In ───────────────────────────────────────────

@router.post("/admin/{code}/employees/{employee_id}/geo-check-in")
def geo_check_in(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: GeoCheckInBody = None,
    db: Session = Depends(get_db),
):
    return ctrl.check_in_with_geo(employee_id, body.model_dump(), db)


# ── Employee Relations ────────────────────────────────────────────

@router.get("/admin/{code}/employees/{employee_id}/relations")
def list_relations(
    code: str = Path(...),
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.list_employee_relations(employee_id, db)


@router.post("/admin/{code}/employees/{employee_id}/relations")
def create_relation(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: RelationCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_employee_relation(employee_id, body.model_dump(exclude_none=True), db)


@router.delete("/admin/{code}/employees/relations/{relation_id}")
def delete_relation(
    code: str = Path(...),
    relation_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    ctrl.remove_employee_relation(relation_id, db)
    return {"message": "Relation removed"}


# ── Work Logs ─────────────────────────────────────────────────────

@router.get("/admin/{code}/employees/{employee_id}/work-logs")
def list_work_logs(
    code: str = Path(...),
    employee_id: int = Path(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    return ctrl.list_work_logs(employee_id, db, from_date=from_date, to_date=to_date, status=status, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/work-logs")
def create_work_log(
    code: str = Path(...),
    employee_id: int = Path(...),
    body: WorkLogCreate = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.create_work_log(employee_id, body.model_dump(exclude_none=True), db)


@router.patch("/admin/{code}/employees/work-logs/{log_id}/approve")
def approve_work_log(
    code: str = Path(...),
    log_id: int = Path(...),
    body: WorkLogApprove = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.approve_work_log(log_id, body.model_dump(exclude_none=True), current_user, db)


# ── QR IAM ────────────────────────────────────────────────────────

@router.post("/employees/{employee_id}/qr-token")
def generate_qr_token(employee_id: int, db: Session = Depends(get_db)):
    return ctrl.generate_qr_login_token(employee_id, db)


@router.post("/employees/qr-login")
def qr_login(body: QrLoginBody, db: Session = Depends(get_db)):
    return ctrl.validate_qr_login(body.qr_token, db)


@router.post("/geo/validate")
def validate_geo(body: GeoValidateBody, db: Session = Depends(get_db)):
    return ctrl.validate_geo_location(body.latitude, body.longitude, body.office_id, db)


# ── Employee Roles ────────────────────────────────────────────────

@router.get("/admin/{code}/employee-roles")
def list_employee_roles(
    code: str = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    enforce_country_access(code, db=db)
    return ctrl.list_employee_roles(code, db)


@router.post("/admin/{code}/employee-roles")
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
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from data.models_employee_models import EmployeeLeaveRequest
    requests = db.query(EmployeeLeaveRequest).order_by(EmployeeLeaveRequest.created_at.desc()).offset(skip).limit(limit).all()
    result = []
    for r in requests:
        employee_name = None
        if r.employee:
            user = r.employee.user
            employee_name = (user.full_name or user.username) if user else r.employee.employee_code
        result.append({
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
    return result


@router.post("/admin/{code}/employees/leave-requests")
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
    from data.models_employee_models import EmployeeLeaveRequest
    r = db.query(EmployeeLeaveRequest).filter(EmployeeLeaveRequest.id == leave_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Leave request not found")
    status = body.status.lower()
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    r.status = status
    r.approved_by = current_user.get("id")
    r.approved_at = _utcnow()
    commit_only(db)
    return {"message": f"Leave request {status}", "id": leave_id}


@router.get("/admin/{code}/employees/shifts")
def list_shifts(
    code: str = Path(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from data.models_employee_models import EmployeeShiftRoster
    shifts = db.query(EmployeeShiftRoster).order_by(EmployeeShiftRoster.shift_date.desc()).offset(skip).limit(limit).all()
    result = []
    for s in shifts:
        employee_name = None
        if s.employee:
            user = s.employee.user
            employee_name = (user.full_name or user.username) if user else s.employee.employee_code
        result.append({
            "id": s.id,
            "employee_id": s.employee_id,
            "employee_name": employee_name,
            "shift_date": s.shift_date.isoformat() if s.shift_date else None,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "shift_type": s.shift_type,
            "status": s.status,
        })
    return result


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
def list_employees_public_route(db: Session = Depends(get_db)):
    return list_employees_public(db)


@router.post("/employees/{employee_id}/kill-switch")
def kill_switch_employee(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ctrl.kill_switch(employee_id, current_user, db)

