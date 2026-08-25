"""Domain-level rate limiting helpers.

Provides decorators and utility functions for applying rate limiting
at the domain/service level, complementing the middleware-based rate limiting.

The middleware (rate_limit_middleware.py) handles HTTP-level rate limiting.
This module provides finer-grained control for domain operations:
- Per-user rate limiting for expensive operations
- Per-API-key rate limiting for external integrations
- Sliding window counters with Redis backend
- In-memory fallback when Redis is unavailable

Usage:
    @rate_limit_domain("product_view", max_requests=100, window=60)
    def view_product(user_id: int, product_id: int, db: Session):
        ...

    @rate_limit_domain("export", max_requests=5, window=3600, key_func=lambda user_id: f"user:{user_id}")
    def export_data(user_id: int, db: Session):
        ...
"""
from __future__ import annotations

import functools
import hashlib
import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

T = TypeVar("T")

# ── In-memory fallback store ──────────────────────────────────────────────
_memory_counters: dict[str, list[float]] = defaultdict(list)
_memory_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)


def _get_redis():
    """Get Redis client or None if unavailable."""
    try:
        from infrastructure.utils.redis_client import redis_client
        return redis_client()
    except Exception:
        return None


def _sliding_window_check(
    key: str,
    max_requests: int,
    window: int,
) -> tuple[bool, int]:
    """Sliding window rate limit check.

    Returns (allowed, retry_after_seconds).
    Uses Redis sorted sets when available, falls back to in-memory counters.
    """
    now = time.time()
    redis_client = _get_redis()

    if redis_client is not None:
        try:
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {f"{now}:{id(pipe)}": now})
            pipe.expire(key, window + 1)
            results = pipe.execute()

            count = results[1]
            if count >= max_requests:
                oldest = redis_client.zrange(key, 0, 0, withscores=True)
                retry_after = int((oldest[0][1] + window - now)) if oldest else window
                return False, max(retry_after, 1)
            return True, 0
        except Exception as e:
            logger.debug("Redis rate limit check failed, falling back to memory: %s", e)

    # In-memory fallback
    lock = _memory_locks[key]
    with lock:
        timestamps = _memory_counters[key]
        timestamps[:] = [t for t in timestamps if now - t < window]
        count = len(timestamps)
        if count >= max_requests:
            retry_after = int(window - (now - timestamps[0])) if timestamps else window
            return False, max(retry_after, 1)
        timestamps.append(now)
        return True, 0


def rate_limit_domain(
    operation: str,
    max_requests: int = 60,
    window: int = 60,
    key_func: Optional[Callable[..., str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for domain-level rate limiting.

    Args:
        operation: Name of the operation (used in cache key).
        max_requests: Maximum requests allowed in the window.
        window: Time window in seconds.
        key_func: Function to extract rate limit key from args.
                  Defaults to using the first argument.

    Usage:
        @rate_limit_domain("product_search", max_requests=30, window=60)
        def search_products(user_id: int, query: str, db: Session):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_func is not None:
                key = f"rl:domain:{operation}:{key_func(*args, **kwargs)}"
            elif args:
                key = f"rl:domain:{operation}:{args[0]}"
            else:
                key = f"rl:domain:{operation}:global"

            allowed, retry_after = _sliding_window_check(key, max_requests, window)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail={
                        "error": "Rate limit exceeded",
                        "operation": operation,
                        "max_requests": max_requests,
                        "window_seconds": window,
                        "retry_after": retry_after,
                    },
                    headers={"Retry-After": str(retry_after)},
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_check(
    key: str,
    max_requests: int = 60,
    window: int = 60,
) -> tuple[bool, int]:
    """Check if a rate limit is exceeded for a given key.

    Returns (allowed, retry_after_seconds).
    Useful for inline rate limiting in service code.

    Usage:
        allowed, retry_after = rate_limit_check(f"export:{user_id}", max_requests=5, window=3600)
        if not allowed:
            raise HTTPException(status_code=429, ...)
    """
    return _sliding_window_check(f"rl:domain:{key}", max_requests, window)


def rate_limit_per_user(
    request: Request,
    operation: str,
    max_requests: int = 60,
    window: int = 60,
) -> None:
    """Rate limit based on request user/IP. Designed for use in route handlers.

    Raises HTTPException(429) if the limit is exceeded.

    Usage:
        async def my_endpoint(request: Request, ...):
            rate_limit_per_user(request, "my_operation", max_requests=30, window=60)
            ...
    """
    user_id = getattr(getattr(request, "state", None), "user_id", None)
    client_ip = getattr(getattr(request, "state", None), "client_ip", None)
    key_suffix = str(user_id) if user_id else (client_ip or "anonymous")
    key = f"rl:user:{operation}:{key_suffix}"

    allowed, retry_after = _sliding_window_check(key, max_requests, window)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "operation": operation,
                "retry_after": retry_after,
            },
            headers={"Retry-After": str(retry_after)},
        )
