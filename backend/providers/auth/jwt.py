"""JWT provider — wraps ``python-jose`` for token (de)serialization.

Centralizes JWT handling so security services don't embed the jose SDK
directly. Part of the providers/ Auth family.
"""
from __future__ import annotations

try:
    from jose import JWTError, jwt
    HAS_JOSE = True
except ImportError:
    HAS_JOSE = False
    JWTError = None  # type: ignore[assignment]
    jwt = None  # type: ignore[assignment]


def decode_unverified_claims(token: str) -> dict:
    """Read claims without verifying the signature (e.g. to read ``jti``)."""
    if not HAS_JOSE:
        raise RuntimeError("python-jose is not installed")
    return jwt.get_unverified_claims(token)


# Re-export canonical decode_token from infrastructure/utils/auth.py
# to avoid duplicate definitions. The infrastructure version adds
# blacklist checking and expected_type validation.
from infrastructure.utils.auth import decode_token  # noqa: F401
