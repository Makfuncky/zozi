import base64
import hashlib
import logging
import os
from functools import lru_cache
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from utils.config import settings

logger = logging.getLogger(__name__)

_ENCRYPTED_PREFIX = "enc::"


def _derive_fernet_key(raw_key: str) -> bytes:
    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class FieldEncryptor:
    def __init__(self, raw_key: str):
        self._fernet = Fernet(_derive_fernet_key(raw_key)) if raw_key else None

    def is_encrypted(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX)

    def encrypt(self, value: Any) -> Any:
        if value is None:
            return None
        if not self._fernet:
            return value
        if not isinstance(value, str):
            value = str(value)
        if value == "" or self.is_encrypted(value):
            return value
        token = self._fernet.encrypt(value.encode("utf-8")).decode("utf-8")
        return f"{_ENCRYPTED_PREFIX}{token}"

    def decrypt(self, value: Any) -> Any:
        if value is None or not isinstance(value, str) or value == "":
            return value
        if not self._fernet:
            return value
        if not self.is_encrypted(value):
            return value
        token = value[len(_ENCRYPTED_PREFIX):]
        try:
            return self._fernet.decrypt(token.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            logger.warning("Encountered unreadable encrypted field; returning raw value")
            return value


def _get_encryption_key() -> str:
    key = settings.field_encryption_key or os.getenv("FIELD_ENCRYPTION_KEY", "")
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
        from utils.vault import get_vault
        return get_vault().decrypt(value)
    if field_encryptor:
        return field_encryptor.decrypt(value)
    return value

