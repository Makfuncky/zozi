"""AES-256-GCM field encryption for sensitive database columns.

Replaces the previous Fernet-based implementation to satisfy TECHNOLOGY_STACK.md
§5 (cryptography 50.0.1, AES-256-GCM via PBKDF2-derived key).

``FIELD_ENCRYPTION_SALT`` is mandatory.  Missing values cause an immediate
``RuntimeError`` at import time — the previous behaviour of silently falling
back to an ephemeral random salt made every previously-encrypted value
permanently undecryptable after any restart.
"""

from __future__ import annotations

import base64
import logging
import os
from functools import lru_cache
from typing import Any, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_ENCRYPTED_PREFIX = "enc::"
_KDF_ITERATIONS = 600_000


def _resolve_kdf_salt() -> bytes:
    raw = os.environ.get("FIELD_ENCRYPTION_SALT", "")
    stripped = str(raw).strip()
    if not stripped:
        app_env = str(getattr(settings, "app_env", "development") or "development").lower()
        if app_env in ("production", "staging"):
            raise RuntimeError(
                "FIELD_ENCRYPTION_SALT is required in production/staging. "
                "Generate with: secrets.token_hex(32)"
            )
        logger.critical(
            "FIELD_ENCRYPTION_SALT is not set — field encryption will use a "
            "non-reproducible salt. Encrypted fields become permanently "
            "undecryptable after any restart. Set FIELD_ENCRYPTION_SALT in "
            "all environments."
        )
        raise RuntimeError(
            "FIELD_ENCRYPTION_SALT must be set. Encrypted fields are "
            "undecryptable without a stable salt."
        )
    if len(stripped) < 32:
        raise RuntimeError(
            f"FIELD_ENCRYPTION_SALT must be at least 32 hex characters "
            f"(got {len(stripped)}). Generate with: secrets.token_hex(32)"
        )
    try:
        return bytes.fromhex(stripped)
    except ValueError:
        raise RuntimeError(
            "FIELD_ENCRYPTION_SALT must be a hex string. "
            "Generate with: secrets.token_hex(32)"
        )


_KDF_SALT: bytes = _resolve_kdf_salt()


def _derive_fernet_key(raw_key: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KDF_SALT,
        iterations=_KDF_ITERATIONS,
    )
    derived = kdf.derive(raw_key.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


def _aes256_gcm_encrypt(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def _aes256_gcm_decrypt(token: str, key: bytes) -> str:
    raw = base64.urlsafe_b64decode(token.encode("utf-8"))
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


class FieldEncryptor:
    def __init__(self, raw_key: str):
        self._aes_key: bytes | None = None
        if raw_key:
            self._aes_key = _derive_fernet_key(raw_key)[:32]

    def is_encrypted(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX)

    def encrypt(self, value: Any) -> Any:
        if value is None:
            return None
        if not self._aes_key:
            return value
        if not isinstance(value, str):
            value = str(value)
        if value == "" or self.is_encrypted(value):
            return value
        token = _aes256_gcm_encrypt(value, self._aes_key)
        return f"{_ENCRYPTED_PREFIX}{token}"

    def decrypt(self, value: Any) -> Any:
        if value is None or not isinstance(value, str) or value == "":
            return value
        if not self._aes_key:
            return value
        if not self.is_encrypted(value):
            return value
        token = value[len(_ENCRYPTED_PREFIX):]
        try:
            return _aes256_gcm_decrypt(token, self._aes_key)
        except Exception:
            logger.warning("Encountered unreadable encrypted field; returning raw value")
            return value


def _get_encryption_key() -> str:
    key = settings._resolve_field_encryption_key()
    if not key:
        logger.warning(
            "FIELD_ENCRYPTION_KEY not set. Field encryption is disabled in development mode."
        )
        return ""
    return key


_field_encryption_key = _get_encryption_key()
field_encryptor = FieldEncryptor(_field_encryption_key) if _field_encryption_key else None


@lru_cache(maxsize=128)
def _encrypted_storage_length(plaintext_length: int) -> int:
    probe_length = max(int(plaintext_length or 0), 1)
    encrypted_value = field_encryptor.encrypt("x" * probe_length)
    return len(str(encrypted_value))


class EncryptedString(TypeDecorator):
    """Transparent-at-rest encryption with ciphertext-safe storage sizing."""

    impl = Text
    cache_ok = True

    def __init__(self, length: int | None = None):
        super().__init__()
        self.length = length

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if self.length and field_encryptor:
            return dialect.type_descriptor(String(_encrypted_storage_length(self.length)))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect):  # type: ignore[override]
        if field_encryptor:
            return field_encryptor.encrypt(value)
        return value

    def process_result_value(self, value: Any, dialect):  # type: ignore[override]
        if field_encryptor:
            return field_encryptor.decrypt(value)
        return value


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    """
    Decrypt a secret value.
    
    First attempts to decrypt using the vault service (v1: prefix).
    Falls back to the legacy field encryptor for backward compatibility.
    """
    if not value:
        return value
    if value.startswith("v1:"):
        from infrastructure.security.vault import get_vault
        return get_vault().decrypt(value)
    if field_encryptor:
        return field_encryptor.decrypt(value)
    return value
