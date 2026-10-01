"""Provider wrapper for the `cryptography` SDK used by the KMS field-level
encryption service.

External SDKs are isolated under `providers/`; `services.security.kms_encryption`
imports these symbols from here rather than from `cryptography` directly.
"""
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False
    Fernet = None  # type: ignore[assignment]
    hashes = None  # type: ignore[assignment]
    PBKDF2HMAC = None  # type: ignore[assignment]

__all__ = ["Fernet", "hashes", "PBKDF2HMAC", "HAS_CRYPTOGRAPHY"]
