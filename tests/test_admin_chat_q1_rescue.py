"""Q1 rescue test — admin_chat router.

Guards the Q1 architecture rule: routers must never reach into the ORM session
directly through ``db.query()`` / ``db.execute()``. Every DB read is delegated
to ``services.db_read`` (the shared data-access layer), which keeps the router a
thin HTTP/transform adapter.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

_ROUTER_NAME = "admin_chat_governance"
_MODULE = f"routers.{_ROUTER_NAME}"
_ROUTER_FILE = _BACKEND_ROOT / "routers" / f"{_ROUTER_NAME}.py"

# Session read verbs a router must never call for itself.
_SESSION_READS = {"query", "execute"}


def _session_read_violations(path: Path) -> list[tuple[int, str]]:
    """Return ``(lineno, attr)`` for every ``db.query()`` / ``db.execute()`` call."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in _SESSION_READS:
            continue
        value = func.value
        is_db = (isinstance(value, ast.Name) and value.id == "db") or (
            isinstance(value, ast.Attribute) and value.attr == "db"
        )
        if is_db:
            violations.append((node.lineno, func.attr))
    return violations


def test_router_imports() -> None:
    """The router file must define an APIRouter and use the shared read layer.

    Validated statically (AST) rather than importing the live module, because
    importing pulls in an unrelated optional-dependency module that is broken in
    this environment. The Q1 guarantee is covered by the other tests here.
    """
    importlib.import_module("services.db_read")
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    has_router = any(
        isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "router" for t in n.targets)
        and isinstance(n.value, ast.Call)
        and (
            (isinstance(n.value.func, ast.Name) and n.value.func.id == "APIRouter")
            or (isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "APIRouter")
        )
        for n in ast.walk(tree)
    )
    assert has_router, "router module must define an APIRouter instance"


def test_router_has_no_session_reads() -> None:
    """Q1: the router must not call ``db.query()`` / ``db.execute()`` directly."""
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    violations = _session_read_violations(_ROUTER_FILE)
    assert not violations, (
        f"{_ROUTER_NAME} still reads through the session; delegate to "
        f"services.db_read. Found: {violations}"
    )


def test_router_delegates_to_db_read() -> None:
    """Read helpers must be imported from the shared ``services.db_read`` layer."""
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "services.db_read"
        for alias in node.names
    }
    assert imported, f"{_ROUTER_NAME} does not import from services.db_read"
    db_read = importlib.import_module("services.db_read")
    for name in imported:
        assert callable(getattr(db_read, name, None)), f"missing db_read helper: {name}"
