"""Employee HR Router — thin router delegating to domain services."""

import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.country.utils.country_rls import enforce_country_access
from domains.hr.services.hr_employee_service import get_hr_employee_service
from domains.hr.services.hierarchy.hierarchy_service import (
    get_org_chart as get_hierarchy_org_chart,
    get_org_unit_subtree,
    get_org_unit_path,
    get_employees_in_subtree,
    rebuild_paths,
    get_user_chain,
    get_all_subordinates,
    get_team_members,
    can_manage,
    reassign_manager,
    backfill_authority_levels,
)
from domains.governance.ports import get_approval_chain
from domains.hr.services.payroll.payroll_engine import PayrollEngine
from domains.hr.services.payroll.payroll_service import (
    process_payroll_batch as svc_process_payroll_batch,
    approve_payroll_batch as svc_approve_payroll_batch,
    calculate_employee_payroll,
    get_employee_payslips,
    employee_bank_accounts,
    verify_bank_account,
    payroll_status as svc_payroll_status,
)
from domains.hr.services.learning.lms_service import (
    assign_training as _assign_training_svc,
    check_permission_lock,
    create_training_module,
    get_training_progress,
    verify_training_completion,
)
from domains.hr.services.succession.succession_service import (
    get_alumni_network,
    get_succession_matrix,
)
from domains.hr.services.perf_service import (
    create_objective as svc_create_objective,
    get_objective_tree,
    update_objective_progress as svc_update_objective_progress,
    create_kpi_metric,
    record_kpi_value,
    get_kpi_dashboard,
    submit_performance_review,
    get_employee_reviews,
    compute_performance_health,
    get_performance_health_board,
)
from rbac.dependencies import require_feature
from domains.hr.services.hierarchy.hierarchy_service import (
    assign_matrix_manager,
    remove_matrix_manager,
    get_matrix_managers,
    get_matrix_subordinates,
    detect_circular_reporting,
)
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

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employee/hr", tags=["employee", "hr"])


# ══════════════════════════════════════════════════════════════════
#  Pydantic Schemas
# ══════════════════════════════════════════════════════════════════


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


class PayrollApproveBody(BaseModel):
    batch_id: str
    approved: bool = True
    notes: Optional[str] = None


# In-memory approval state (production would use DB)
PENDING_PAYROLL_APPROVALS: dict = {}


