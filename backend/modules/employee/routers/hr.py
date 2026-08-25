"""Employee hr router — consolidated from 10 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status


router = APIRouter(prefix="/api/v1/employee/hr", tags=["employee", "hr"])


# === From hr_dashboard.py ===
"""hr dashboard router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/hr_dashboard/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "hr_dashboard", "prefix": "/api/v1"}


# === From employees.py ===

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

# from modules.employee.routers import employees_controller as ctrl  # FIXME: circular import
from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.models.employee_models import Employee
from domains.country.utils.country_rls import enforce_country_access
from infrastructure.utils.datetime_utils import utcnow as _utcnow


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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from domains.accounts.models.core import Address

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        return []
    addresses = db.query(Address).filter(Address.user_id == employee.user_id).all()
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
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from domains.hr.models.employee_models import EmployeeDependent

    dependents = (
        db.query(EmployeeDependent).filter(EmployeeDependent.employee_id == employee_id).all()
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from domains.hr.models.employee_models import EmployeeLeaveRequest
    requests = db.query(EmployeeLeaveRequest).order_by(EmployeeLeaveRequest.created_at.desc()).all()
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    enforce_country_access(code, db=db)
    from domains.hr.models.employee_models import EmployeeShiftRoster
    shifts = db.query(EmployeeShiftRoster).order_by(EmployeeShiftRoster.shift_date.desc()).all()
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


# === From hierarchy.py ===
"""Hierarchy Router — Org chart, reporting lines, matrix management, approval chains."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.country.models.countries import CountryConfig
from domains.country.models.country_enhancements import CountryHolidayCalendar
from domains.country.models.country_enhancements import CountryStaffAssignment
from domains.hr.models.employee_models import OrgUnit
from domains.country.models.country_enhancements import CountryLocalization
from domains.hr.services._auto_stubs import assign_matrix_manager
from domains.hr.services.hierarchy.hierarchy_service import backfill_authority_levels
from domains.hr.services.hierarchy.hierarchy_service import can_manage
from domains.hr.services._auto_stubs import detect_circular_reporting
from domains.hr.services.hierarchy.hierarchy_service import get_all_subordinates
from domains.governance.services.approval.approval_matrix_service import get_approval_chain
from domains.hr.services._auto_stubs import get_employees_in_subtree
from domains.hr.services._auto_stubs import get_matrix_managers
from domains.hr.services._auto_stubs import get_matrix_subordinates
from domains.hr.services.hierarchy.hierarchy_service import get_org_chart
from domains.hr.services._auto_stubs import get_org_unit_path
from domains.hr.services._auto_stubs import get_org_unit_subtree
from domains.hr.services.hierarchy.hierarchy_service import get_team_members
from domains.hr.services.hierarchy.hierarchy_service import get_user_chain
from domains.hr.services.hierarchy.hierarchy_service import reassign_manager
from domains.hr.services._auto_stubs import rebuild_paths
from domains.hr.services._auto_stubs import remove_matrix_manager

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ══════════════════════════════════════════════════════════════════


class OrgUnitCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: Optional[int] = None
    country_code: str
    level: int = 1


class OrgUnitUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None
    level: Optional[int] = None


class ManagerReassign(BaseModel):
    employee_user_id: int
    new_manager_user_id: int


class MatrixAssign(BaseModel):
    employee_id: int
    matrix_manager_id: int
    relation_type: str = "matrix_manager"
    notes: Optional[str] = None


class ApprovalChainQuery(BaseModel):
    employee_id: int
    resource_type: str = "leave"
    min_authority_level: Optional[int] = None


# ══════════════════════════════════════════════════════════════════
#  Org Unit CRUD + Path Management
# ══════════════════════════════════════════════════════════════════


@router.get("/org-units", response_model=dict)
def list_org_units(
    country_code: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    q = db.query(OrgUnit).filter(OrgUnit.is_active == True)
    if country_code:
        q = q.filter(OrgUnit.country_code == country_code)
    units = q.order_by(OrgUnit.path, OrgUnit.name).all()
    return {
        "units": [
            {
                "id": u.id,
                "name": u.name,
                "parent_id": u.parent_id,
                "path": u.path,
                "depth": u.depth,
                "level": u.level,
                "country_code": u.country_code,
                "is_active": u.is_active,
            }
            for u in units
        ]
    }


@router.post("/org-units", status_code=201)
def create_org_unit(
    payload: OrgUnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    unit = OrgUnit(
        name=payload.name,
        parent_id=payload.parent_id,
        country_code=payload.country_code,
        level=payload.level,
    )
    db.add(unit)
    db.flush()
    _update_unit_path(db, unit)
    db.commit()
    db.refresh(unit)
    return {
        "id": unit.id,
        "name": unit.name,
        "path": unit.path,
        "depth": unit.depth,
    }


@router.put("/org-units/{unit_id}")
def update_org_unit(
    unit_id: int = Path(...),
    payload: OrgUnitUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    unit = db.query(OrgUnit).filter(OrgUnit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Org unit not found")

    if payload.name is not None:
        unit.name = payload.name
    if payload.level is not None:
        unit.level = payload.level
    if payload.is_active is not None:
        unit.is_active = payload.is_active
    if payload.parent_id is not None:
        unit.parent_id = payload.parent_id

    db.flush()
    _update_unit_path(db, unit)
    db.commit()
    return {"id": unit.id, "path": unit.path, "depth": unit.depth}


@router.get("/org-chart")
def org_chart(
    org_unit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return get_org_chart(db, org_unit_id)


@router.get("/org-units/{unit_id}/subtree")
def org_unit_subtree(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"subtree": get_org_unit_subtree(db, unit_id)}


@router.get("/org-units/{unit_id}/path")
def org_unit_ancestor_path(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"path": get_org_unit_path(db, unit_id)}


@router.get("/org-units/{unit_id}/employees")
def employees_in_subtree(
    unit_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"employees": get_employees_in_subtree(db, unit_id)}


@router.post("/org-units/rebuild-paths")
def rebuild_org_unit_paths(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated = rebuild_paths(db)
    db.commit()
    return {"message": f"Rebuilt paths for {updated} org units"}


# ══════════════════════════════════════════════════════════════════
#  Employee Hierarchy & Reporting
# ══════════════════════════════════════════════════════════════════


@router.get("/employee/{user_id}/chain")
def employee_chain(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"chain": get_user_chain(db, user_id)}


@router.get("/employee/{user_id}/subordinates")
def employee_subordinates(
    user_id: int = Path(...),
    direct_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if direct_only:
        return {"subordinates": get_team_members(db, user_id)}
    return {"subordinates": get_all_subordinates(db, user_id)}


@router.get("/employee/{user_id}/can-manage/{target_user_id}")
def check_can_manage(
    user_id: int = Path(...),
    target_user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"can_manage": can_manage(db, user_id, target_user_id)}


@router.post("/reassign-manager")
def reassign_employee_manager(
    payload: ManagerReassign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = reassign_manager(db, payload.employee_user_id, payload.new_manager_user_id)
    db.commit()
    return result


@router.post("/backfill-authority-levels")
def refresh_authority_levels(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    updated = backfill_authority_levels(db)
    db.commit()
    return {"message": f"Updated {updated} employee authority levels"}


# ══════════════════════════════════════════════════════════════════
#  Matrix / Dotted-Line Management
# ══════════════════════════════════════════════════════════════════


@router.post("/matrix/assign")
def assign_matrix(
    payload: MatrixAssign,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = assign_matrix_manager(
        db,
        employee_id=payload.employee_id,
        matrix_manager_id=payload.matrix_manager_id,
        relation_type=payload.relation_type,
        notes=payload.notes,
    )
    db.commit()
    return result


@router.delete("/matrix/{relation_id}")
def remove_matrix(
    relation_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    result = remove_matrix_manager(db, relation_id)
    db.commit()
    return result


@router.get("/employee/{employee_id}/matrix-managers")
def matrix_managers(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"matrix_managers": get_matrix_managers(db, employee_id)}


@router.get("/employee/{manager_id}/matrix-subordinates")
def matrix_subordinates(
    manager_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}


# ══════════════════════════════════════════════════════════════════
#  Circular Reference Detection & Approval Chains
# ══════════════════════════════════════════════════════════════════


@router.get("/detect-circular")
def detect_circular(
    employee_id: int = Query(...),
    proposed_manager_id: int = Query(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)
    return {
        "is_circular": is_circular,
        "message": "Circular reporting detected" if is_circular else "No circular relationship",
    }


@router.post("/approval-chain")
def approval_chain(
    payload: ApprovalChainQuery,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return {
        "approvers": get_approval_chain(
            db,
            employee_id=payload.employee_id,
            resource_type=payload.resource_type,
            min_authority_level=payload.min_authority_level,
        )
    }


# ══════════════════════════════════════════════════════════════════
#  Country Scope & Localization
# ══════════════════════════════════════════════════════════════════


@router.get("/country-scope/{user_id}")
def user_country_scope(
    user_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all country assignments for a user."""
    assignments = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.is_active == True,
        )
        .all()
    )
    return {
        "countries": [
            {
                "id": a.id,
                "country_code": a.country_code,
                "role_in_country": a.role_in_country,
            }
            for a in assignments
        ]
    }


