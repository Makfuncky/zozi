"""Supplier payout write operations.

Owns the DB write for creating a supplier-initiated payout request.
Routers must not mutate the session directly for this operation.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from domains.payments.models.payments import Payout
import structlog
logger = structlog.get_logger(__name__)


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
