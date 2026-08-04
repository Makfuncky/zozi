"""Shared SlowAPI rate-limiter instance.

This module owns the single `Limiter` instance for the whole application:
  • `main.py` imports `limiter` from here, attaches it to `app.state.limiter`,
    and registers the `RateLimitExceeded` exception handler.
  • Routers import `limiter` from here and apply `@limiter.limit(...)` to the
    endpoints they want to protect.

Centralising the instance in its own module breaks what would otherwise be a
circular import (main.py imports the routers, so the routers cannot import
back from main.py). Every consumer now imports from this leaf module instead.

SlowAPI mechanics (verified against slowapi/extension.py): the decorator binds
to the limiter *instance* it is called on, and enforcement is gated by that
instance's `enabled` flag. Using one shared instance therefore guarantees that
a limit applied via `@limiter.limit(...)` is honoured when the request runs.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

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

