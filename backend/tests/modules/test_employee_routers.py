"""Employee module router law tests.

Verifies Laws 1, 2, 87, 88, 89, 90, 99, 132-139 for the employee module.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

# Ensure backend root is importable regardless of cwd or conftest state.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from ._ast_helpers import (
    AUTH_DEPENDENCIES,
    BACKEND_ROOT,
    GATE_DEPENDENCIES,
    MODULE_PREFIXES,
    _delegates_to_service,
    _handler_auth_names,
    _has_raw_sql,
    _find_route_handlers,
    get_registered_module_names,
    parse_file,
    iter_router_files,
)

MODULE = "employee"


class TestEmployeeStructure:
    """Law 132-137: module directory structure."""

    def test_auth_dir_exists(self):
        assert (BACKEND_ROOT / "modules" / MODULE / "auth").is_dir()

    def test_routers_dir_exists(self):
        assert (BACKEND_ROOT / "modules" / MODULE / "routers").is_dir()

    def test_serializers_dir_exists(self):
        assert (BACKEND_ROOT / "modules" / MODULE / "serializers").is_dir()

    def test_routers_init_lists_all_files(self):
        """Law 135: every router file is registered."""
        registered = set(get_registered_module_names(MODULE))
        for path in iter_router_files(MODULE):
            assert path.stem in registered, (
                f"{path.name} not in __init__.py _module_names"
            )


class TestEmployeeRouterImports:
    """Law 1/99: modules import domains, not infrastructure directly."""

    def test_module_imports_domains(self):
        domain_imports = 0
        for path in iter_router_files(MODULE):
            tree = parse_file(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("domains."):
                        domain_imports += 1
        assert domain_imports > 0, "employee routers never import from domains"


class TestEmployeeRouterLaw8788:
    """Law 87/88: auth + feature gate on every handler."""

    def test_all_handlers_have_auth_and_gate(self):
        failures: list[str] = []
        for path in iter_router_files(MODULE):
            tree = parse_file(path)
            for handler in _find_route_handlers(tree):
                auth = _handler_auth_names(handler)
                if not (auth & AUTH_DEPENDENCIES):
                    failures.append(f"{path.name}:{handler.name} (no auth)")
                if not (auth & GATE_DEPENDENCIES):
                    failures.append(f"{path.name}:{handler.name} (no gate)")
        assert not failures, f"Law 87/88 violations: {failures}"


class TestEmployeeRouterLaw290:
    """Law 2/90: thin routers — no raw SQL, delegate to services."""

    def test_no_raw_sql(self):
        violations: list[str] = []
        for path in iter_router_files(MODULE):
            tree = parse_file(path)
            raw = _has_raw_sql(tree)
            if raw:
                violations.append(f"{path.name}: {raw}")
        assert not violations, f"raw SQL violations: {violations}"

    def test_handlers_delegate_to_services(self):
        failures: list[str] = []
        for path in iter_router_files(MODULE):
            tree = parse_file(path)
            for handler in _find_route_handlers(tree):
                if not _delegates_to_service(handler):
                    failures.append(f"{path.name}:{handler.name}")
        assert not failures, f"non-delegating handlers: {failures}"


class TestEmployeeRouterLaw139:
    """Law 139: route prefixes match /employee/*."""

    def test_router_prefix(self):
        expected = MODULE_PREFIXES[MODULE]
        for path in iter_router_files(MODULE):
            tree = parse_file(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "router":
                            if isinstance(node.value, ast.Call):
                                for kw in node.value.keywords:
                                    if kw.arg == "prefix" and isinstance(
                                        kw.value, ast.Constant
                                    ):
                                        if kw.value.value:
                                            assert kw.value.value.startswith(expected), (
                                                f"{path.name} prefix "
                                                f"'{kw.value.value}' != '{expected}/*'"
                                            )


class TestEmployeeModuleInit:
    """Law 135: module __init__ exports routers."""

    def test_module_init_exists(self):
        init = BACKEND_ROOT / "modules" / MODULE / "__init__.py"
        assert init.exists()
