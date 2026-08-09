"""Supplier batch-publish write service.

Owns the DB transaction verbs (``flush`` / ``commit`` / ``rollback``) that were
previously issued directly from ``routers.public_batch_upload_access.batch_publish_products``.

Layer-1 code (routers, controllers, middleware) must never drive a ``Session``
write verb itself; instead it delegates to the functions below, which take the
request-scoped ``db: Session`` as their first argument and own the verb.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)


def flush_supplier_product(db: Session) -> None:
    """Flush the pending supplier product for the current batch item."""
    db.flush()


def commit_supplier_products(db: Session) -> None:
    """Commit the whole batch-publish transaction."""
    db.commit()


def rollback_supplier_products(db: Session) -> None:
    """Roll back the batch-publish transaction on a failure."""
    db.rollback()
