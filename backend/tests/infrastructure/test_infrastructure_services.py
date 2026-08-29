"""Law-aligned tests for infrastructure services (Law 145/146/33/38/32).

Laws covered:
  - Law 145: observability wiring (structlog, OTEL, Prometheus, Sentry)
  - Law 146: security wrapper location (JWT/bcrypt in infrastructure.security)
  - Law 33: JWT type claim (access/refresh/temp)
  - Law 38: bcrypt 72-byte limit
  - Law 32: secrets management
"""
from __future__ import annotations

from datetime import timedelta

import pytest


class TestSecurityJWT:
    """Law 33: JWT type claim, Law 38: bcrypt 72-byte limit."""

    def test_password_hash_and_verify(self) -> None:
        from infrastructure.utils.auth import get_password_hash, verify_password
        password = "SecureP@ss123"
        hashed = get_password_hash(password)
        assert hashed is not None
        assert verify_password(password, hashed) is True
        assert verify_password("wrong", hashed) is False

    def test_create_access_token_has_type_claim(self) -> None:
        """Law 33: JWT must include 'type' claim."""
        from infrastructure.utils.auth import create_access_token, decode_token
        token = create_access_token(data={"sub": "1", "role": "admin"})
        payload = decode_token(token, expected_type="access", check_blacklist=False)
        assert payload.get("type") == "access"

    def test_create_refresh_token_has_type_claim(self) -> None:
        """Law 33: refresh token must have type='refresh'."""
        from infrastructure.utils.auth import create_refresh_token, decode_token
        token = create_refresh_token(data={"sub": "1"})
        payload = decode_token(token, expected_type="refresh", check_blacklist=False)
        assert payload.get("type") == "refresh"

    def test_create_temp_token_has_type_claim(self) -> None:
        """Law 33: temp token must have type='temp'."""
        from infrastructure.utils.auth import create_temp_token, decode_token
        token = create_temp_token(data={"sub": "1"})
        payload = decode_token(token, expected_type="temp", check_blacklist=False)
        assert payload.get("type") == "temp"

    def test_access_token_has_jti(self) -> None:
        """JWT must include jti for revocation."""
        from infrastructure.utils.auth import create_access_token, decode_token
        token = create_access_token(data={"sub": "1"})
        payload = decode_token(token, expected_type="access", check_blacklist=False)
        assert "jti" in payload
        assert len(payload["jti"]) > 0

    def test_verify_token_returns_subject(self) -> None:
        from infrastructure.utils.auth import create_access_token, verify_token
        token = create_access_token(data={"sub": "42", "role": "customer"})
        subject = verify_token(token)
        assert subject == "42"

    def test_verify_refresh_token_returns_family(self) -> None:
        from infrastructure.utils.auth import create_refresh_token, verify_refresh_token
        token = create_refresh_token(data={"sub": "99"})
        subject, family_id = verify_refresh_token(token)
        assert subject == "99"
        assert family_id is not None

    def test_token_blacklist(self) -> None:
        from infrastructure.utils.auth import blacklist_token, is_token_blacklisted
        jti = "test-jti-12345"
        blacklist_token(jti, ttl_seconds=60)
        assert is_token_blacklisted(jti) is True

    def test_token_not_blacklisted(self) -> None:
        from infrastructure.utils.auth import is_token_blacklisted
        assert is_token_blacklisted("nonexistent-jti") is False

    def test_password_complexity_valid(self) -> None:
        from infrastructure.utils.auth import validate_password_complexity
        validate_password_complexity("ValidP@ss1")

    def test_password_complexity_invalid(self) -> None:
        from infrastructure.utils.auth import validate_password_complexity
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            validate_password_complexity("weak")

    def test_password_exceeds_72_bytes_rejected(self) -> None:
        """Law 38: bcrypt 72-byte limit."""
        from infrastructure.utils.auth import get_password_hash
        long_password = "a" * 73
        with pytest.raises(ValueError, match="72"):
            get_password_hash(long_password)

    def test_password_at_72_bytes_accepted(self) -> None:
        """Law 38: exactly 72 bytes should be accepted."""
        from infrastructure.utils.auth import get_password_hash, verify_password
        password = "a" * 72
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_account_lockout(self) -> None:
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

    def test_refresh_token_rotation(self) -> None:
        """Refresh token rotation: old token marked used, new tokens issued."""
        from infrastructure.utils.auth import (
            create_refresh_token,
            rotate_refresh_token,
            verify_refresh_token,
        )
        token = create_refresh_token(data={"sub": "1"})
        new_access, new_refresh = rotate_refresh_token(token)
        assert new_access is not None
        assert new_refresh is not None
        # New refresh token is valid
        subject, family_id = verify_refresh_token(new_refresh)
        assert subject == "1"


