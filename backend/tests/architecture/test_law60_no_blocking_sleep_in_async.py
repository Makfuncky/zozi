"""Law 60 gate: async code must not block the event loop with ``time.sleep``.

R-22 (RUNTIME_PROBLEM.md): retry/backoff helpers reachable from request
handlers called ``time.sleep``. The event bus now exposes ``publish_async``
(awaiting ``asyncio.sleep``) and background jobs run in a worker thread outside
tests, but nothing stopped the pattern from re-appearing.

This test walks every ``async def`` in the production packages (including sync
functions nested inside them, which execute on the same loop thread) and fails
on ``time.sleep(...)`` / ``time.monotonic``-style blocking sleeps.
"""
from __future__ import annotations

import ast
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

PRODUCTION_PACKAGES = (
    "modules",
    "domains",
    "rbac",
    "kernel",
    "providers",
    "jobs",
    "middleware",
    "infrastructure",
)
PRODUCTION_ROOT_FILES = ("main.py", "lifespan.py", "config.py")
_SKIPPED_DIRS = {"tests", "__pycache__", ".venv", "node_modules", "scripts"}


def _python_files():
    for name in PRODUCTION_PACKAGES:
        root = os.path.join(_BACKEND_ROOT, name)
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _SKIPPED_DIRS]
            for fn in filenames:
                if fn.endswith(".py"):
                    yield os.path.join(dirpath, fn)
    for fn in PRODUCTION_ROOT_FILES:
        path = os.path.join(_BACKEND_ROOT, fn)
        if os.path.isfile(path):
            yield path


def _is_blocking_sleep(node: ast.Call) -> bool:
    """True for ``time.sleep(...)`` / ``sleep(...)`` imported from ``time``."""
    func = node.func
    if isinstance(func, ast.Attribute) and func.attr == "sleep":
        if isinstance(func.value, ast.Name) and func.value.id in {"time", "monotonic"}:
            return True
    return False


def _violations_in_async(fn: ast.AsyncFunctionDef, rel: str) -> list[str]:
    found: list[str] = []
    for child in ast.walk(fn):
        if child is fn:
            continue
        # nested coroutine or sync function inside an async def still runs on
        # the loop thread when invoked inline
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child is not fn:
            for sub in ast.walk(child):
                if isinstance(sub, ast.Call) and _is_blocking_sleep(sub):
                    found.append(f"{rel}:{sub.lineno}: {child.name}() (nested in async {fn.name})")
            continue
        if isinstance(child, ast.Call) and _is_blocking_sleep(child):
            found.append(f"{rel}:{child.lineno}: async {fn.name}()")
    return found


def _violations(path: str) -> list[str]:
    with open(path, encoding="utf-8-sig") as fh:
        source = fh.read()
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:  # pragma: no cover
        return [f"{path}: syntax error: {exc}"]
    rel = os.path.relpath(path, _BACKEND_ROOT)
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            seen: set[int] = set()
            for line in _violations_in_async(node, rel):
                if line not in seen:
                    seen.add(line)
                    found.append(line)
    return found


def test_no_blocking_sleep_inside_async_functions():
    offenders: list[str] = []
    for path in _python_files():
        offenders.extend(_violations(path))
    assert not offenders, (
        "Law 60 violation — time.sleep() inside async code blocks the event "
        "loop; use asyncio.sleep() or run the work in an executor:\n"
        + "\n".join(offenders)
    )


def test_production_packages_were_actually_scanned():
    files = list(_python_files())
    assert len(files) > 200, f"scan only covered {len(files)} files — glob is broken"
