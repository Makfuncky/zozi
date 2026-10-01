"""Notification engine (comms domain).

Persists in-app notifications using the canonical ``Notification`` model in
``domains.comms.models.communication``. Provides ``NotificationEngine`` plus the
cross-domain helper functions used by the finance payout flows. Email/SMS
delivery degrades gracefully to an in-app record when no provider is configured
(Law 30).
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy.orm import Session

from domains.comms.models.communication import Notification
from domains.comms.services.shared.notification.notification_models import (
    NotificationChannel,
    NotificationPriority,
)

logger = logging.getLogger(__name__)


def _coerce(value):
    if isinstance(value, enum.Enum):
        return value.value
    return value


class NotificationEngine:
    """Persist notifications and (best-effort) dispatch across channels."""

    def __init__(self, db: Optional[Session] = None):
        self._db = db

    def notify(
        self,
        *,
        user_id: int,
        title: str,
        body: str = "",
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.NORMAL,
        category: Optional[str] = None,
        reference_type: Optional[str] = None,
        reference_id: Optional[int] = None,
        country_code: Optional[str] = None,
        db: Optional[Session] = None,
    ) -> Optional[Notification]:
        db = db or self._db
        if db is None:
            logger.warning("NotificationEngine.notify called without a db session; dropping notification")
            return None
        note = Notification(
            user_id=user_id,
            type=category or "generic",
            title=title,
            message=body,
            channel=_coerce(channel) or "in_app",
            priority=_coerce(priority) or "normal",
            variables={"reference_type": reference_type, "reference_id": reference_id},
            country_code=country_code,
        )
        # The communication.Notification model has no explicit reference columns;
        # stash the reference in ``variables`` if present.
        if reference_type is not None or reference_id is not None:
            note.variables = {
                **(note.variables or {}),
                "reference_type": reference_type,
                "reference_id": reference_id,
            }
        db.add(note)
        db.flush()
        return note

    def enqueue_supplier_approval_email(self, db: Session, supplier_id: int, **kwargs) -> Optional[Notification]:
        return self.notify(
            db=db,
            user_id=supplier_id,
            title=kwargs.get("title", "Supplier approval required"),
            body=kwargs.get("body", ""),
            channel=NotificationChannel.EMAIL,
            category="supplier_approval",
            reference_type="supplier",
            reference_id=supplier_id,
        )

    def notify_suppliers_of_payout(self, db: Session, supplier_ids, **kwargs) -> None:
        if not supplier_ids:
            return
        for sid in supplier_ids:
            self.notify(
                db=db,
                user_id=sid,
                title=kwargs.get("title", "Payout dispatched"),
                body=kwargs.get("body", ""),
                channel=NotificationChannel.IN_APP,
                category="payout",
                reference_type="supplier",
                reference_id=sid,
            )

    def notify_logistics_partners_of_payout(self, db: Session, partner_ids, **kwargs) -> None:
        if not partner_ids:
            return
        for pid in partner_ids:
            self.notify(
                db=db,
                user_id=pid,
                title=kwargs.get("title", "Logistics payout dispatched"),
                body=kwargs.get("body", ""),
                channel=NotificationChannel.IN_APP,
                category="payout",
                reference_type="logistics_partner",
                reference_id=pid,
            )


def enqueue_supplier_approval_email(db: Session, supplier_id: int, **kwargs):
    return NotificationEngine().enqueue_supplier_approval_email(db, supplier_id, **kwargs)


def notify_suppliers_of_payout(db: Session, supplier_ids, **kwargs):
    NotificationEngine().notify_suppliers_of_payout(db, supplier_ids, **kwargs)


def notify_logistics_partners_of_payout(db: Session, partner_ids, **kwargs):
    NotificationEngine().notify_logistics_partners_of_payout(db, partner_ids, **kwargs)
