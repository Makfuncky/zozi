"""Regression tests: no dead ``Unknown``-referencing stubs remain.

These auto-generated read-service helpers (``get_unknown_first``,
``get_unknown_scalar``, ``get_unknown_by_condition``, ``count_unknown``)
referenced an undefined ``Unknown`` symbol (latent NameError) and were never
called anywhere. They were removed module-by-module:
ai, security, orders, catalog, supplier, logistics.
"""
from __future__ import annotations

import ast
import importlib
import os
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"

_MODULES = {
    "ai": ("services.ai.ai_service", "services/ai/ai_service.py"),
    "security": (
        "services.security.permissions_read_service",
        "services/security/permissions_read_service.py",
    ),
    "orders": (
        "services.orders.orders_router_service",
        "services/orders/orders_router_service.py",
    ),
    "catalog": (
        "services.catalog.products_read_service",
        "services/catalog/products_read_service.py",
    ),
    "supplier": (
        "services.supplier.supplier_read_service",
        "services/supplier/supplier_read_service.py",
    ),
    "logistics": (
        "services.logistics.logistics_read_service",
        "services/logistics/logistics_read_service.py",
    ),
}

_DEAD_FUNCS = (
    "get_unknown_first",
    "get_unknown_scalar",
    "get_unknown_by_condition",
    "count_unknown",
)


for _p in (str(_BACKEND_DIR), str(Path(__file__).resolve().parent.parent)):
    if _p not in os.sys.path:
        os.sys.path.insert(0, _p)


def _module_ast(rel_path: str) -> ast.Module:
    return ast.parse((_BACKEND_DIR / rel_path).read_text(encoding="utf-8"))


def test_no_dead_unknown_functions_present():
    for _name, (mod_name, _rel) in _MODULES.items():
        mod = importlib.import_module(mod_name)
        present = [f for f in _DEAD_FUNCS if hasattr(mod, f)]
        assert not present, f"{mod_name} still exports dead stubs: {present}"


def test_no_unknown_symbol_references_in_source():
    for _name, (_mod, rel) in _MODULES.items():
        tree = _module_ast(rel)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                assert node.id != "Unknown", (
                    f"{rel}: Name 'Unknown' at line {node.lineno}"
                )
            if isinstance(node, ast.Attribute):
                assert node.attr != "Unknown", (
                    f"{rel}: Attr '.Unknown' at line {node.lineno}"
                )
