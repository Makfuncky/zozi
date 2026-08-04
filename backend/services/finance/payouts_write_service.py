"""Service methods for payout write operations."""
from __future__ import annotations
from sqlalchemy.orm import Session
from data.models import Payout


def create_payout(db: Session, supplier_id: int, amount: float, **kwargs) -> Payout:
    """Create a new payout."""
    payout = Payout(supplier_id=supplier_id, amount=amount, **kwargs)
    db.add(payout)
    db.commit()
    db.refresh(payout)
    return payout


def update_payout_status(db: Session, payout_id: int, status: str) -> Payout | None:
    """Update payout status."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        return None
    payout.status = status
    db.commit()
    db.refresh(payout)
    return payout


def delete_payout(db: Session, payout_id: int) -> bool:
    """Delete a payout."""
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if not payout:
        return False
    db.delete(payout)
    db.commit()
    return True
