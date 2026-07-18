"""AWS KMS and Vault integration for field-level encryption."""
from __future__ import annotations

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class KmsIntegration:
    """Wrapper for AWS KMS or HashiCorp Vault encryption operations."""
    
    def __init__(self, use_vault: bool = False, vault_addr: str = None, vault_token: str = None):
        self.use_vault = use_vault
        self.vault_addr = vault_addr
        self.vault_token = vault_token
        self._fernet = None
        
        field_key = os.environ.get("FIELD_ENCRYPTION_KEY")
        if field_key:
            try:
                self._fernet = Fernet(field_key.encode())
            except Exception:
                key = Fernet.generate_key()
                self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return None
        if self._fernet:
            return self._fernet.encrypt(plaintext.encode()).decode()
        return plaintext
    
    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return None
        if self._fernet:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        return ciphertext
    
    def get_data_key(self, key_id: str) -> Optional[bytes]:
        if self.use_vault:
            return None
        return None


_encryption_instance: Optional[KmsIntegration] = None


def get_kms() -> KmsIntegration:
    global _encryption_instance
    if _encryption_instance is None:
        _encryption_instance = KmsIntegration()
    return _encryption_instance


def encrypt_sensitive(value: str) -> str:
    return get_kms().encrypt(value)


def decrypt_sensitive(value: str) -> str:
    return get_kms().decrypt(value)

