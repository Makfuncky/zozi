"""Admin HR router — thin HTTP layer delegating to HR domain services."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Body
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.hr.services.employees.hr_service import (
    assign_asset,
    check_coi_conflict,
    create_coi_report,
    create_disciplinary_case,
    create_offboarding_case,
    get_employee_graph,
    get_leave_balance,
    list_disciplinary_cases,
    list_offboarding_cases,
    register_address,
    register_dependent,
    submit_expense,
    validate_gcc_compliance,
)

router = APIRouter(prefix="/api/v1/admin/hr", tags=["admin", "hr"])


class ExpenseSubmitRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field(default="OMR", max_length=3)
    category: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=1000)
    receipt_url: str | None = Field(None, max_length=500)


class AddressRequest(BaseModel):
    street: str = Field(..., min_length=1, max_length=300)
    city: str = Field(..., min_length=1, max_length=100)
    state: str | None = Field(None, max_length=100)
    country_code: str = Field(..., min_length=2, max_length=10)
    postal_code: str | None = Field(None, max_length=20)
    is_primary: bool = False


class DependentRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    relationship: str = Field(..., min_length=1, max_length=50)
    date_of_birth: str | None = None


class COIReportRequest(BaseModel):
    conflict_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    party_name: str | None = Field(None, max_length=200)


class DisciplinaryCaseRequest(BaseModel):
    case_type: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=2000)
    severity: str = Field("medium", max_length=20)


class OffboardingCaseRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)
    last_working_date: str | None = None
    notes: str | None = Field(None, max_length=2000)


@router.get("/employees/{employee_id}/leave-balance")
def get_leave_balance_route(
    employee_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.leave.read")),
):
    return get_leave_balance(employee_id=employee_id, current_user=_, db=db)


@router.post("/employees/{employee_id}/expenses")
def submit_expense_route(
    employee_id: int,
    request: ExpenseSubmitRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return submit_expense(employee_id=employee_id, expense_data=request.model_dump(), current_user=_, db=db)


@router.post("/employees/{employee_id}/assets")
def assign_asset_route(
    employee_id: int,
    asset_type: str = Body(...),
    asset_tag: str | None = Body(None),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return assign_asset(employee_id=employee_id, asset_type=asset_type, asset_tag=asset_tag, current_user=_, db=db)


@router.get("/compliance/work-hours/{employee_id}")
def check_work_hours(
    employee_id: int,
    date: str = Query(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.attendance.read")),
):
    from domains.hr.services.compliance import get_compliance_engine
    engine = get_compliance_engine(db)
    from datetime import datetime
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    return engine.validate_work_hours(employee_id, dt)


@router.get("/compliance/report/{employee_id}")
def get_report(
    employee_id: int,
    month: str = Query(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.attendance.read")),
):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(month + "-01")
    return engine.get_compliance_report(employee_id, dt)


@router.post("/compliance/overtime")
def calculate_overtime(
    employee_id: int,
    week_start: str = Query(...),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.attendance.manage")),
):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(week_start + "-01")
    return {"overtime_hours": str(engine.calculate_overtime(employee_id, dt))}


@router.post("/hr/{employee_id}/addresses", status_code=201, tags=["hr"])
def register_address_route(
    employee_id: int,
    address_data: AddressRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return register_address(employee_id=employee_id, address_data=address_data.model_dump(), db=db)


@router.post("/hr/{employee_id}/dependents", status_code=201, tags=["hr"])
def register_dependent_route(
    employee_id: int,
    dependent_data: DependentRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return register_dependent(employee_id=employee_id, dependent_data=dependent_data.model_dump(), db=db)


@router.get("/hr/{employee_id}/coi-check", status_code=200, tags=["hr"])
def check_coi_conflict_route(
    employee_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.read")),
):
    return check_coi_conflict(employee_id=employee_id, db=db)


@router.post("/hr/{employee_id}/coi-report", status_code=201, tags=["hr"])
def create_coi_report_route(
    employee_id: int,
    report_data: COIReportRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return create_coi_report(employee_id=employee_id, report_data=report_data.model_dump(), db=db)


@router.get("/hr/{employee_id}/compliance", status_code=200, tags=["hr"])
def validate_gcc_compliance_route(
    employee_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.read")),
):
    return validate_gcc_compliance(employee_id=employee_id, db=db)


@router.get("/hr/{employee_id}/graph", status_code=200, tags=["hr"])
def get_employee_graph_route(
    employee_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.read")),
):
    return get_employee_graph(employee_id=employee_id, db=db)


@router.get("/hr/disciplinary", status_code=200, tags=["hr"])
def get_disciplinary_cases_route(
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.read")),
):
    return list_disciplinary_cases(db, limit, cursor)


@router.post("/hr/{employee_id}/disciplinary", status_code=201, tags=["hr"])
def create_disciplinary_case_route(
    employee_id: int,
    case_data: DisciplinaryCaseRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return create_disciplinary_case(employee_id=employee_id, case_data=case_data.model_dump(), db=db)


@router.get("/hr/offboarding", status_code=200, tags=["hr"])
def get_offboarding_cases_route(
    limit: int = Query(50, ge=1, le=100),
    cursor: str | None = Query(None, description="Cursor for keyset pagination"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.read")),
):
    return list_offboarding_cases(db, limit, cursor)


@router.post("/hr/{employee_id}/offboarding", status_code=201, tags=["hr"])
def create_offboarding_case_route(
    employee_id: int,
    case_data: OffboardingCaseRequest,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.employee.manage")),
):
    return create_offboarding_case(employee_id=employee_id, case_data=case_data.model_dump(), db=db)
