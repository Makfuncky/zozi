"""Supplier payouts sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infrastructure.database.database import get_db
from infrastructure.database.schemas import PayoutOut
from domains.governance.models.user import User
from infrastructure.utils.dependencies import require_supplier
from domains.suppliers.services.supplier_payout_service import create_supplier_payout
from domains.suppliers.services.supplier_payout_service import list_supplier_payouts
from domains.suppliers.services.supplier_profile_write_service import get_supplier_profile

router = APIRouter(prefix="/api/v1/supplier")


@router.get("", response_model=list[PayoutOut])
def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    profile = get_supplier_profile(current_user, db)
    return list_supplier_payouts(db, profile.id)


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
    profile = get_supplier_profile(current_user, db)

    amount = payload.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(400, "A positive payout amount is required")

    payout = create_supplier_payout(
        db,
        profile.id,
        float(amount),
        payload.get("method", "bank"),
        payload.get("notes", "Supplier-initiated payout request"),
    )
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}

