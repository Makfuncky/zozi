"""Regression test for SUP-001: supplier health routes must require supplier role.

Verifies that GET /health/suppliers and GET /health/suppliers/{supplier_id}
in backend/modules/supplier/routers/suppliers.py use require_supplier,
not get_current_user, to prevent enumeration of supplier health data by
non-supplier authenticated users.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

SUPPLIERS_ROUTER = _BACKEND_ROOT / "modules" / "supplier" / "routers" / "suppliers.py"


def _get_health_handlers() -> list[ast.FunctionDef]:
    """Extract the two health route handlers from suppliers.py."""
    source = SUPPLIERS_ROUTER.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(SUPPLIERS_ROUTER))
    handlers: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            if not isinstance(dec.func, ast.Attribute):
                continue
            if dec.func.attr not in {"get", "post", "put", "delete", "patch"}:
                continue
            # Check if this is a /health/suppliers route by looking at the
            # function body for the route path or by function name.
            if node.name in {"get_supplier_health_route", "list_supplier_health_route"}:
                handlers.append(node)
    return handlers


def _get_depends_names(defaults: list[ast.AST]) -> set[str]:
    """Extract dependency names from function parameter defaults."""
    names: set[str] = set()
    for default in defaults:
        if not isinstance(default, ast.Call):
            continue
        func = default.func
        # Match both Depends(...) and bare module.Depends(...)
        is_depends = False
        if isinstance(func, ast.Name) and func.id == "Depends":
            is_depends = True
        elif isinstance(func, ast.Attribute) and func.attr == "Depends":
            is_depends = True
        if not is_depends:
            continue
        for arg in default.args:
            if isinstance(arg, ast.Name):
                names.add(arg.id)
            elif isinstance(arg, ast.Attribute):
                names.add(arg.attr)
    return names


class TestSUPOO1HealthRouteAuth:
    """SUP-001 regression: health routes must require supplier role."""

    def test_health_routes_use_require_supplier(self):
        handlers = _get_health_handlers()
        assert len(handlers) == 2, f"expected 2 health handlers, found {len(handlers)}"

        for handler in handlers:
            deps = _get_depends_names(list(handler.args.defaults))
            assert "require_supplier" in deps, (
                f"{handler.name} does not use require_supplier; found deps: {deps}"
            )

    def test_health_routes_do_not_use_get_current_user(self):
        """Outcome test: non-supplier users must be rejected at the router level."""
        handlers = _get_health_handlers()
        for handler in handlers:
            deps = _get_depends_names(list(handler.args.defaults))
            assert "get_current_user" not in deps, (
                f"{handler.name} still uses get_current_user; "
                f"any authenticated user can enumerate supplier health data"
            )

    def test_supplier_orders_also_uses_require_supplier(self):
        """Error-path sanity: sibling supplier routes already follow the pattern."""
        source = SUPPLIERS_ROUTER.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(SUPPLIERS_ROUTER))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            if node.name == "list_supplier_orders_route":
                deps = _get_depends_names(list(node.args.defaults))
                assert "require_supplier" in deps, (
                    "list_supplier_orders_route should use require_supplier"
                )
                break
        else:
            pytest.fail("list_supplier_orders_route not found in suppliers.py")
