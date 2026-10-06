"""Tests for verified runtime fixes aligned with ARCHITECTURE_STACK.md and TECHNOLOGY_STACK.md."""
from __future__ import annotations

import os
import sys
import importlib

import pytest

_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("CSRF_DISABLED", "true")


class TestCorsMiddlewareRegistration:
    """CORS middleware must be registered in the Foundation layer (Law 40)."""

    def test_cors_in_foundation_layer(self):
        from middleware.orchestrator import _FOUNDATION
        from fastapi.middleware.cors import CORSMiddleware
        assert CORSMiddleware in _FOUNDATION

    def test_cors_resolves_allow_origins(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "allow_origins" in kwargs
        assert isinstance(kwargs["allow_origins"], list)
        assert len(kwargs["allow_origins"]) > 0

    def test_cors_allows_authorization_header(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "Authorization" in kwargs["allow_headers"]

    def test_cors_allows_content_type_header(self):
        from middleware.orchestrator import _resolve_kwargs
        from fastapi.middleware.cors import CORSMiddleware
        kwargs = _resolve_kwargs(CORSMiddleware)
        assert "Content-Type" in kwargs["allow_headers"]


class TestHealthEndpointReadinessFlags:
    """Health endpoints must honor readiness_require_* flags consistently."""

    def test_readiness_flags_default_to_false_in_dev(self):
        from infrastructure.utils.config import get_settings
        settings = get_settings()
        assert settings.readiness_require_valkey is False
        assert settings.readiness_require_email is False
        assert settings.readiness_require_payments is False

    def test_health_endpoint_imports(self):
        import main as main_mod
        assert hasattr(main_mod, "health_check")
        assert hasattr(main_mod, "health_deps")
        assert hasattr(main_mod, "health_ready")


class TestDatabaseAsyncFirstConfiguration:
    """Database configuration must support asyncpg URLs for dev (TECHNOLOGY_STACK.md)."""

    def test_env_uses_asyncpg_scheme(self):
        env_path = os.path.join(_BACKEND_ROOT, "backend", ".env")
        with open(env_path, "r") as f:
            content = f.read()
        assert "postgresql+asyncpg://" in content
        assert "sqlite:///./zozi.db" not in content

    def test_env_has_database_url_direct(self):
        env_path = os.path.join(_BACKEND_ROOT, "backend", ".env")
        with open(env_path, "r") as f:
            content = f.read()
        assert "DATABASE_URL_DIRECT=" in content

    def test_env_has_valkey_url(self):
        env_path = os.path.join(_BACKEND_ROOT, "backend", ".env")
        with open(env_path, "r") as f:
            content = f.read()
        assert "VALKEY_URL=" in content
        assert "valkey://" in content

    def test_database_py_has_sync_fallback(self):
        from infrastructure.database import database as db_mod
        assert hasattr(db_mod, "engine")
        assert hasattr(db_mod, "_async_engine")
        assert hasattr(db_mod, "_AsyncSessionLocal")
        assert hasattr(db_mod, "get_db")
        assert hasattr(db_mod, "get_async_db")


class TestThrowawayScriptsRemoved:
    """Throwaway debug scripts must be removed (Law 27)."""

    def test_no_health_test_scripts_in_root(self):
        backend_root = os.path.join(_BACKEND_ROOT, "backend")
        for item in os.listdir(backend_root):
            if item.startswith("health_test_") and item.endswith(".py"):
                pytest.fail(f"Throwaway script still present: {item}")

    def test_no_check_db_scripts_in_root(self):
        backend_root = os.path.join(_BACKEND_ROOT, "backend")
        forbidden = ["check_db.py", "check_db_accounts.py", "check_bom.py",
                     "check_baseline_cols.py", "check_auth_import.py",
                     "check_tables.py", "check_domain_imports.py",
                     "check_db_data.py", "check_db_activity.py"]
        for fname in forbidden:
            path = os.path.join(backend_root, fname)
            assert not os.path.exists(path), f"Throwaway script still present: {fname}"

    def test_no_audit_scripts_in_root(self):
        backend_root = os.path.join(_BACKEND_ROOT, "backend")
        forbidden = ["_audit_imports.py", "_audit_boot_check.py"]
        for fname in forbidden:
            path = os.path.join(backend_root, fname)
            assert not os.path.exists(path), f"Throwaway script still present: {fname}"


class TestMobilePnpmWorkspace:
    """Mobile app pnpm workspace must be valid."""

    def test_pnpm_workspace_yaml_valid(self):
        workspace_path = os.path.join(_BACKEND_ROOT, "frontend", "mobile_app", "pnpm-workspace.yaml")
        with open(workspace_path, "r") as f:
            content = f.read()
        assert "set this to true or false" not in content
        assert "@sentry/cli" in content

    def test_mobile_node_modules_populated(self):
        node_modules = os.path.join(_BACKEND_ROOT, "frontend", "mobile_app", "node_modules")
        assert os.path.isdir(node_modules)
        assert len(os.listdir(node_modules)) > 0
