"""Admin orders write service — transaction ownership for admin bulk order flows.

Layer-1 code (routers / controllers) must never drive session transaction state
directly; it delegates here so that only ``services/`` owns DB transactions.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)


def discard_bulk_delete_transaction(db: Session) -> None:
    """Discard pending session state after a bulk delete removed nothing.

    ``services.orders.orders_write_service.delete_order_with_savepoint`` commits
    each successful deletion and rolls its own savepoint back on failure, so when
    no order at all could be deleted there is nothing worth keeping: drop whatever
    is still pending on the session.
    """
    db.rollback()
