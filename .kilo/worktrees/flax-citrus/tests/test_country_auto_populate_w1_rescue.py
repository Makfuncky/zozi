"""W1 (+Q1) rescue test — country_auto_populate router (Country Administration domain).

Verifies the router no longer calls session.add()/commit()/delete()/refresh()
directly (W1); persistence now lives in
``services.geography.country_auto_populate_write_service``. The read-only
suggestion fetch stays in ``data.services_country_auto_populate``. Import
integrity is checked so the boot router-load chain (main.py) stays intact.
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

_ROUTER_FILE = _BACKEND_ROOT / "routers" / "country_auto_populate.py"
_SERVICE_MODULE = "services.geography.country_auto_populate_write_service"
_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def test_router_and_service_import_cleanly() -> None:
    importlib.import_module(_SERVICE_MODULE)
    importlib.import_module("routers.public_country_auto_populate_access")


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
    assert not violations, f"country_auto_populate still writes to the session: {violations}"


def test_service_owns_persistence() -> None:
    svc = importlib.import_module(_SERVICE_MODULE)
    for fn in ["save_country_from_suggestion"]:
        assert callable(getattr(svc, fn)), f"missing service function: {fn}"
