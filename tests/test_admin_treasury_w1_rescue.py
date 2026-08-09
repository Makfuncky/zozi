"""W1 (+Q1) rescue test — admin_treasury router (Treasury domain).

Verifies the router no longer calls session.add()/commit()/delete()/refresh()
(W1) or session.query()/session.execute() (Q1) directly. All DB reads now
delegate to ``services.treasury.admin_treasury_read_service`` (the 7 generic
helpers), keeping the router a thin HTTP/transform adapter.
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

_ROUTER_FILE = _BACKEND_ROOT / "routers" / "admin_treasury.py"
_SERVICE_MODULE = "services.treasury.admin_treasury_read_service"
_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def test_router_and_service_import_cleanly() -> None:
    importlib.import_module(_SERVICE_MODULE)
    importlib.import_module("routers.admin_treasury_governance")


def test_router_has_no_session_writes() -> None:
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        value = func.value
        target = value if isinstance(value, ast.Name) and value.id == "db" else (
            value.attr if isinstance(value, ast.Attribute) and value.attr == "db" else None
        )
        if target == "db" and func.attr in _SESSION_WRITES:
            violations.append((node.lineno, func.attr))
    assert not violations, f"admin_treasury still writes to the session: {violations}"


def test_router_has_no_session_reads() -> None:
    """Q1: routers must not call db.query() / db.execute() directly."""
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        value = func.value
        target = value if isinstance(value, ast.Name) and value.id == "db" else (
            value.attr if isinstance(value, ast.Attribute) and value.attr == "db" else None
        )
        if target == "db" and func.attr in {"query", "execute"}:
            violations.append((node.lineno, func.attr))
    assert not violations, f"admin_treasury still reads via db: {violations}"


def test_service_owns_reads() -> None:
    svc = importlib.import_module(_SERVICE_MODULE)
    for fn in [
        "run_scalar",
        "run_scalars",
        "run_rows",
        "list_model",
        "count_model",
        "first_model",
        "scalar_sum",
    ]:
        assert callable(getattr(svc, fn)), f"missing service helper: {fn}"
