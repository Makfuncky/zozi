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

import random
import time

from typing import Any

from infrastructure.observability.metrics import _safe_metric
from infrastructure.utils.config import settings

from prometheus_fastapi_instrumentator.metrics import Counter

logger = None
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    pass

valkey_fallback_total = _safe_metric(
    Counter,
    'valkey_fallback_total',
    'Number of times Valkey client fell back to NoOp',
    ['reason']
)
valkey_reconnect_total = _safe_metric(
    Counter,
    'valkey_reconnect_total',
    'Number of Valkey reconnect attempts after initial failure',
)


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
    """Return the process-wide Valkey client (singleton; Law 142).

    On connection failure, retry with exponential backoff before falling back
    to ``_NoOpValkey``. Emits metrics and logs WARNING on fallback.
    """
    global _client
    if not _valkey_available:
        if logger is not None:
            logger.warning("valkey_fallback", reason="import_unavailable")
        valkey_fallback_total.labels(reason="import_unavailable").inc()
        _client = _NoOpValkey()
        return _client
    if _client is not None:
        return _client
    client = valkey.Valkey.from_url(
        settings.valkey_url,
        decode_responses=True,
        socket_timeout=2,
        socket_connect_timeout=2,
    )
    last_exception: Exception | None = None
    for attempt in range(1, 4):
        try:
            client.ping()
        except Exception as exc:
            last_exception = exc
            if attempt < 3:
                delay = min(2 ** attempt + random.uniform(0, 0.5), 5.0)
                if logger is not None:
                    logger.warning(
                        "valkey_retry",
                        attempt=attempt,
                        max_attempts=3,
                        delay=round(delay, 2),
                        error=str(exc),
                    )
                valkey_reconnect_total.inc()
                time.sleep(delay)
                continue
            break
        else:
            _client = client
            return _client
    if logger is not None:
        logger.warning(
            "valkey_fallback",
            reason="connection_exhausted",
            error=str(last_exception) if last_exception else None,
        )
    valkey_fallback_total.labels(reason="connection_exhausted").inc()
    _client = _NoOpValkey()
    return _client


get_valkey = valkey_client




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
