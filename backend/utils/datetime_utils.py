"""Timezone-aware "now" helpers used across routers."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return the current UTC time as a naive datetime (DB stores naive UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
