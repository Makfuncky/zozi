"""Supplier order operations service.

Owns the DB writes for supplier order status transitions. Routers and
controllers must not mutate the session directly for these operations.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from data.models import Order
import structlog
logger = structlog.get_logger(__name__)


def mark_order_prepared_if_processing(order: Order, db: Session) -> bool:
    """Transition an order from 'processing' to 'prepared' and commit.

    Returns True if the status changed, False if it was not in 'processing'.
    """
    if order.status == "processing":
        order.status = "prepared"
        db.commit()
        return True
    return False
