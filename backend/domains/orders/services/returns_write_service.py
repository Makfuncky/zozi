"""Backward-compatible re-export shim for return-request write operations.

This module intentionally performs NO imports at module-load time. The
canonical handlers live in `controllers.orders.returns_controller`, which imports this
shim back; resolving names lazily via module-level `__getattr__` breaks that
import-time cycle.
"""
from __future__ import annotations

import importlib
from typing import Any

_REEXPORTS: dict[str, tuple[str, str]] = {
    "create_return_request": ("controllers.orders.returns_controller", "create_return_request"),
    "update_return_request": ("controllers.orders.returns_controller", "update_return_request"),
}


def __getattr__(name: str) -> Any:
    if name in _REEXPORTS:
        module_path, attr = _REEXPORTS[name]
        return getattr(importlib.import_module(module_path), attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


from typing import Optional

from sqlalchemy.orm import Session

from _legacy.models import Notification
from db.database import SessionLocal
import structlog
logger = structlog.get_logger(__name__)


def create_return_notification(
    db: Optional[Session] = None,
    *,
    return_request=None,
    user_id: Optional[int] = None,
    country_code: str = "OM",
    type: Optional[str] = None,
    title: str = "",
    message: str = "",
    link: Optional[str] = None,
    is_read: bool = False,
    **kw,
) -> Notification:
    """Create a notification for a return-request event.

    Compatible with the legacy controller form ``create_return_notification(
    user_id=..., type=..., title=..., message=..., link=...)`` where ``db`` is
    not passed; in that case a short-lived session is opened and committed.
    """
    if return_request is not None:
        user_id = user_id if user_id is not None else getattr(return_request, "customer_id", None)
        if country_code == "OM":
            country_code = getattr(return_request, "country_code", None) or "OM"

    own_session = False
    if db is None:
        db = SessionLocal()
        own_session = True

    try:
        record = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link,
            type=type,
            is_read=bool(is_read),
            country_code=country_code,
            **kw,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        if own_session:
            db.close()
