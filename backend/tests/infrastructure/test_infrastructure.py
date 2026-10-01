"""Smoke tests for the backend infrastructure layer.

Verifies:
  1. Database connection (get_db) works with the test engine.
  2. Redis client is available (real or NoOp fallback).
  3. Security utilities (JWT, hashing) function correctly.
  4. Pagination utilities clamp and paginate as expected.
"""
from __future__ import annotations

import os
import sys
from datetime import timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

# Ensure backend root is importable
_BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")


class TestDatabaseConnection:
    """Database connectivity and session management."""

    def test_get_db_yields_session(self, db_session):
        assert db_session is not None
        result = db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1

    def test_db_session_rollback(self, db_session):
        """Verify the rollback session does not persist data."""
        result = db_session.execute(text("SELECT 1 AS val"))
        row = result.fetchone()
        assert row[0] == 1

    def test_engine_fixture_exists(self, engine):
        assert engine is not None
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1

    def test_check_connection_health(self):
        from infrastructure.database.database import check_connection_health
        assert check_connection_health() is True

    def test_validate_connection_pool(self):
        from infrastructure.database.database import validate_connection_pool
        result = validate_connection_pool()
        assert isinstance(result, dict)
        assert result.get("validation_ok") is True

    def test_get_pool_metrics(self):
        from infrastructure.database.database import get_pool_metrics
        result = get_pool_metrics()
        assert isinstance(result, dict)
        assert "size" in result


class TestRedisConnection:
    """Redis client availability and fallback behavior."""

    def test_redis_client_returns_object(self):
        from infrastructure.database.redis_client import redis_client
        client = redis_client()
        assert client is not None

    def test_redis_noop_fallback(self):
        from infrastructure.database.redis_client import _NoOpRedis
        noop = _NoOpRedis()
        assert noop.get("any_key") is None
        assert noop.set("key", "val") is None
        assert noop.exists("key") is None
        assert noop.delete("key") is None
        assert noop.keys() == []

    def test_redis_health_status(self):
        from infrastructure.database.redis_client import get_redis_health_status
        status = get_redis_health_status()
        assert isinstance(status, dict)
        assert "available" in status

    def test_redis_noop_pipeline(self):
        from infrastructure.database.redis_client import _NoOpPipeline
        pipe = _NoOpPipeline()
        result = pipe.set("k", "v").execute()
        assert result == []


class TestSecurityUtilities:
    """JWT token creation/verification and password hashing."""

    def test_password_hash_and_verify(self):
        from infrastructure.utils.auth import get_password_hash, verify_password
        password = "SecureP@ss123"
        hashed = get_password_hash(password)
        assert hashed is not None
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_create_access_token(self):
        from infrastructure.utils.auth import create_access_token
        token = create_access_token(data={"sub": "1", "role": "admin"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token(self):
        from infrastructure.utils.auth import create_access_token, verify_token
        token = create_access_token(data={"sub": "42", "role": "customer"})
        subject = verify_token(token)
        assert subject == "42"

    def test_create_refresh_token(self):
        from infrastructure.utils.auth import create_refresh_token
        token = create_refresh_token(data={"sub": "1"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_refresh_token(self):
        from infrastructure.utils.auth import create_refresh_token, verify_refresh_token
        token = create_refresh_token(data={"sub": "99"})
        subject, family_id = verify_refresh_token(token)
        assert subject == "99"
        assert family_id is not None

    def test_token_blacklist(self):
        from infrastructure.utils.auth import blacklist_token, is_token_blacklisted
        jti = "test-jti-12345"
        blacklist_token(jti, ttl_seconds=60)
        assert is_token_blacklisted(jti) is True

    def test_token_not_blacklisted(self):
        from infrastructure.utils.auth import is_token_blacklisted
        assert is_token_blacklisted("nonexistent-jti") is False

    def test_password_complexity_valid(self):
        from infrastructure.utils.auth import validate_password_complexity
        # Should not raise
        validate_password_complexity("ValidP@ss1")

    def test_password_complexity_invalid(self):
        from infrastructure.utils.auth import validate_password_complexity
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_password_complexity("weak")

    def test_account_lockout(self):
        from infrastructure.utils.auth import (
            clear_failed_logins,
            is_account_locked,
            record_failed_login,
        )
        identifier = "test-user@example.com"
        clear_failed_logins(identifier)
        for _ in range(5):
            record_failed_login(identifier)
        assert is_account_locked(identifier) is True
        clear_failed_logins(identifier)
        assert is_account_locked(identifier) is False


class TestPaginationUtilities:
    """Pagination helpers clamp and paginate correctly."""

    def test_safe_page_defaults(self):
        from infrastructure.utils.pagination import safe_page
        page, size = safe_page(None, None)
        assert page == 1
        assert size == 20

    def test_safe_page_clamps_size(self):
        from infrastructure.utils.pagination import safe_page, MAX_PAGE_SIZE
        page, size = safe_page(1, 500)
        assert size == MAX_PAGE_SIZE

    def test_safe_page_minimums(self):
        from infrastructure.utils.pagination import safe_page
        page, size = safe_page(0, 0)
        assert page == 1
        assert size == 1

    def test_get_max_page_size(self):
        from infrastructure.utils.pagination import get_max_page_size
        result = get_max_page_size()
        assert isinstance(result, int)
        assert result > 0

    def test_encode_decode_keyset_cursor(self):
        from infrastructure.utils.pagination import (
            decode_keyset_cursor,
            encode_keyset_cursor,
        )
        values = [100, "test", 3.14]
        cursor = encode_keyset_cursor(values)
        decoded = decode_keyset_cursor(cursor)
        assert decoded is not None
        assert decoded[0] == 100

    def test_encode_decode_keyset_cursor_with_secret(self):
        from infrastructure.utils.pagination import (
            decode_keyset_cursor,
            encode_keyset_cursor,
        )
        values = [42, "secret-test"]
        cursor = encode_keyset_cursor(values, secret="my-secret")
        decoded = decode_keyset_cursor(cursor, secret="my-secret")
        assert decoded is not None
        assert decoded[0] == 42

    def test_decode_invalid_cursor(self):
        from infrastructure.utils.pagination import decode_keyset_cursor
        assert decode_keyset_cursor(None) is None
        assert decode_keyset_cursor("") is None
        assert decode_keyset_cursor("invalid-data") is None

    def test_build_cursor_pagination_payload(self):
        from infrastructure.utils.pagination import build_cursor_pagination_payload
        payload = build_cursor_pagination_payload([], None, 20)
        assert payload["items"] == []
        assert payload["next_cursor"] is None
        assert payload["has_next"] is False
        assert payload["page_size"] == 20
