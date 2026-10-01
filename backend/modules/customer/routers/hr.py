"""HR router for customer module — thin delegating to domain services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import get_current_user
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/customer/hr", tags=["customer", "hr"])


@router.get("/profile")
def get_hr_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.profile.read")),
):
    """Return the authenticated employee's HR profile."""
    from domains.hr.services.ess.ess_service import ess_get_profile
    return ess_get_profile(current_user, db)


@router.get("/leave/history")
def get_hr_leave_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.leave.read")),
):
    """Return the authenticated employee's leave request history."""
    from domains.hr.services.ess.ess_service import ess_leave_history
    return ess_leave_history(current_user, db)


@router.post("/leave/requests", status_code=201)
def create_hr_leave_request(
    leave_type: str = Query(..., description="Type of leave"),
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    reason: str = Query("", description="Reason for leave"),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.leave.create")),
):
    """Submit a new leave request for the authenticated employee."""
    from domains.hr.services.ess.ess_service import ess_request_leave
    return ess_request_leave(leave_type, start_date, end_date, reason, current_user, db)


@router.get("/payslips")
def get_hr_payslips(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.payslip.read")),
):
    """Return the authenticated employee's payslips."""
    from domains.hr.services.ess.ess_service import ess_payslips
    return ess_payslips(current_user, db)
