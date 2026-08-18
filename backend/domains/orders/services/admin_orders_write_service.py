"""Admin orders write service — transaction ownership for admin bulk order flows.

Layer-1 code (routers / controllers) must never drive session transaction state
directly; it delegates here so that only ``services/`` owns DB transactions.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
import structlog
from domains.orders.models.orders import Order
logger = structlog.get_logger(__name__)


def bulk_update_order_status(db: Session, ids: list, status: str) -> dict:
    """Set ``status`` on every order id in ``ids`` that still exists.

    Behaviour-preserving extraction of the inline loop formerly in
    ``routers.admin_orders_status.bulk_update_order_status``: one commit per
    request, count of actually-updated rows returned as-is.
    """
    updated = 0
    for oid in ids:
        o = db.query(Order).filter(Order.id == oid).first()
        if o:
            o.status = status
            updated += 1
    db.commit()
    return {"message": f"Status updated for {updated} orders", "updated": updated}


def discard_bulk_delete_transaction(db: Session) -> None:
    """Discard pending session state after a bulk delete removed nothing.

    ``services.orders.orders_write_service.delete_order_with_savepoint`` commits
    each successful deletion and rolls its own savepoint back on failure, so when
    no order at all could be deleted there is nothing worth keeping: drop whatever
    is still pending on the session.
    """
    db.rollback()
