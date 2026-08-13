"""Route-contract decorators — the ONLY HTTP-contract declarations controllers may use.

These are metadata-only: a controller never imports FastAPI. The auto-router
generator (``routers/generated/auto_router.py``) reads them via AST by name, so
the runtime behaviour here is just "tag the function".

They live in ``core`` (NOT in ``routers``) so that controllers depend on a
neutral module and never on the router surface — preserving the
``routers -> controllers -> services`` layering. This is the single source of
truth; ``routers/generated/auto_router.py`` re-exports them for backwards
compatibility during migration.
"""
from __future__ import annotations

from typing import Any, Optional


def route(
    method: str,
    path: str,
    *,
    deps: "Optional[list]" = None,
    query: "Optional[list]" = None,
    body=None,
    response_model=None,
    status_code: int = 200,
    tags: "Optional[list]" = None,
    rls: "Optional[str]" = None,
    skip: bool = False,
    **kwargs,
) -> "Any":
    """Declare the HTTP contract for a controller function. No FastAPI here."""
    def decorator(func):
        func._route_meta = {
            "method": method.upper(),
            "path": path,
            "deps": list(deps or []),
            "query": list(query or []),
            "body": body,
            "response_model": response_model,
            "status_code": status_code,
            "tags": list(tags or []),
            "rls": rls,
            "skip": bool(skip),
            **kwargs,
        }
        return func
    return decorator


def get(path: str, **kw):
    return route("GET", path, **kw)


def post(path: str, **kw):
    kw.setdefault("status_code", 201)
    return route("POST", path, **kw)


def put(path: str, **kw):
    return route("PUT", path, **kw)


def patch(path: str, **kw):
    return route("PATCH", path, **kw)


def delete(path: str, **kw):
    return route("DELETE", path, **kw)
