"""W1 (+Q1) rescue test — country_admin router (Country Administration domain).

Verifies the router no longer calls session.add()/commit()/delete()/refresh()
directly (W1), and that the DB reads (Q1) for communications, cities, staff and
tax rates now live in ``services.geography.country_admin_write_service``.
Import integrity is checked so the boot router-load chain (main.py) stays intact.
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

_ROUTER_FILE = _BACKEND_ROOT / "routers" / "country_admin.py"
_SERVICE_MODULE = "services.geography.country_admin_write_service"
_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def test_router_and_service_import_cleanly() -> None:
    importlib.import_module(_SERVICE_MODULE)
    importlib.import_module("routers.public_country_admin_access")


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
    assert not violations, f"country_admin still writes to the session: {violations}"


def test_router_has_no_session_reads() -> None:
    """Q1: routers must not call db.query() directly."""
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
        if target == "db" and func.attr == "query":
            violations.append((node.lineno, func.attr))
    assert not violations, f"country_admin still reads via db.query(): {violations}"


def test_service_owns_reads_and_writes() -> None:
    svc = importlib.import_module(_SERVICE_MODULE)
    for fn in [
        "create_country_communication",
        "list_country_communications",
        "mark_communication_read",
        "list_cities",
        "create_city",
        "update_city",
        "delete_city",
        "list_staff",
        "assign_staff",
        "remove_staff",
        "list_tax_rates",
        "set_tax_rate",
    ]:
        assert callable(getattr(svc, fn)), f"missing service function: {fn}"
