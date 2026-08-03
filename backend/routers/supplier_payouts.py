"""Supplier payouts sub-router.

All DB work is delegated to ``services/supplier/supplier_payouts_service.py``
so this router stays a thin delegator (layering: LC1/W1).
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from data.db import get_db
from data.models import User
from data.schemas import PayoutOut
from utils.dependencies import require_supplier

from services.supplier.supplier_payouts_service import (
    create_payout_request,
    list_supplier_payouts,
)

router = APIRouter()


@router.get("", response_model=list[PayoutOut])
def list_payouts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    return list_supplier_payouts(db, current_user.id, skip=skip, limit=limit)


@router.post("/request")
def request_payout(
    payload: dict,
    current_user: User = Depends(require_supplier),
    db: Session = Depends(get_db),
):
    """Create a payout request from the supplier.

    Body:
      amount (float): Payout amount
      method (str, optional): Payment method, default "bank"
      notes (str, optional): Supplier notes
    """
    return create_payout_request(db, current_user.id, payload)
