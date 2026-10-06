"""Security tests for customer auth endpoints (FILE-133)."""
from __future__ import annotations

import os
import inspect
from pathlib import Path

# Ensure .env is loaded before settings are instantiated.
_ROOT = Path(__file__).resolve().parent.parent.parent.parent
try:
    from dotenv import load_dotenv
    load_dotenv(_ROOT / ".env", override=False)
    load_dotenv(_ROOT / "backend" / ".env", override=False)
except ImportError:
    pass
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", os.getenv("TEST_SECRET_KEY", ""))
os.environ.setdefault("FIELD_ENCRYPTION_KEY", os.getenv("TEST_FIELD_ENCRYPTION_KEY", "a" * 64))
os.environ.setdefault("AUDIT_CHAIN_KEY", os.getenv("TEST_AUDIT_CHAIN_KEY", "b" * 32))
# Force DATABASE_URL to a valid scheme so Settings() can be instantiated in tests.
os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from slowapi import Limiter
from slowapi.util import get_remote_address

from infrastructure.security.rate_limiter import limiter as global_limiter, RL_SENSITIVE
from modules.customer.routers.accounts import (
    login,
    refresh,
    auth_register,
    auth_register_form,
    auth_verify_email,
    auth_resend_verification_public,
    auth_forgot_password,
    auth_reset_password,
    auth_totp_complete,
    auth_social_google_id_token,
    me,
)


class TestLoginRateLimited:
    """Login endpoint must enforce rate limiting."""

    def test_login_has_limiter_decorator(self):
        """The login endpoint must carry the @limiter.limit(RL_SENSITIVE) decorator."""
        route_key = f"{login.__module__}.{login.__name__}"
        assert route_key in global_limiter._route_limits, (
            f"Login endpoint missing rate limiter decorator. "
            f"Expected '{route_key}' in limiter._route_limits"
        )
        limits = global_limiter._route_limits[route_key]
        assert any("10" in str(l) for l in limits), (
            "Expected RL_SENSITIVE (10/minute) limit on login endpoint"
        )

    def test_refresh_has_limiter_decorator(self):
        """The refresh endpoint must carry the @limiter.limit(RL_SENSITIVE) decorator."""
        route_key = f"{refresh.__module__}.{refresh.__name__}"
        assert route_key in global_limiter._route_limits, (
            f"Refresh endpoint missing rate limiter decorator. "
            f"Expected '{route_key}' in limiter._route_limits"
        )


class TestRevokedTokenRejectedOnMe:
    """Blacklisted tokens must be rejected by /auth/me."""

    def test_revoked_token_rejected_on_me(self):
        """The /auth/me endpoint must pass check_blacklist=True to decode_token."""
        source = inspect.getsource(me)
        assert "check_blacklist=True" in source, (
            "me() must pass check_blacklist=True to decode_token "
            "to reject blacklisted tokens"
        )


class TestPublicEndpointsRequireCaptcha:
    """Public auth endpoints must require CAPTCHA verification."""

    @pytest.mark.parametrize(
        "endpoint",
        [
            login,
            auth_register,
            auth_register_form,
            auth_verify_email,
            auth_resend_verification_public,
            auth_forgot_password,
            auth_reset_password,
            auth_totp_complete,
            auth_social_google_id_token,
        ],
    )
    def test_endpoint_has_captcha_parameter(self, endpoint):
        """Each public auth endpoint must have a _captcha: None = Depends(verify_captcha) parameter."""
        sig = inspect.signature(endpoint)
        params = list(sig.parameters.keys())
        assert "_captcha" in params, (
            f"{endpoint.__name__} missing _captcha parameter for CAPTCHA verification"
        )


class TestAuthEndpointSecurity:
    """General security checks for auth endpoints."""

    def test_auth_endpoint_security(self):
        """Public auth endpoints must have CAPTCHA, rate limiting, and blacklist checks."""
        # Verify rate limiting decorators are present on sensitive endpoints
        route_key_login = f"{login.__module__}.{login.__name__}"
        route_key_refresh = f"{refresh.__module__}.{refresh.__name__}"
        assert route_key_login in global_limiter._route_limits
        assert route_key_refresh in global_limiter._route_limits

        # Verify CAPTCHA dependency on all public endpoints
        public_endpoints = [
            login,
            auth_register,
            auth_register_form,
            auth_verify_email,
            auth_resend_verification_public,
            auth_forgot_password,
            auth_reset_password,
            auth_totp_complete,
            auth_social_google_id_token,
        ]
        for endpoint in public_endpoints:
            sig = inspect.signature(endpoint)
            assert "_captcha" in sig.parameters, (
                f"{endpoint.__name__} missing _captcha parameter"
            )

        # Verify /auth/me checks token blacklist explicitly
        source = inspect.getsource(me)
        assert "check_blacklist=True" in source


def test_auth_endpoint_security():
    """Paired test: verify all security fixes are in place (contract §20)."""
    # Rate limiting on login and refresh
    route_key_login = f"{login.__module__}.{login.__name__}"
    route_key_refresh = f"{refresh.__module__}.{refresh.__name__}"
    assert route_key_login in global_limiter._route_limits
    assert route_key_refresh in global_limiter._route_limits

    # CAPTCHA on all public endpoints
    public_endpoints = [
        login,
        auth_register,
        auth_register_form,
        auth_verify_email,
        auth_resend_verification_public,
        auth_forgot_password,
        auth_reset_password,
        auth_totp_complete,
        auth_social_google_id_token,
    ]
    for endpoint in public_endpoints:
        sig = inspect.signature(endpoint)
        assert "_captcha" in sig.parameters

    # Blacklist check on /auth/me
    source = inspect.getsource(me)
    assert "check_blacklist=True" in source
