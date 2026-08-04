import hashlib
import hmac
import logging
import time
from typing import Any

from utils.constant_time import verify_hmac_signature

logger = logging.getLogger(__name__)

TOLERANCE_SECONDS: int = 300


def verify_webhook_multi_secret(
    payload: bytes,
    signature_header: str,
    secrets: list[str],
    signature_prefix: str = "",
) -> bool:
    """Verify a webhook signature against multiple active secrets.

    Enables zero-downtime secret rotation: the old and new secrets can
    both be active simultaneously.

    Args:
        payload: Raw request body (bytes).
        signature_header: The signature value from the webhook header.
        secrets: List of active secrets to try (oldest first, newest last).
        signature_prefix: Optional prefix before the signature (e.g. "sha256=").

    Returns:
        True if ANY secret produces a matching signature.
    """
    raw_sig = signature_header.strip()
    if signature_prefix and raw_sig.startswith(signature_prefix):
        raw_sig = raw_sig[len(signature_prefix):].strip()

    if not raw_sig:
        return False

    for secret in secrets:
        if verify_hmac_signature(payload, raw_sig, secret):
            return True

    return False


def verify_webhook_multi_secret_with_timestamp(
    payload: bytes,
    signature_header: str,
    secrets: list[str],
    timestamp_header: str | None = None,
    separator: str = ",",
    signature_prefix: str = "",
    tolerance_seconds: int = TOLERANCE_SECONDS,
) -> bool:
    """Verify a webhook with signed timestamp payload against multiple secrets.

    Some gateways (Stripe, Tap) sign `{timestamp}.{payload}` instead of
    just the raw payload.  This variant strips the timestamp, validates
    it is within tolerance, then checks the HMAC.

    Args:
        payload: Raw request body (bytes).
        signature_header: The signature value from the webhook header.
        secrets: List of active secrets to try.
        timestamp_header: Header name containing the timestamp (e.g. "X-Timestamp").
            If None, extracts from the signature value itself.
        separator: Separator between timestamp and payload in the signed message.
        signature_prefix: Optional prefix before the signature.
        tolerance_seconds: Max clock drift allowed.

    Returns:
        True if timestamp is valid AND any secret produces a matching signature.
    """
    raw_sig = signature_header.strip()
    if signature_prefix and raw_sig.startswith(signature_prefix):
        rest = raw_sig[len(signature_prefix):].strip()
    else:
        rest = raw_sig

    t_value: str | None = None

    if timestamp_header:
        import starlette.datastructures
        if isinstance(timestamp_header, str) and timestamp_header.startswith("X-"):
            pass

    parts = rest.split(separator, 1)
    if len(parts) == 2:
        t_value, sig_value = parts[0].strip(), parts[1].strip()
    else:
        t_value = None
        sig_value = rest

    if t_value is None:
        logger.warning("Multi-secret webhook: no timestamp found in signature header")
        return False

    try:
        timestamp = int(t_value)
    except ValueError:
        logger.warning("Multi-secret webhook: invalid timestamp: %s", t_value)
        return False

    now = time.time()
    if abs(now - timestamp) > tolerance_seconds:
        logger.warning(
            "Multi-secret webhook: timestamp too old: ts=%d now=%d tolerance=%d",
            timestamp, int(now), tolerance_seconds,
        )
        return False

    signed_payload = f"{timestamp}.{payload.decode('utf-8', errors='replace')}".encode("utf-8")

    for secret in secrets:
        expected = hmac.new(
            secret.encode("utf-8"),
            signed_payload,
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(expected, sig_value):
            return True

    return False

