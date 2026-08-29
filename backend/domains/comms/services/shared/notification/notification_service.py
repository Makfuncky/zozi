"""Notification service layer (comms domain).

Thin CRUD surface over the canonical ``Notification`` model in
``domains.comms.models.communication``.
"""
from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from domains.comms.models.communication import Notification
from domains.comms.services.shared.notification.notification_models import (
    NotificationChannel,
    NotificationPriority,
)
from domains.comms.services.shared.notification.notification_engine import NotificationEngine

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session):
        self._db = db
        self._engine = NotificationEngine(db)

    def create(
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
    ) -> Notification:
        return self._engine.notify(
            db=self._db,
            user_id=user_id,
            title=title,
            body=body,
            channel=channel,
            priority=priority,
            category=category,
            reference_type=reference_type,
            reference_id=reference_id,
            country_code=country_code,
        )

    def list_for_user(self, user_id: int, *, unread_only: bool = False, limit: int = 50):
        stmt = select(Notification).where(
            Notification.user_id == user_id, Notification.is_deleted == False  # noqa: E712
        )
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)  # noqa: E712
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        return self._db.execute(stmt).scalars().all()

    def mark_read(self, notification_id: int, user_id: int) -> bool:
        from sqlalchemy import func

        note = self._db.get(Notification, notification_id)
        if note is None or note.user_id != user_id:
            return False
        note.is_read = True
        note.read_at = func.now()
        self._db.flush()
        return True

    def mark_all_read(self, user_id: int) -> int:
        notes = self.list_for_user(user_id, unread_only=True, limit=1000)
        from sqlalchemy import func

        for n in notes:
            n.is_read = True
            n.read_at = func.now()
        self._db.flush()
        return len(notes)

    def delete(self, notification_id: int, user_id: int) -> bool:
        note = self._db.get(Notification, notification_id)
        if note is None or note.user_id != user_id:
            return False
        note.is_deleted = True
        self._db.flush()
        return True

    def unread_count(self, user_id: int) -> int:
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False,  # noqa: E712
            Notification.is_deleted == False,  # noqa: E712
        )
        return len(self._db.execute(stmt).scalars().all())


def create_notification_service(db: Session) -> NotificationService:
    return NotificationService(db)


def get_user_notifications(db: Session, user_id: int, *, unread_only: bool = False, limit: int = 50):
    return NotificationService(db).list_for_user(user_id, unread_only=unread_only, limit=limit)


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> bool:
    return NotificationService(db).mark_read(notification_id, user_id)


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    return NotificationService(db).mark_all_read(user_id)


def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    return NotificationService(db).delete(notification_id, user_id)


def get_unread_count(db: Session, user_id: int) -> int:
    return NotificationService(db).unread_count(user_id)
