import hashlib
import hmac
import logging

logger = logging.getLogger(__name__)


def verify_hmac_signature(
    raw_body: bytes,
    signature_header: str,
    secret: str,
    hash_func: type[hashlib._Hash] = hashlib.sha256,
    encoding: str = "utf-8",
) -> bool:
    """Constant-time HMAC verification.

    Uses hmac.compare_digest() to prevent timing attacks.
    The comparison takes the same amount of time regardless of how
    many bytes match, making it impossible for attackers to
    character-by-character guess the signature.

    Args:
        raw_body: The raw byte body of the request (never parsed JSON)
        signature_header: The signature value from the gateway's header
        secret: The shared webhook secret
        hash_func: Hash function (default: hashlib.sha256)
        encoding: String encoding (default: utf-8)

    Returns:
        True if the signature is valid, False otherwise
    """
    if not raw_body or not signature_header or not secret:
        logger.warning("HMAC verification skipped: missing body, signature, or secret")
        return False

    expected_hash = hmac.new(
        secret.encode(encoding),
        raw_body,
        hash_func,
    ).hexdigest()

    return hmac.compare_digest(expected_hash, signature_header)


def verify_hmac_with_timestamp(
    raw_body: bytes,
    signature_header: str,
    timestamp_header: str | None,
    secret: str,
    delimiter: str = "-",
    hash_func: type[hashlib._Hash] = hashlib.sha256,
    encoding: str = "utf-8",
) -> bool:
    """HMAC verification where the timestamp is part of the signed payload.

    Some gateways (e.g., Thawani) sign the concatenation of body and timestamp:
        signature = HMAC(secret, body + delimiter + timestamp)

    Args:
        raw_body: The raw byte body
        signature_header: The gateway's signature
        timestamp_header: The timestamp from the gateway's header
        secret: The shared webhook secret
        delimiter: The delimiter between body and timestamp (default: "-")
        hash_func: Hash function (default: hashlib.sha256)
        encoding: String encoding (default: utf-8)

    Returns:
        True if signature is valid, False otherwise
    """
    if not raw_body or not signature_header or not secret:
        return False

    if not timestamp_header:
        return False

    payload = raw_body + delimiter.encode(encoding) + timestamp_header.encode(encoding)

    expected_hash = hmac.new(
        secret.encode(encoding),
        payload,
        hash_func,
    ).hexdigest()

    return hmac.compare_digest(expected_hash, signature_header)

