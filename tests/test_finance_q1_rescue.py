"""Q1 rescue test — routers/finance.py.

Guards the Q1 architecture rule: routers must NOT call ``db.query()`` /
``db.execute()`` directly. All read access is delegated to
``services.db_read``.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_ROOT = _REPO_ROOT / "backend"
for _p in (str(_BACKEND_ROOT), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

_MODULE = "routers.public_finance_access"
_ROUTER_FILE = _BACKEND_ROOT / "routers" / "public_finance_access.py"
_FORBIDDEN = {"query", "execute"}


def _session_direct_reads(source: str) -> list[tuple[int, str]]:
    """Return every ``db.query(...)`` / ``db.execute(...)`` call site."""
    tree = ast.parse(source)
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in _FORBIDDEN:
            continue
        value = func.value
        is_db = (
            (isinstance(value, ast.Name) and value.id == "db")
            or (isinstance(value, ast.Attribute) and value.attr == "db")
        )
        if is_db:
            violations.append((node.lineno, f"db.{func.attr}"))
    return violations


def test_router_imports() -> None:
    assert importlib.import_module(_MODULE) is not None


def test_db_read_layer_importable() -> None:
    importlib.import_module("services.db_read")


def test_router_has_no_direct_session_reads() -> None:
    source = _ROUTER_FILE.read_text(encoding="utf-8")
    violations = _session_direct_reads(source)
    assert not violations, (
        f"{_ROUTER_FILE.name} still calls the session directly: {violations}"
    )


def test_router_delegates_to_db_read() -> None:
    source = _ROUTER_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "services.db_read"
        for alias in node.names
    }
    assert imported, "router must import helpers from services.db_read"
    assert {"rows", "scalar", "scalars"} <= imported


def test_db_read_helpers_are_callable() -> None:
    db_read = importlib.import_module("services.db_read")
    for name in ("rows", "scalar", "scalars"):
        assert callable(getattr(db_read, name, None)), f"missing helper {name}"
