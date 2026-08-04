"""
Supplier Payouts Service
========================
Owns the DB work that previously lived in ``routers/supplier/supplier_payouts.py``
so the router stays a thin delegator (layering: LC1/W1).

Routers must not perform ``db.query``/writes directly; they delegate here.
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from data.models import Payout, SupplierProfile
from data.services_write_helpers import add_and_flush, commit_and_refresh


def list_supplier_payouts(db: Session, user_id: int, skip: int = 0, limit: int = 20) -> list[Payout]:
    """Return a page of payouts belonging to the supplier owning ``user_id``."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .offset(skip).limit(limit)
        .all()
    )


def create_payout_request(db: Session, user_id: int, payload: dict) -> dict:
    """Create a payout request from the supplier.

    Body:
      amount (float): Payout amount
      method (str, optional): Payment method, default "bank"
      notes (str, optional): Supplier notes
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
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
