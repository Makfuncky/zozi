"""Shared user-context helper."""
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from domains.governance.models.user import User


def _user_ctx(u: "User") -> dict:
    """Convert a User object to an acting-user dict for audit trails."""
    return {"id": u.id, "username": u.username, "role": u.role}
