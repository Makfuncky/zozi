"""Shared DB write helpers — the canonical home for session write primitives.

Controllers must not call ``db.add/commit/refresh/delete/flush/rollback``
directly (governance rule W1). These helpers wrap those primitives so the
service layer owns every session write. They are intentionally trivial;
domain-specific write logic should live in a dedicated ``*_write_service``
module, which may reuse these primitives.
"""
from typing import Any

from sqlalchemy.orm import Session


def add_and_flush(db: Session, obj: Any) -> Any:
    """Stage a new ORM object in the session and flush to obtain its PK."""
    db.add(obj)
    db.flush()
    return obj


def commit_and_refresh(db: Session, obj: Any) -> Any:
    """Commit the pending transaction and refresh the given object."""
    db.commit()
    db.refresh(obj)
    return obj


def commit_only(db: Session) -> None:
    """Commit the pending transaction without refreshing an object."""
    db.commit()


def flush_only(db: Session) -> None:
    """Flush pending changes to the DB within the current transaction."""
    db.flush()


def refresh_only(db: Session, obj: Any) -> Any:
    """Refresh an ORM object from the DB without committing."""
    db.refresh(obj)
    return obj


def delete_only(db: Session, obj: Any) -> None:
    """Stage a delete on an ORM object within the current transaction."""
    db.delete(obj)


def rollback_only(db: Session) -> None:
    """Roll back the current transaction."""
    db.rollback()
