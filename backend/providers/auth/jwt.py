"""JWT provider — wraps ``PyJWT`` for token (de)serialization.

Centralizes JWT handling so security services don't embed the PyJWT SDK
directly. Part of the providers/ Auth family.
"""
from __future__ import annotations

try:
    import jwt
    from jwt import InvalidTokenError
    HAS_JWT = True
    JWTError = InvalidTokenError
except ImportError:
    HAS_JWT = False
    InvalidTokenError = None  # type: ignore[assignment]
    JWTError = None  # type: ignore[assignment]
    jwt = None  # type: ignore[assignment]


def decode_unverified_claims(token: str) -> dict:
    """Read claims without verifying the signature (e.g. to read ``jti``)."""
    if not HAS_JWT:
        raise RuntimeError("PyJWT is not installed")
    return jwt.decode(token, options={"verify_signature": False})


# Re-export canonical decode_token from infrastructure/utils/auth.py
# to avoid duplicate definitions. The infrastructure version adds
# blacklist checking and expected_type validation.
from infrastructure.utils.auth import decode_token  # noqa: F401
