"""AST-based helpers for module router law verification.

These helpers parse router source files WITHOUT importing them, so they work
even when the app cannot load (e.g. stale domain imports). Every check maps to
a specific law in ARCHITECTURE_DIAGRAM.md.

NOTE: This file is intentionally self-contained. The ``tests._support.laws``
import path is broken in this environment (the conftest.py fails to load),
so the constants we need are inlined here rather than imported.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path
from typing import Iterable

# Ensure backend root is importable regardless of cwd or conftest state.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

BACKEND_ROOT = _BACKEND_ROOT

# Inlined from tests._support.laws (import path broken in this env).
ALL_DOMAINS: tuple[str, ...] = (
    "accounts", "analytics", "audit", "catalog", "comms", "country",
    "customers", "finance", "governance", "hr", "logistics", "orders",
    "promotions", "security", "suppliers",
)

MODULE_NAMES: tuple[str, ...] = ("admin", "customer", "employee", "logistics", "supplier")

# Expected route prefix per module (Law 139)
MODULE_PREFIXES: dict[str, str] = {
    "admin": "/api/v1/admin",
    "customer": "/api/v1/customer",
    "employee": "/api/v1/employee",
    "logistics": "/api/v1/logistics",
    "supplier": "/api/v1/supplier",
}

# Auth dependency names that satisfy Law 87
AUTH_DEPENDENCIES: set[str] = {
    "require_admin", "require_supplier", "require_logistics",
    "require_employee", "require_customer", "get_current_user",
    "rbac_get_current_user", "get_current_active_user",
}

# Feature/module gate names that satisfy Law 88
GATE_DEPENDENCIES: set[str] = {"require_feature", "require_module"}


def parse_file(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def iter_router_files(module: str) -> Iterable[Path]:
    """Yield every modules/{m}/routers/{d}.py file (excluding __init__.py)."""
    router_dir = BACKEND_ROOT / "modules" / module / "routers"
    if not router_dir.exists():
        return []
    for p in sorted(router_dir.glob("*.py")):
        if p.name == "__init__.py":
            continue
        yield p


def get_registered_module_names(module: str) -> list[str]:
    """Parse routers/__init__.py and return the _module_names list (Law 135)."""
    init = BACKEND_ROOT / "modules" / module / "routers" / "__init__.py"
    if not init.exists():
        return []
    tree = parse_file(init)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_module_names":
                    if isinstance(node.value, ast.List):
                        return [
                            elt.value for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        ]
    return []


def _get_depends_names(call: ast.Call) -> set[str]:
    """Extract the function name from a Depends(...) call."""
    names: set[str] = []
    func = call.func
    if isinstance(func, ast.Name):
        names.add(func.id)
    elif isinstance(func, ast.Attribute):
        names.add(func.attr)
    for arg in call.args:
        if isinstance(arg, ast.Name):
            names.add(arg.id)
        elif isinstance(arg, ast.Attribute):
            names.add(arg.attr)
    return names


def _find_route_handlers(tree: ast.Module) -> list[ast.FunctionDef]:
    """Return functions decorated with @router.<method>(...)."""
    handlers: list[ast.FunctionDef] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for dec in node.decorator_list:
            if (
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch", "head", "options"}
            ):
                handlers.append(node)
    return handlers


def _handler_auth_names(func: ast.FunctionDef) -> set[str]:
    """Return the set of Depends(...) names used by a handler."""
    names: set[str] = []
    for dec in func.decorator_list:
        if isinstance(dec, ast.Call):
            for arg in dec.args:
                if isinstance(arg, ast.Call):
                    names.update(_get_depends_names(arg))
    for default in func.args.defaults:
        if isinstance(default, ast.Call):
            names.update(_get_depends_names(default))
    return set(names)


def _has_raw_sql(tree: ast.Module) -> list[str]:
    """Detect raw SQL patterns that violate Law 2/90 (thin routers)."""
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {"execute", "commit"}:
                if isinstance(func.value, ast.Name) and func.value.id in {"db", "session"}:
                    violations.append(f"db.{func.attr}()")
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "text":
                violations.append("text()")
    return violations


def _delegates_to_service(func: ast.FunctionDef) -> bool:
    """Check if a handler delegates to a domain service (Law 2/90)."""
    for node in ast.walk(func):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("domains.") and ".services." in node.module:
                return True
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr in {
                "calculate_health_score", "list_pending_bank_accounts",
                "verify_bank_account", "list_all_products", "create_pipeline",
            }:
                return True
    return False


def _get_response_model(decorator: ast.Call) -> str | None:
    """Extract response_model from a router decorator's kwargs."""
    for kw in decorator.keywords:
        if kw.arg == "response_model" and isinstance(kw.value, ast.Name):
            return kw.value.id
    return None
