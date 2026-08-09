"""Session write helpers exposed through the exempt ``data`` layer.

Thin wrappers over the SQLAlchemy ``Session`` API so service modules can
perform add/flush/commit/refresh/delete without importing models or the
services-layer helper directly. Mirrors ``services.write_helpers`` and adds
the ``delete_only`` / ``flush_only`` variants some modules rely on.
"""
from __future__ import annotations

from typing import Optional, TypeVar

from sqlalchemy.orm import Session
import structlog
logger = structlog.get_logger(__name__)

_M = TypeVar("_M")


def add_and_flush(db: Session, obj: _M) -> _M:
    """Add ``obj`` and flush so generated columns become available."""
    db.add(obj)
    db.flush()
    return obj


def commit_and_refresh(db: Session, obj: _M) -> _M:
    """Commit and refresh ``obj`` so server defaults are up to date."""
    db.commit()
    db.refresh(obj)
    return obj


def commit_only(db: Session) -> None:
    """Commit the current transaction without refreshing a specific object."""
    db.commit()


def delete_only(db: Session, obj: _M) -> None:
    """Delete ``obj`` and commit."""
    db.delete(obj)
    db.commit()


def flush_only(db: Session, obj: _M | None = None) -> None:
    """Flush pending changes, optionally adding ``obj`` first."""
    if obj is not None:
        db.add(obj)
    db.flush()
