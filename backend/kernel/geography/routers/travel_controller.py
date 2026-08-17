"""controllers.geography.travel_controller (CONTROLLERS layer).

Wraps ``services.geography.travel_service`` and exposes the corporate travel
endpoints. The HTTP contract is declared with ``core.route_contract`` decorators
so ``routers/generated/auto_router.py`` can auto-generate the thin router — the
previous hand-written ``routers/travel.py`` only instantiated the service and
passed args through, which is controller-level orchestration that now lives
here.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from core.route_contract import post

from domains.country.services.travel_service import get_travel_service

@post(
    "/requests",
    deps=["user", "db"],
    query=["employee_id", "destination_country", "start_date", "end_date", "purpose"],
)
def create_travel_request(
    employee_id: int,
    destination_country: str,
    start_date: str,
    end_date: str,
    purpose: str,
    current_user: dict = None,
    db: Session = None,
):
    """Create a corporate travel request."""
    service = get_travel_service(db)
    return service.create_travel_request(
        employee_id=employee_id,
        destination_country=destination_country,
        start_date=start_date,
        end_date=end_date,
        purpose=purpose,
    )

@post(
    "/expenses/validate",
    deps=["user", "db"],
    query=["employee_id", "amount", "currency", "description", "receipt_image_hash"],
)
def validate_expense(
    employee_id: int,
    amount: float,
    currency: str,
    description: str,
    receipt_image_hash: Optional[str] = None,
    current_user: dict = None,
    db: Session = None,
):
    """Validate a travel expense."""
    service = get_travel_service(db)
    return service.validate_expense(
        employee_id=employee_id,
        amount=amount,
        currency=currency,
        description=description,
        receipt_image_hash=receipt_image_hash,
    )

@post("/requests/{request_id}/approve", deps=["user", "db"])
def approve_travel_request(request_id: int, current_user: dict = None, db: Session = None):
    """Approve a travel request on behalf of the current user."""
    service = get_travel_service(db)
    return service.approve_travel_request(request_id, int(current_user["sub"]))

__all__ = ["create_travel_request", "validate_expense", "approve_travel_request"]
