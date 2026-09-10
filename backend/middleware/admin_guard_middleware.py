"""
Server-side admin guard middleware.

Closes the audit finding that customer accounts could fetch ``/admin/*`` and
``/api/v1/admin/*`` paths and simply be hidden from the rendered UI by a
client-side ``localStorage`` flag.  This middleware inspects the request path
**before** it reaches the router and, when the path belongs to the admin
namespace, requires ``request.state.user_role`` to be one of
``{"admin", "super_admin", "superadmin"}``.

This is an **outermost guard** in addition to the per-router
``require_module("admin")`` / ``require_feature(...)`` checks that individual
admin routes already use.  It does **not** replace those checks; it just
shields every admin route uniformly so that a missing per-route
``require_module`` can never accidentally expose an endpoint.
"""
from __future__ import annotations

import logging
import re
from typing import Iterable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


# Path prefixes that the admin guard protects.  These are matched as
# prefixes (with a trailing slash boundary check) so that legitimate
# non-admin paths starting with similar words (e.g. ``/administrators``)
# are not affected.
_ADMIN_PREFIXES: tuple[str, ...] = (
    "/admin/",
    "/admin",
    "/api/v1/admin/",
    "/api/v1/admin",
)


# The set of JWT role values that are allowed to access admin routes.
# This list is intentionally small and explicit -- adding a new role
# here must be a deliberate, reviewable change.
_ADMIN_ROLES: frozenset[str] = frozenset({"admin", "super_admin", "superadmin"})

# Path patterns that are allowed without an admin role even when the URL
# starts with one of the admin prefixes.  This currently only excludes the
# admin login / health-check endpoints, which the auth pipeline routes to
# before populating ``request.state.user_role``.
_ALLOWLIST: tuple[re.Pattern[str], ...] = (
    re.compile(r"^/admin/(login|health)(/|$)"),
    re.compile(r"^/api/v1/admin/(login|health)(/|$)"),
)


def is_admin_path(path: str) -> bool:
    """Return True when *path* falls under the protected admin namespace."""
    if not path:
        return False
    for pat in _ALLOWLIST:
        if pat.match(path):
            return False
    for prefix in _ADMIN_PREFIXES:
        if path == prefix or path.startswith(prefix):
            return True
    return False


def is_admin_role(role: Optional[str]) -> bool:
    """Return True when *role* is one of the values allowed by the guard."""
    if not role:
        return False
    return str(role).strip().lower() in _ADMIN_ROLES


class AdminGuardMiddleware(BaseHTTPMiddleware):
    """Reject non-admin requests targeting the admin namespace with 403.

    The guard runs **after** :class:`AuthenticationMiddleware` so that
    ``request.state.user_role`` is populated.  Unauthenticated requests get
    a 403 (not 401) because the admin namespace is intentionally
    indistinguishable to unauthenticated callers -- we do not leak the
    existence of admin endpoints to anonymous probes.
    """

    async def dispatch(self, request: Request, call_next):
        path = request.url.path or ""
        if not is_admin_path(path):
            return await call_next(request)

        role = getattr(request.state, "user_role", None)
        if not is_admin_role(role):
            user_id = getattr(request.state, "user_id", None)
            logger.warning(
                "admin_guard_forbidden path=%s user_id=%s role=%s",
                path,
                user_id,
                role,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Admin access required",
                    "code": "admin_required",
                    "path": path,
                },
            )

        return await call_next(request)


__all__ = [
    "AdminGuardMiddleware",
    "is_admin_path",
    "is_admin_role",
]
