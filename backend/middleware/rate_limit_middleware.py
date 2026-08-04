from __future__ import annotations
import logging
import time
import os
import threading
import hashlib
import math
from typing import Callable, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from utils.config import settings
from utils.ip_utils import get_request_ip
from utils.redis_client import redis_client

logger = logging.getLogger(__name__)

PATH_LIMITS: list[tuple[str, int, int]] = [
    ("/auth/register", 5, 60),
    ("/auth/login", 10, 60),
    ("/auth/forgot", 5, 60),
    ("/auth/reset-password", 5, 60),
    ("/auth/2fa/admin-verify", 5, 60),
    ("/admin/payouts", 5, 60),
    ("/admin/bulk", 5, 60),
    ("/admin/backup", 3, 60),
    ("/admin/security", 3, 60),
    ("/payments", 20, 60),
    ("/cart", 30, 60),
    ("/orders", 20, 60),
]

LOADTEST_PATH_LIMITS: list[tuple[str, int, int]] = [
    ("/auth/register", 120, 60),
    ("/auth/login", 300, 60),
    ("/auth/forgot", 60, 60),
    ("/auth/reset-password", 60, 60),
    ("/auth/2fa/admin-verify", 60, 60),
    ("/admin/payouts", 60, 60),
    ("/admin/bulk", 60, 60),
    ("/admin/backup", 20, 60),
    ("/admin/security", 20, 60),
    ("/payments", 200, 60),
    ("/cart", 300, 60),
    ("/orders", 200, 60),
]

DEFAULT_LIMIT = (60, 60)
LOADTEST_DEFAULT_LIMIT = (600, 60)
STATE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})

_memory_store: Dict[str, list] = defaultdict(list)
_memory_store_locks: Dict[str, threading.Lock] = defaultdict(threading.Lock)


def _cleanup_memory_store():
    """Periodically clean up expired entries from memory store."""
    while True:
        time.sleep(60)
        now = time.time()
        for key in list(_memory_store.keys()):
            with _memory_store_locks[key]:
                _memory_store[key] = [t for t in _memory_store[key] if now - t < 3600]
                if not _memory_store[key]:
                    del _memory_store[key]
                    _memory_store_locks.pop(key, None)


_cleanup_thread = threading.Thread(target=_cleanup_memory_store, daemon=True)
_cleanup_thread.start()


def _get_redis() -> object | None:
    try:
        import redis as redis_module
        client = redis_module.from_url(
            str(settings.redis_url),
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
        )
        client.ping()
        return client
    except Exception:
        return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Callable):
        super().__init__(app)
        self._redis = None

    def _ensure_redis(self) -> object | None:
        if self._redis is None:
            self._redis = _get_redis()
        return self._redis

    def _get_path_tier(self, path: str) -> tuple[int, int]:
        limits = LOADTEST_PATH_LIMITS if settings.loadtest_profile_enabled else PATH_LIMITS
        for prefix, max_r, window in limits:
            if path.startswith(prefix):
                return max_r, window
        return LOADTEST_DEFAULT_LIMIT if settings.loadtest_profile_enabled else DEFAULT_LIMIT

    def _check_memory_limit(self, key: str, max_r: int, window: int) -> tuple[bool, int]:
        now = time.time()
        with _memory_store_locks[key]:
            requests = _memory_store[key]
            requests[:] = [t for t in requests if now - t < window]
            count = len(requests)
        return count < max_r, max(1, int(window - (now - (requests[0] if requests else now))))

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        app_env = str(getattr(settings, "app_env", "development")).lower()
        if app_env == "test" or not settings.rate_limit_enabled:
            return await call_next(request)

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.method not in STATE_METHODS:
            return await call_next(request)

        if settings.loadtest_profile_enabled:
            logger.warning("loadtest_profile_enabled is ON — using elevated rate limits")

        max_r, window = self._get_path_tier(request.url.path)
        client_ip = get_request_ip(request)
        user_id = getattr(getattr(request, "state", None), "user_id", None)
        key_suffix = str(user_id) if user_id else client_ip
        key = f"rl:{key_suffix}:{request.method}:{request.url.path}"

        redis = self._ensure_redis()
        if redis is not None:
            try:
                now = time.time()
                pipeline = redis.pipeline()
                pipeline.zremrangebyscore(key, 0, now - window)
                pipeline.zcard(key)
                pipeline.zadd(key, {str(now): now})
                pipeline.expire(key, window)
                results = pipeline.execute()

                current_count = results[1]

                if current_count >= max_r:
                    oldest = redis.zrange(key, 0, 0, withscores=True)
                    retry_after = int((oldest[0][1] + window - now)) if oldest else window
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Too many requests. Please slow down."},
                        headers={"Retry-After": str(max(retry_after, 1))},
                    )

                return await call_next(request)
            except Exception:
                pass

        is_allowed, retry_after = self._check_memory_limit(key, max_r, window)
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )

        with _memory_store_locks[key]:
            _memory_store[key].append(time.time())
        return await call_next(request)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float
    burst_capacity: int
    window_size: int = 1


class TokenBucket:
    """Token bucket algorithm implementation."""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.rate = config.requests_per_second
        self.capacity = config.burst_capacity

    def consume(self, tokens: int = 1) -> Tuple[bool, int, int]:
        """
        Consume tokens from bucket.
        Returns: (allowed, remaining_tokens, retry_after_seconds)
        """
        now = time.time()
        bucket_key = f"bucket:{hashlib.sha256(str(now).encode()).hexdigest()[:16]}"

        redis = redis_client()
        if not redis:
            return True, self.capacity - tokens, 0

        try:
            pipe = redis.pipeline()
            pipe.get(bucket_key)
            pipe.ttl(bucket_key)
            current, ttl = pipe.execute()

            if current is None:
                current = self.capacity
                last_update = now
            else:
                current = float(current)
                last_update = now - ttl

            tokens_to_add = (now - last_update) * self.rate
            current = min(self.capacity, current + tokens_to_add)

            if current >= tokens:
                current -= tokens
                redis.mset({
                    bucket_key: current,
                    "last_update:" + bucket_key: now
                })
                redis.expire(bucket_key, int(self.config.window_size))
                return True, int(current), 0
            else:
                retry_after = math.ceil((tokens - current) / self.rate)
                return False, int(current), retry_after

        except Exception:
            return True, self.capacity - tokens, 0
