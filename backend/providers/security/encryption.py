"""Provider wrapper for the `cryptography` SDK used by the KMS field-level
encryption service.

External SDKs are isolated under `providers/`; `services.security.kms_encryption`
imports these symbols from here rather than from `cryptography` directly.
"""
import base64
import hashlib
import logging
import os
from typing import Optional, Tuple, Union

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

logger = logging.getLogger(__name__)


def _derive_key(secret: bytes, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret))


def encrypt_data(plaintext: Union[str, bytes], key: Optional[bytes] = None) -> Optional[str]:
    if not HAS_CRYPTOGRAPHY:
        return None
    if key is None:
        key = generate_key()
    f = Fernet(key)
    if isinstance(plaintext, bytes):
        return f.encrypt(plaintext).decode()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_data(token: Union[str, bytes], key: bytes) -> Optional[str]:
    if not HAS_CRYPTOGRAPHY:
        return None
    f = Fernet(key)
    if isinstance(token, bytes):
        return f.decrypt(token).decode()
    return f.decrypt(token.encode()).decode()


def generate_key() -> Optional[bytes]:
    if not HAS_CRYPTOGRAPHY:
        return None
    return Fernet.generate_key()


__all__ = [
    "Fernet",
    "hashes",
    "PBKDF2HMAC",
    "HAS_CRYPTOGRAPHY",
    "encrypt_data",
    "decrypt_data",
    "generate_key",
]
