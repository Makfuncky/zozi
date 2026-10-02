"""Backward-compat shim — canonical location is infrastructure/valkey/client.py."""

from infrastructure.valkey.client import valkey_client as redis_client  # noqa: F401
from infrastructure.valkey.client import get_valkey_health_status as get_redis_health_status  # noqa: F401

__all__ = ["redis_client", "get_redis_health_status"]
