"""
Corporate Travel Router
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data.models_employee_models import Employee
from services.travel_service import get_travel_service, TravelService
from data.db import get_db
from data.dependencies_auth import get_current_user

router = APIRouter()


@router.post("/requests", response_model=dict)
async def create_travel_request(
    employee_id: int,
    destination_country: str,
    start_date: str,
    end_date: str,
    purpose: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.create_travel_request(
        employee_id=employee_id,
        destination_country=destination_country,
        start_date=start_date,
        end_date=end_date,
        purpose=purpose
    )


@router.post("/expenses/validate", response_model=dict)
async def validate_expense(
    employee_id: int,
    amount: float,
    currency: str,
    description: str,
    receipt_image_hash: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.validate_expense(
        employee_id=employee_id,
        amount=amount,
        currency=currency,
        description=description,
        receipt_image_hash=receipt_image_hash
    )


@router.post("/requests/{request_id}/approve", response_model=dict)
async def approve_travel_request(
    request_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = get_travel_service(db)
    return service.approve_travel_request(request_id, int(current_user["sub"]))
