"""TOTP (2FA) provider — wraps the ``pyotp`` SDK.

Centralizes one-time-password secret generation, provisioning-URI building
and code verification so the security services never embed the pyotp SDK
directly. Part of the providers/ Auth family: external/SDK auth code lives
in providers/, services only call into it.
"""
from __future__ import annotations

try:
    import pyotp
    HAS_PYOTP = True
except ImportError:
    HAS_PYOTP = False
    pyotp = None  # type: ignore[assignment]


def generate_secret() -> str:
    """Return a new base32 TOTP secret for enrolling a user."""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp is not installed")
    return pyotp.random_base32()


def provisioning_uri(secret: str, name: str, issuer_name: str) -> str:
    """Build an ``otpauth://`` provisioning URI for QR-code enrollment."""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp is not installed")
    return pyotp.TOTP(secret).provisioning_uri(name=name, issuer_name=issuer_name)


def verify(secret: str, code: str, valid_window: int = 0) -> bool:
    """Verify a TOTP *code* against *secret*. Empty inputs fail fast."""
    if not HAS_PYOTP:
        raise RuntimeError("pyotp is not installed")
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=valid_window)
