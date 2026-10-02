"""Catalog domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Canonical event type constants (shared contract)
EVENT_PRODUCT_CREATED = "catalog.product.created"
EVENT_PRODUCT_UPDATED = "catalog.product.updated"
EVENT_PRODUCT_DELETED = "catalog.product.deleted"

# ── base ──────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class CatalogEvent:
    """Base class for all catalog-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d


# ── product lifecycle events ───────────────────────────────────────────────


@dataclass(frozen=True)
class ProductDeleted(CatalogEvent):
    product_id: int = 0
    product_name: str = ""
    supplier_id: int = 0
    event_type: str = field(default=EVENT_PRODUCT_DELETED, init=False)


# ── publish helpers (integrate with canonical event bus) ──────────────────


def publish_product_deleted(
    product_id: int,
    product_name: str,
    supplier_id: int,
) -> None:
    """Publish a ProductDeleted event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish

        event = ProductDeleted(
            product_id=product_id,
            product_name=product_name,
            supplier_id=supplier_id,
        )
        publish(EVENT_PRODUCT_DELETED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish ProductDeleted event: %s", exc)


__all__ = [
    # Event type constants
    "EVENT_PRODUCT_CREATED",
    "EVENT_PRODUCT_UPDATED",
    "EVENT_PRODUCT_DELETED",
    # Event classes
    "CatalogEvent",
    "ProductDeleted",
    # Publish helpers
    "publish_product_deleted",
]
