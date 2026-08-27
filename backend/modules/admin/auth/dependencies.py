"""Canonical auth dependencies for the admin module.

Per ``ARCHITECTURE_DIAGRAM.md`` the admin module keeps a thin HTTP surface;
the actual role/session gates live here (re-exported from the platform-wide
sources) so every admin router imports its auth from one place.
"""
from __future__ import annotations

from fastapi import HTTPException

from domains.security.services.iam.security_dependencies import require_admin, require_roles, get_current_user  # noqa: F401


def require_admin_role(current_user: dict) -> None:
    """Raise 403 unless the acting user holds an admin or sub_admin role."""
    role = current_user["role"]
    if role not in {"admin", "sub_admin"}:
        raise HTTPException(status_code=403, detail="Admin access required.")


__all__ = ["require_admin", "require_admin_role", "require_roles", "get_current_user"]
