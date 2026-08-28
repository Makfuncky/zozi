"""Supplier payout operations.

Consolidates supplier_payouts_service.py (list/request payouts) and
supplier_payout_service.py (ORM-based payout operations).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from infrastructure.database.schemas import PayoutOut
from domains.governance.ports import User
from domains.comms.ports import SupplierProfile
from domains.finance.ports import Payout
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


# ── ORM-based Payout Operations (merged from supplier_payout_service.py) ──────

def list_supplier_payouts(db: Session, supplier_id: int) -> list[Payout]:
    """Return payout requests for a supplier, newest first."""
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier_id)
        .order_by(Payout.created_at.desc())
        .all()
    )


def create_supplier_payout(
    db: Session,
    supplier_id: int,
    amount: float,
    method: str,
    notes: str,
) -> Payout:
    """Persist a new pending payout request and return the created row."""
    payout = Payout(
        supplier_id=supplier_id,
        amount=float(amount),
        method=method,
        notes=notes,
        status="pending",
    )
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