# ══════════════════════════════════════════════════════════════════
#  Offices
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/offices")
def list_offices(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_offices(code, db)


@router.post("/admin/{code}/offices")
def create_office(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_office(code, body or {}, db)


@router.put("/admin/{code}/offices/{office_id}")
def update_office(code: str, office_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.update")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_office(office_id, body or {}, db)


@router.delete("/admin/{code}/offices/{office_id}")
def delete_office(code: str, office_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.delete")
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).delete_office(office_id, db)
    return {"message": "Office deleted"}


# ══════════════════════════════════════════════════════════════════
#  Employee CRUD
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees")
def list_employees(
    code: str, department: Optional[str] = Query(None),
    status: Optional[str] = Query(None, alias="employment_status"),
    q: Optional[str] = Query(None), limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
):
    require_feature("hr.read")
    require_feature("hr.create")
    require_feature("hr.update")
    require_feature("hr.delete")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employees(code, db, department=department, status=status, query=q, limit=limit)


@router.post("/admin/{code}/employees")
def create_employee(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee(code, body or {}, current_user, db)


@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_hr_employee_service(db).get_employee(employee_id, db)


@router.patch("/admin/{code}/employees/{employee_id}")
def update_employee(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.update")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_employee(employee_id, body or {}, current_user, db)


@router.delete("/admin/{code}/employees/{employee_id}")
def delete_employee(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.delete")
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).delete_employee(employee_id, current_user, db)
    return {"message": "Employee deleted"}


# ══════════════════════════════════════════════════════════════════
#  Employee Documents
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/{employee_id}/documents")
def list_employee_documents(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_documents(employee_id, db)


@router.post("/admin/{code}/employees/{employee_id}/documents")
def create_employee_document(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_document(employee_id, body or {}, db)


@router.patch("/admin/{code}/employees/documents/{doc_id}")
def update_employee_document_status(code: str, doc_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.update")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).update_employee_document_status(doc_id, body or {}, db)


# ══════════════════════════════════════════════════════════════════
#  Employee Addresses & Dependents
# ══════════════════════════════════════════════════════════════════


@router.get("/employees/{employee_id}/addresses")
def list_employee_addresses(
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("hr.read")
    return get_hr_employee_service(db).list_employee_addresses(employee_id)


@router.get("/employees/{employee_id}/dependents")
def list_employee_dependents(
    employee_id: int = Path(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_feature("hr.read")
    return get_hr_employee_service(db).list_employee_dependents(employee_id)


# ══════════════════════════════════════════════════════════════════
#  Attendance
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/{employee_id}/attendance")
def list_attendance(
    code: str, employee_id: int,
    from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=365), db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_feature("hr.create")
    require_feature("hr.read")
    require_feature("hr.update")
    require_feature("hr.delete")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_attendance(employee_id, db, from_date=from_date, to_date=to_date, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/check-in")
def check_in(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).check_in_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/check-out")
def check_out(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).check_out_employee(employee_id, body or {}, db)


@router.post("/admin/{code}/employees/{employee_id}/geo-check-in")
def geo_check_in(code: str, employee_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).check_in_with_geo(employee_id, body or {}, db)


# ══════════════════════════════════════════════════════════════════
#  Employee Relations
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/{employee_id}/relations")
def list_relations(code: str, employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_relations(employee_id, db)


@router.post("/admin/{code}/employees/{employee_id}/relations")
def create_relation(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_relation(employee_id, body or {}, db)


@router.delete("/admin/{code}/employees/relations/{relation_id}")
def delete_relation(code: str, relation_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.delete")
    enforce_country_access(code, db=db)
    get_hr_employee_service(db).remove_employee_relation(relation_id, db)
    return {"message": "Relation removed"}


# ══════════════════════════════════════════════════════════════════
#  Work Logs
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/{employee_id}/work-logs")
def list_work_logs(
    code: str, employee_id: int,
    from_date: Optional[str] = Query(None), to_date: Optional[str] = Query(None),
    status: Optional[str] = Query(None), limit: int = Query(50, ge=1, le=365),
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user),
):
    require_feature("hr.create")
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_work_logs(employee_id, db, from_date=from_date, to_date=to_date, status=status, limit=limit)


@router.post("/admin/{code}/employees/{employee_id}/work-logs")
def create_work_log(code: str, employee_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_work_log(employee_id, body or {}, db)


@router.patch("/admin/{code}/employees/work-logs/{log_id}/approve")
def approve_work_log(code: str, log_id: int, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.update")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).approve_work_log(log_id, body or {}, current_user, db)


# ══════════════════════════════════════════════════════════════════
#  QR IAM
# ══════════════════════════════════════════════════════════════════


@router.post("/employees/{employee_id}/qr-token")
def generate_qr_token(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).generate_qr_login_token(employee_id, db)


@router.post("/employees/qr-login")
def qr_login(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).validate_qr_login(body.get("qr_token", ""), db)


@router.post("/geo/validate")
def validate_geo(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).validate_geo_location(
        body.get("latitude", 0), body.get("longitude", 0), body.get("office_id", 0), db
    )


# ══════════════════════════════════════════════════════════════════
#  Employee Roles
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employee-roles")
def list_employee_roles(code: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_employee_roles(code, db)


@router.post("/admin/{code}/employee-roles")
def create_employee_role(code: str, body: dict = None, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).create_employee_role(code, body or {}, db)


# ══════════════════════════════════════════════════════════════════
#  Leave Requests
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/leave-requests")
def list_leave_requests(code: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
                        db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_leave_requests(db, code, page=page, limit=limit)


@router.post("/admin/{code}/employees/leave-requests")
def create_leave_request(code: str, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    data = body or {}
    return get_hr_employee_service(db).create_leave_request(data.get("employee_id", 0), data, current_user, db)


@router.patch("/admin/{code}/employees/leave-requests/{leave_id}")
def update_leave_request_status(code: str, leave_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.update")
    enforce_country_access(code, db=db)
    status = (body or {}).get("status", "").lower()
    return get_hr_employee_service(db).update_leave_request_status(db, leave_id, status, current_user)


# ══════════════════════════════════════════════════════════════════
#  Shifts
# ══════════════════════════════════════════════════════════════════


@router.get("/admin/{code}/employees/shifts")
def list_shifts(code: str, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100),
                db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    enforce_country_access(code, db=db)
    return get_hr_employee_service(db).list_shifts(db, code, page=page, limit=limit)


@router.post("/admin/{code}/employees/shifts")
def create_shift_roster(code: str, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    enforce_country_access(code, db=db)
    data = body or {}
    return get_hr_employee_service(db).create_shift_roster(data.get("employee_id", 0), data, current_user, db)


# ══════════════════════════════════════════════════════════════════
#  Kill Switch
# ══════════════════════════════════════════════════════════════════


@router.post("/employees/{employee_id}/kill-switch")
def kill_switch_employee(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    return get_hr_employee_service(db).kill_switch(employee_id, current_user, db)


# ══════════════════════════════════════════════════════════════════
#  Public Endpoint
# ══════════════════════════════════════════════════════════════════


@router.get("/public")
def list_employees_public(db: Session = Depends(get_db)):
    try:
        return get_hr_employee_service(db).list_employees_public()
    except Exception as e:
        return {"error": str(e)}


# ══════════════════════════════════════════════════════════════════
#  ESS Portal — Employee Self-Service
# ══════════════════════════════════════════════════════════════════


@router.get("/profile")
def ess_get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    emp_id = current_user.get("id")
    return get_employee_profile(db, emp_id)


@router.put("/profile")
def ess_update_profile(
    phone: Optional[str] = None, address: Optional[str] = None,
    emergency_contact_name: Optional[str] = None, emergency_contact_phone: Optional[str] = None,
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
):
    require_feature("hr.create")
    require_feature("hr.update")
    require_feature("hr.read")
    return update_employee_profile(db, current_user.get("id"), phone, address, emergency_contact_name, emergency_contact_phone)


@router.get("/leave/balance")
def ess_leave_balance(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return get_leave_balance(db, current_user.get("id"))


@router.post("/leave/request")
def ess_request_leave(
    leave_type: str, start_date: str, end_date: str, reason: str,
    current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
):
    require_feature("hr.read")
    require_feature("hr.create")
    return svc_create_leave_request(db, current_user.get("id"), leave_type, start_date, end_date, reason)


@router.get("/leave/history")
def ess_leave_history(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return get_leave_history(db, current_user.get("id"))


@router.get("/payslips")
def ess_payslips(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return get_payslips(db, current_user.get("id"))


@router.get("/attendance")
def ess_attendance(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return svc_get_attendance(db, current_user.get("id"))


@router.get("/okrs")
def ess_okrs(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return get_okrs(db, current_user.get("id"))


@router.get("/org-chart")
def ess_org_chart(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    return svc_get_org_chart(db, None, current_user.get("id"))


# ══════════════════════════════════════════════════════════════════
#  Org Units & Hierarchy
# ══════════════════════════════════════════════════════════════════


@router.get("/org-units")
def list_org_units(country_code: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_hr_employee_service(db).list_org_units(db, country_code=country_code)


@router.post("/org-units", status_code=201)
def create_org_unit(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return get_hr_employee_service(db).create_org_unit(db, payload)


@router.put("/org-units/{unit_id}")
def update_org_unit(unit_id: int, payload: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.update")
    return get_hr_employee_service(db).update_org_unit(db, unit_id, payload or {})


@router.get("/org-chart/{org_unit_id}")
def org_chart_detail(org_unit_id: Optional[int] = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_hierarchy_org_chart(db, org_unit_id)


@router.get("/org-units/{unit_id}/subtree")
def org_unit_subtree(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"subtree": get_org_unit_subtree(db, unit_id)}


@router.get("/org-units/{unit_id}/path")
def org_unit_ancestor_path(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"path": get_org_unit_path(db, unit_id)}


@router.get("/org-units/{unit_id}/employees")
def employees_in_subtree(unit_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"employees": get_employees_in_subtree(db, unit_id)}


@router.post("/org-units/rebuild-paths")
def rebuild_org_unit_paths(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    updated = rebuild_paths(db)
    return {"message": f"Rebuilt paths for {updated} org units"}


@router.get("/employee/{user_id}/chain")
def employee_chain(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"chain": get_user_chain(db, user_id)}


@router.get("/employee/{user_id}/subordinates")
def employee_subordinates(user_id: int, direct_only: bool = Query(False), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    if direct_only:
        return {"subordinates": get_team_members(db, user_id)}
    return {"subordinates": get_all_subordinates(db, user_id)}


@router.get("/employee/{user_id}/can-manage/{target_user_id}")
def check_can_manage(user_id: int, target_user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"can_manage": can_manage(db, user_id, target_user_id)}


@router.post("/reassign-manager")
def reassign_employee_manager(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    result = reassign_manager(db, payload.get("employee_user_id", 0), payload.get("new_manager_user_id", 0))
    return result


@router.post("/backfill-authority-levels")
def refresh_authority_levels(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    updated = backfill_authority_levels(db)
    return {"message": f"Updated {updated} employee authority levels"}


# ══════════════════════════════════════════════════════════════════
#  Matrix / Dotted-Line Management
# ══════════════════════════════════════════════════════════════════


@router.post("/matrix/assign")
def assign_matrix(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    result = assign_matrix_manager(db, employee_id=payload.get("employee_id", 0), matrix_manager_id=payload.get("matrix_manager_id", 0), relation_type=payload.get("relation_type", "matrix_manager"), notes=payload.get("notes"))
    return result


@router.delete("/matrix/{relation_id}")
def remove_matrix(relation_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.delete")
    result = remove_matrix_manager(db, relation_id)
    return result


@router.get("/employee/{employee_id}/matrix-managers")
def matrix_managers(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"matrix_managers": get_matrix_managers(db, employee_id)}


@router.get("/employee/{manager_id}/matrix-subordinates")
def matrix_subordinates(manager_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}


@router.get("/detect-circular")
def detect_circular(employee_id: int = Query(...), proposed_manager_id: int = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    is_circular = detect_circular_reporting(db, employee_id, proposed_manager_id)
    return {"is_circular": is_circular, "message": "Circular reporting detected" if is_circular else "No circular relationship"}


@router.post("/approval-chain")
def approval_chain(payload: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return {"approvers": get_approval_chain(db, employee_id=payload.get("employee_id", 0), resource_type=payload.get("resource_type", "leave"), min_authority_level=payload.get("min_authority_level"))}


# ══════════════════════════════════════════════════════════════════
#  Country Scope & Localization
# ══════════════════════════════════════════════════════════════════


@router.get("/country-scope/{user_id}")
def user_country_scope(user_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_hr_employee_service(db).get_user_country_scope(db, user_id)


@router.post("/country-scope/switch")
def switch_country_scope(country_code: str = Query(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    user_id = int(current_user.get("id", 0))
    normalized = country_code.upper()
    role = str(current_user.get("role", "")).lower()
    return get_hr_employee_service(db).switch_country_scope(db, user_id, normalized, role)


@router.get("/localization/{country_code}")
def country_localization(country_code: str = Query(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    normalized = country_code.upper()
    return get_hr_employee_service(db).get_country_localization(db, normalized)


# ══════════════════════════════════════════════════════════════════
#  Authority Level Helpers
# ══════════════════════════════════════════════════════════════════


@router.get("/required-authority/{resource_type}")
def required_authority_for_resource(
    resource_type: str = Path(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    require_feature("hr.read")
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
#  LMS — Learning Management System
# ══════════════════════════════════════════════════════════════════


@router.post("/modules")
def create_module(module_data: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return create_training_module(module_data, db)


@router.post("/{employee_id}/assign")
def lms_assign_training(employee_id: int, module_id: str = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return _assign_training_svc(employee_id, module_id, db)


@router.post("/{employee_id}/complete")
def complete_training(employee_id: int, module_id: str = Query(...), quiz_score: float = Query(...), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return verify_training_completion(employee_id, module_id, quiz_score, db)


@router.get("/{employee_id}/lock/{permission}")
def check_lock(employee_id: int, permission: str, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return check_permission_lock(employee_id, permission, db)


@router.get("/{employee_id}/progress")
def training_progress(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_training_progress(employee_id, db)


# ══════════════════════════════════════════════════════════════════
#  OKR Endpoints
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
#  Payroll
# ══════════════════════════════════════════════════════════════════


@router.post("/payroll/calculate/{employee_id}")
def calculate_employee_payroll(employee_id: int, month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2020), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return calculate_employee_payroll(employee_id, month, year, db, current_user)


@router.post("/payroll/batch")
def process_payroll_batch(country_code: str = Query(..., min_length=2, max_length=10), month: int = Query(..., ge=1, le=12), year: int = Query(..., ge=2020), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return svc_process_payroll_batch(country_code, month, year, db, current_user)


@router.post("/payroll/approve")
def approve_payroll_batch(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    from domains.hr.services.payroll.payroll_service import PayrollApproveBody
    approve_body = PayrollApproveBody(**body)
    return svc_approve_payroll_batch(approve_body, db, current_user)


@router.get("/payroll/payslips/{employee_id}")
def get_employee_payslips(employee_id: int, page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_employee_payslips(employee_id, db, current_user)


@router.get("/payroll/bank-accounts/{employee_id}")
def employee_bank_accounts_route(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return employee_bank_accounts(employee_id, db, current_user)


@router.post("/payroll/bank-accounts/{account_id}/verify")
def verify_bank_account_route(account_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return verify_bank_account(account_id, db, current_user)


@router.get("/payroll/status/{country_code}")
def payroll_status_route(country_code: str = Query(..., min_length=2, max_length=10), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return svc_payroll_status(country_code, db)


# ══════════════════════════════════════════════════════════════════
#  OKR / KPI / Performance Endpoints (from performance.py)
# ══════════════════════════════════════════════════════════════════


@router.post("/hr/okr", summary="Create an OKR objective")
def create_objective_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    try:
        return svc_create_objective(db=db, **body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hr/okr/{objective_id}", summary="Get objective tree with children")
def get_objective_tree_endpoint(objective_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    result = get_objective_tree(db, objective_id)
    if not result:
        raise HTTPException(status_code=404, detail="Objective not found")
    return result


@router.patch("/hr/okr/{objective_id}/progress", summary="Update objective progress")
def update_objective_progress_endpoint(objective_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.update")
    return svc_update_objective_progress(db, objective_id, **(body or {}))


@router.post("/hr/kpi", summary="Create a KPI metric under an objective")
def create_kpi_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    return create_kpi_metric(db=db, **body)


@router.put("/hr/kpi/{kpi_id}/value", summary="Record a KPI value")
def record_kpi_value_endpoint(kpi_id: int, body: dict = None, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.update")
    if body is None:
        raise HTTPException(status_code=422, detail="Request body required")
    return record_kpi_value(db, kpi_id, **body)


@router.get("/hr/kpi/employee/{employee_id}", summary="Get KPI dashboard for an employee")
def get_kpi_dashboard_endpoint(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_kpi_dashboard(db, employee_id)


@router.post("/hr/reviews", summary="Submit a 360 performance review")
def submit_review_endpoint(body: dict, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.create")
    try:
        return submit_performance_review(db=db, **body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/hr/reviews/{employee_id}", summary="Get reviews for an employee")
def get_employee_reviews_endpoint(employee_id: int, review_cycle: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_employee_reviews(db, employee_id, review_cycle=review_cycle)


@router.get("/hr/health/{employee_id}", summary="Compute performance health for an employee")
def compute_health_endpoint(employee_id: int, db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.update")
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
    require_feature("hr.read")
    try:
        from domains.hr.models.employee_models import EmployeeRelation
    except Exception as exc:
        logger.warning("EmployeeRelation model not available: %s", exc)
        return {"employee_id": employee_id, "has_conflicts": False, "conflicts": []}

    return get_hr_employee_service(db).coi_check(employee_id)


@router.get("/hr/health-board", summary="Get performance health board for a manager's team")
def health_board_endpoint(manager_employee_id: int = Query(...), department: Optional[str] = Query(None), db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    require_feature("hr.read")
    return get_performance_health_board(db, manager_employee_id, department=department)


# ══════════════════════════════════════════════════════════════════
#  Succession & Alumni Network
# ══════════════════════════════════════════════════════════════════


@router.get("/bench-strength", response_model=dict)
async def get_bench_strength_report(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    service = get_succession_matrix(db)
    return service.get_bench_strength_report()


@router.get("/successors/{role_name}", response_model=list)
async def get_successors(role_name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    service = get_succession_matrix(db)
    return service.identify_successors(role_name)


@router.post("/alumni", response_model=dict)
async def grant_alumni_status(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.create")
    service = get_alumni_network(db)
    return service.grant_alumni_status(employee_id)


@router.get("/alumni/{employee_id}/eligibility", response_model=dict)
async def check_alumni_eligibility(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("hr.read")
    service = get_alumni_network(db)
    return service.check_alumni_eligibility(employee_id)


# ══════════════════════════════════════════════════════════════════
#  Health Checks
# ══════════════════════════════════════════════════════════════════


@router.get("/shift_handover/health")
def shift_handover_health():
    """Liveness probe for shift handover router."""
    return {"status": "ok", "router": "shift_handover", "prefix": "/api/v1/shift-handover"}


@router.get("/hr_dashboard/health")
def hr_dashboard_health():
    """Liveness probe for HR dashboard router."""
    return {"status": "ok", "router": "hr_dashboard", "prefix": "/api/v1"}
