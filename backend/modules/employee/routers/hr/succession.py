"""Succession & alumni network sub-router — thin delegators."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.security.dependencies import get_current_user
from infrastructure.database.database import get_db
from domains.hr.services.succession.succession_service import (
    get_alumni_network,
    get_succession_matrix,
)
from rbac.dependencies import require_feature

router = APIRouter()


@router.get("/bench-strength", response_model=dict)
async def get_bench_strength_report(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    service = get_succession_matrix(db)
    return service.get_bench_strength_report()


@router.get("/successors/{role_name}", response_model=list)
async def get_successors(role_name: str, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    service = get_succession_matrix(db)
    return service.identify_successors(role_name)


@router.post("/alumni", response_model=dict)
async def grant_alumni_status(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.create"))
):
    service = get_alumni_network(db)
    return service.grant_alumni_status(employee_id)


@router.get("/alumni/{employee_id}/eligibility", response_model=dict)
async def check_alumni_eligibility(employee_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db),
    _rf_gate: None = Depends(require_feature("hr.read"))
):
    service = get_alumni_network(db)
    return service.check_alumni_eligibility(employee_id)