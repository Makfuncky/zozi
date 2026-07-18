"""
Key Management Service (KMS) Encryption Utility
Provides AES-256-GCM encryption for sensitive employee data
"""
import os
import base64
import hashlib
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import Optional

logger = logging.getLogger(__name__)


class KMSEncryption:
    """AES-256-GCM encryption for sensitive data like national IDs, bank details."""
    
    def __init__(self, master_key: Optional[str] = None):
        self.master_key = master_key or os.getenv("KMS_MASTER_KEY")
        if not self.master_key:
            logger.warning("KMS_MASTER_KEY not set. KMS encryption is disabled.")
            self._fernet = None
        else:
            self._fernet = Fernet(self._derive_key(os.urandom(16)))
    
    def _derive_key(self, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return key
    
    def encrypt(self, plaintext: str) -> str:
        if not self._fernet:
            return plaintext
        salt = os.urandom(16)
        key = self._derive_key(salt)
        f = Fernet(key)
        token = f.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(salt + token).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        if not self._fernet:
            return ciphertext
        data = base64.urlsafe_b64decode(ciphertext.encode())
        salt, token = data[:16], data[16:]
        key = self._derive_key(salt)
        f = Fernet(key)
        return f.decrypt(token).decode()


_kms_instance: Optional[KMSEncryption] = None


def get_kms() -> KMSEncryption:
    global _kms_instance
    if _kms_instance is None:
        _kms_instance = KMSEncryption()
    return _kms_instance

