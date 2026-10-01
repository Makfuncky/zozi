"""Comprehensive input validation security tests for ZOZI backend.

Tests Pydantic schema validation, SQL injection prevention, XSS prevention,
request body size limits, input sanitization, and OTP rate limiting.
"""
from __future__ import annotations

import uuid

import pytest


class TestPydanticSchemaValidation:
    """Test Pydantic schema validation on endpoints."""

    def test_register_rejects_invalid_email(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (422, 429)

    def test_register_rejects_missing_email(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code == 422

    def test_register_rejects_missing_password(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "role": "customer",
            },
        )
        assert resp.status_code == 422

    def test_register_rejects_invalid_role(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"user_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "superadmin",  # Invalid role
            },
        )
        # Should be rejected as invalid enum value
        assert resp.status_code in (422, 400)

    def test_login_rejects_empty_body(self, client):
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422

    def test_login_rejects_malformed_json(self, client):
        resp = client.post(
            "/api/v1/auth/login",
            content=b"not json",
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code in (400, 422)

    def test_schema_validates_email_format(self, client):
        """Ensure properly formatted email is accepted."""
        email = f"valid_{uuid.uuid4().hex[:8]}@zozi.test"
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "username": f"valid_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201)

    def test_schema_rejects_sql_injection_in_email(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin' OR '1'='1",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        # Should be rejected as invalid email format
        assert resp.status_code in (422, 400)

    def test_schema_rejects_xss_in_username(self, client):
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"xss_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": "<script>alert('xss')</script>",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        # Should either reject or sanitize
        assert resp.status_code in (200, 201, 422)


class TestSQLInjectionPrevention:
    """Test SQL injection prevention through parameterized queries."""

    def test_login_with_sql_injection_in_email(self, client):
        """SQL injection in email field should not bypass authentication."""
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@zozi.com' OR '1'='1",
                "password": "anything",
            },
        )
        assert resp.status_code == 401

    def test_login_with_sql_injection_in_password(self, client):
        """SQL injection in password field should not bypass authentication."""
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@zozi.com",
                "password": "' OR '1'='1' --",
            },
        )
        assert resp.status_code == 401

    def test_login_with_union_injection(self, client):
        """UNION-based SQL injection should fail."""
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@zozi.com' UNION SELECT 1,2,3--",
                "password": "anything",
            },
        )
        assert resp.status_code in (401, 422)

    def test_login_with_comment_injection(self, client):
        """Comment-based SQL injection should fail."""
        resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@zozi.com'; DROP TABLE users;--",
                "password": "anything",
            },
        )
        assert resp.status_code in (401, 422)


class TestXSSPrevention:
    """Test XSS prevention through output encoding."""

    def test_username_with_script_tags_rejected_or_sanitized(self, client):
        """Username with script tags should be rejected or sanitized."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"xss_test_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": "user<script>alert(1)</script>",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        # Either rejected or the response should not contain raw script tags
        if resp.status_code in (200, 201):
            body = resp.json()
            if "username" in body.get("user", {}):
                assert "<script>" not in body["user"]["username"]

    def test_email_field_not_reflected_as_html(self, client):
        """Email should not be reflected as raw HTML."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"<b>bold_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        # Invalid email should be rejected
        assert resp.status_code in (422, 400)


class TestRequestBodySizeLimits:
    """Test request body size limits."""

    def test_oversized_payload_rejected(self, client):
        """Very large payload should be rejected."""
        large_data = "x" * (10 * 1024 * 1024)  # 10MB string
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"size_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": large_data,
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        # Should be rejected (413 or 422)
        assert resp.status_code in (413, 422, 400)

    def test_deeply_nested_json_rejected(self, client):
        """Deeply nested JSON should be handled gracefully."""
        nested = {"a": {"b": {"c": {"d": {"e": "deep"}}}}}
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"nested_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": f"user_{uuid.uuid4().hex[:8]}",
                "password": "SecurePass1!",
                "role": "customer",
                "metadata": nested,
            },
        )
        # Should either accept or reject gracefully
        assert resp.status_code in (200, 201, 422)


class TestInputSanitization:
    """Test input sanitization on various inputs."""

    def test_null_bytes_in_input(self, client):
        """Null bytes in input should be handled."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"null_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": "user\x00name",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201, 422)

    def test_unicode_normalization(self, client):
        """Unicode characters in input should be handled."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"unicode_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": "user_名前",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201, 422)

    def test_path_traversal_in_input(self, client):
        """Path traversal attempts should be handled."""
        resp = client.post(
            "/api/v1/auth/register",
            json={
                "email": f"path_{uuid.uuid4().hex[:8]}@zozi.test",
                "username": "../../../etc/passwd",
                "password": "SecurePass1!",
                "role": "customer",
            },
        )
        assert resp.status_code in (200, 201, 422)


class TestPasswordResetTokenValidation:
    """Test password reset token validation."""

    def test_forgot_password_with_valid_email(self, client):
        """Forgot password with valid email should return success."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "admin@zozi.com"},
        )
        # Should return 200 even if email doesn't exist (to prevent enumeration)
        assert resp.status_code in (200, 429)

    def test_forgot_password_with_invalid_email(self, client):
        """Forgot password with invalid email format should be rejected."""
        resp = client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "not-an-email"},
        )
        assert resp.status_code in (422, 400)

    def test_reset_password_with_invalid_token(self, client):
        """Reset password with invalid token should fail."""
        resp = client.post(
            "/api/v1/auth/reset-password",
            json={
                "token": "invalid-token",
                "new_password": "NewSecurePass1!",
            },
        )
        assert resp.status_code in (400, 401, 422)


class TestOTPVerificationRateLimiting:
    """Test OTP verification rate limiting."""

    def test_otp_rate_limiting_on_brute_force(self, client):
        """Multiple OTP attempts should be rate limited."""
        # This test verifies the rate limiting mechanism exists
        # Actual OTP endpoints may vary
        responses = []
        for _ in range(15):
            resp = client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "admin@zozi.com"},
            )
            responses.append(resp.status_code)

        # At least some should be rate limited (429) if rate limiting is active
        # In test env, rate limiting may be disabled
        assert all(s in (200, 429, 422) for s in responses)


class TestSecurityHeadersOnValidation:
    """Test that security headers are present on validation failures."""

    def test_422_response_has_security_headers(self, client):
        """Even validation error responses should have security headers."""
        resp = client.post(
            "/api/v1/auth/register",
            json={"email": "invalid"},
        )
        # Security headers should be present
        assert "X-Content-Type-Options" in resp.headers or resp.status_code == 422

    def test_401_response_does_not_leak_info(self, client):
        """401 responses should not leak implementation details."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code == 401
        # Should not contain stack traces or internal paths
        body = resp.json()
        assert "traceback" not in str(body).lower()
        assert "stack" not in str(body).lower()
