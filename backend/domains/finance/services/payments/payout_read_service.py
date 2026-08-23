"""Supplier payout read service (W1).

Owns the read behind ``supplier_payout_controller.list_supplier_payouts`` so the
controller no longer reaches into the ORM directly.
"""
from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.suppliers import SupplierProfile
from domains.payments.models.payments import Payout
import structlog

logger = structlog.get_logger(__name__)


def list_supplier_payouts(current_user, db: Session) -> list[Payout]:
    """Return all payouts for the calling supplier's profile."""
    supplier = (
        db.query(SupplierProfile)
        .filter(SupplierProfile.user_id == current_user.id)
        .first()
    )
    if not supplier:
        raise HTTPException(404)
    return (
        db.query(Payout)
        .filter(Payout.supplier_id == supplier.id)
        .order_by(Payout.created_at.desc())
        .all()
    )
