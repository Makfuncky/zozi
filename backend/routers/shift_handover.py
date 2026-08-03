"""
Shift Handover Router
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from data.db import get_db
from data.dependencies_auth import get_current_user
from services.shift_handover import ShiftHandoverService, get_shift_handover_service

router = APIRouter(tags=["shift-handover"])


@router.post("/sessions")
def create_handover(
    outgoing_employee_id: int,
    country_code: Optional[str] = None,
    notes: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_shift_handover_service(db)
    return service.create_handover(outgoing_employee_id, country_code, notes)


@router.post("/sessions/{session_id}/assign")
def assign_incoming(
    session_id: int,
    incoming_employee_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_shift_handover_service(db)
    return service.assign_incoming(session_id, incoming_employee_id)


@router.post("/sessions/{session_id}/tasks")
def add_task(
    session_id: int,
    description: str,
    priority: str = "normal",
    assigned_to: Optional[int] = None,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_shift_handover_service(db)
    return service.add_task(session_id, description, priority, assigned_to)


@router.post("/sessions/{session_id}/acknowledge")
def acknowledge_handover(
    session_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = get_shift_handover_service(db)
    return service.acknowledge_handover(session_id)


@router.get("/pending")
def get_pending_handovers(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    employee_id = current_user.get("employee_id") or current_user.get("id")
    service = get_shift_handover_service(db)
    return {"handovers": service.get_pending_handovers(employee_id)}
