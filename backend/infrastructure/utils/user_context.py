"""Shared user-context helper."""
from __future__ import annotations
from typing import Protocol, runtime_checkable


@runtime_checkable
class UserLike(Protocol):
    """Minimal user protocol for audit-trail context extraction."""
    id: int
    username: str
    role: str


def _user_ctx(u: UserLike) -> dict:
    """Convert a User object to an acting-user dict for audit trails."""
    return {"id": u.id, "username": u.username, "role": u.role}
