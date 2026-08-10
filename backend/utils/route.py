"""Route metadata for controller-first routing.

Attach ``@route`` (or the ``get/post/put/delete/patch`` helpers) to a
controller function to declare its HTTP route. The function itself keeps the
FastAPI parameter annotations (``Body``/``Path``/``Query``/``Depends``);
the router generator in ``scripts/gen_routers.py`` reads this metadata and
wires ``add_api_route`` pointing at the controller function.

Nothing here touches FastAPI at import time, so controllers stay importable
without an app instance.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional


@dataclass
class RouteSpec:
    method: str
    path: str
    auth: Optional[Any] = None
    rls: Optional[Any] = None
    prefix: Optional[str] = None
    response_model: Any = None
    status_code: int = 200
    tags: List[str] = field(default_factory=list)


def route(
    method: str,
    path: str,
    *,
    auth: Optional[Any] = None,
    rls: Optional[Any] = None,
    prefix: Optional[str] = None,
    response_model: Any = None,
    status_code: int = 200,
    tags: Optional[List[str]] = None,
) -> Callable:
    """Declare an HTTP route on a controller function."""

    def deco(fn: Callable) -> Callable:
        fn.__route__ = RouteSpec(
            method=str(method).upper(),
            path=path,
            auth=auth,
            rls=rls,
            prefix=prefix,
            response_model=response_model,
            status_code=status_code or 200,
            tags=list(tags or []),
        )
        return fn

    return deco


def get(path: str, **kw: Any) -> Callable:
    return route("GET", path, **kw)


def post(path: str, **kw: Any) -> Callable:
    return route("POST", path, **kw)


def put(path: str, **kw: Any) -> Callable:
    return route("PUT", path, **kw)


def delete(path: str, **kw: Any) -> Callable:
    return route("DELETE", path, **kw)


def patch(path: str, **kw: Any) -> Callable:
    return route("PATCH", path, **kw)
