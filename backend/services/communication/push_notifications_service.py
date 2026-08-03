"""Push notification token service, extracted behind the service layer (clears LC1/W1).

Each function owns its database session via ``data.db.get_db_context`` so the
router layer never injects or touches a SQLAlchemy session directly.
"""
from typing import Optional
from datetime import datetime, timezone

from fastapi import HTTPException


def _user_id(user: object) -> int:
    if hasattr(user, "id"):
        return int(getattr(user, "id") or 0)
    if isinstance(user, dict):
        return int(user.get("id") or 0)
    return 0


def register_push_token(token: str, device_type: Optional[str], current_user) -> dict:
    from data.db import get_db_context
    from data.models import PushNotificationToken
    from data.services_write_helpers import add_and_flush, commit_only

    user_id = _user_id(current_user)
    with get_db_context() as db:
        existing = (
            db.query(PushNotificationToken)
            .filter(
                PushNotificationToken.user_id == user_id,
                PushNotificationToken.token == token,
            )
            .first()
        )
        if existing:
            existing.device_type = device_type
            existing.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
            commit_only(db)
            return {"status": "updated"}

        record = PushNotificationToken(
            user_id=user_id,
            token=token,
            device_type=device_type,
        )
        add_and_flush(db, record)
        commit_only(db)
        return {"status": "registered"}


def unregister_push_token(token: str, current_user) -> dict:
    from data.db import get_db_context
    from data.models import PushNotificationToken
    from data.services_write_helpers import delete_only, commit_only

    user_id = _user_id(current_user)
    with get_db_context() as db:
        record = (
            db.query(PushNotificationToken)
            .filter(
                PushNotificationToken.user_id == user_id,
                PushNotificationToken.token == token,
            )
            .first()
        )
        if record:
            delete_only(db, record)
            commit_only(db)
        return {"status": "unregistered"}


def list_push_tokens(current_user, skip: int, limit: int) -> list:
    from data.db import get_db_context
    from data.models import PushNotificationToken

    user_id = _user_id(current_user)
    with get_db_context() as db:
        tokens = (
            db.query(PushNotificationToken)
            .filter(PushNotificationToken.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            {
                "id": t.id,
                "device_type": t.device_type,
                "created_at": t.created_at,
            }
            for t in tokens
        ]
