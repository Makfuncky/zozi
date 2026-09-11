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

    def pipeline(self, *args: Any, **kwargs: Any) -> "_NoOpPipeline":
        return _NoOpPipeline()

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


class _NoOpPipeline:
    """Fallback pipeline that no-ops all operations and returns empty results."""

    def __getattr__(self, name: str) -> Any:
        def _noop(*args: Any, **kwargs: Any) -> "_NoOpPipeline":
            return self
        return _noop

    def execute(self) -> list:
        return []


try:
    import valkey
    _redis_available = True
except ImportError:
    redis = None  # type: ignore
    _redis_available = False

_client: redis.Redis | _NoOpValkey | None = None


def valkey_client() -> redis.Redis | _NoOpValkey:
    global _client
    if not _redis_available:
        return _NoOpValkey()
    if _client is not None:
        return _client
    # Use short timeouts so a missing Redis doesn't hang requests
    client = redis.Redis.from_url(
        settings.redis_url,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )
    try:
        client.ping()
    except Exception:
        # Do NOT cache the NoOp fallback — retry on next call so a
        # temporarily unreachable Redis can recover without a restart.
        return _NoOpValkey()
    _client = client
    return _client


get_redis = valkey_client


def get_redis_health_status() -> dict[str, Any]:
    if not _redis_available:
        return {"configured": False, "available": False, "backend": None}
    try:
        client = valkey_client()
        if isinstance(client, _NoOpValkey):
            return {"configured": False, "available": False, "backend": None}
        client.ping()
        return {"configured": True, "available": True, "backend": "redis"}
    except Exception as e:
        return {"configured": True, "available": False, "backend": "redis", "error": str(e)}


