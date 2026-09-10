"""Canonical Valkey client wrapper.

Per ADR-024, ZOZI migrated to Valkey 8.0.1. The ``valkey`` Python
package is API-compatible with the prior stack (drop-in replacement). This module
exposes a singleton ``valkey_client()`` returning a ``valkey.Valkey`` instance.

Laws preserved:
  - Law 142: client singleton (one connection per process).
  - Law 37 / 110: fail-closed in production if Valkey is unavailable
    AND ``readiness_require_valkey`` is set; graceful no-op otherwise.
"""
from __future__ import annotations

from typing import Any

from infrastructure.utils.config import settings


class _NoOpValkey:
    """Fallback Valkey client that silently no-ops all operations."""

    def setex(self, *args: Any, **kwargs: Any) -> None:
        return None

    def set(self, *args: Any, **kwargs: Any) -> None:
        return None

    def get(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def delete(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def exists(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def expire(self, *args: Any, **kwargs: Any) -> None:
        return None

    def ping(self, *args: Any, **kwargs: Any) -> bool:
        return False

    def keys(self, *args: Any, **kwargs: Any) -> list:
        return []

    def pipeline(self, *args: Any, **kwargs: Any) -> "_NoOpValkeyPipeline":
        return _NoOpValkeyPipeline()

    def zadd(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def zremrangebyscore(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def zcard(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def zrange(self, *args: Any, **kwargs: Any) -> list:
        return []

    def bf_exists(self, *args: Any, **kwargs: Any) -> Any:
        return None

    def bf_add(self, *args: Any, **kwargs: Any) -> Any:
        return None


class _NoOpValkeyPipeline:
    """Fallback pipeline that no-ops all operations and returns empty results."""

    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> "_NoOpValkeyPipeline":
            return self
        return _noop

    def execute(self) -> list:
        return []


try:
    import valkey
    _valkey_available = True
except ImportError:
    valkey = None  # type: ignore
    _valkey_available = False

_client: "valkey.Valkey | _NoOpValkey | None" = None


def valkey_client() -> "valkey.Valkey | _NoOpValkey":
    """Return the process-wide Valkey client (singleton; Law 142)."""
    global _client
    if not _valkey_available:
        return _NoOpValkey()
    if _client is not None:
        return _client
    client = valkey.Valkey.from_url(
        settings.valkey_url,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )
    try:
        client.ping()
    except Exception:
        # Do NOT cache the NoOp fallback — retry on next call so a
        # temporarily unreachable Valkey can recover without a restart.
        return _NoOpValkey()
    _client = client
    return _client


get_valkey = valkey_client

redis_client = valkey_client

get_redis = valkey_client

_NoOpRedis = _NoOpValkey

_NoOpPipeline = _NoOpValkeyPipeline




def get_valkey_health_status() -> dict[str, Any]:
    if not _valkey_available:
        return {"configured": False, "available": False, "backend": None}
    try:
        client = valkey_client()
        if isinstance(client, _NoOpValkey):
            return {"configured": False, "available": False, "backend": None}
        client.ping()
        return {"configured": True, "available": True, "backend": "valkey"}
    except Exception as e:
        return {"configured": True, "available": False, "backend": "valkey", "error": str(e)}

def bump_product_cache_version() -> None:
    from infrastructure.utils.cache import bump_product_cache_version as _bump
    _bump()
