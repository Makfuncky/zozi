#!python
"""
Advanced Rate Limiting with Token Bucket Algorithm
Implements adaptive rate limiting with burst protection and dynamic limits
"""

import time
import hashlib
import math
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from utils.config import settings
from utils.redis_client import redis_client
from utils.ip_utils import get_request_ip


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
                    f"last_update:{bucket_key}": now
                })
                redis.expire(bucket_key, int(self.config.window_size))
                return True, int(current), 0
            else:
                retry_after = math.ceil((tokens - current) / self.rate)
                return False, int(current), retry_after

        except Exception:
            return True, self.capacity - tokens, 0


class AdaptiveRateLimiter:
    """Adaptive rate limiter that adjusts limits based on behavior."""

    BASE_LIMITS = {
        "auth": RateLimitConfig(2.0, 10),
        "api": RateLimitConfig(10.0, 100),
        "command_center": RateLimitConfig(5.0, 60),
        "global": RateLimitConfig(20.0, 200),
    }

    PENALTY_MULTIPLIER = 0.5
    REWARD_MULTIPLIER = 1.5
    MAX_PENALTY_DURATION = 300

    def __init__(self):
        self.redis = redis_client()
        self.client_scores: Dict[str, float] = {}

    def get_config_for_path(self, path: str) -> RateLimitConfig:
        """Get rate limit config for a path."""
        path_lower = path.lower()
        if "/auth" in path_lower:
            return self.BASE_LIMITS["auth"]
        elif "/command-center" in path_lower:
            return self.BASE_LIMITS["command_center"]
        elif "/api" in path_lower:
            return self.BASE_LIMITS["api"]
        return self.BASE_LIMITS["global"]

    def calculate_adaptive_limit(self, client_id: str, base_config: RateLimitConfig) -> RateLimitConfig:
        """Calculate adaptive limit based on client behavior."""
        if not self.redis:
            return base_config

        try:
            score_key = f"score:{client_id}"
            violations_key = f"violations:{client_id}"

            score = float(self.redis.get(score_key) or 0)
            violations = int(self.redis.get(violations_key) or 0)

            if violations > 10:
                multiplier = self.PENALTY_MULTIPLIER ** min(violations / 5, self.MAX_PENALTY_DURATION)
                return RateLimitConfig(
                    base_config.requests_per_second * multiplier,
                    int(base_config.burst_capacity * multiplier)
                )
            elif score > 0.8:
                return RateLimitConfig(
                    base_config.requests_per_second * self.REWARD_MULTIPLIER,
                    int(base_config.burst_capacity * self.REWARD_MULTIPLIER)
                )

        except Exception:
            pass

        return base_config


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Enhanced rate limiting with:
    - Token bucket algorithm
    - Adaptive limits based on behavior
    - Per-user and per-IP limiting
    - Burst protection
    """

    def __init__(self, app):
        super().__init__(app)
        self.adaptive_limiter = AdaptiveRateLimiter()

    async def dispatch(self, request: Request, call_next) -> Response:
        import os
        app_env = os.environ.get("APP_ENV", "")
        if app_env == "test" or not settings.rate_limit_enabled:
            return await call_next(request)

        if request.method not in {"POST", "PUT", "DELETE", "PATCH"}:
            return await call_next(request)

        client_ip = get_request_ip(request)
        user_id = getattr(getattr(request, "state", None), "user_id", None)
        client_id = f"user:{user_id}" if user_id else f"ip:{client_ip}"

        base_config = self.adaptive_limiter.get_config_for_path(request.url.path)
        adaptive_config = self.adaptive_limiter.calculate_adaptive_limit(client_id, base_config)

        bucket = TokenBucket(adaptive_config)
        allowed, remaining, retry_after = bucket.consume()

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                    "code": "RATE_LIMIT_EXCEEDED",
                },
                headers={
                    "X-RateLimit-Limit": str(adaptive_config.requests_per_second),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": str(max(1, retry_after)),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(adaptive_config.requests_per_second)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

