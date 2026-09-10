"""Request-scoped current-user context (ContextVar plumbing).

Hosts the context-variable trio that used to live in ``rbac.dependencies`` so
the RBAC layer stops depending on infrastructure modules for request-state
management. This module is a dependency leaf — it imports nothing beyond the
standard library — so both ``rbac`` and ``infrastructure`` can depend on it
without a circular import.

``set_current_user`` is called by auth dependency resolution
(``infrastructure.security.dependencies``) and read by the ``require_feature`` /
``require_module`` / ``require_admin`` direct-call paths in ``rbac``.
"""
from __future__ import annotations

from contextvars import ContextVar
from typing import Any, Optional

_current_user_ctx: ContextVar = ContextVar("_current_user_ctx", default=None)


def _get_current_user() -> Any:
    """Return the user published to the current request context (None when
    the request is unauthenticated or the dependency was not resolved)."""
    return _current_user_ctx.get()


def set_current_user(user: Optional[Any]) -> None:
    """Set the current user for the active request context."""
    _current_user_ctx.set(user)


__all__ = ["_get_current_user", "set_current_user"]