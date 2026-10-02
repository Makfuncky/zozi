"""Performance caching for hot-path domain services.

Provides high-level cache helpers for frequently-accessed data:
- Product listings (with cache stampede protection)
- Search results (with probabilistic early expiry)
- Session lookups (with automatic invalidation)
- Country configurations (with versioned keys)

All functions gracefully degrade to None when Valkey is unavailable.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

# TTL constants (seconds)
TTL_PRODUCT_LISTING = 60
TTL_SEARCH_RESULT = 120
TTL_SESSION_LOOKUP = 300
TTL_COUNTRY_CONFIG = 600
TTL_USER_PROFILE = 300
TTL_CATEGORY_LIST = 900

# Cache key prefixes
PREFIX_PRODUCT = "perf:product"
PREFIX_SEARCH = "perf:search"
PREFIX_SESSION = "perf:session"
PREFIX_COUNTRY = "perf:country"
PREFIX_USER = "perf:user"
PREFIX_CATEGORY = "perf:category"


def _get_valkey():
    """Get Valkey client or None if unavailable."""
    try:
        from infrastructure.valkey.client import valkey_client
        return valkey_client()
    except Exception:
        return None


def _make_key(prefix: str, *parts: str) -> str:
    """Build a deterministic cache key from prefix and parts."""
    raw = ":".join(str(p) for p in parts)
    if len(raw) > 200:
        raw = hashlib.sha256(raw.encode()).hexdigest()
    return f"{prefix}:{raw}"


# PERF-005: Valkey-backed implementations replacing no-op shim in cache.py.
# These allow the 24 service/test imports that currently use cache.py to
# migrate to real Valkey-backed caching without changing function signatures.


def cache_get_json(key: str, default: Any = None) -> Any:
    """Retrieve and deserialize a JSON value from Valkey."""
    try:
        client = _get_valkey()
        if client is None:
            return default
        raw = client.get(key)
        if raw is None:
            return default
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("cache_get_json failed for %s: %s", key, e)
        return default


def cache_set_json(key: str, value: Any, ttl: int = 300) -> None:
    """Serialize and store a JSON value in Valkey with the given TTL."""
    try:
        client = _get_valkey()
        if client is None:
            return
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.debug("cache_set_json failed for %s: %s", key, e)


def cache_delete(key: str) -> None:
    """Delete a key from Valkey."""
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("cache_delete failed for %s: %s", key, e)


def cache_or_compute(key: str, compute_fn: Callable[[], T], ttl: int = 300,
                     namespace: str = "default") -> Any:
    """Return cached value or compute, cache, and return it."""
    try:
        cached = cache_get_json(key)
        if cached is not None:
            return cached
    except Exception:
        pass
    try:
        value = compute_fn()
        cache_set_json(key, value, ttl=ttl)
        return value
    except Exception as e:
        logger.debug("cache_or_compute compute_fn failed for %s: %s", key, e)
        return None


def build_versioned_cache_key(prefix: str, *parts: Any) -> str:
    """Build a versioned cache key (delegates to _make_key for consistency)."""
    return _make_key(prefix, *parts)


def bump_cache_version(namespace: str) -> None:
    """Increment the cache version for a namespace, invalidating stale entries."""
    try:
        client = _get_valkey()
        if client is None:
            return
        version_key = f"perf:version:{namespace}"
        raw = client.get(version_key)
        version = int(raw) + 1 if raw is not None and str(raw).isdigit() else 2
        client.setex(version_key, 86400, str(version))
    except Exception as e:
        logger.debug("bump_cache_version failed for %s: %s", namespace, e)


def get_cache_version(namespace: str) -> str:
    """Return the current cache version for a namespace, defaulting to 'v1'."""
    try:
        client = _get_valkey()
        if client is None:
            return "v1"
        raw = client.get(f"perf:version:{namespace}")
        if raw is not None and str(raw).isdigit():
            return f"v{raw}"
    except Exception as e:
        logger.debug("get_cache_version failed for %s: %s", namespace, e)
    return "v1"


def bump_product_cache_version() -> None:
    """Invalidate all cached product listings by bumping the product version."""
    try:
        invalidate_product_listings()
        bump_cache_version("product")
    except Exception as e:
        logger.debug("bump_product_cache_version failed: %s", e)


def get_valkey_client() -> Optional[Any]:
    """Return the Valkey client instance, or None if unavailable.
    
    Compatibility shim mirroring cache.py's get_valkey_client so services
    can migrate from the no-op shim to real Valkey-backed caching.
    """
    return _get_valkey()


def cache_product_listing(category: str, page: int, limit: int, filters_hash: str = "") -> Optional[list[dict]]:
    """Retrieve cached product listing if available."""
    key = _make_key(PREFIX_PRODUCT, category, f"p{page}", f"l{limit}", filters_hash)
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for product listing: %s", e)
        return None


def set_product_listing(category: str, page: int, limit: int, data: list[dict], filters_hash: str = "", ttl: int = TTL_PRODUCT_LISTING) -> None:
    """Cache product listing with jittered TTL to prevent thundering herd."""
    key = _make_key(PREFIX_PRODUCT, category, f"p{page}", f"l{limit}", filters_hash)
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for product listing: %s", e)


def cache_search_results(query_hash: str, page: int, limit: int) -> Optional[dict]:
    """Retrieve cached search results if available."""
    key = _make_key(PREFIX_SEARCH, query_hash, f"p{page}", f"l{limit}")
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for search results: %s", e)
        return None


def set_search_results(query_hash: str, page: int, limit: int, data: dict, ttl: int = TTL_SEARCH_RESULT) -> None:
    """Cache search results with jittered TTL."""
    key = _make_key(PREFIX_SEARCH, query_hash, f"p{page}", f"l{limit}")
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for search results: %s", e)


def cache_session(session_id: str) -> Optional[dict]:
    """Retrieve cached session data if available."""
    key = _make_key(PREFIX_SESSION, session_id)
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for session: %s", e)
        return None


def set_session(session_id: str, data: dict, ttl: int = TTL_SESSION_LOOKUP) -> None:
    """Cache session data."""
    key = _make_key(PREFIX_SESSION, session_id)
    try:
        client = _get_valkey()
        if client is None:
            return
        client.setex(key, ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for session: %s", e)


def invalidate_session(session_id: str) -> None:
    """Invalidate cached session data."""
    key = _make_key(PREFIX_SESSION, session_id)
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for session: %s", e)


def cache_country_config(country_code: str) -> Optional[dict]:
    """Retrieve cached country configuration if available."""
    key = _make_key(PREFIX_COUNTRY, country_code.upper())
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for country config: %s", e)
        return None


def set_country_config(country_code: str, data: dict, ttl: int = TTL_COUNTRY_CONFIG) -> None:
    """Cache country configuration with jittered TTL."""
    key = _make_key(PREFIX_COUNTRY, country_code.upper())
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for country config: %s", e)


def invalidate_country_config(country_code: str) -> None:
    """Invalidate cached country configuration."""
    key = _make_key(PREFIX_COUNTRY, country_code.upper())
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for country config: %s", e)


def cache_user_profile(user_id: int) -> Optional[dict]:
    """Retrieve cached user profile if available."""
    key = _make_key(PREFIX_USER, str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for user profile: %s", e)
        return None


def set_user_profile(user_id: int, data: dict, ttl: int = TTL_USER_PROFILE) -> None:
    """Cache user profile with jittered TTL."""
    key = _make_key(PREFIX_USER, str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for user profile: %s", e)


def invalidate_user_profile(user_id: int) -> None:
    """Invalidate cached user profile."""
    key = _make_key(PREFIX_USER, str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for user profile: %s", e)


def invalidate_product_listings() -> None:
    """Invalidate all cached product listings (on product update)."""
    try:
        client = _get_valkey()
        if client is None:
            return
        keys = client.keys(f"{PREFIX_PRODUCT}:*")
        if keys:
            client.delete(*keys)
    except Exception as e:
        logger.debug("Cache invalidation failed for product listings: %s", e)


def cached_call(
    prefix: str,
    ttl: int,
    key_parts: tuple[str, ...],
    compute_fn: Callable[[], T],
) -> T:
    """Generic cached call pattern: check cache, compute on miss, store result.

    Uses probabilistic early expiry to prevent thundering herd on cache miss.
    """
    cache_key = _make_key(prefix, *key_parts)
    client = _get_valkey()

    if client is not None:
        try:
            raw = client.get(cache_key)
            if raw is not None:
                if isinstance(raw, (bytes, bytearray)):
                    raw = raw.decode("utf-8")
                data = json.loads(raw)
                # Probabilistic early expiry: if we're past 80% of TTL, 
                # recompute with small probability to spread recompute load
                if isinstance(data, dict) and "_ts" in data:
                    age = time.time() - data["_ts"]
                    remaining_ratio = 1.0 - (age / ttl)
                    if remaining_ratio < 0.2 and random.random() > 0.9:
                        raise KeyError("probabilistic early expiry")
                return data.get("value") if isinstance(data, dict) and "value" in data else data
        except (json.JSONDecodeError, KeyError):
            pass
        except Exception as e:
            logger.debug("Cache get failed in cached_call: %s", e)

    value = compute_fn()

    if client is not None:
        try:
            jitter = int(ttl * 0.1)
            effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
            payload = {"value": value, "_ts": time.time()}
            client.setex(cache_key, effective_ttl, json.dumps(payload, default=str))
        except Exception as e:
            logger.debug("Cache set failed in cached_call: %s", e)

    return value


def cache_decorator(prefix: str, ttl: int, key_fn: Optional[Callable[..., tuple[str, ...]]] = None):
    """Decorator for caching function results.

    Usage:
        @cache_decorator("perf:myfunc", ttl=60, key_fn=lambda x, y: (str(x), str(y)))
        def my_function(x, y):
            return expensive_computation(x, y)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            if key_fn is not None:
                parts = key_fn(*args, **kwargs)
            else:
                parts = tuple(str(a) for a in args) + tuple(f"{k}={v}" for k, v in sorted(kwargs.items()))
            return cached_call(prefix, ttl, parts, lambda: func(*args, **kwargs))
        return wrapper
    return decorator


