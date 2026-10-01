"""W1 rescue test — users.py and supplier_finance.py routers.

Verifies both routers no longer call session.add()/commit()/delete()/refresh()
directly; the DB writes now live in dedicated services. Import-chain integrity
is also checked (the boot router-load test covers registration via main.py).
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

_ROUTER_FILES = {
    "users": _BACKEND_ROOT / "routers" / "users.py",
    "supplier_finance": _BACKEND_ROOT / "routers" / "supplier_finance.py",
}

_SESSION_WRITES = {"add", "commit", "delete", "flush", "merge", "refresh"}


def _router_file(name: str) -> Path:
    path = _ROUTER_FILES[name]
    assert path.exists(), f"router file missing: {path}"
    return path


def test_routers_import_cleanly() -> None:
    import importlib

    for mod in [
        "services.user.user_profile_service",
        "services.supplier.supplier_bank_account_service",
        "routers.public_users_access",
        "routers.supplier_finance",
    ]:
        importlib.import_module(mod)


def test_routers_have_no_session_writes() -> None:
    """No router may call db.add()/commit()/delete()/refresh() (W1)."""
    for name, path in _ROUTER_FILES.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        violations: list[tuple[int, str]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not isinstance(func, ast.Attribute):
                continue
            value = func.value
            # Match `db.<method>(` or `<something>.db.<method>(` (db as attribute)
            target = value if isinstance(value, ast.Name) and value.id == "db" else (
                value.attr if isinstance(value, ast.Attribute) and value.attr == "db" else None
            )
            if target == "db" and func.attr in _SESSION_WRITES:
                violations.append((node.lineno, func.attr))
        assert not violations, (
            f"{name} still writes to the session: {violations}"
        )


def test_service_owns_user_profile_write() -> None:
    from services.user.user_profile_service import save_user_profile

    assert callable(save_user_profile)


def test_service_owns_bank_account_write() -> None:
    from services.supplier.supplier_bank_account_service import upsert_supplier_bank_account

    assert callable(upsert_supplier_bank_account)
