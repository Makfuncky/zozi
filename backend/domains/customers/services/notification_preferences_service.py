"""Notification preferences service — per-channel, per-topic opt-in flags.

Persists customer notification preferences in the ``NotificationPreference``
table owned by the customers domain (schema ``customer``). The model supports
channel-wide defaults (topic NULL) and per-topic overrides.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.customers.models import NotificationPreference
import structlog

logger = structlog.get_logger(__name__)


_ALLOWED_CHANNELS = {"email", "sms", "push", "in_app", "whatsapp"}


def _serialize(row: NotificationPreference) -> Dict[str, Any]:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "channel": row.channel,
        "topic": row.topic,
        "enabled": row.enabled,
        "updated_at": row.updated_at,
    }


def _coerce_entries(
    payload: Dict[str, Any],
) -> List[Tuple[str, Optional[str], bool]]:
    """Normalise the payload into ``(channel, topic, enabled)`` triples.

    Accepts either an envelope ``{"entries": [...]}`` or a list of entries
    passed as a top-level list. Each entry must be a dict with ``channel`` and
    optional ``topic`` and ``enabled``.
    """
    if "entries" in payload and isinstance(payload["entries"], list):
        raw_entries = payload["entries"]
    elif isinstance(payload, list):
        raw_entries = payload
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Payload must include an 'entries' list.",
        )
    if not raw_entries:
        return []
    out: List[Tuple[str, Optional[str], bool]] = []
    for entry in raw_entries:
        if not isinstance(entry, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Each entry must be a JSON object.",
            )
        channel = entry.get("channel")
        if channel not in _ALLOWED_CHANNELS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"channel must be one of {sorted(_ALLOWED_CHANNELS)}",
            )
        topic = entry.get("topic")
        if topic is not None and not isinstance(topic, str):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="topic must be a string or null.",
            )
        enabled_raw = entry.get("enabled", True)
        if not isinstance(enabled_raw, bool):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="enabled must be a boolean.",
            )
        out.append((channel, topic, enabled_raw))
    return out


class NotificationPreferencesService:
    """Service facade for per-customer notification preferences."""

    def __init__(self, db: Session):
        self.db = db

    def get_notification_preferences(self, user_id: int) -> Dict[str, Any]:
        """Return all notification preferences for a user."""
        rows = (
            self.db.query(NotificationPreference)
            .filter(
                NotificationPreference.user_id == int(user_id),
                NotificationPreference.is_deleted.is_(False),
            )
            .order_by(
                NotificationPreference.channel.asc(),
                NotificationPreference.topic.asc().nulls_first(),
            )
            .all()
        )
        return {
            "user_id": int(user_id),
            "items": [_serialize(r) for r in rows],
        }

    def update_notification_preferences(
        self, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upsert notification-preference rows for a user."""
        entries = _coerce_entries(payload or {})
        if not entries:
            return self.get_notification_preferences(user_id)

        for row in self._upsert(user_id, entries):
            self.db.add(row)
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            logger.warning(
                "notification_prefs.update_conflict",
                user_id=user_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict updating notification preferences.",
            ) from exc
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "notification_prefs.update_failed",
                user_id=user_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification preferences.",
            ) from exc
        return self.get_notification_preferences(user_id)

    def _upsert(
        self, user_id: int, entries: Iterable[Tuple[str, Optional[str], bool]]
    ) -> Iterable[NotificationPreference]:
        for channel, topic, enabled in entries:
            existing = (
                self.db.query(NotificationPreference)
                .filter(
                    NotificationPreference.user_id == int(user_id),
                    NotificationPreference.channel == channel,
                    NotificationPreference.topic.is_(None) if topic is None
                    else NotificationPreference.topic == topic,
                )
                .first()
            )
            if existing is None:
                yield NotificationPreference(
                    user_id=int(user_id),
                    channel=channel,
                    topic=topic,
                    enabled=enabled,
                )
            else:
                existing.enabled = enabled
                existing.is_deleted = False
                yield existing