def invalidate_role_permissions_cache(role_name: str) -> None:
    """Invalidate cached role permissions for a specific role."""
    try:
        client = _get_valkey()
        if client is None:
            return
        pattern = f"perf:permissions:role_perms:{role_name}:*"
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        logger.debug("Cache invalidation failed for role permissions: %s", e)


def invalidate_user_cache(user_id: int) -> None:
    """Invalidate all cached entries associated with a user.

    Convenience helper that invalidates the user profile cache, the user
    permissions cache, and any other per-user cache keys. Use this whenever
    a user's state changes (role update, active toggle, password reset,
    profile change, 2FA toggle, deletion, etc.).
    """
    try:
        invalidate_user_profile(user_id)
    except Exception as e:
        logger.debug("Cache invalidation failed for user profile: %s", e)
    try:
        invalidate_user_permissions_cache(user_id)
    except Exception as e:
        logger.debug("Cache invalidation failed for user permissions: %s", e)


def invalidate_user_permissions_cache(user_id: int) -> None:
    """Invalidate cached user permission checks."""
    try:
        client = _get_valkey()
        if client is None:
            return
        pattern = f"perf:permissions:check:{user_id}:*"
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
    except Exception as e:
        logger.debug("Cache invalidation failed for user permissions: %s", e)


