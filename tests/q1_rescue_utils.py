"""Shared helpers for Q1 rescue tests.

Q1 forbids controllers/routers/middleware from calling ``db.query()`` /
``db.execute()`` / ``db.get()`` directly. They must delegate to
``services.db_read``. These helpers statically verify that property so the
rescue tests need neither a database nor app boot.
"""
from __future__ import annotations

import ast
import importlib
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")

# Session-like receiver names that own direct DB reads.
_SESSION_NAMES = {"db", "session", "db_session", "sess"}
_READ_ATTRS = {"query", "execute", "get"}


def _receiver_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def find_session_reads(backend_rel: str) -> list[tuple[int, str]]:
    """Return (lineno, snippet) for every session-owned db.query/execute/get call."""
    path = BACKEND_ROOT / backend_rel
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr not in _READ_ATTRS:
            continue
        name = _receiver_name(func.value)
        if name in _SESSION_NAMES or (
            isinstance(func.value, ast.Attribute) and func.value.attr in _SESSION_NAMES
        ):
            hits.append((node.lineno, f"{name}.{func.attr}"))
    return hits


def assert_no_session_reads(backend_rel: str) -> None:
    hits = find_session_reads(backend_rel)
    assert not hits, f"{backend_rel} still reads via session: {hits}"


def assert_imports_db_read(backend_rel: str) -> None:
    """File must import read helpers from services.db_read (all names valid)."""
    path = BACKEND_ROOT / backend_rel
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "services.db_read":
            for alias in node.names:
                imported.add(alias.name)
    assert imported, f"{backend_rel} does not import from services.db_read"
    db_read = importlib.import_module("services.db_read")
    for name in imported:
        assert callable(getattr(db_read, name, None)), f"missing db_read helper: {name}"
