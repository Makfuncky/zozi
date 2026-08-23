"""Treasury payout-approval / routing service.

Backs the payout-approval controller. Kept minimal so the routers ->
controllers -> services circuit (CIR2) is preserved for payout approvals and
batch dispatch.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from domains.finance.models.finance import PayoutBatch
from domains.payments.models.payments import Payout
import structlog
logger = structlog.get_logger(__name__)


def get_pending_payouts(db: Session, skip: int = 0, limit: int = 50, **kwargs: Any) -> list:
    return (
        db.query(Payout)
        .filter(Payout.status == "pending")
        .order_by(Payout.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def approve_payout(
    db: Session, payout_id: int, approved_by: Optional[int] = None, **kwargs: Any
) -> Optional[Payout]:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout is None:
        return None
    payout.status = "approved"
    db.commit()
    db.refresh(payout)
    return payout


def reject_payout(
    db: Session,
    payout_id: int,
    reason: Optional[str] = None,
    rejected_by: Optional[int] = None,
    **kwargs: Any,
) -> Optional[Payout]:
    payout = db.query(Payout).filter(Payout.id == payout_id).first()
    if payout is None:
        return None
    payout.status = "rejected"
    if reason:
        payout.notes = (payout.notes or "") + f"\nRejected: {reason}"
    db.commit()
    db.refresh(payout)
    return payout


def approve_batch(
    db: Session, batch_id: int, approved_by: Optional[int] = None, **kwargs: Any
) -> Optional[PayoutBatch]:
    batch = db.query(PayoutBatch).filter(PayoutBatch.id == batch_id).first()
    if batch is None:
        return None
    batch.status = "approved"
    db.commit()
    db.refresh(batch)
    return batch


def reject_batch(
    db: Session,
    batch_id: int,
    reason: Optional[str] = None,
    rejected_by: Optional[int] = None,
    **kwargs: Any,
) -> Optional[PayoutBatch]:
    batch = db.query(PayoutBatch).filter(PayoutBatch.id == batch_id).first()
    if batch is None:
        return None
    batch.status = "rejected"
    db.commit()
    db.refresh(batch)
    return batch


def dispatch_batch(
    db: Session, batch_id: int, dispatched_by: Optional[int] = None, **kwargs: Any
) -> Optional[PayoutBatch]:
    batch = db.query(PayoutBatch).filter(PayoutBatch.id == batch_id).first()
    if batch is None:
        return None
    batch.status = "dispatched"
    db.commit()
    db.refresh(batch)
    return batch
