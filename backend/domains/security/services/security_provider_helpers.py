"""Security domain — provider-facing helpers.

Wraps auth (JWT, TOTP), encryption, and watchlist providers into high-level
domain operations. Lives in the services layer so the ``features`` module
remains a pure feature-atom catalog.
"""
from __future__ import annotations

import base64
import hashlib
import os

from infrastructure.utils.config import settings
from providers.auth.jwt import decode_token
from providers.auth.totp import generate_secret, provisioning_uri, verify as verify_totp
from providers.security.encryption import PBKDF2HMAC, Fernet, hashes
from providers.security.watchlist import WatchlistProviderError, screen_watchlist


def _get_encryption_salt() -> bytes:
    """Get encryption salt from environment or secure default.

    Uses ENCRYPTION_SALT env var (hex-encoded) if set, otherwise falls back
    to a derived value from the secret key for backward compatibility.
    """
    salt_hex = os.environ.get("ENCRYPTION_SALT")
    if salt_hex:
        try:
            return bytes.fromhex(salt_hex)
        except ValueError:
            pass
    secret = settings.secret_key or "fallback-zozi-secret"
    return hashlib.sha256(secret.encode("utf-8", errors="replace")).digest()[:16]


def _derive_fernet_key(key: str) -> bytes:
    """Derive a 32-byte URL-safe base64 key from a settings string for Fernet encryption."""
    derived = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_get_encryption_salt(),
        iterations=100_000,
    ).derive(key.encode("utf-8", errors="replace"))
    return base64.urlsafe_b64encode(derived)


def encrypt_pii(plaintext: str) -> str:
    """Encrypt PII using the security provider's Fernet primitives."""
    key = settings.field_encryption_key or settings.encryption_key
    return Fernet(_derive_fernet_key(key)).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt PII using the security provider's Fernet primitives."""
    key = settings.field_encryption_key or settings.encryption_key
    return Fernet(_derive_fernet_key(key)).decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def verify_user_token(token: str):
    """Decode and verify a JWT using the auth provider."""
    return decode_token(token, secret=settings.secret_key, algorithms=[settings.jwt_algorithm])


def setup_2fa_for_user(user_email: str):
    """Generate a TOTP secret and provisioning URI via the auth provider."""
    secret = generate_secret()
    uri = provisioning_uri(secret, name=user_email, issuer_name="ZOZI")
    return {"secret": secret, "provisioning_uri": uri}


def verify_2fa_code(secret: str, code: str) -> bool:
    """Verify a TOTP 2FA code against a user's secret using the auth provider."""
    return verify_totp(secret, code)


def screen_entity(name: str, country_code: str):
    """Screen an entity against watchlists using the security provider."""
    try:
        return screen_watchlist(
            employee_code="",
            full_name=name,
            country_code=country_code,
        )
    except WatchlistProviderError as exc:
        return {"status": "error", "score": 0.0, "details": str(exc), "flagged_categories": []}


__all__ = [
    "encrypt_pii",
    "decrypt_pii",
    "verify_user_token",
    "setup_2fa_for_user",
    "verify_2fa_code",
    "screen_entity",
]