class TestRedisCache:
    """Redis cache abstraction tests."""

    def test_redis_client_returns_object(self) -> None:
        from infrastructure.database.redis_client import redis_client
        client = redis_client()
        assert client is not None

    def test_redis_noop_fallback(self) -> None:
        from infrastructure.database.redis_client import _NoOpRedis
        noop = _NoOpRedis()
        assert noop.get("any_key") is None
        assert noop.set("key", "val") is None
        assert noop.exists("key") is None
        assert noop.delete("key") is None
        assert noop.keys() == []

    def test_redis_health_status(self) -> None:
        from infrastructure.database.redis_client import get_redis_health_status
        status = get_redis_health_status()
        assert isinstance(status, dict)
        assert "available" in status

    def test_redis_noop_pipeline(self) -> None:
        from infrastructure.database.redis_client import _NoOpPipeline
        pipe = _NoOpPipeline()
        result = pipe.set("k", "v").execute()
        assert result == []

    def test_cache_get_json_no_redis(self) -> None:
        """cache_get_json should return None when Redis is unavailable."""
        from infrastructure.utils.cache import cache_get_json
        result = cache_get_json("nonexistent-key")
        assert result is None

    def test_cache_set_json_no_redis(self) -> None:
        """cache_set_json should not raise when Redis is unavailable."""
        from infrastructure.utils.cache import cache_set_json
        cache_set_json("key", {"data": "value"}, ttl=60)

    def test_cache_version_no_redis(self) -> None:
        from infrastructure.utils.cache import get_cache_version
        version = get_cache_version("test-namespace")
        assert isinstance(version, str)

    def test_cache_delete_no_redis(self) -> None:
        from infrastructure.utils.cache import cache_delete
        cache_delete("nonexistent-key")


class TestStorageAbstraction:
    """Object-storage abstraction tests."""

    def test_storage_backend_is_abstract(self) -> None:
        from infrastructure.storage.storage import StorageBackend
        assert hasattr(StorageBackend, "__abstractmethods__")

    def test_local_storage_save_and_read(self, tmp_path) -> None:
        from infrastructure.storage.storage import LocalStorage
        storage = LocalStorage(base_dir=str(tmp_path))
        url = storage.save("test/file.txt", b"hello world")
        assert url.endswith("test/file.txt")
        data = storage.read("test/file.txt")
        assert data == b"hello world"

    def test_local_storage_delete(self, tmp_path) -> None:
        from infrastructure.storage.storage import LocalStorage
        storage = LocalStorage(base_dir=str(tmp_path))
        storage.save("to_delete.txt", b"data")
        storage.delete("to_delete.txt")
        # Should not raise
        storage.delete("nonexistent.txt")

    def test_local_storage_list(self, tmp_path) -> None:
        from infrastructure.storage.storage import LocalStorage
        storage = LocalStorage(base_dir=str(tmp_path))
        storage_save = storage.save("a.txt", b"a")
        storage_save = storage.save("b.txt", b"b")
        items = storage.list()
        assert len(items) == 2

    def test_local_storage_path_traversal_blocked(self, tmp_path) -> None:
        from infrastructure.storage.storage import LocalStorage
        storage = LocalStorage(base_dir=str(tmp_path))
        with pytest.raises(ValueError, match="Unsafe"):
            storage.save("../../etc/passwd", b"evil")

    def test_get_storage_returns_backend(self) -> None:
        from infrastructure.storage.storage import get_storage, LocalStorage
        storage = get_storage()
        assert isinstance(storage, LocalStorage)


