"""Backward-compat shim — canonical location is infrastructure/database/redis_client.py."""

from infrastructure.database.redis_client import valkey_client as redis_client  # noqa: F401
from infrastructure.database.redis_client import get_redis  # noqa: F401
from infrastructure.database.redis_client import get_redis_health_status  # noqa: F401

__all__ = ["redis_client", "get_redis", "get_redis_health_status"]
