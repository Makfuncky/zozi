"""
Succession & Alumni Network Router
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from models.employee_models import Employee
from services.succession_service import get_succession_matrix, get_alumni_network, SuccessionMatrix, AlumniNetwork
from db.database import get_db
from controllers.auth_controller import get_current_user

router = APIRouter()


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
