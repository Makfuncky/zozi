"""HTTP route-contract decorator utilities (platform layer).

This module is the home of the metadata-only route-contract decorators
(``get``/``post``/``put``/``delete``/``patch``/``route``) after the old
``routers/generated/auto_router.py`` migration bridge was retired. Controllers
import these markers from ``infrastructure.routing.route_contract`` (which
re-exports them) to declare their HTTP contract without importing FastAPI.

The OLD architecture generated thin FastAPI routers from ``@get/@post/...``
decorators declared on controller functions. During the NEW_STRUCTURE migration
the code-generator surface was retired (the platform has no central router
system), but the controller modules still carry these decorators as HTTP-contract
markers. This module keeps the import contract alive by providing no-op decorators
that simply return the decorated function (with optional route metadata attached).
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Iterable, Optional

_METHODS = ("get", "post", "put", "delete", "patch")


def _make_decorator(method: str) -> Callable[..., Callable[..., Any]]:
    def decorator(
        path: str,
        *,
        deps: Optional[Iterable[str]] = None,
        query: Optional[Iterable[str]] = None,
        body: Optional[Iterable[str]] = None,
        tags: Optional[Iterable[str]] = None,
        summary: Optional[str] = None,
        **_: Any,
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def wrap(fn: Callable[..., Any]) -> Callable[..., Any]:
            contract = getattr(fn, "__route_contract__", None)
            if contract is None:
                contract = {}
                try:
                    fn.__route_contract__ = contract
                except (AttributeError, TypeError):
                    pass
            contract.setdefault("methods", []).append(method)
            contract["path"] = path
            if deps is not None:
                contract["deps"] = list(deps)
            if query is not None:
                contract["query"] = list(query)
            if body is not None:
                contract["body"] = (
                    list(body) if isinstance(body, (list, tuple, set)) else [body]
                )
            if tags is not None:
                contract["tags"] = list(tags)
            if summary is not None:
                contract["summary"] = summary
            return fn

        return wrap

    decorator.__name__ = method
    return decorator


# Public decorator surface used by controllers: get, post, put, delete, patch
globals().update({m: _make_decorator(m) for m in _METHODS})


def route(
    path: str,
    *,
    method: str = "GET",
    deps: Optional[Iterable[str]] = None,
    query: Optional[Iterable[str]] = None,
    body: Optional[Iterable[str]] = None,
    tags: Optional[Iterable[str]] = None,
    summary: Optional[str] = None,
    **_: Any,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Generic route decorator (method-agnostic) used by the codegen bridge."""
    return _make_decorator(method.lower())(
        path, deps=deps, query=query, body=body, tags=tags, summary=summary
    )


def scan_controllers(root: str = ".") -> list:
    """Best-effort discovery of decorated controller functions (codegen helper)."""
    import ast
    import os

    found = []
    for dp, _dn, files in os.walk(root):
        if "venv" in dp or "__pycache__" in dp:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            try:
                tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8").read())
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") in _METHODS:
                            found.append((os.path.join(dp, f), node.name))
                            break
    return found


def _derive_filename(func_name: str) -> str:
    return func_name
