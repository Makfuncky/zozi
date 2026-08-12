"""DB write helpers for the payment provider adapters.

Per ``ARCHITECTURE_DIAGRAM.md`` (rule V4), providers must not perform database
writes directly -- persistence belongs in the services layer. The payment
adapters under ``providers/payments`` used to call ``db.add`` / ``db.commit`` /
``db.refresh`` / ``db.flush`` inline. Those low-level write calls are delegated
here instead.

This module imports ONLY ``models`` and SQLAlchemy so that it can be imported by
the provider layer without creating an import cycle (the provider layer is
imported by several services, e.g. ``services/gateways/payments.py``).
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from models import ProcessedWebhookEvent


def commit(db: Session) -> None:
    """Flush pending changes and commit the current transaction."""
    db.commit()


def flush(db: Session) -> None:
    """Flush pending changes to the database without committing."""
    db.flush()


def refresh(db: Session, instance: Any) -> None:
    """Refresh ``instance`` from the database."""
    db.refresh(instance)


def add(db: Session, instance: Any) -> None:
    """Stage ``instance`` for insertion/upsert."""
    db.add(instance)


def add_and_commit(db: Session, instance: Any) -> None:
    """Stage ``instance`` and commit."""
    db.add(instance)
    db.commit()


def add_refresh(db: Session, instance: Any) -> Any:
    """Stage ``instance``, commit, and refresh it. Returns ``instance``."""
    db.add(instance)
    db.commit()
    db.refresh(instance)
    return instance


def record_webhook_event(
    db: Session,
    event_id: str,
    processor: str,
    payload_hash: Optional[str] = None,
) -> None:
    """Idempotently record a processed webhook event for ``processor``."""
    if payload_hash is not None:
        db.add(
            ProcessedWebhookEvent(
                event_id=event_id,
                processor=processor,
                payload_hash=payload_hash,
            )
        )
    else:
        db.add(ProcessedWebhookEvent(event_id=event_id, processor=processor))
    db.commit()
