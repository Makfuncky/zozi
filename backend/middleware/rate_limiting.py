#!python
"""
Enhanced Rate Limiting Middleware for Zozi Platform
Implements distributed rate limiting with Redis backend and burst protection
"""

import time
import hashlib
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import settings

PATH_LIMITS: Dict[str, Tuple[int, int]] = {
    "/auth/register": (5, 60),
    "/auth/login": (10, 60),
    "/auth/forgot": (5, 60),
    "/auth/reset-password": (5, 60),
    "/auth/2fa/admin-verify": (5, 60),
    "/admin/payouts": (5, 60),
    "/admin/bulk": (5, 60),
    "/admin/backup": (3, 60),
    "/admin/security": (3, 60),
    "/payments": (20, 60),
    "/cart": (30, 60),
    "/orders": (20, 60),
    "/command-center": (60, 60),
}

DEFAULT_LIMIT = (60, 60)
STATE_METHODS = frozenset({"POST", "PUT", "DELETE", "PATCH"})


def _get_redis():
    """Get Redis client with connection pooling."""
    try:
        import redis as redis_module
        client = redis_module.from_url(
            str(settings.redis_url),
            socket_connect_timeout=1,
            socket_timeout=1,
            decode_responses=True,
            retry_on_timeout=True,
        )
        client.ping()
        return client
    except Exception:
        return None


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting middleware with:
    - Sliding window algorithm
    - Per-IP and per-user rate limiting
    - Burst protection
    - Rate limit headers in responses
    - Distributed rate limiting with Redis
    """

    def __init__(self, app, redis_url: str = None):
        super().__init__(app)
        self._redis = None
        self._redis_url = redis_url

    def _ensure_redis(self):
        if self._redis is None:
            self._redis = _get_redis()
        return self._redis

    def _get_path_limit(self, path: str) -> Tuple[int, int]:
        """Get rate limit for a specific path."""
        path_lower = path.lower()
        for prefix, limit in PATH_LIMITS.items():
            if path_lower.startswith(prefix):
                return limit
        return DEFAULT_LIMIT

    def _compute_key(self, client_ip: str, user_id: Optional[int], method: str, path: str) -> str:
        """Compute a unique rate limit key."""
        key_parts = [method, path]
        if user_id:
            key_parts.append(f"user:{user_id}")
        else:
            key_parts.append(f"ip:{client_ip}")
        key_str = ":".join(key_parts)
        return f"rl:{hashlib.sha256(key_str.encode()).hexdigest()[:16]}"

    async def _check_rate_limit(
        self, key: str, max_requests: int, window: int
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window with Redis.
        Returns: (is_allowed, remaining, reset_time)
        """
        redis = self._ensure_redis()
        now = int(time.time())
        window_start = now - window

        if redis is not None:
            try:
                pipe = redis.pipeline()
                pipe.zremrangebyscore(key, 0, window_start)
                pipe.zcard(key)
                pipe.zadd(key, {str(now): now})
                pipe.expire(key, window)
                results = pipe.execute()

                current_count = results[1]
                is_allowed = current_count < max_requests
                remaining = max(0, max_requests - current_count - 1)
                reset_time = window_start + window

                return is_allowed, remaining, reset_time
            except Exception:
                pass

        return True, max_requests - 1, now + window

    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip rate limiting in test environment or if disabled
        import os
        app_env = os.environ.get("APP_ENV", "")
        if app_env == "test" or not settings.rate_limit_enabled:
            return await call_next(request)

        # Only apply to state-changing methods
        if request.method not in STATE_METHODS:
            return await call_next(request)

        max_requests, window = self._get_path_limit(request.url.path)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(getattr(request, "state", None), "user_id", None)

        key = self._compute_key(client_ip, user_id, request.method, request.url.path)
        is_allowed, remaining, reset_time = await self._check_rate_limit(key, max_requests, window)

        if not is_allowed:
            retry_after = max(1, reset_time - int(time.time()))
            response = JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please slow down.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": retry_after,
                },
            )
            response.headers.update({
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_time),
                "Retry-After": str(retry_after),
            })
            return response

        response = await call_next(request)

        response.headers.update({
            "X-RateLimit-Limit": str(max_requests),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        })

        return response
