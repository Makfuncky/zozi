"""JWT provider — wraps ``python-jose`` for token (de)serialization.

Centralizes JWT handling so security services don't embed the jose SDK
directly. Part of the providers/ Auth family.
"""
from __future__ import annotations

from jose import JWTError, jwt


def decode_unverified_claims(token: str) -> dict:
    """Read claims without verifying the signature (e.g. to read ``jti``)."""
    return jwt.get_unverified_claims(token)


def decode_token(token: str, secret: str, algorithms) -> dict:
    """Verify and decode a signed JWT with the given secret/algorithms."""
    return jwt.decode(token, secret, algorithms=algorithms)
