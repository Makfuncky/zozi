"""Paired tests for cache.py get_valkey_client export and Law 110 degradation.

These tests verify:
1. get_valkey_client is importable from infrastructure.utils.cache (the missing
   export defect that caused ImportError in zozi_coins_service and payment_engine).
2. Cache operations degrade safely when Valkey is unreachable (Law 110):
   sessions->DB fallback; caching pass-through; never raise into request path.
"""
from __future__ import annotations

import sys
from unittest.mock import patch

import pytest


class TestGetValkeyClientExport:
    """Verify get_valkey_client is exported from infrastructure.utils.cache."""

    def test_get_valkey_client_importable_from_cache(self):
        """get_valkey_client must be importable from infrastructure.utils.cache.

        This is the paired test for the missing-symbol defect:
        ImportError: cannot import name 'get_valkey_client' from
        'infrastructure.utils.cache'.
        """
        from infrastructure.utils.cache import get_valkey_client
        assert callable(get_valkey_client)

    def test_get_valkey_client_returns_client_or_none(self):
        """get_valkey_client returns a client instance or None, never raises."""
        from infrastructure.utils.cache import get_valkey_client
        client = get_valkey_client()
        assert client is None or hasattr(client, "get")

    def test_get_valkey_client_returns_none_when_valkey_down(self):
        """Law 110: when Valkey is unreachable, get_valkey_client returns None."""
        from infrastructure.utils.cache import get_valkey_client
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            client = get_valkey_client()
            assert client is None


class TestCacheLaw110Degradation:
    """Law 110: caching is pass-through on failure, never fail-closed."""

    def test_cache_get_json_returns_none_when_valkey_down(self):
        """cache_get_json must return None when Valkey is unreachable."""
        from infrastructure.utils.cache import cache_get_json
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            result = cache_get_json("any-key")
            assert result is None

    def test_cache_set_json_does_not_raise_when_valkey_down(self):
        """cache_set_json must not raise when Valkey is unreachable."""
        from infrastructure.utils.cache import cache_set_json
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            cache_set_json("key", {"data": "value"}, ttl=60)

    def test_cache_delete_does_not_raise_when_valkey_down(self):
        """cache_delete must not raise when Valkey is unreachable."""
        from infrastructure.utils.cache import cache_delete
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            cache_delete("any-key")

    def test_get_cache_version_returns_string_when_valkey_down(self):
        """get_cache_version must return a string fallback when Valkey is down."""
        from infrastructure.utils.cache import get_cache_version
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            version = get_cache_version("test-namespace")
            assert isinstance(version, str)

    def test_build_versioned_cache_key_never_raises(self):
        """build_versioned_cache_key is pure and never raises."""
        from infrastructure.utils.cache import build_versioned_cache_key
        key = build_versioned_cache_key("prefix", "a", "b", "c")
        assert key == "prefix:a:b:c"

    def test_cache_operations_never_raise_into_request_path(self):
        """No cache operation in infrastructure.utils.cache may raise when
        Valkey is unreachable. This is the Law 110 pass-through contract."""
        from infrastructure.utils.cache import (
            cache_delete,
            cache_get_json,
            cache_set_json,
            get_cache_version,
        )
        with patch(
            "infrastructure.valkey.client.valkey_client",
            side_effect=ConnectionError("Valkey unreachable"),
        ):
            cache_get_json("k")
            cache_set_json("k", {"v": 1}, ttl=10)
            cache_delete("k")
            get_cache_version("ns")
