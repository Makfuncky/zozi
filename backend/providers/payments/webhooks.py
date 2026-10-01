"""Payment gateway provider: webhook signature verification.

Pure cryptographic verification of webhook signatures from payment providers.
These functions verify that incoming webhooks genuinely came from the provider
by validating HMAC signatures against a shared secret.
"""
from __future__ import annotations

import hashlib
import hmac

__all__ = [
    "_verify_paytabs_signature",
    "_verify_tap_signature",
]


def _verify_paytabs_signature(payload: bytes, signature: str, webhook_secret: str) -> bool:
    """Verify a PayTabs webhook signature using HMAC-SHA256."""
    if not webhook_secret or not signature:
        return False
    hmac_digest = hmac.new(
        webhook_secret.encode("utf-8"),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, hmac_digest)


def _verify_tap_signature(raw_body: bytes, sig_header: str, webhook_secret: str) -> bool:
    """Verify an incoming Tap webhook request.

    Tap signs each webhook POST with an HMAC-SHA256 digest calculated over the
    raw request body, using TAP_WEBHOOK_SECRET as the key. The digest is
    delivered in the 'hashstring' header (Tap docs, 2024 API reference).

    Returns True when the signature is valid, False otherwise.
    """
    if not webhook_secret:
        return False
    hmac_digest = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(hmac_digest, sig_header)
