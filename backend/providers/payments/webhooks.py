"""Payment gateway provider: webhook signature verification.

Pure cryptographic verification of webhook signatures from payment providers.
These functions verify that incoming webhooks genuinely came from the provider
by validating HMAC signatures against a shared secret. An in-memory idempotency
key cache prevents replay of identical webhook payloads.
"""
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Optional

_IDEMPOTENCY_CACHE: dict[str, float] = {}
_IDEMPOTENCY_TTL = 3600
_IDEMPOTENCY_CACHE_LIMIT = 500


def _idempotency_cleanup() -> None:
    if len(_IDEMPOTENCY_CACHE) <= _IDEMPOTENCY_CACHE_LIMIT:
        return
    cutoff = time.time() - _IDEMPOTENCY_TTL
    expired = [k for k, v in _IDEMPOTENCY_CACHE.items() if v < cutoff]
    for key in expired:
        del _IDEMPOTENCY_CACHE[key]
    if len(_IDEMPOTENCY_CACHE) > _IDEMPOTENCY_CACHE_LIMIT:
        oldest = sorted(_IDEMPOTENCY_CACHE.items(), key=lambda item: item[1])
        for key, _ in oldest[: len(_IDEMPOTENCY_CACHE) - _IDEMPOTENCY_CACHE_LIMIT]:
            del _IDEMPOTENCY_CACHE[key]

__all__ = [
    "_verify_paytabs_signature",
    "_verify_tap_signature",
]


def _verify_paytabs_signature(payload: bytes, signature: str, webhook_secret: str) -> bool:
    """Verify a PayTabs webhook signature using HMAC-SHA256."""
    if not webhook_secret or not signature:
        return False
    idempotency_key = hashlib.sha256(payload).hexdigest()
    _idempotency_cleanup()
    cached = _IDEMPOTENCY_CACHE.get(idempotency_key)
    if cached is not None and (time.time() - cached) < _IDEMPOTENCY_TTL:
        return False
    hmac_digest = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    result = hmac.compare_digest(signature, hmac_digest)
    if result:
        _IDEMPOTENCY_CACHE[idempotency_key] = time.time()
    return result


def _verify_tap_signature(raw_body: bytes, sig_header: str, webhook_secret: str) -> bool:
    """Verify an incoming Tap webhook request.

    Tap signs each webhook POST with an HMAC-SHA256 digest calculated over the
    raw request body, using TAP_WEBHOOK_SECRET as the key. The digest is
    delivered in the 'hashstring' header (Tap docs, 2024 API reference).

    Returns True when the signature is valid, False otherwise.
    """
    if not webhook_secret:
        return False
    idempotency_key = hashlib.sha256(raw_body).hexdigest()
    _idempotency_cleanup()
    cached = _IDEMPOTENCY_CACHE.get(idempotency_key)
    if cached is not None and (time.time() - cached) < _IDEMPOTENCY_TTL:
        return False
    hmac_digest = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    result = hmac.compare_digest(hmac_digest, sig_header)
    if result:
        _IDEMPOTENCY_CACHE[idempotency_key] = time.time()
    return result
