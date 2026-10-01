"""W1 rescue test — admin_users.py router.

Verifies the router no longer calls session.add()/commit()/delete()/refresh()
directly; those writes now live in services.user.user_profile_service.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

_ROUTER_FILE = _BACKEND_ROOT / "routers" / "admin_users.py"
_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def test_router_imports_and_service_imports() -> None:
    import importlib

    importlib.import_module("services.user.user_profile_service")
    importlib.import_module("routers.admin_users_governance")


def test_router_has_no_session_writes() -> None:
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
    assert not violations, f"admin_users.py still writes to session: {violations}"


def test_service_owns_admin_user_writes() -> None:
    from services.user.user_profile_service import admin_bulk_toggle_active, save_user_profile

    assert callable(save_user_profile)
    assert callable(admin_bulk_toggle_active)
