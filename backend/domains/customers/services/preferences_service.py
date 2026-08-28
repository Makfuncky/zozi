"""Preferences service — per-user key/value preference store.

Persists customer preferences in the ``CustomerPreference`` table owned by the
customers domain (schema ``customer``). Reads/writes the canonical model in
``domains.customers.models`` (no cross-domain imports needed for the
underlying table).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from domains.customers.models import CustomerPreference
import structlog

logger = structlog.get_logger(__name__)


def _serialize(pref: CustomerPreference) -> Dict[str, Any]:
    return {
        "id": pref.id,
        "user_id": pref.user_id,
        "key": pref.key,
        "value": pref.value,
        "updated_at": pref.updated_at,
    }


class PreferencesService:
    """Service facade for per-customer preference read/update."""

    def __init__(self, db: Session):
        self.db = db

    def get_preferences(self, user_id: int) -> Dict[str, Any]:
        """Return the full preference set for a user as a ``{key: value}`` map
        plus the raw rows. Missing users produce an empty map (not 404) so
        brand-new accounts are not penalised.
        """
        rows = (
            self.db.query(CustomerPreference)
            .filter(
                CustomerPreference.user_id == int(user_id),
                CustomerPreference.is_deleted.is_(False),
            )
            .all()
        )
        return {
            "user_id": int(user_id),
            "items": [_serialize(r) for r in rows],
            "values": {r.key: r.value for r in rows},
        }

    def update_preferences(
        self, user_id: int, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Upsert one or more preference entries for a user.

        ``payload`` may be a ``{"values": {key: value, ...}}`` envelope or a
        flat ``{key: value, ...}`` mapping. Returns the updated preferences
        snapshot.
        """
        if not isinstance(payload, dict):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Payload must be a JSON object.",
            )
        if "values" in payload and isinstance(payload["values"], dict):
            updates: Dict[str, Any] = dict(payload["values"])
        else:
            updates = {k: v for k, v in payload.items() if k != "user_id"}

        if not updates:
            return self.get_preferences(user_id)

        rows = self._upsert_rows(user_id, updates.items())
        try:
            self.db.add_all(rows)
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            logger.warning(
                "preferences.update_conflict", user_id=user_id, error=str(exc)
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Conflict updating preferences.",
            ) from exc
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "preferences.update_failed", user_id=user_id, error=str(exc)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update preferences.",
            ) from exc
        return self.get_preferences(user_id)

    def _upsert_rows(
        self, user_id: int, items: Iterable
    ) -> Iterable[CustomerPreference]:
        """Upsert each (key, value) pair and yield the persisted rows."""
        for key, value in items:
            existing = (
                self.db.query(CustomerPreference)
                .filter(
                    CustomerPreference.user_id == int(user_id),
                    CustomerPreference.key == key,
                )
                .first()
            )
            if existing is None:
                yield CustomerPreference(user_id=int(user_id), key=key, value=value)
            else:
                existing.value = value
                existing.is_deleted = False
                yield existing
