"""Supplier payout write operations.

Owns the DB write for creating a supplier-initiated payout request.
Routers must not mutate the session directly for this operation.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models import Payout
import structlog
logger = structlog.get_logger(__name__)


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
