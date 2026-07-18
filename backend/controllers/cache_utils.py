"""Shared Redis-backed cache helpers for public read-heavy endpoints."""
from __future__ import annotations

import hashlib
import json
from typing import Any, cast


def get_redis_client():
    try:
        from utils.auth import _get_redis

        return _get_redis()
    except Exception:
        return None


def cache_get_json(key: str) -> Any | None:
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return None
        raw = redis_client.get(key)
        if not raw:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(cast(str, raw))
    except Exception:
        return None


def cache_set_json(key: str, value: Any, ttl: int) -> None:
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def get_cache_version(namespace: str) -> str:
    version_key = f"{namespace}:cache:version"
    try:
        redis_client = get_redis_client()
        if redis_client is None:
            return "0"
        raw = redis_client.get(version_key)
        if raw is None:
            redis_client.set(version_key, "1")
            return "1"
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8")
        return str(raw)
    except Exception:
        return "0"


def bump_cache_version(namespace: str) -> None:
    version_key = f"{namespace}:cache:version"
    try:
        redis_client = get_redis_client()
        if redis_client is not None:
            redis_client.incr(version_key)
    except Exception:
        pass


def build_versioned_cache_key(namespace: str, prefix: str, payload: dict[str, Any]) -> str:
    version = get_cache_version(namespace)
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"{namespace}:{prefix}:v{version}:{digest}"

