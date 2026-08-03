"""
Product Verification Router — spec checks at supply chain touchpoints.
All business logic in controllers/product_verification_controller.py.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from data.db import get_db
from routers.auth import get_current_user
import controllers.product_verification_controller as ctrl
from utils.constants import MAX_BULK_ITEMS

router = APIRouter()


@router.get("/")
def list_verifications(
    product_id: Optional[int] = Query(None),
    order_id: Optional[int] = Query(None),
    verification_type: Optional[str] = Query(None),
    result: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List product verifications — filtered by role."""
    return ctrl.list_verifications(
        current_user, db,
        product_id=product_id,
        order_id=order_id,
        verification_type=verification_type,
        result=result,
        page=page,
        page_size=page_size,
    )


@router.post("/", status_code=201)
def create_verification(
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a product spec verification at a supply chain checkpoint."""
    return ctrl.create_verification(data, current_user, db)


class BulkVerificationUpdateBody(BaseModel):
    verification_ids: List[int]
    result: str
    notes: str | None = None

    @field_validator("verification_ids")
    @classmethod
    def limit_bulk_size(cls, value: List[int]) -> List[int]:
        if len(value) > MAX_BULK_ITEMS:
            raise ValueError(f"Cannot process more than {MAX_BULK_ITEMS} items at once")
        return value


@router.put("/bulk")
def bulk_update_verification_records(
    body: BulkVerificationUpdateBody,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Bulk-update verification record result and optional notes."""
    return ctrl.bulk_update_verifications(body.model_dump(), current_user, db)


@router.put("/{verification_id}")
def update_verification(
    verification_id: int,
    data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a single verification record result or notes."""
    return ctrl.update_verification(verification_id, data, current_user, db)


@router.get("/{verification_id}")
def get_verification(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a single verification record."""
    return ctrl.get_verification(verification_id, current_user, db)

