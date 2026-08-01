"""Supplier payouts sub-router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.database import get_db
from models import Payout, SupplierProfile, User
from db.schemas import PayoutOut
from utils.dependencies import require_supplier

from services.write_helpers import add_and_flush, commit_and_refresh
router = APIRouter()


@router.get("", response_model=list[PayoutOut])
def list_payouts(current_user: User = Depends(require_supplier), db: Session = Depends(get_db)):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .all()
    )


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
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier:
        raise HTTPException(404, "Supplier profile not found")

    amount = payload.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(400, "A positive payout amount is required")

    payout = Payout(
        supplier_id=supplier.id,
        amount=float(amount),
        method=payload.get("method", "bank"),
        notes=payload.get("notes", "Supplier-initiated payout request"),
        status="pending",
    )
    add_and_flush(db, payout)
    commit_and_refresh(db, payout)
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}

