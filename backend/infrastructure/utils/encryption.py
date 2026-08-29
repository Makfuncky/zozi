"""Backwards-compatible re-export shim.

``FieldEncryptor`` and ``encrypt_data`` now live in
``infrastructure.security.encryption`` (per the platform security layout). This
module keeps legacy import sites working without changes.
"""
from __future__ import annotations

from typing import Any, Optional

from infrastructure.security.encryption import (  # noqa: F401
    FieldEncryptor,
    field_encryptor,
)

__all__ = ["FieldEncryptor", "encrypt_data", "field_encryptor"]


def encrypt_data(data: Any, key_suffix: Optional[str] = None) -> Any:
    """Encrypt ``data`` for at-rest storage.

    ``key_suffix`` is accepted for API compatibility (country-scoped keys) but
    the shared field-encryption key is used here; per-suffix key derivation is a
    future enhancement. Returns the value unchanged when encryption is disabled.
    """
    if field_encryptor is None:
        return data
    return field_encryptor.encrypt(data)


def decrypt_secret(value: Any) -> Any:
    """Decrypt a secret previously encrypted via ``FieldEncryptor``.

    Returns the value unchanged when the encryptor is unavailable so callers
    never crash on missing secrets (Law 30).
    """
    if field_encryptor is None or value is None:
        return value
    try:
        return field_encryptor.decrypt(value)
    except Exception:
        return value
