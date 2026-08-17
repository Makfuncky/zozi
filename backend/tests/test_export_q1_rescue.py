"""Q1 rescue test for the export router.

Guards the Q1 architecture rule: routers must never touch the ORM session
directly through ``db.query()`` / ``db.execute()``. All read access is
delegated to the shared data-access layer ``services.common.db_read``.
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_ROUTER_NAME = "export"
_ROUTER_PATH = _BACKEND_ROOT / "routers" / f"{_ROUTER_NAME}.py"
_MODULE = f"routers.{_ROUTER_NAME}"

# Session read verbs that must not appear in a router.
_FORBIDDEN_ATTRS = {"query", "execute"}
# Names the request-scoped Session is bound to in routers.
_SESSION_NAMES = {"db"}


def _session_name(value: ast.AST) -> str | None:
    """Return the receiver name for ``<recv>.query(...)`` style calls."""
    if isinstance(value, ast.Name):
        return value.id
    if isinstance(value, ast.Attribute):
        return value.attr
    return None


def _find_direct_db_reads(source: str) -> list[str]:
    tree = ast.parse(source)
    findings: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr not in _FORBIDDEN_ATTRS:
            continue
        name = _session_name(node.func.value)
        if name in _SESSION_NAMES:
            findings.append(f"line {node.lineno}: {name}.{node.func.attr}()")
    return findings


@pytest.fixture(scope="module")
def router_src() -> str:
    return _ROUTER_PATH.read_text(encoding="utf-8")


def test_router_has_no_direct_db_reads(router_src: str) -> None:
    findings = _find_direct_db_reads(router_src)
    assert findings == [], (
        f"{_ROUTER_NAME} router must not call db.query()/db.execute() directly; "
        f"delegate to services.common.db_read. Found: {findings}"
    )


def test_router_delegates_to_db_read(router_src: str) -> None:
    tree = ast.parse(router_src)
    imports_db_read = any(
        isinstance(node, ast.ImportFrom) and node.module == "services.common.db_read"
        for node in ast.walk(tree)
    )
    assert imports_db_read, (
        f"{_ROUTER_NAME} router should import its read helpers from domains.media.services.db_read"
    )


def test_router_imports() -> None:
    module = importlib.import_module(_MODULE)
    assert module.router is not None