@router.post("/country-scope/switch")
def switch_country_scope(
    country_code: str = Query(..., min_length=2, max_length=10),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Switch the active country scope for the current user (sets RLS context)."""
    user_id = int(current_user.get("id", 0))
    normalized = country_code.upper()

    # Verify the user has access to this country
    assignment = (
        db.query(CountryStaffAssignment)
        .filter(
            CountryStaffAssignment.user_id == user_id,
            CountryStaffAssignment.country_code == normalized,
            CountryStaffAssignment.is_active == True,
        )
        .first()
    )
    role = str(current_user.get("role", "")).lower()
    if not assignment and role not in ("admin", "super_admin"):
        raise HTTPException(status_code=403, detail=f"No access to country '{normalized}'")

    # Set RLS context
    from infrastructure.utils.rls_interceptor import set_rls_context
    set_rls_context(normalized)

    return {"active_country": normalized, "message": f"Switched to {normalized}"}


@router.get("/localization/{country_code}")
def country_localization(
    country_code: str = Path(..., min_length=2, max_length=10),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get localization settings for a country (leave policies, holidays, labor rules)."""
    normalized = country_code.upper()
    country = db.query(CountryConfig).filter(CountryConfig.code == normalized).first()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")

    holidays = (
        db.query(CountryHolidayCalendar)
        .filter(CountryHolidayCalendar.country_code == normalized)
        .order_by(CountryHolidayCalendar.date)
        .all()
    )
    localization = (
        db.query(CountryLocalization)
        .filter(CountryLocalization.country_code == normalized)
        .all()
    )

    return {
        "country": {
            "code": country.code,
            "name": country.name,
            "currency": country.currency,
            "timezone": country.timezone,
            "language": country.language,
        },
        "holidays": [
            {
                "id": h.id,
                "name": h.holiday_name,
                "date": str(h.date),
                "type": h.holiday_type,
            }
            for h in holidays
        ],
        "localization": {
            loc.key: loc.value
            for loc in localization
        },
    }


# ══════════════════════════════════════════════════════════════════
#  Authority Level Helpers
# ══════════════════════════════════════════════════════════════════


@router.get("/required-authority/{resource_type}")
def required_authority_for_resource(
    resource_type: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    thresholds = {
        "leave": 1,
        "expense_500": 2,
        "expense_2000": 3,
        "expense_10000": 4,
        "payroll_release": 4,
        "offboarding_approve": 3,
        "disciplinary_final": 4,
        "hiring_approve": 3,
    }
    return {
        "resource_type": resource_type,
        "required_authority_level": thresholds.get(resource_type, 1),
    }


# ══════════════════════════════════════════════════════════════════
#  Internal Helpers
# ══════════════════════════════════════════════════════════════════


def _update_unit_path(db: Session, unit: OrgUnit) -> None:
    """Compute the materialized path and depth for a unit based on its parent."""
    if unit.parent_id:
        parent = db.query(OrgUnit).filter(OrgUnit.id == unit.parent_id).first()
        if parent:
            unit.path = f"{parent.path}{unit.id}/" if parent.path else f"/{parent.id}/{unit.id}/"
            unit.depth = (parent.depth or 0) + 1
        else:
            unit.path = f"/{unit.id}/"
            unit.depth = 0
    else:
        unit.path = f"/{unit.id}/"
        unit.depth = 0
    db.flush()


# === From lms.py ===
"""Learning Management System Router."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from domains.hr.services.learning.lms_service import assign_training
from domains.hr.services.learning.lms_service import check_permission_lock
from domains.hr.services.learning.lms_service import create_training_module
from domains.hr.services.learning.lms_service import get_training_progress
from domains.hr.services.learning.lms_service import verify_training_completion
from infrastructure.database.database import get_db


@router.post("/modules")
def create_module(module_data: dict, db: Session = Depends(get_db)):
    return create_training_module(module_data, db)


@router.post("/{employee_id}/assign")
def assign_training(employee_id: int, module_id: str = Query(...), db: Session = Depends(get_db)):
    return assign_training(employee_id, module_id, db)


@router.post("/{employee_id}/complete")
def complete_training(employee_id: int, module_id: str = Query(...), quiz_score: float = Query(...), db: Session = Depends(get_db)):
    return verify_training_completion(employee_id, module_id, quiz_score, db)


@router.get("/{employee_id}/lock/{permission}")
def check_lock(employee_id: int, permission: str, db: Session = Depends(get_db)):
    return check_permission_lock(employee_id, permission, db)


@router.get("/{employee_id}/progress")
def training_progress(employee_id: int, db: Session = Depends(get_db)):
    return get_training_progress(employee_id, db)


# === From okr.py ===
"""
OKR API Router
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services._auto_stubs import get_okr_engine


class ObjectiveCreate(BaseModel):
    employee_id: int
    title: str
    description: str
    key_results: List[Dict[str, Any]] = []
    period_start: str
    period_end: str


class KpiEvaluate(BaseModel):
    employee_id: int
    metric_query_hash: str
    target_value: float
    current_value: float


@router.post("/objectives", response_model=dict)
async def create_objective(
    payload: ObjectiveCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    result = engine.create_objective(
        employee_id=payload.employee_id,
        title=payload.title,
        description=payload.description,
        key_results=payload.key_results,
        period_start=payload.period_start,
        period_end=payload.period_end
    )
    return result


@router.post("/evaluate", response_model=dict)
async def evaluate_kpi(
    payload: KpiEvaluate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    result = engine.evaluate_kpi(
        employee_id=payload.employee_id,
        metric_query_hash=payload.metric_query_hash,
        target_value=payload.target_value,
        current_value=payload.current_value
    )
    return result


@router.get("/employee/{employee_id}", response_model=List[dict])
async def get_employee_okrs(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    engine = get_okr_engine(db)
    return engine.get_employee_okrs(employee_id)


# === From payroll.py ===
"""Payroll Router — batch processing, maker-checker approval, disbursement, payslips."""

import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.models.employee_models import EmployeeDocument
from domains.governance.services._auto_stubs import check_permission
from domains.hr.services.payroll.payroll_engine import PayrollEngine

logger = logging.getLogger(__name__)


# In-memory approval state (production would use DB)
PENDING_PAYROLL_APPROVALS: dict = {}


class PayrollApproveBody(BaseModel):
    batch_id: str
    approved: bool = True
    notes: Optional[str] = None


@router.post("/payroll/calculate/{employee_id}")
def calculate_employee_payroll(
    employee_id: int = Path(...),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    engine = PayrollEngine(db)
    period = date(year, month, 1)
    result = engine.calculate_monthly_payroll(employee_id, period)
    return result


@router.post("/payroll/batch")
def process_payroll_batch(
    country_code: str = Query(..., min_length=2, max_length=10),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Generate payroll batch (Maker step)."""
    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.release", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.release permission")

    engine = PayrollEngine(db)
    period = date(year, month, 1)

    # Check if already approved
    batch_key = f"{country_code}:{year}:{month:02d}"
    existing = PENDING_PAYROLL_APPROVALS.get(batch_key)
    if existing and existing.get("status") == "disbursed":
        raise HTTPException(status_code=400, detail="This period has already been disbursed")

    payroll = engine.process_payroll_batch(period, country_code.upper())
    payroll["country_code"] = country_code.upper()
    payroll["status"] = "pending_approval"
    PENDING_PAYROLL_APPROVALS[batch_key] = payroll
    return payroll


@router.post("/payroll/approve")
def approve_payroll_batch(
    body: PayrollApproveBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Approve payroll for disbursement (Checker step - cannot be same user as Maker)."""
    parts = body.batch_id.split("-")
    if len(parts) < 3:
        raise HTTPException(status_code=400, detail="Invalid batch_id format")
    country_code = parts[1]
    year = parts[2]
    month = parts[3] if len(parts) > 3 else "01"
    batch_key = f"{country_code}:{year}:{month}"

    user_id = int(current_user.get("id", 0))
    if not check_permission(user_id, "hr.payroll.approve", country_code.upper(), db):
        raise HTTPException(status_code=403, detail="Missing hr.payroll.approve permission")

    pending = PENDING_PAYROLL_APPROVALS.get(batch_key)
    if not pending or pending.get("status") != "pending_approval":
        raise HTTPException(status_code=400, detail="No pending payroll batch found for this period")

    maker_user_id = pending.get("maker_user_id")
    if maker_user_id and maker_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot approve your own payroll batch")

    if not body.approved:
        PENDING_PAYROLL_APPROVALS[batch_key]["status"] = "rejected"
        return {"status": "rejected", "batch_id": body.batch_id}

    # Execute auto-disbursement
    engine = PayrollEngine(db)
    period = date(int(year), int(month), 1)
    disbursement = engine.auto_disburse(period, approved_by=user_id)
    disbursement["batch_id"] = body.batch_id
    disbursement["status"] = "disbursed"
    disbursement["approved_by"] = user_id
    disbursement["approved_at"] = datetime.utcnow().isoformat()

    PENDING_PAYROLL_APPROVALS[batch_key] = disbursement
    return disbursement


@router.get("/payroll/payslips/{employee_id}")
def get_employee_payslips(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    docs = (
        db.query(EmployeeDocument)
        .filter(
            EmployeeDocument.employee_id == employee_id,
            EmployeeDocument.doc_type == "payslip",
        )
        .order_by(EmployeeDocument.created_at.desc())
        .all()
    )
    return {
        "payslips": [
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "file_url": d.file_url,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in docs
        ]
    }


@router.get("/payroll/bank-accounts/{employee_id}")
def employee_bank_accounts(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    engine = PayrollEngine(db)
    return {"bank_accounts": engine.get_employee_bank_accounts(employee_id)}


@router.post("/payroll/bank-accounts/{account_id}/verify")
def verify_bank_account(
    account_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user.get("id", 0))
    engine = PayrollEngine(db)
    return engine.validate_bank_account(account_id, verified_by=user_id)


@router.get("/payroll/status/{country_code}")
def payroll_status(
    country_code: str = Path(..., min_length=2, max_length=10),
    db: Session = Depends(get_current_user),
):
    """Get current payroll batch status for a country."""
    results = {}
    for key, value in PENDING_PAYROLL_APPROVALS.items():
        if key.startswith(country_code.upper()):
            results[key] = {
                "status": value.get("status"),
                "processed": value.get("processed"),
                "total_net": value.get("total_net"),
            }
    return {"payroll_batches": results}


# === From performance.py ===
"""Performance Management Router — OKRs, KPIs, 360° reviews, health board.
Wraps the performance_service functions as REST endpoints under the /hr prefix.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ══════════════════════════════════════════════════════════════════


class ObjectiveCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300, description="OKR objective title")
    cascade_level: str = Field(..., description="One of: company, department, team, individual")
    owner_employee_id: int = Field(..., description="Employee ID who owns this objective")
    quarter: Optional[str] = Field(None, description="e.g. Q1, Q2, Q3, Q4")
    year: Optional[int] = None
    parent_objective_id: Optional[int] = None
    org_unit_id: Optional[int] = None
    description: Optional[str] = None
    key_results: Optional[List[Dict[str, Any]]] = None
    weight: float = 1.0


class KpiCreate(BaseModel):
    objective_id: int
    employee_id: int
    metric_name: str = Field(..., min_length=1, max_length=200)
    target_value: float
    unit: str = "number"
    weight: float = 1.0
    auto_source_query: Optional[str] = None


class KpiValueUpdate(BaseModel):
    value: float
    source: Optional[str] = None


class ReviewSubmit(BaseModel):
    employee_id: int
    reviewer_id: int
    review_type: str = Field(..., description="One of: self, manager, peer, subordinate")
    score: float = Field(..., ge=0, le=5, description="Score 0-5")
    strengths: Optional[str] = None
    areas_for_improvement: Optional[str] = None
    comments: Optional[str] = None


class ObjectiveProgressUpdate(BaseModel):
    progress_pct: Optional[float] = None
    status: Optional[str] = None


# ══════════════════════════════════════════════════════════════════
#  OKR Endpoints
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/okr", summary="Create an OKR objective")
def create_objective_endpoint(
    body: ObjectiveCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create an OKR objective at any cascade level (company → individual).
    Optionally accepts key_results to create KPIs in the same call.
    """
    from domains.hr.services.performance.performance_service import create_objective
    try:
        result = create_objective(
            db=db,
            title=body.title,
            cascade_level=body.cascade_level,
            owner_employee_id=body.owner_employee_id,
            quarter=body.quarter,
            year=body.year,
            parent_objective_id=body.parent_objective_id,
            org_unit_id=body.org_unit_id,
            description=body.description,
            key_results=body.key_results,
            weight=body.weight,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hr/okr/{objective_id}", summary="Get objective tree with children")
def get_objective_tree_endpoint(
    objective_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get an objective with all its child objectives (aligned cascade)."""
    from domains.hr.services.performance.performance_service import get_objective_tree
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result


@router.patch("/hr/okr/{objective_id}/progress", summary="Update objective progress")
def update_objective_progress_endpoint(
    objective_id: int = Path(...),
    body: ObjectiveProgressUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update objective progress. Auto-computes from child KPIs if progress_pct not provided."""
    from domains.hr.services.performance.performance_service import update_objective_progress
    return update_objective_progress(
        db, objective_id,
        progress_pct=body.progress_pct if body else None,
        status=body.status if body else None,
    )


# ══════════════════════════════════════════════════════════════════
#  KPI Endpoints
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/kpi", summary="Create a KPI metric under an objective")
def create_kpi_endpoint(
    body: KpiCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a KPI metric tied to an objective."""
    from domains.hr.services.performance.performance_service import create_kpi_metric
    return create_kpi_metric(
        db=db,
        objective_id=body.objective_id,
        employee_id=body.employee_id,
        metric_name=body.metric_name,
        target_value=body.target_value,
        unit=body.unit,
        weight=body.weight,
        auto_source_query=body.auto_source_query,
    )


@router.put("/hr/kpi/{kpi_id}/value", summary="Record a KPI value")
def record_kpi_value_endpoint(
    kpi_id: int = Path(...),
    body: KpiValueUpdate = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a new current value for a KPI metric and recalc objective progress."""
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    from domains.hr.services.performance.performance_service import record_kpi_value
    return record_kpi_value(db, kpi_id, value=body.value, source=body.source)


@router.get("/hr/kpi/employee/{employee_id}", summary="Get KPI dashboard for an employee")
def get_kpi_dashboard_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all KPIs and objectives for an employee."""
    from domains.hr.services.performance.performance_service import get_kpi_dashboard
    return get_kpi_dashboard(db, employee_id)


# ══════════════════════════════════════════════════════════════════
#  Performance Review Endpoints (360°)
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/reviews", summary="Submit a 360° performance review")
def submit_review_endpoint(
    body: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Submit a 360° performance review entry (self, manager, peer, subordinate)."""
    from domains.hr.services.performance.performance_service import submit_performance_review
    try:
        return submit_performance_review(
            db=db,
            employee_id=body.employee_id,
            reviewer_id=body.reviewer_id,
            review_type=body.review_type,
            score=body.score,
            strengths=body.strengths,
            areas_for_improvement=body.areas_for_improvement,
            comments=body.comments,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hr/reviews/{employee_id}", summary="Get reviews for an employee")
def get_employee_reviews_endpoint(
    employee_id: int = Path(...),
    review_cycle: Optional[str] = Query(None, description="e.g. 2026-H1"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all reviews for an employee, grouped by review type."""
    from domains.hr.services.performance.performance_service import get_employee_reviews
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)


# ══════════════════════════════════════════════════════════════════
#  Performance Health Endpoints
# ══════════════════════════════════════════════════════════════════


@router.get("/hr/health/{employee_id}", summary="Compute performance health for an employee")
def compute_health_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Compute a Performance Health Score (red/amber/green) from multiple signals."""
    from domains.hr.services.performance.performance_service import compute_performance_health
    result = compute_performance_health(db, employee_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/hr/{employee_id}/coi-check", summary="Run a conflict-of-interest check for an employee")
def coi_check_endpoint(
    employee_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Run a simple conflict-of-interest check by examining employee relations
    and shared departments. Returns any detected conflicts."""
    try:
        from domains.hr.models.employee_models import Employee
        from domains.hr.models.employee_models import EmployeeRelation
    except Exception as exc:
        logger.warning("EmployeeRelation model not available: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    from sqlalchemy import or_

    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    conflicts = []

    # Check employee relations for potential conflicts
    try:
        relations = (
            db.query(EmployeeRelation)
            .filter(
                or_(
                    EmployeeRelation.employee_id == employee_id,
                    EmployeeRelation.internal_employee_id == employee_id,
                )
            )
            .all()
        )
    except Exception as exc:
        logger.warning("EmployeeRelation query failed (table may not exist): %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    for rel in relations:
        other_id = (
            rel.internal_employee_id
            if rel.employee_id == employee_id
            else rel.employee_id
        )
        other = db.query(Employee).filter(Employee.id == other_id).first()
        if other and other.department and employee.department:
            if other.department == employee.department:
                conflicts.append({
                    "type": "same_department",
                    "employee_id": other.id,
                    "employee_code": other.employee_code,
                    "relation_type": rel.relation_type,
                    "description": f"{employee.employee_code} and {other.employee_code} are in the same department ({employee.department}) with a {rel.relation_type} relation",
                    "severity": "medium",
                })

    # Check if employee's manager is a relative
    if employee.reporting_manager_id:
        manager = db.query(Employee).filter(Employee.id == employee.reporting_manager_id).first()
        if manager:
            for rel in relations:
                other_id = (
                    rel.internal_employee_id
                    if rel.employee_id == employee_id
                    else rel.employee_id
                )
                if other_id == manager.id:
                    conflicts.append({
                        "type": "manager_relation",
                        "employee_id": manager.id,
                        "employee_code": manager.employee_code,
                        "relation_type": rel.relation_type,
                        "description": f"{employee.employee_code}'s {rel.relation_type} ({manager.employee_code}) is their direct manager",
                        "severity": "high",
                    })

    return {
        "employee_id": employee_id,
        "employee_code": employee.employee_code,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
    }


@router.get("/hr/health-board", summary="Get performance health board for a manager's team")
def health_board_endpoint(
    manager_employee_id: int = Query(..., description="Manager's employee ID"),
    department: Optional[str] = Query(None, description="Filter by department"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a performance health board for all subordinates of a manager."""
    from domains.hr.services.performance.performance_service import get_performance_health_board
    return get_performance_health_board(db, manager_employee_id, department=department)


# === From succession.py ===
"""
Succession & Alumni Network Router
"""
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.succession.succession_service import get_alumni_network
from domains.hr.services.succession.succession_service import get_succession_matrix


@router.get("/bench-strength", response_model=dict)
async def get_bench_strength_report(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_succession_matrix(db)
    return service.get_bench_strength_report()


@router.get("/successors/{role_name}", response_model=List[dict])
async def get_successors(
    role_name: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_succession_matrix(db)
    return service.identify_successors(role_name)


@router.post("/alumni", response_model=dict)
async def grant_alumni_status(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_alumni_network(db)
    return service.grant_alumni_status(employee_id)


@router.get("/alumni/{employee_id}/eligibility", response_model=dict)
async def check_alumni_eligibility(
    employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_alumni_network(db)
    is_eligible = service.check_alumni_eligibility(employee_id)
    return {"employee_id": employee_id, "is_eligible": is_eligible}


# === From ess.py ===
"""ESS Portal — Employee Self-Service endpoints for profile, leave, attendance, payslips."""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from rbac import get_current_user
from infrastructure.database.database import get_db
from domains.governance.models.user import User
from domains.hr.models.employee_models import Employee
from domains.hr.services._auto_stubs import log_activity

logger = logging.getLogger(__name__)


def _get_employee(user: User, db: Session) -> Employee:
    """Get the Employee record for the current user."""
    emp = db.query(Employee).filter(Employee.user_id == user.id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee record not found")
    return emp


# ── Profile ──────────────────────────────────────────────────────


@router.get("/profile")
def ess_get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    row = db.execute(
        text("""
            SELECT e.*, u.email, u.full_name, u.role,
                   ou.name as unit_name, ou.path as unit_path
            FROM employees e
            JOIN users u ON u.id = e.user_id
            LEFT JOIN org_units ou ON ou.id = e.org_unit_id
            WHERE e.id = :eid
        """),
        {"eid": emp.id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Profile not found")
    return dict(row)


@router.put("/profile")
def ess_update_profile(
    phone: Optional[str] = None,
    address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None,
    emergency_contact_phone: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    updates = []
    params: dict = {"eid": emp.id}
    if phone is not None:
        updates.append("phone = :phone")
        params["phone"] = phone
    if address is not None:
        updates.append("address = :address")
        params["address"] = address
    if emergency_contact_name is not None:
        updates.append("emergency_contact_name = :ec_name")
        params["ec_name"] = emergency_contact_name
    if emergency_contact_phone is not None:
        updates.append("emergency_contact_phone = :ec_phone")
        params["ec_phone"] = emergency_contact_phone
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    db.execute(
        text(f"UPDATE employees SET {', '.join(updates)} WHERE id = :eid"),
        params,
    )
    db.commit()
    log_activity(db, emp.id, "profile_updated", "employee_profile", str(emp.id))
    return {"status": "updated", "fields": [u.split(" =")[0] for u in updates]}


# ── Leave ────────────────────────────────────────────────────────


@router.get("/leave/balance")
def ess_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT leave_type, year, allocated_days, used_days,
                   carried_forward_days, pending_days,
                   (allocated_days + carried_forward_days - used_days - pending_days) as remaining_days
            FROM employee_leave_ledgers
            WHERE employee_id = :eid
            ORDER BY year DESC, leave_type
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("/leave/request")
def ess_request_leave(
    leave_type: str,
    start_date: str,
    end_date: str,
    reason: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    result = db.execute(
        text("""
            INSERT INTO leave_requests
                (employee_id, leave_type, start_date, end_date, reason, status, created_at)
            VALUES
                (:eid, :leave_type, :start_date, :end_date, :reason, 'pending', :now)
            RETURNING id
        """),
        {
            "eid": emp.id,
            "leave_type": leave_type,
            "start_date": start_date,
            "end_date": end_date,
            "reason": reason,
            "now": text("NOW()"),
        },
    )
    leave_id = result.scalar()
    db.commit()
    log_activity(db, emp.id, "leave_requested", "leave_request", str(leave_id))
    return {"id": leave_id, "status": "pending"}


@router.get("/leave/history")
def ess_leave_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, leave_type, start_date, end_date, reason, status, created_at
            FROM leave_requests
            WHERE employee_id = :eid
            ORDER BY created_at DESC
            LIMIT 50
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Payslips ─────────────────────────────────────────────────────


@router.get("/payslips")
def ess_payslips(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, payroll_date, gross_amount, net_amount, deductions, status, created_at
            FROM payroll_records
            WHERE employee_id = :eid
            ORDER BY payroll_date DESC
            LIMIT 24
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Attendance ───────────────────────────────────────────────────


@router.get("/attendance")
def ess_attendance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, clock_in, clock_out, status, created_at
            FROM attendance_records
            WHERE employee_id = :eid
            ORDER BY clock_in DESC
            LIMIT 60
        """),
        {"eid": emp.id},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── OKRs ─────────────────────────────────────────────────────────


@router.get("/okrs")
def ess_okrs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    rows = db.execute(
        text("""
            SELECT id, title, description, objective_type, quarter, year,
                   status, progress_pct, confidence_level, created_at
            FROM okr_objectives
            WHERE employee_id = :eid
            ORDER BY year DESC, quarter DESC
        """),
        {"eid": emp.id},
    ).mappings().all()
    objectives = []
    for obj in rows:
        obj_dict = dict(obj)
        kpis = db.execute(
            text("""
                SELECT id, metric_name, metric_type, target_value, current_value, weight_pct
                FROM kpi_metrics
                WHERE objective_id = :oid
            """),
            {"oid": obj_dict["id"]},
        ).mappings().all()
        obj_dict["kpis"] = [dict(k) for k in kpis]
        objectives.append(obj_dict)
    return objectives


# ── Org Chart (self) ─────────────────────────────────────────────


@router.get("/org-chart")
def ess_org_chart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    emp = _get_employee(current_user, db)
    row = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.path, ou.depth, ou.parent_unit_id,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.id = :ouid
        """),
        {"ouid": emp.org_unit_id},
    ).mappings().first()

    if not row:
        return {"org_unit": None, "colleagues": [], "sub_units": []}

    org_unit = dict(row)

    # Colleagues in the same unit
    colleagues = db.execute(
        text("""
            SELECT e.id, u.full_name, e.employee_code, e.job_title
            FROM employees e
            JOIN users u ON u.id = e.user_id
            WHERE e.org_unit_id = :ouid AND e.id != :eid AND e.employment_status = 'active'
            ORDER BY u.full_name
        """),
        {"ouid": emp.org_unit_id, "eid": emp.id},
    ).mappings().all()

    # Sub-units
    sub_units = db.execute(
        text("""
            SELECT ou.id, ou.name, ou.depth,
                   e.id as manager_employee_id, u.full_name as manager_name
            FROM org_units ou
            LEFT JOIN employees e ON e.id = ou.manager_employee_id
            LEFT JOIN users u ON u.id = e.user_id
            WHERE ou.parent_unit_id = :ouid
            ORDER BY ou.name
        """),
        {"ouid": emp.org_unit_id},
    ).mappings().all()

    return {
        "org_unit": org_unit,
        "colleagues": [dict(c) for c in colleagues],
        "sub_units": [dict(s) for s in sub_units],
    }


# === From shift_handover.py ===
"""shift handover router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter


@router.get("/shift_handover/health")
def health():
    """Liveness probe for this router."""
    return {"status": "ok", "router": "shift_handover", "prefix": "/api/v1/shift-handover"}

