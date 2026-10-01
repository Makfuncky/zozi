"""Bulk order operations service.

Owns the DB writes for admin bulk order status updates. Routers and
controllers must not mutate the session directly for this operation.
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from domains.orders.models.orders import Order
import structlog
logger = structlog.get_logger(__name__)


def bulk_update_order_status(ids: List[int], status: str, db: Session) -> dict:
    """Set ``status`` on every order in ``ids`` that exists. Returns a count."""
    updated = 0
    for oid in ids:
        o = db.query(Order).filter(Order.id == oid).first()
        if o:
            o.status = status
            updated += 1
    db.commit()
    return {"message": f"Status modified for {updated} orders", "updated": updated}
