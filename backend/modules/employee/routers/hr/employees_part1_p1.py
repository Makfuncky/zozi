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
from hr.router import router  # noqa: F401



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