class TestObservability:
    """Law 145: observability wiring."""

    def test_logging_config_has_pii_scrubbing(self) -> None:
        from infrastructure.observability.logging_config import _scrub_pii
        assert callable(_scrub_pii)

    def test_logging_config_has_context_enrichment(self) -> None:
        from infrastructure.observability.logging_config import _add_context
        assert callable(_add_context)

    def test_structlog_context_vars(self) -> None:
        from infrastructure.observability.logging_config import (
            get_request_id,
            set_request_id,
            get_country_code,
            set_country_code,
        )
        set_request_id("test-123")
        assert get_request_id() == "test-123"
        set_country_code("AE")
        assert get_country_code() == "AE"

    def test_prometheus_metrics_registered(self) -> None:
        from infrastructure.observability import metrics
        assert hasattr(metrics, "http_requests_total")
        assert hasattr(metrics, "http_request_duration_seconds")
        assert hasattr(metrics, "db_query_duration_seconds")
        assert hasattr(metrics, "db_connections")

    def test_time_it_decorator(self) -> None:
        from infrastructure.observability.metrics import time_it

        @time_it
        def sample_func():
            return 42

        result = sample_func()
        assert result == 42

    def test_error_handler_class_exists(self) -> None:
        from infrastructure.observability.error_handler import ErrorHandler
        handler = ErrorHandler()
        assert handler is not None

    def test_error_categories_defined(self) -> None:
        from infrastructure.observability.error_handler import ErrorCategory
        assert hasattr(ErrorCategory, "AUTHENTICATION")
        assert hasattr(ErrorCategory, "AUTHORIZATION")
        assert hasattr(ErrorCategory, "VALIDATION")
        assert hasattr(ErrorCategory, "NOT_FOUND")
        assert hasattr(ErrorCategory, "DATABASE")
        assert hasattr(ErrorCategory, "INTERNAL")

    def test_app_error_class(self) -> None:
        from infrastructure.observability.error_handler import AppError
        err = AppError("test error", error_code="TEST_ERROR", status_code=400)
        assert err.message == "test error"
        assert err.error_code == "TEST_ERROR"
        assert err.status_code == 400


class TestPagination:
    """Pagination helpers clamp and paginate correctly."""

    def test_safe_page_defaults(self) -> None:
        from infrastructure.utils.pagination import safe_page
        page, size = safe_page(None, None)
        assert page == 1
        assert size == 20

    def test_safe_page_clamps_size(self) -> None:
        from infrastructure.utils.pagination import safe_page, MAX_PAGE_SIZE
        page, size = safe_page(1, 500)
        assert size == MAX_PAGE_SIZE

    def test_safe_page_minimums(self) -> None:
        from infrastructure.utils.pagination import safe_page
        page, size = safe_page(0, 0)
        assert page == 1
        assert size == 1

    def test_get_max_page_size(self) -> None:
        from infrastructure.utils.pagination import get_max_page_size
        result = get_max_page_size()
        assert isinstance(result, int)
        assert result > 0

    def test_encode_decode_keyset_cursor(self) -> None:
        from infrastructure.utils.pagination import (
            decode_keyset_cursor,
            encode_keyset_cursor,
        )
        values = [100, "test", 3.14]
        cursor = encode_keyset_cursor(values)
        decoded = decode_keyset_cursor(cursor)
        assert decoded is not None
        assert decoded[0] == 100

    def test_encode_decode_keyset_cursor_with_secret(self) -> None:
        from infrastructure.utils.pagination import (
            decode_keyset_cursor,
            encode_keyset_cursor,
        )
        values = [42, "secret-test"]
        cursor = encode_keyset_cursor(values, secret="my-secret")
        decoded = decode_keyset_cursor(cursor, secret="my-secret")
        assert decoded is not None
        assert decoded[0] == 42

    def test_decode_invalid_cursor(self) -> None:
        from infrastructure.utils.pagination import decode_keyset_cursor
        assert decode_keyset_cursor(None) is None
        assert decode_keyset_cursor("") is None
        assert decode_keyset_cursor("invalid-data") is None

    def test_build_cursor_pagination_payload(self) -> None:
        from infrastructure.utils.pagination import build_cursor_pagination_payload
        payload = build_cursor_pagination_payload([], None, 20)
        assert payload["items"] == []
        assert payload["next_cursor"] is None
        assert payload["has_next"] is False
        assert payload["page_size"] == 20
