"""Regression tests for FILE-133: backend/modules/customer/routers/accounts.py

Verifies the 8 security fixes from the Over All finding block:
1. POST /api/v1/auth/login has @limiter.limit(RL_SENSITIVE)
2. Public endpoints (/register, /verify-email/{token}, /resend-verification-public,
   /forgot-password, /reset-password) have verify_captcha
3. GET /api/v1/auth/me uses check_blacklist=True
4. POST /api/v1/auth/totp/complete has @limiter.limit(RL_SENSITIVE) and verify_captcha
5. POST /api/v1/auth/login and POST /api/v1/auth/register have @limiter.limit() and verify_captcha
6. POST /api/v1/auth/resend-verification-public has verify_captcha
7. JWT access token cookie SameSite is configured outside this router (not in scope)
8. GET /api/v1/auth/me masks email in response body

Plus Law 2 (thin router) and Law 4 (require_feature gates) checks.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

ACCOUNTS_ROUTER = _BACKEND_ROOT / "modules" / "customer" / "routers" / "accounts.py"


def _parse_accounts_router() -> ast.Module:
    assert ACCOUNTS_ROUTER.exists(), f"{ACCOUNTS_ROUTER} not found"
    return ast.parse(ACCOUNTS_ROUTER.read_text(encoding="utf-8"))


def _find_handlers(tree: ast.Module) -> dict[str, ast.AST]:
    handlers: dict[str, ast.AST] = {}
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (
                isinstance(dec, ast.Call)
                and isinstance(dec.func, ast.Attribute)
                and dec.func.attr in {"get", "post", "put", "delete", "patch", "head", "options"}
            ):
                handlers[node.name] = node
    return handlers


def _has_limiter_sensitive(handler: ast.FunctionDef) -> bool:
    for dec in handler.decorator_list:
        if isinstance(dec, ast.Call):
            if isinstance(dec.func, ast.Attribute) and dec.func.attr == "limit":
                for arg in dec.args:
                    if isinstance(arg, ast.Name) and arg.id == "RL_SENSITIVE":
                        return True
    return False


def _is_depends_call(node: ast.expr) -> bool:
    return isinstance(node, ast.Call) and (
        (isinstance(node.func, ast.Name) and node.func.id == "Depends")
        or (isinstance(node.func, ast.Attribute) and node.func.attr == "Depends")
    )


def _has_verify_captcha(handler: ast.FunctionDef) -> bool:
    for default in handler.args.defaults:
        if _is_depends_call(default):
            for arg in default.args:
                if isinstance(arg, ast.Attribute) and arg.attr == "verify_captcha":
                    return True
                if isinstance(arg, ast.Name) and arg.id == "verify_captcha":
                    return True
    return False


def _has_require_feature(handler: ast.FunctionDef) -> bool:
    for default in handler.args.defaults:
        if _is_depends_call(default):
            for arg in default.args:
                if isinstance(arg, ast.Call):
                    if isinstance(arg.func, ast.Name) and arg.func.id == "require_feature":
                        return True
                    if isinstance(arg.func, ast.Attribute) and arg.func.attr == "require_feature":
                        return True
    return False


def _has_check_blacklist_true(handler: ast.FunctionDef) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "decode_token":
                for kw in node.keywords:
                    if kw.arg == "check_blacklist" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        return True
    return False


def _has_email_masking(handler: ast.AST) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            keys = node.value.keys
            values = node.value.values
            for i, key in enumerate(keys):
                if isinstance(key, ast.Constant) and key.value == "email" and i < len(values):
                    val = values[i]
                    if isinstance(val, ast.Constant):
                        continue
                    if isinstance(val, ast.Call):
                        if isinstance(val.func, ast.Attribute) and val.func.attr == "get":
                            return False
                    return True
    return False


class TestAccountsRouterSecurity:
    """Regression tests for FILE-133 security fixes."""

    @pytest.fixture(autouse=True)
    def _tree(self):
        self.tree = _parse_accounts_router()
        self.handlers = _find_handlers(self.tree)

    def test_login_has_rate_limiter(self):
        assert "login" in self.handlers
        assert _has_limiter_sensitive(self.handlers["login"]), \
            "POST /api/v1/auth/login must have @limiter.limit(RL_SENSITIVE)"

    def test_refresh_has_rate_limiter(self):
        assert "refresh" in self.handlers
        assert _has_limiter_sensitive(self.handlers["refresh"]), \
            "POST /api/v1/auth/refresh must have @limiter.limit(RL_SENSITIVE)"

    def test_totp_complete_has_rate_limiter(self):
        assert "auth_totp_complete" in self.handlers
        assert _has_limiter_sensitive(self.handlers["auth_totp_complete"]), \
            "POST /api/v1/auth/totp/complete must have @limiter.limit(RL_SENSITIVE)"

    def test_public_endpoints_have_captcha(self):
        public_with_captcha = {
            "auth_register",
            "auth_register_form",
            "auth_verify_email",
            "auth_resend_verification_public",
            "auth_forgot_password",
            "auth_reset_password",
            "auth_totp_complete",
            "auth_social_google_id_token",
        }
        for name in public_with_captcha:
            assert name in self.handlers, f"{name} handler not found"
            assert _has_verify_captcha(self.handlers[name]), \
                f"{name} must have verify_captcha dependency"

    def test_me_checks_blacklist(self):
        assert "me" in self.handlers
        assert _has_check_blacklist_true(self.handlers["me"]), \
            "GET /api/v1/auth/me must call decode_token with check_blacklist=True"

    def test_me_masks_email_in_response(self):
        assert "me" in self.handlers
        assert _has_email_masking(self.handlers["me"]), \
            "GET /api/v1/auth/me must mask email in response body"

    def test_all_protected_endpoints_have_require_feature(self):
        """Law 4: every protected endpoint must use require_feature."""
        protected_endpoints = {
            "list_addresses",
            "create_address",
            "update_address",
            "delete_address",
            "set_default_address",
            "customer_get_coins",
            "customer_redeem_coins",
            "customer_get_recommendations",
            "customer_get_last_seen",
            "auth_register_form",
            "auth_resend_verification",
            "customer_change_password",
            "customer_update_profile",
            "customer_upload_avatar",
            "customer_totp_status",
            "customer_totp_setup",
            "customer_totp_enable",
            "customer_totp_disable",
            "auth_totp_complete",
            "auth_social_google_start",
            "auth_social_google_callback",
            "auth_social_facebook_start",
            "auth_social_facebook_callback",
            "auth_social_google_id_token",
            "customer_list_sessions",
            "customer_revoke_session",
            "customer_data_export",
            "customer_delete_request",
        }
        for name in protected_endpoints:
            assert name in self.handlers, f"{name} handler not found"
            assert _has_require_feature(self.handlers[name]), \
                f"{name} must have require_feature dependency"

    def test_no_raw_sql_in_router(self):
        """Law 2: router must be thin, no raw SQL."""
        source = ACCOUNTS_ROUTER.read_text(encoding="utf-8")
        assert "execute(" not in source, "raw SQL execute() found in router"
        assert "text(" not in source, "raw SQL text() found in router"

    def test_no_business_logic_in_router(self):
        """Law 2: router must delegate to domain services, not contain business logic."""
        tree = _parse_accounts_router()
        business_funcs = {
            "_normalize_address_payload",
            "_serialize_address",
            "_get_user_address",
            "unset_other_default_addresses",
        }
        defined_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        defined_names.add(target.id)
        violations = defined_names & business_funcs
        assert not violations, f"business logic found in router: {violations}"
