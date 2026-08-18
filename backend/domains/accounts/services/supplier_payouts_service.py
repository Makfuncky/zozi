"""Auto-migrated service logic from routers/supplier_payouts.py."""
from __future__ import annotations

from fastapi import Depends, HTTPException

from sqlalchemy.orm import Session

from infrastructure.database.database import get_db

from infrastructure.database.schemas import PayoutOut

from domains.accounts.models.user import User
from domains.comms.models.suppliers import SupplierProfile
from domains.payments.models.payments import Payout

from infrastructure.utils.dependencies import require_supplier

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

def request_payout(payload: dict, current_user: User, db: Session):
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
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return {"status": "success", "payout": {"id": payout.id, "amount": float(payout.amount), "status": payout.status}}


