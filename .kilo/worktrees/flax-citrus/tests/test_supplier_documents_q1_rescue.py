"""Q1 rescue test — supplier_documents router.

Verifies the router no longer calls ``db.query()`` / ``db.execute()`` directly.
All DB reads now delegate to ``services.db_read`` (the shared data-access
layer), keeping the router a thin HTTP/transform adapter.
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

_MODULE = "routers.supplier_documents"
_ROUTER_FILE = _BACKEND_ROOT / "routers" / "supplier_documents.py"
_SESSION_READS = {"query", "execute"}


def _session_read_violations(path: Path) -> list[tuple[int, str]]:
    """Return (lineno, attr) for every ``db.query()`` / ``db.execute()`` call."""
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


def test_router_imports_cleanly() -> None:
    importlib.import_module("services.db_read")
    assert importlib.import_module(_MODULE) is not None


def test_router_has_no_session_reads() -> None:
    """Q1: routers must not call db.query() / db.execute() directly."""
    assert _ROUTER_FILE.exists(), f"router file missing: {_ROUTER_FILE}"
    violations = _session_read_violations(_ROUTER_FILE)
    assert not violations, f"supplier_documents still reads via db: {violations}"


def test_router_delegates_to_db_read() -> None:
    """The router must import its read helpers from services.db_read."""
    tree = ast.parse(_ROUTER_FILE.read_text(encoding="utf-8"))
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "services.db_read"
        for alias in node.names
    }
    assert imported, "supplier_documents does not import from services.db_read"
    db_read = importlib.import_module("services.db_read")
    for name in imported:
        assert callable(getattr(db_read, name, None)), f"missing db_read helper: {name}"
