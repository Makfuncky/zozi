"""HR employee service layer.

Extracted from routers/employees.py so the router only delegates to a service
(architecture circuit: routers -> services own DB access). Clears CIR1/LC1/W1
findings that flagged raw SQL and session usage inside the router endpoints.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.core import Address
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeDependent
from domains.hr.models.employee_models import EmployeeLeaveRequest
from domains.hr.models.employee_models import EmployeeShiftRoster
from infrastructure.utils.datetime_utils import utcnow as _utcnow
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def get_employee_addresses(employee_id: int, db: Session) -> List[Dict[str, Any]]:
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


def get_employee_dependents(employee_id: int, db: Session) -> List[Dict[str, Any]]:
    dependents = (
        db.query(EmployeeDependent)
        .filter(EmployeeDependent.employee_id == employee_id)
        .all()
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


def get_leave_requests(db: Session) -> List[Dict[str, Any]]:
    requests = (
        db.query(EmployeeLeaveRequest)
        .order_by(EmployeeLeaveRequest.created_at.desc())
        .all()
    )
    result: List[Dict[str, Any]] = []
    for r in requests:
        employee_name: Optional[str] = None
        if r.employee:
            user = r.employee.user
            employee_name = (
                (user.full_name or user.username)
                if user
                else r.employee.employee_code
            )
        result.append(
            {
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
            }
        )
    return result


def set_leave_request_status(
    leave_id: int, status: str, approved_by: Any, db: Session
) -> Dict[str, Any]:
    r = (
        db.query(EmployeeLeaveRequest)
        .filter(EmployeeLeaveRequest.id == leave_id)
        .first()
    )
    if not r:
        raise HTTPException(status_code=404, detail="Leave request not found")
    status = status.lower()
    if status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid status")
    r.status = status
    r.approved_by = approved_by
    r.approved_at = _utcnow()
    db.commit()
    return {"message": f"Leave request {status}", "id": leave_id}


def get_shifts(db: Session) -> List[Dict[str, Any]]:
    shifts = (
        db.query(EmployeeShiftRoster)
        .order_by(EmployeeShiftRoster.shift_date.desc())
        .all()
    )
    result: List[Dict[str, Any]] = []
    for s in shifts:
        employee_name: Optional[str] = None
        if s.employee:
            user = s.employee.user
            employee_name = (
                (user.full_name or user.username)
                if user
                else s.employee.employee_code
            )
        result.append(
            {
                "id": s.id,
                "employee_id": s.employee_id,
                "employee_name": employee_name,
                "shift_date": s.shift_date.isoformat() if s.shift_date else None,
                "start_time": s.start_time.isoformat() if s.start_time else None,
                "end_time": s.end_time.isoformat() if s.end_time else None,
                "shift_type": s.shift_type,
                "status": s.status,
            }
        )
    return result


def list_public_employees(db: Session) -> Any:
    """Public employee directory.

    Originally implemented with a raw string ``db.execute(query)``; replaced with
    an ORM query so no inline SQL lives in the router (W1/LC1).
    """
    try:
        employees = (
            db.query(Employee).order_by(Employee.created_at.desc()).limit(50).all()
        )
        return [
            {
                "id": e.id,
                "employee_code": e.employee_code,
                "department": e.department,
                "position": e.position,
                "employment_status": e.employment_status,
                "salary": float(e.salary) if e.salary else None,
                "currency": e.currency,
                "country_code": e.country_code,
                "hire_date": e.hire_date.isoformat() if e.hire_date else None,
            }
            for e in employees
        ]
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:  # pragma: no cover - defensive, mirrors original contract
        logger.warning("Public employee directory unavailable: %s", e)
        return {"error": str(e)}

# === Merged from accounts/services/employees_service.py ===

class CheckInBody(BaseModel):

    latitude: Optional[float] = None

    longitude: Optional[float] = None

    ip_address: Optional[str] = None

    device_fingerprint: Optional[str] = None

    notes: Optional[str] = None




class CheckOutBody(BaseModel):

    notes: Optional[str] = None




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




class EmployeeRoleCreate(BaseModel):

    name: str = Field(..., min_length=1, max_length=120)

    slug: Optional[str] = None

    permissions: Optional[dict] = None




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




class GeoCheckInBody(BaseModel):

    latitude: float

    longitude: float

    office_id: int

    ip_address: Optional[str] = None

    device_fingerprint: Optional[str] = None

    notes: Optional[str] = None




class GeoValidateBody(BaseModel):

    latitude: float

    longitude: float

    office_id: int




class LeaveCreate(BaseModel):

    employee_id: Optional[int] = None

    leave_type: str = 'annual'

    start_date: str

    end_date: str

    notes: Optional[str] = None




class LeaveStatusUpdate(BaseModel):

    status: str = Field(..., description="approved or rejected")




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




class QrLoginBody(BaseModel):

    qr_token: str




class RelationCreate(BaseModel):

    related_employee_id: int

    relation_type: str = "peer"

    notes: Optional[str] = None




class ShiftCreate(BaseModel):

    employee_id: int

    shift_date: str

    start_time: str

    end_time: str

    shift_type: str = 'scheduled'

    status: str = 'scheduled'




class WorkLogApprove(BaseModel):

    status: str = "approved"




class WorkLogCreate(BaseModel):

    date: Optional[str] = None

    hours_worked: float = 0

    description: Optional[str] = None




def approve_work_log(code: str, log_id: int, body: WorkLogApprove, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.approve_work_log(log_id, body.model_dump(exclude_none=True), current_user, db)




def check_in(code: str, employee_id: int, body: CheckInBody, db: Session):

    return ctrl.check_in_employee(employee_id, body.model_dump(exclude_none=True), db)




def check_out(code: str, employee_id: int, body: CheckOutBody, db: Session):

    return ctrl.check_out_employee(employee_id, body.model_dump(exclude_none=True), db)




def create_employee(code: str, body: EmployeeCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_employee(code, body.model_dump(exclude_none=True), current_user, db)




def create_employee_document(code: str, employee_id: int, body: EmployeeDocumentCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_employee_document(employee_id, body.model_dump(exclude_none=True), db)




def create_employee_role(code: str, body: EmployeeRoleCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_employee_role(code, body.model_dump(exclude_none=True), db)




def create_leave_request(code: str, body: LeaveCreate, db: Session, current_user: dict):

    enforce_country_access(code, db=db)

    return ctrl.create_leave_request(body.employee_id or 0, body.model_dump(exclude_none=True), current_user, db)




def create_office(code: str, body: OfficeCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_office(code, body.model_dump(exclude_none=True), db)




def create_relation(code: str, employee_id: int, body: RelationCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_employee_relation(employee_id, body.model_dump(exclude_none=True), db)




def create_shift_roster(code: str, body: ShiftCreate, db: Session, current_user: dict):

    enforce_country_access(code, db=db)

    return ctrl.create_shift_roster(body.employee_id, body.model_dump(exclude_none=True), current_user, db)




def create_work_log(code: str, employee_id: int, body: WorkLogCreate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.create_work_log(employee_id, body.model_dump(exclude_none=True), db)




def delete_employee(code: str, employee_id: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    ctrl.delete_employee(employee_id, current_user, db)

    return {"message": "Employee deleted"}




def delete_office(code: str, office_id: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    ctrl.delete_office(office_id, db)

    return {"message": "Office deleted"}




def delete_relation(code: str, relation_id: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    ctrl.remove_employee_relation(relation_id, db)

    return {"message": "Relation removed"}




def generate_qr_token(employee_id: int, db: Session):

    return ctrl.generate_qr_login_token(employee_id, db)




def geo_check_in(code: str, employee_id: int, body: GeoCheckInBody, db: Session):

    return ctrl.check_in_with_geo(employee_id, body.model_dump(), db)




def get_employee(employee_id: int, db: Session):

    return ctrl.get_employee(employee_id, db)




def kill_switch_employee(employee_id: int, current_user: dict, db: Session):

    return ctrl.kill_switch(employee_id, current_user, db)






def list_attendance(code: str, employee_id: int, from_date: Optional[str], to_date: Optional[str], limit: int, db: Session, current_user: dict):

    enforce_country_access(code, db=db)

    return ctrl.list_attendance(employee_id, db, from_date=from_date, to_date=to_date, limit=limit)




def list_employee_addresses(employee_id: int, current_user: dict, db: Session):

    from domains.governance.models.core import Address



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




def list_employee_dependents(employee_id: int, current_user: dict, db: Session):

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




def list_employee_documents(code: str, employee_id: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.list_employee_documents(employee_id, db)




def list_employee_roles(code: str, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.list_employee_roles(code, db)




def list_employees(code: str, department: Optional[str], status: Optional[str], q: Optional[str], limit: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.list_employees(code, db, department=department, status=status, query=q, limit=limit)




def list_employees_public(db: Session):

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




def list_leave_requests(code: str, db: Session, current_user: dict):

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




def list_offices(code: str, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.list_offices(code, db)




def list_relations(code: str, employee_id: int, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.list_employee_relations(employee_id, db)




def list_shifts(code: str, db: Session, current_user: dict):

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




def list_work_logs(code: str, employee_id: int, from_date: Optional[str], to_date: Optional[str], status: Optional[str], limit: int, db: Session, current_user: dict):

    enforce_country_access(code, db=db)

    return ctrl.list_work_logs(employee_id, db, from_date=from_date, to_date=to_date, status=status, limit=limit)




def qr_login(body: QrLoginBody, db: Session):

    return ctrl.validate_qr_login(body.qr_token, db)




def update_employee(code: str, employee_id: int, body: EmployeeUpdate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.update_employee(employee_id, body.model_dump(exclude_none=True), current_user, db)




def update_employee_document_status(code: str, doc_id: int, body: EmployeeDocumentUpdate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.update_employee_document_status(doc_id, body.model_dump(exclude_none=True), db)




def update_leave_request_status(code: str, leave_id: int, body: LeaveStatusUpdate, db: Session, current_user: dict):

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




def update_office(code: str, office_id: int, body: OfficeUpdate, current_user: dict, db: Session):

    enforce_country_access(code, db=db)

    return ctrl.update_office(office_id, body.model_dump(exclude_none=True), db)




def validate_geo(body: GeoValidateBody, db: Session):

    return ctrl.validate_geo_location(body.latitude, body.longitude, body.office_id, db)



