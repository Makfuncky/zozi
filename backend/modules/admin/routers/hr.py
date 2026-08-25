"""Admin hr router — canonical."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from .admin_security_operations import router as admin_security_operations_router
from .employees import router as employees_router
from .hierarchy import router as hierarchy_router
from .operations import router as operations_router
from .payroll import router as payroll_router
from __future__ import annotations
from datetime import datetime
from datetime import datetime, timezone
from decimal import Decimal
from domains.audit.services.compliance_engine import GCCComplianceEngine
from domains.audit.services.compliance_engine import get_compliance_engine
from domains.comms.services._auto_stubs import AssetTrackingService
from domains.country.services.core.country_service import get_current_country_scope as get_country_scope
from domains.finance.services.ledger.general_ledger_service import ExpenseProcessingService
from domains.governance.models.admin import EmployeeExpense
from domains.hr.models.employee_models import Employee
from domains.hr.models.employee_models import EmployeeLeaveLedger
from domains.hr.services._auto_stubs import LeaveAccrualEngine
from domains.hr.services.employees.hr_service import check_coi_conflict
from domains.hr.services.employees.hr_service import create_coi_report
from domains.hr.services.employees.hr_service import create_disciplinary_case
from domains.hr.services.employees.hr_service import create_offboarding_case
from domains.hr.services.employees.hr_service import get_disciplinary_cases
from domains.hr.services.employees.hr_service import get_employee_graph
from domains.hr.services.employees.hr_service import get_offboarding_cases
from domains.hr.services.employees.hr_service import register_address
from domains.hr.services.employees.hr_service import register_dependent
from domains.hr.services.employees.hr_service import validate_gcc_compliance
from domains.hr.services.hierarchy.hierarchy_service import assign_matrix
from domains.hr.services.hierarchy.hierarchy_service import create_org_unit
from domains.hr.services.hierarchy.hierarchy_service import reassign_employee_manager
from domains.hr.services.hierarchy.hierarchy_service import rebuild_org_unit_paths
from domains.hr.services.hierarchy.hierarchy_service import refresh_authority_levels
from domains.hr.services.hierarchy.hierarchy_service import remove_matrix
from domains.hr.services.hierarchy.hierarchy_service import update_org_unit
from infrastructure.database.database import get_db
from infrastructure.utils.dependencies import require_admin
from pydantic import BaseModel
from rbac import get_current_user
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Any
from typing import Optional
import csv
import io
import logging
import logging as _l; _l.getLogger(__name__).warning("skip admin_security_operations: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip employees_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip hierarchy_router: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip operations: %s", _e)
import logging as _l; _l.getLogger(__name__).warning("skip payroll_router: %s", _e)

router = APIRouter(prefix="/api/v1/admin/hr", tags=["admin", "hr"])

@router.get("/pay-equity")
def export_pay_equity(db: Session = Depends(get_db)):
    """Export pay-equity metrics as a CSV file."""
    metrics = _compute_equity_rows(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["category", "avg_male", "avg_female", "disparity_percent", "flagged"])
    for m in metrics:
        writer.writerow([
            m["category"], m["avg_male"], m["avg_female"],
            m["disparity_percent"], m["flagged"],
        ])
    csv_data = buf.getvalue()
    headers = {
        "Content-Disposition": f"attachment; filename=pay-equity-{datetime.now(timezone.utc).date().isoformat()}.csv"
    }
    return Response(content=csv_data, media_type="text/csv", headers=headers)




@router.get("/employees/{employee_id}/leave-balance", response_model=LeaveBalanceResponse)
def get_leave_balance(
    employee_id: int,
    current_user: dict,
    scope: Optional[set[str]] = Depends(get_country_scope),
    db: Session = Depends(get_db),


@router.post("/employees/{employee_id}/expenses")
def submit_expense(
    employee_id: int,
    request: ExpenseSubmissionRequest,
    current_user: dict,
    db: Session = Depends(get_db),


@router.post("/employees/{employee_id}/assets")
def assign_asset(
    employee_id: int,
    asset_type: str,
    asset_tag: Optional[str] = None,
    current_user: dict = Depends(lambda: None),
    db: Session = Depends(get_db),


@router.get("/compliance/work-hours/{employee_id}")
def check_work_hours(employee_id: int, date: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(date.replace("Z", "+00:00"))
    return engine.validate_work_hours(employee_id, dt)




@router.get("/compliance/report/{employee_id}")
def get_report(employee_id: int, month: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(month + "-01")
    return engine.get_compliance_report(employee_id, dt)




@router.post("/compliance/overtime")
def calculate_overtime(employee_id: int, week_start: str, db: Session = Depends(get_db)):
    engine = get_compliance_engine(db)
    dt = datetime.fromisoformat(week_start + "-01")
    return {"overtime_hours": str(engine.calculate_overtime(employee_id, dt))}



@router.post("/hr/{employee_id}/addresses", status_code=201, tags=['hr'])
def register_address_route(
    employee_id: int,
    db: Session = Depends(get_db),
    address_data: dict = Body(...)


@router.post("/hr/{employee_id}/dependents", status_code=201, tags=['hr'])
def register_dependent_route(
    employee_id: int,
    db: Session = Depends(get_db),
    dependent_data: dict = Body(...)


@router.get("/hr/{employee_id}/coi-check", status_code=200, tags=['hr'])
def check_coi_conflict_route(
    employee_id: int,
    db: Session = Depends(get_db)


@router.post("/hr/{employee_id}/coi-report", status_code=201, tags=['hr'])
def create_coi_report_route(
    employee_id: int,
    db: Session = Depends(get_db),
    report_data: dict = Body(...)


@router.get("/hr/{employee_id}/compliance", status_code=200, tags=['hr'])
def validate_gcc_compliance_route(
    employee_id: int,
    db: Session = Depends(get_db)


@router.get("/hr/{employee_id}/graph", status_code=200, tags=['hr'])
def get_employee_graph_route(
    employee_id: int,
    db: Session = Depends(get_db)


@router.get("/hr/disciplinary", status_code=200, tags=['hr'])
def get_disciplinary_cases_route(
    db: Session = Depends(get_db)


@router.post("/hr/{employee_id}/disciplinary", status_code=201, tags=['hr'])
def create_disciplinary_case_route(
    employee_id: int,
    db: Session = Depends(get_db),
    case_data: dict = Body(...)


@router.get("/hr/offboarding", status_code=200, tags=['hr'])
def get_offboarding_cases_route(
    db: Session = Depends(get_db)


@router.post("/hr/{employee_id}/offboarding", status_code=201, tags=['hr'])
def create_offboarding_case_route(
    employee_id: int,
    db: Session = Depends(get_db),
    case_data: dict = Body(...)


@router.post("/hierarchy/org-units", status_code=201, tags=['hierarchy'], summary="Create an org unit")
def create_org_unit_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.put("/hierarchy/org-units/{unit_id}", status_code=200, tags=['hierarchy'], summary="Update an org unit")
def update_org_unit_route(
    unit_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/hierarchy/org-units/rebuild-paths", status_code=201, tags=['hierarchy'], summary="Rebuild org unit materialized paths")
def rebuild_org_unit_paths_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/hierarchy/employees/reassign-manager", status_code=201, tags=['hierarchy'], summary="Reassign an employee's manager")
def reassign_employee_manager_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.post("/hierarchy/authority-levels/refresh", status_code=201, tags=['hierarchy'], summary="Refresh authority levels")
def refresh_authority_levels_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)


@router.post("/hierarchy/matrix", status_code=201, tags=['hierarchy'], summary="Assign a matrix (dotted-line) relation")
def assign_matrix_route(
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
    payload: Any = Body(...)


@router.delete("/hierarchy/matrix/{relation_id}", status_code=200, tags=['hierarchy'], summary="Remove a matrix relation")
def remove_matrix_route(
    relation_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)

