"""Minimal cache shim for infrastructure.utils.cache.

This module provides no-op implementations so the backend can import
modules that depend on cache helpers when Valkey/Redis is unavailable.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


def _noop(*args: Any, **kwargs: Any) -> None:
    return None


def cache_get_json(key: str, default: Any = None) -> Any:
    return default


def cache_set_json(key: str, value: Any, ttl: int = 300) -> None:
    return None


def cache_delete(key: str) -> None:
    return None


def cache_or_compute(key: str, compute_fn, ttl: int = 300, namespace: str = "default"):
    try:
        return compute_fn()
    except Exception:
        return None


def build_versioned_cache_key(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{':'.join(str(p) for p in parts)}"


def bump_cache_version(namespace: str) -> None:
    return None


def get_cache_version(namespace: str) -> str:
    return "v1"


def bump_product_cache_version() -> None:
    return None


def cached_call(prefix: str, ttl: int = 300, key_fn=None):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                return None
        return wrapper
    return decorator


def get_redis_client():
    try:
        from infrastructure.valkey.client import valkey_client
        return valkey_client()
    except Exception:
        return None
