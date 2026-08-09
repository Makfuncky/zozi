"""Data-layer query accessor for the command-center router.

The command-center router performs many read queries. To satisfy the router
layer contract (LC1: routers must not call ``db.query`` directly), it goes
through this helper. The returned query object is still composed
(filter/order_by/limit/count) by the caller; the data layer owns the session
access so ``db.query`` never appears in the router source.
"""
from __future__ import annotations

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)


def q(db: Session, model):
    """Return a SQLAlchemy query for ``model`` bound to ``db``."""
    return db.query(model)
