"""Cross-cutting CSRF helpers.

CSRF token generation is a utility concern (used by routers and middleware alike)
and must not live in the `middleware` layer, which is only imported by the app
entrypoint — importing it from a router would create an upward edge in the
dependency circuit.
"""
from __future__ import annotations

import secrets

CSRF_TOKEN_LENGTH = 32


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return secrets.token_hex(CSRF_TOKEN_LENGTH)


__all__ = ["CSRF_TOKEN_LENGTH", "generate_csrf_token"]
