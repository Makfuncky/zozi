"""Q1 sweep gate — routers must not call db.query()/db.execute() directly.

The canonical data-access layer is ``services.db_read``. Routers build
``select()`` / ``text()`` statements (session-free) or pass a model + column
filters to the ``db_read`` helpers; they never touch the session's read API.

This test is a hard gate: every file under ``routers/`` must have ZERO
``db.query`` / ``db.execute`` calls. A router that needs DB reads delegates to
``services.db_read`` instead.
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

_ROUTER_DIR = _BACKEND_ROOT / "routers"


def _router_files():
    return sorted(_ROUTER_DIR.rglob("*.py"))


def _count_violations(path: Path) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    n = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute):
            continue
        value = func.value
        is_db = (isinstance(value, ast.Name) and value.id == "db") or (
            isinstance(value, ast.Attribute) and value.attr == "db"
        )
        if is_db and func.attr in {"query", "execute"}:
            n += 1
    return n


def test_no_session_reads_in_any_router():
    violations = {}
    for p in _router_files():
        c = _count_violations(p)
        if c:
            violations[p.relative_to(_BACKEND_ROOT).as_posix()] = c
    assert not violations, f"routers still call db.query/db.execute: {violations}"
