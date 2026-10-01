"""Logistics orders router regression tests.

Verifies LOGISTICS_ORDERS_001: router is not a stub and uses require_feature gates.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

ROUTER_FILE = _BACKEND_ROOT / "modules" / "logistics" / "routers" / "orders.py"


class TestLogisticsOrdersRouterNotStub:
    """LOGISTICS_ORDERS_001: router must have implemented endpoints."""

    def test_no_todo_comment(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        assert "TODO" not in source, "router must not contain unresolved TODO comments"

    def test_has_multiple_endpoints(self):
        tree = ast.parse(ROUTER_FILE.read_text(encoding="utf-8"))
        handlers = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if (
                        isinstance(dec, ast.Call)
                        and isinstance(dec.func, ast.Attribute)
                        and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                    ):
                        handlers.append(node.name)
        assert len(handlers) > 1, f"router must have multiple endpoints, found: {handlers}"


class TestLogisticsOrdersRouterThin:
    """Law 2/90: router must be thin — no raw SQL, delegates to services."""

    def test_no_raw_sql(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        assert "db.execute" not in source
        assert "db.commit" not in source
        assert "session.execute" not in source
        assert "text(" not in source

    def test_require_feature_on_protected_endpoints(self):
        source = ROUTER_FILE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        protected = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == "health":
                    continue
                has_gate = False
                for default in node.args.defaults:
                    if isinstance(default, ast.Call):
                        if (
                            isinstance(default.func, ast.Name)
                            and default.func.id == "Depends"
                        ):
                            for arg in default.args:
                                if (
                                    isinstance(arg, ast.Call)
                                    and isinstance(arg.func, ast.Name)
                                    and arg.func.id == "require_feature"
                                ):
                                    has_gate = True
                if has_gate:
                    protected.append(node.name)
        handler_count = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and any(
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch"}
                for dec in node.decorator_list
            )
            and node.name != "health"
        )
        assert len(protected) == handler_count, (
            f"require_feature missing on some protected endpoints: "
            f"{handler_count - len(protected)} missing"
        )


class TestLogisticsOrdersRouterStructure:
    """Law 139: route prefix matches module prefix."""

    def test_router_prefix(self):
        tree = ast.parse(ROUTER_FILE.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "router":
                        if isinstance(node.value, ast.Call):
                            for kw in node.value.keywords:
                                if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                                    assert kw.value.value.startswith("/api/v1/logistics"), (
                                        f"prefix '{kw.value.value}' != '/api/v1/logistics/*'"
                                    )
