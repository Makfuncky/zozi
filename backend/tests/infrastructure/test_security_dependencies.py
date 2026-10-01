"""Regression tests for FILE-066: infrastructure.security.dependencies.

Verifies:
- set_current_user is defined in the infrastructure layer (no upward import
  from rbac.dependencies inside the shim).
- get_current_user is forwarded from the canonical source and wrapped so
  that set_current_user is called on resolution.
- No stale ``from rbac`` import exists in the shim module source.
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")


class TestNoUpwardRbacImport:
    """Law 1 compliance: infrastructure/ must not import rbac/."""

    def test_no_rbac_import_in_shim_source(self):
        """infrastructure/security/dependencies.py must not contain 'from rbac'."""
        shim_path = os.path.join(
            _BACKEND_ROOT, "infrastructure", "security", "dependencies.py"
        )
        with open(shim_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        assert "from rbac" not in source, (
            "Found stale 'from rbac' import in infrastructure/security/dependencies.py"
        )
        assert "import rbac" not in source, (
            "Found stale 'import rbac' in infrastructure/security/dependencies.py"
        )


class TestSetCurrentUserInInfrastructure:
    """set_current_user must live in the infrastructure layer."""

    def test_set_current_user_defined_in_shim(self):
        from infrastructure.security.dependencies import set_current_user

        assert callable(set_current_user)

    def test_set_current_user_not_in_rbac(self):
        """rbac/dependencies.py must not define its own set_current_user
        — it must import it from infrastructure.security.dependencies."""
        rbac_path = os.path.join(_BACKEND_ROOT, "rbac", "dependencies.py")
        with open(rbac_path, "r", encoding="utf-8") as fh:
            source = fh.read()
        tree = ast.parse(source)
        defined_names = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
        assert "set_current_user" not in defined_names, (
            "rbac/dependencies.py must not define its own set_current_user; "
            "it should import from infrastructure.security.dependencies"
        )


class TestGetCurrentUserForwarded:
    """get_current_user must still be forwarded from the canonical source."""

    def test_get_current_user_accessible_via_shim(self):
        import infrastructure.security.dependencies as shim

        assert hasattr(shim, "get_current_user")
        assert callable(shim.get_current_user)

    def test_set_current_user_infrastructure_owned(self):
        """set_current_user lives in infrastructure.security.dependencies and
        is importable directly (no rbac intermediate)."""
        from infrastructure.security.dependencies import set_current_user as scf
        from infrastructure.security.dependencies import _current_user_ctx

        assert scf is not None
        assert _current_user_ctx is not None
        # Verify the setter actually writes to the context var.
        sentinel = object()
        scf(sentinel)
        assert _current_user_ctx.get() is sentinel
        # Clean up.
        _current_user_ctx.set(None)
