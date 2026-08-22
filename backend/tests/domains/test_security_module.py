"""
Smoke tests for the rescued Security module.

Verifies that the authentic Security-domain import violations have been resolved:
  * `controllers/auth_controller.py` resolves (`services.security.auth_write_service` was
    broken/missing, and all audit imports now resolve to the canonical `infrastructure.utils.audit`).
  * `utils/security_audit.py` no longer imports `models` at module top (CIR1).
  * `routers/auth.py` no longer imports the `generate_csrf_token` upward edge.
  * `services/auth_write_service.py` exposes the write-helper callables.

These tests only exercise importability / callability — no database is required.
"""
from __future__ import annotations

import importlib
import os

import pytest

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-security-module-tests")


def test_auth_controller_imports():
    mod = importlib.import_module("controllers.security.auth_controller")
    assert hasattr(mod, "get_current_user")


def test_security_audit_no_top_level_models_import():
    import ast

    src = importlib.import_module("infrastructure.utils.security_audit").__file__
    tree = ast.parse(open(src, encoding="utf-8").read())
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            assert node.module != "models", "utils must not import models at top level"
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name == "models"


def test_routers_auth_no_middleware_csrf_import():
    import ast

    src = importlib.import_module("routers.public_auth_access").__file__
    tree = ast.parse(open(src, encoding="utf-8").read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module != "middleware.csrf_middleware"


def test_auth_write_service_helpers_callable():
    mod = importlib.import_module("services.security.auth_write_service")
    required = [
        "create_user",
        "create_social_user",
        "update_user",
        "update_user_email_verification",
        "create_email_verification_token",
        "mark_email_verification_token_used",
        "create_password_reset_token",
        "mark_password_reset_token_used",
        "execute_password_reset",
        "create_supplier_profile",
        "create_logistics_partner",
        "ensure_referral_code",
        "record_referral_event",
        "update_user_referral_points",
        "claim_share_points",
        "record_login_history",
        "update_user_device_fingerprint",
        "update_user_totp",
        "disable_user_totp",
        "commit_user_registration",
        "persist_last_login",
        "flush_user",
        "update_or_create_social_user",
        "update_user_profile",
        "update_user_points",
        "add_user_device",
        "update_user_email_verified",
        "expire_email_verification_token",
    ]
    for name in required:
        assert callable(getattr(mod, name)), f"missing auth_write_service helper: {name}"


def test_audit_single_canonical_source():
    """`infrastructure.utils.audit` is the single source of truth; the `services/audit` package is a
    real (non-shim) package and no longer re-exports the audit primitives."""
    import pathlib

    mod = importlib.import_module("infrastructure.utils.audit")
    assert hasattr(mod, "AuditAction")
    assert callable(mod.audit_log)

    pkg = importlib.import_module("services.audit")
    assert not hasattr(pkg, "audit_log"), "shim re-export must be gone"
    assert not (pathlib.Path(pkg.__file__).parent / "audit_service.py").exists()


def test_admin_auth_lives_in_security_domain():
    """Admin auth helpers moved from the admin surface folder into the security
    domain (controllers/security/admin_auth.py); importers were updated."""
    import pathlib

    ctrl_dir = pathlib.Path(__file__).resolve().parents[1] / "controllers"
    assert (ctrl_dir / "security" / "admin_auth.py").exists(), "security/admin_auth.py must exist"
    assert not (ctrl_dir / "admin" / "auth.py").exists(), "old admin/auth.py must be gone"

    users_src = (ctrl_dir / "customer" / "users.py").read_text(encoding="utf-8")
    assert "from modules.admin.routers.auth import" not in users_src
    assert "controllers.admin.admin_auth" not in users_src

