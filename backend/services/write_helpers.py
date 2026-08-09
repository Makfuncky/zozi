"""Small SQLAlchemy session helpers used across the treasury service layer.

Centralises the common add/flush/commit/refresh patterns so individual
service functions stay readable and consistent. These are thin wrappers over
the SQLAlchemy ``Session`` API -- no business logic lives here.
"""
from __future__ import annotations

from typing import Any, Optional, TypeVar

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)

_M = TypeVar("_M")


def add_and_flush(db: Session, obj: _M) -> _M:
    """Add ``obj`` to the session and flush so its generated columns (ids,
    defaults) become available without a full commit."""
    db.add(obj)
    db.flush()
    return obj


def commit_and_refresh(db: Session, obj: _M) -> _M:
    """Commit the current transaction and refresh ``obj`` so its
    database-generated/ server-default fields are up to date."""
    db.commit()
    db.refresh(obj)
    return obj


def commit_only(db: Session) -> None:
    """Commit the current transaction without refreshing any specific object."""
    db.commit()
