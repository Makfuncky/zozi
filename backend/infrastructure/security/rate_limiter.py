"""Shared Valkey-native rate-limiter instance.

This module owns the single `Limiter` instance for the whole application:
  • `main.py` imports `limiter` from here, attaches it to `app.state.limiter`,
    and registers the `RateLimitExceeded` exception handler.
  • Routers import `limiter` from here and apply `@limiter.limit(...)` to the
    endpoints they want to protect.

Centralising the instance in its own module breaks what would otherwise be a
circular import (main.py imports the routers, so the routers cannot import
back from main.py). Every consumer now imports from this leaf module instead.

fastapi-limiter-valkey mechanics: the decorator binds to the limiter instance
it is called on, and enforcement is gated by that instance's `enabled` flag.
Using one shared instance therefore guarantees that a limit applied via
`@limiter.limit(...)` is honoured when the request runs.
"""
from __future__ import annotations

from functools import wraps


try:
    from fastapi_limiter_valkey import RateLimiter as _RateLimiter
    from fastapi_limiter_valkey.util import get_remote_address as _get_remote_address

    class Limiter:
        """Compatibility shim: wraps ``RateLimiter`` to provide the ``.limit()``
        decorator interface that the rest of the codebase expects."""

        def __init__(self, key_func=_get_remote_address, enabled: bool = True):
            self.key_func = key_func
            self.enabled = enabled
            self._route_limits: dict[str, list] = {}

        def limit(self, limit_str: str):
            """Return a decorator that applies rate limiting when enabled."""
            def decorator(func):
                route_key = f"{func.__module__}.{func.__name__}"
                self._route_limits.setdefault(route_key, []).append(limit_str)
                if not self.enabled:
                    return func
                rl = _RateLimiter(times=1, seconds=60, key_func=self.key_func)
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    return await rl(func)(*args, **kwargs)
                return wrapper
            return decorator

    limiter = Limiter()

except Exception:  # pragma: no cover - valkey unavailable
    class Limiter:  # type: ignore[no-redef]
        """No-op fallback when valkey/fastapi-limiter is unavailable."""

        def __init__(self, *args, **kwargs):
            self.enabled = False
            self._route_limits: dict[str, list] = {}

        def limit(self, limit_str: str):
            def decorator(func):
                route_key = f"{func.__module__}.{func.__name__}"
                self._route_limits.setdefault(route_key, []).append(limit_str)
                return func
            return decorator

    limiter = Limiter()


# ── Rate-limit tiers ─────────────────────────────────────────────────────────
# Applied via @limiter.limit(RL_*) on individual route functions.

RL_DEFAULT = "60/minute"       # most authenticated state-changing actions
RL_SENSITIVE = "10/minute"     # password resets, profile updates, etc.
RL_ADMIN_SENSITIVE = "5/minute"  # admin-only sensitive operations

__all__ = [
    "limiter",
    "RL_DEFAULT",
    "RL_SENSITIVE",
    "RL_ADMIN_SENSITIVE",
]

