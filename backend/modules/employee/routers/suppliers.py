"""Employee suppliers router — consolidated from 7 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import Optional, List

from rbac import get_current_user
from rbac.dependencies import require_feature
from infrastructure.database.database import get_db
from domains.hr.ports import get_travel_service
from domains.comms.ports import (
    NotificationChannel,
    NotificationPriority,
    list_support_tickets,
    create_support_ticket,
    get_support_ticket,
    reply_to_support_ticket,
)

router = APIRouter(prefix="/api/v1/employee/suppliers", tags=["employee", "suppliers"])


# === From travel.py ===
"""
Corporate Travel Router
"""


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
    require_feature("suppliers.profile.write")
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
    require_feature("suppliers.profile.write")
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
    require_feature("suppliers.profile.write")
    service = get_travel_service(db)
    return service.approve_travel_request(request_id, int(current_user["sub"]))


# === From tickets.py ===
"""Support tickets router."""


def _user_to_dict(user: dict) -> dict:
    """Normalize current_user dict to the shape expected by comms services."""
    return {"id": user.get("id") or user.get("sub"), "role": user.get("role")}


@router.get("")
def list_tickets(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    require_feature("suppliers.profile.read")
    return list_support_tickets(db, _user_to_dict(current_user), page=page, page_size=page_size)


@router.post("", status_code=201)
def create_ticket(payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("suppliers.profile.write")
    return create_support_ticket(db, payload, _user_to_dict(current_user))


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int, current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("suppliers.profile.read")
    return get_support_ticket(db, ticket_id, _user_to_dict(current_user))


@router.post("/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("suppliers.profile.write")
    return reply_to_support_ticket(db, ticket_id, payload, _user_to_dict(current_user))


@router.post("/{ticket_id}/messages", status_code=201)
def add_message(ticket_id: int, payload: dict = Body(...), current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    require_feature("suppliers.profile.write")
    return reply_to_support_ticket(db, ticket_id, payload, _user_to_dict(current_user))


# === From notifications.py ===
"""
Notification Engine API Endpoints
"""


# === From push_notifications.py ===
"""push notifications router.

Functional router placeholder. Implement domain endpoints here,
delegating to the appropriate controller/service.
"""
from fastapi import APIRouter



@router.get("/push_notifications/health")
def health():
    """Liveness probe for this router."""
    require_feature("suppliers.profile.read")
    return {"status": "ok", "router": "push_notifications", "prefix": "/api/v1/push-notifications"}


