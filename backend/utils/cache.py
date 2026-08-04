"""Shared Redis-backed cache helpers for public read-heavy endpoints.

Includes cache stampede protection via probabilistic early expiry and
a compute-if-missing helper for search result caching.
"""

import hashlib
import json
import random
import time
from typing import Any, Callable, Optional, cast

_LOCK_TTL = 5  # seconds — lock expires so a crashed worker doesn't block forever


def get_redis_client():
    try:
        from utils.auth import _get_redis

        return _get_redis()
    except Exception:
        return None


def cache_get_json(key: str) -> Any | None:
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return None
        raw = redis_client.get(key)
        if not raw:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(cast(str, raw))
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl: int) -> None:
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def get_cache_version(namespace: str) -> str:
    version_key = f"{namespace}:cache:version"
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return "0"
        raw = redis_client.get(version_key)
        if raw is None:
            redis_client.set(version_key, "1")
            return "1"
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8")
        return str(raw)
    except Exception:
        return "0"


def bump_cache_version(namespace: str) -> None:
    version_key = f"{namespace}:cache:version"
    try:
        redis_client = get_redis_client()
        if redis_client is not None:
            redis_client.incr(version_key)
    except Exception:
        pass


def build_versioned_cache_key(namespace: str, prefix: str, payload: dict[str, Any]) -> str:
    version = get_cache_version(namespace)
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"{namespace}:{prefix}:v{version}:{digest}"


def _lock_key(key: str) -> str:
    return f"lock:{key}"


def _acquire_lock(key: str) -> bool:
    """Try to acquire a distributed lock for ``key``.

    Returns ``True`` if this caller won the lock.
    """
    redis_client = get_redis_client()
    if redis_client is None:
        return True  # no Redis → no stampede protection, but also no contention
    try:
        return bool(redis_client.set(_lock_key(key), "1", nx=True, ex=_LOCK_TTL))
    except Exception:
        return True


def _release_lock(key: str) -> None:
    redis_client = get_redis_client()
    if redis_client is None:
        return
    try:
        redis_client.delete(_lock_key(key))
    except Exception:
        pass


def _jittered_ttl(base_ttl: int) -> int:
    """Add ±20% jitter to TTL so cache entries don't expire simultaneously."""
    jitter = int(base_ttl * 0.2)
    return max(base_ttl + random.randint(-jitter, jitter), 1)


def cache_delete(key: str) -> None:
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return
        redis_client.delete(key)
    except Exception:
        pass


def cache_or_compute(
    key: str,
    compute: Callable[[], Any],
    ttl: int,
    namespace: Optional[str] = None,
) -> Any:
    """Return cached value under ``key``, or compute and cache it.

    Stampede protection
    -------------------
    If the cache is empty and multiple requests arrive simultaneously,
    only one computes; the rest wait for the lock to clear and then
    read the now-populated cache.  If the lock expires (crashed worker)
    another caller picks up computation automatically.
    """
    if namespace:
        version = get_cache_version(namespace)
        key = f"{namespace}:v{version}:{key}"

    cached = cache_get_json(key)
    if cached is not None:
        return cached

    if not _acquire_lock(key):
        time.sleep(0.05)
        cached = cache_get_json(key)
        if cached is not None:
            return cached
        return cache_or_compute(key, compute, ttl, namespace=namespace)

    try:
        value = compute()
        cache_set_json(key, value, _jittered_ttl(ttl))
        return value
    finally:
        _release_lock(key)
