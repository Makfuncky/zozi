"""Minimal cache shim for infrastructure.utils.cache.

Delegates to Valkey-backed performance_cache.py so services importing
from this module get real caching behavior.
"""
from __future__ import annotations

from infrastructure.utils.performance_cache import (
    bump_cache_version,
    bump_product_cache_version,
    cache_delete,
    cache_get_json,
    cache_or_compute,
    cache_set_json,
    cached_call,
    get_cache_version,
    get_valkey_client,
)


def build_versioned_cache_key(prefix: str, *parts: Any) -> str:
    return f"{prefix}:{':'.join(str(p) for p in parts)}"