def cache_cart(user_id: int) -> Optional[dict]:
    """Retrieve cached cart data if available."""
    key = _make_key("perf:cart", str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for cart: %s", e)
        return None


def set_cart(user_id: int, data: dict, ttl: int = 60) -> None:
    """Cache cart data with short TTL (carts change frequently)."""
    key = _make_key("perf:cart", str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for cart: %s", e)


def invalidate_cart(user_id: int) -> None:
    """Invalidate cached cart data."""
    key = _make_key("perf:cart", str(user_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for cart: %s", e)


def cache_payment_status(payment_id: int) -> Optional[dict]:
    """Retrieve cached payment status if available."""
    key = _make_key("perf:payment", str(payment_id))
    try:
        client = _get_valkey()
        if client is None:
            return None
        raw = client.get(key)
        if raw is None:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        logger.debug("Cache get failed for payment status: %s", e)
        return None


def set_payment_status(payment_id: int, data: dict, ttl: int = 120) -> None:
    """Cache payment status with jittered TTL."""
    key = _make_key("perf:payment", str(payment_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        jitter = int(ttl * 0.1)
        effective_ttl = max(ttl + random.randint(-jitter, jitter), 1)
        client.setex(key, effective_ttl, json.dumps(data, default=str))
    except Exception as e:
        logger.debug("Cache set failed for payment status: %s", e)


def invalidate_payment_status(payment_id: int) -> None:
    """Invalidate cached payment status."""
    key = _make_key("perf:payment", str(payment_id))
    try:
        client = _get_valkey()
        if client is None:
            return
        client.delete(key)
    except Exception as e:
        logger.debug("Cache delete failed for payment status: %s", e)
