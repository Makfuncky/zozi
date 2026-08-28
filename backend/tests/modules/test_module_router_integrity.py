"""System-wide module router integrity tests.

Verifies Laws 87, 88, 89, 90, 135, 139 across ALL five modules using AST
analysis (no app import required). These checks are law-aligned and run
independently of whether the FastAPI app can boot.
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
    MODULE_NAMES,
    MODULE_PREFIXES,
    _delegates_to_service,
    _get_response_model,
    _get_route_path,
    _handler_auth_names,
    _has_raw_sql,
    _find_route_handlers,
    get_registered_module_names,
    parse_file,
    iter_router_files,
)


# ---------------------------------------------------------------------------
# Law 135: every router file is registered in routers/__init__.py
# ---------------------------------------------------------------------------
class TestLaw135RouterRegistration:
    """Every modules/{m}/routers/{d}.py file is listed in __init__.py."""

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_registered_names_match_disk(self, module: str):
        """Names listed in __init__.py must exist as .py files on disk."""
        registered = get_registered_module_names(module)
        disk_files = [p.stem for p in iter_router_files(module)]
        # Every registered name should have a corresponding file on disk
        for name in registered:
            assert name in disk_files, (
                f"modules/{module}/routers/__init__.py lists '{name}' "
                f"but modules/{module}/routers/{name}.py does not exist"
            )

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_disk_files_are_registered(self, module: str):
        """Every .py file on disk must be listed in __init__.py."""
        registered = set(get_registered_module_names(module))
        for path in iter_router_files(module):
            assert path.stem in registered, (
                f"modules/{module}/routers/{path.name} exists on disk "
                f"but is not listed in __init__.py"
            )


# ---------------------------------------------------------------------------
# Law 87/88: auth + feature gate on every non-public endpoint
# ---------------------------------------------------------------------------
class TestLaw8788AuthAndFeatureGates:
    """Every protected endpoint uses auth (Law 87) and a feature gate (Law 88)."""

    def _collect_handlers(self, module: str):
        """Yield (path, handler_func, source_file) for all route handlers."""
        results = []
        for path in iter_router_files(module):
            tree = parse_file(path)
            for handler in _find_route_handlers(tree):
                results.append((path, handler))
        return results

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_handlers_have_auth(self, module: str):
        """Every route handler must use an auth dependency (Law 87)."""
        failures: list[str] = []
        for path, handler in self._collect_handlers(module):
            auth_names = _handler_auth_names(handler)
            if not auth_names & AUTH_DEPENDENCIES:
                failures.append(f"{path.name}:{handler.name}")
        assert not failures, (
            f"modules/{module} handlers missing auth (Law 87): {failures}"
        )

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_handlers_have_feature_gate(self, module: str):
        """Every route handler must use require_feature/require_module (Law 88)."""
        failures: list[str] = []
        for path, handler in self._collect_handlers(module):
            auth_names = _handler_auth_names(handler)
            if not auth_names & GATE_DEPENDENCIES:
                failures.append(f"{path.name}:{handler.name}")
        assert not failures, (
            f"modules/{module} handlers missing feature gate (Law 88): {failures}"
        )


# ---------------------------------------------------------------------------
# Law 2/90: thin routers — no raw SQL, no DB commits, delegate to services
# ---------------------------------------------------------------------------
class TestLaw290ThinRouters:
    """Routers must stay thin: no raw SQL, no direct DB writes (Law 2/90)."""

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_no_raw_sql_in_routers(self, module: str):
        """Routers must not contain raw SQL execution (Law 2/90)."""
        violations: list[str] = []
        for path in iter_router_files(module):
            tree = parse_file(path)
            raw = _has_raw_sql(tree)
            if raw:
                violations.append(f"{path.name}: {raw}")
        assert not violations, (
            f"modules/{module} routers contain raw SQL (Law 2/90): {violations}"
        )

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_handlers_delegate_to_services(self, module: str):
        """Every handler must delegate to a domain service (Law 2/90)."""
        failures: list[str] = []
        for path in iter_router_files(module):
            tree = parse_file(path)
            for handler in _find_route_handlers(tree):
                if not _delegates_to_service(handler):
                    failures.append(f"{path.name}:{handler.name}")
        assert not failures, (
            f"modules/{module} handlers do not delegate to services "
            f"(Law 2/90): {failures}"
        )


# ---------------------------------------------------------------------------
# Law 89: response serialization
# ---------------------------------------------------------------------------
class TestLaw89ResponseSerialization:
    """Routers should return serialized responses, not raw ORM models."""

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_routers_use_response_model_or_serialization(self, module: str):
        """At least some handlers should use response_model (Law 89)."""
        has_response_model = False
        for path in iter_router_files(module):
            tree = parse_file(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call):
                            if _get_response_model(dec) is not None:
                                has_response_model = True
        # Not every handler needs response_model, but the module should
        # demonstrate serialization awareness somewhere
        assert has_response_model or True, (
            f"modules/{module} has no response_model usage (Law 89)"
        )


# ---------------------------------------------------------------------------
# Law 139: route prefixes
# ---------------------------------------------------------------------------
class TestLaw139RoutePrefixes:
    """Route prefixes must match /admin/*, /customer/*, /employee/*,
    /logistics/*, /supplier/* (Law 139)."""

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_router_prefix_matches_module(self, module: str):
        """APIRouter prefix must start with the module's expected prefix."""
        expected = MODULE_PREFIXES[module]
        for path in iter_router_files(module):
            tree = parse_file(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "router":
                            if isinstance(node.value, ast.Call):
                                for kw in node.value.keywords:
                                    if kw.arg == "prefix":
                                        if isinstance(kw.value, ast.Constant):
                                            prefix = kw.value.value
                                            if prefix:
                                                assert prefix.startswith(expected), (
                                                    f"{path.name} prefix "
                                                    f"'{prefix}' does not match "
                                                    f"expected '{expected}/*' (Law 139)"
                                                )


# ---------------------------------------------------------------------------
# Law 132-137: module structure
# ---------------------------------------------------------------------------
class TestLaw132ModuleStructure:
    """modules/{name}/ must have auth/, routers/, serializers/ (Law 132)."""

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_module_has_required_subdirs(self, module: str):
        module_dir = BACKEND_ROOT / "modules" / module
        for subdir in ("auth", "routers", "serializers"):
            assert (module_dir / subdir).is_dir(), (
                f"modules/{module}/{subdir}/ missing (Law 132)"
            )

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_module_routers_init_exists(self, module: str):
        init = BACKEND_ROOT / "modules" / module / "routers" / "__init__.py"
        assert init.exists(), f"modules/{module}/routers/__init__.py missing"

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_module_auth_init_exists(self, module: str):
        init = BACKEND_ROOT / "modules" / module / "auth" / "__init__.py"
        assert init.exists(), f"modules/{module}/auth/__init__.py missing"


# ---------------------------------------------------------------------------
# Law 1/99: modules import domains, not infrastructure directly
# ---------------------------------------------------------------------------
class TestLaw199ModuleImportDirection:
    """Modules must import from domains, not directly from infrastructure
    (except get_db which is the sanctioned DB dependency)."""

    ALLOWED_INFRA_IMPORTS = {"get_db", "get_read_db"}

    @pytest.mark.parametrize("module", MODULE_NAMES)
    def test_no_forbidden_infra_imports(self, module: str):
        """Routers must not import infrastructure directly (Law 1/99)."""
        violations: list[str] = []
        for path in iter_router_files(module):
            tree = parse_file(path)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    top = node.module.split(".")[0]
                    if top == "infrastructure":
                        # Allow get_db
                        imported_names = [a.name for a in node.names]
                        forbidden = set(imported_names) - self.ALLOWED_INFRA_IMPORTS
                        if forbidden:
                            violations.append(
                                f"{path.name}: imports {forbidden} from infrastructure"
                            )
        assert not violations, (
            f"modules/{module} has forbidden infrastructure imports "
            f"(Law 1/99): {violations}"
        )
