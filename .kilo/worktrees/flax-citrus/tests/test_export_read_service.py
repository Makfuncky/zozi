"""Regression tests for ``backend/services/core/export_read_service.py``.

These tests lock in the HL502 fix (removal of the ``from data.models import *``
star import) and verify the module's read helpers keep working after the change.

They must never touch ``scripts/`` and never modify the module under test.
"""
from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

import pytest

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
_MODULE_PATH = _BACKEND_DIR / "services" / "core" / "export_read_service.py"

# Ensure backend/ and repo root are importable.
for _p in (str(_BACKEND_DIR), str(Path(__file__).resolve().parent.parent)):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)


def _module_ast() -> ast.Module:
    return ast.parse(_MODULE_PATH.read_text(encoding="utf-8"))


def test_no_star_import_in_export_read_service():
    """HL502 guard: the module must not use any ``from X import *``."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.names:
            assert node.names[0].name != "*", (
                f"Star import found at line {node.lineno}: "
                f"from {node.module or ''} import *"
            )


def test_explicit_imports_resolve():
    """The explicit ``from models import ...`` / ``from utils.constants import ...``
    / ``from data.services_write_helpers import ...`` symbols resolve."""
    mod = importlib.import_module("services.core.export_read_service")
    for name in (
        "User",
        "Order",
        "Product",
        "Coupon",
        "AuditLog",
        "MAX_EXPORT_ROWS",
        "add_and_flush",
        "commit_only",
    ):
        assert hasattr(mod, name), f"Expected symbol {name!r} missing after import"


def test_no_get_unknown_scalar_dead_function():
    """The dangling ``get_unknown_scalar`` (referenced an undefined ``Unknown``
    model) must be gone."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            assert node.name != "get_unknown_scalar", (
                "Dead get_unknown_scalar still present"
            )


def test_unknown_model_not_referenced():
    """No reference to a symbol named ``Unknown`` should survive."""
    tree = _module_ast()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            assert node.id != "Unknown", f"Reference to 'Unknown' at line {node.lineno}"
        if isinstance(node, ast.Attribute):
            assert node.attr != "Unknown", (
                f"Reference to '.Unknown' at line {node.lineno}"
            )


def test_max_export_rows_constant_value():
    mod = importlib.import_module("services.core.export_read_service")
    assert mod.MAX_EXPORT_ROWS == 5000


class _FakeQuery:
    """Minimal stand-in for a SQLAlchemy query that records the LIMIT value
    (the export cap) without needing a live DB / configured mappers."""

    def __init__(self, model):
        self.model = model
        self.limit_value = None

    def filter(self, *args, **kwargs):
        return self

    def offset(self, n):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def limit(self, n):
        self.limit_value = n
        return self

    def all(self):
        return []

    def first(self):
        return None

    def scalar(self):
        return 0


class _FakeSession:
    """Records which model each query targets; never touches real mappers."""

    def __init__(self):
        self.last_model = None
        self.last_query = None

    def query(self, model):
        self.last_model = model
        q = _FakeQuery(model)
        self.last_query = q
        return q


def test_list_and_count_functions_callable():
    """The read helpers must be callable and return empty results when the
    backing store is empty (verified via a mock session that avoids the
    unrelated ``User.products`` mapper-config bug in the test env)."""
    mod = importlib.import_module("services.core.export_read_service")
    sess = _FakeSession()
    assert mod.list_user(sess) == []
    assert mod.list_order(sess) == []
    assert mod.list_product(sess) == []
    assert mod.list_coupon(sess) == []
    assert mod.count_user(sess) == 0
    assert mod.count_order(sess) == 0
    assert mod.count_product(sess) == 0
    assert mod.count_coupon(sess) == 0


def test_capped_export_query_builders():
    """The ``db_*_all_*`` helpers must apply the MAX_EXPORT_ROWS cap."""
    mod = importlib.import_module("services.core.export_read_service")
    sess = _FakeSession()
    for fn_name in (
        "db_user_all_0",
        "db_order_all_1",
        "db_product_all_2",
        "db_coupon_all_3",
    ):
        getattr(mod, fn_name)(sess)
        assert sess.last_query.limit_value == mod.MAX_EXPORT_ROWS, (
            f"{fn_name} did not apply the MAX_EXPORT_ROWS cap"
        )
