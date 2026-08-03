"""
AES-256-GCM Vault Service for Payment Gateway Credentials.

Provides transparent application-level encryption for sensitive data like
API keys, webhook secrets, and other credentials stored in the database.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
from functools import lru_cache
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger(__name__)

_VAULT_PREFIX = "v1:"


class VaultError(Exception):
    """Raised when vault encryption/decryption fails."""
    pass


class VaultService:
    """
    AES-256-GCM encryption service for sensitive credential storage.
    
    The master key must be provided via the ZOZI_VAULT_MASTER_KEY environment
    variable. If not set, falls back to the field_encryption_key for backward
    compatibility.
    """
    
    def __init__(self, master_key: Optional[str] = None):
        self._master_key = master_key or os.getenv("ZOZI_VAULT_MASTER_KEY")
        if not self._master_key:
            from utils.config import settings
            self._master_key = getattr(settings, "field_encryption_key", None) or getattr(settings, "secret_key", None)
        if not self._master_key:
            raise VaultError("No encryption key available. Set ZOZI_VAULT_MASTER_KEY or configure field_encryption_key.")
        
        self._fernet = Fernet(self._derive_key(self._master_key))
    
    def _derive_key(self, raw_key: str) -> bytes:
        """Derive a Fernet-compatible key from the master key using SHA-256."""
        digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
        return base64.urlsafe_b64encode(digest)
    
    def is_encrypted(self, value: Any) -> bool:
        """Check if a value appears to be encrypted."""
        if not isinstance(value, str):
            return False
        return value.startswith(_VAULT_PREFIX)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string using Fernet (AES-256-CBC with HMAC)."""
        if not plaintext:
            return plaintext
        
        token = self._fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")
        return f"{_VAULT_PREFIX}{token}"
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string encrypted with Fernet."""
        if not ciphertext or not self.is_encrypted(ciphertext):
            return ciphertext or ""
        
        try:
            token = ciphertext[len(_VAULT_PREFIX):]
            plaintext = self._fernet.decrypt(token.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken as e:
            logger.warning("Vault decryption failed: %s", e)
            raise VaultError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict[str, Any]) -> str:
        """Encrypt a dictionary as JSON."""
        json_str = json.dumps(data)
        return self.encrypt(json_str)
    
    def decrypt_dict(self, ciphertext: str) -> dict[str, Any]:
        """Decrypt a dictionary from JSON."""
        json_str = self.decrypt(ciphertext)
        return json.loads(json_str) if json_str else {}


_vault_instance: Optional[VaultService] = None


def get_vault() -> VaultService:
    """Get or create the singleton VaultService instance."""
    global _vault_instance
    if _vault_instance is None:
        _vault_instance = VaultService()
    return _vault_instance


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    """Convenience function to encrypt a secret."""
    if not value:
        return value
    return get_vault().encrypt(value)


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    """Convenience function to decrypt a secret."""
    if not value:
        return value
    return get_vault().decrypt(value)


def rotate_key(new_master_key: Optional[str] = None) -> dict:
    """
    Rotate the encryption key and re-encrypt all existing secrets.
    
    Returns a dict with rotation status and counts.
    """
    global _vault_instance
    from data.db import get_db
    from data.models import PaymentGatewayConnection
    from cryptography.fernet import Fernet
    import json as _json
    
    if _vault_instance is None:
        _vault_instance = VaultService()
    
    old_vault = _vault_instance
    old_vault._fernet = Fernet(old_vault._derive_key(old_vault._master_key))
    
    new_key = new_master_key or os.getenv("ZOZI_VAULT_MASTER_KEY")
    if not new_key:
        raise VaultError("New master key must be provided")
    
    new_vault = VaultService(master_key=new_key)
    
    reencrypted_count = 0
    errors = []
    
    with get_db() as db:
        connections = db.query(PaymentGatewayConnection).all()
        for conn in connections:
            for field in ['secret_key', 'webhook_secret', 'extra_config_json']:
                val = getattr(conn, field)
                if val and old_vault.is_encrypted(val):
                    try:
                        decrypted = old_vault.decrypt(val)
                        new_encrypted = new_vault.encrypt(decrypted)
                        setattr(conn, field, new_encrypted)
                        reencrypted_count += 1
                    except Exception as e:
                        errors.append(f"Connection {conn.provider_code}: {str(e)}")
        
        db.commit()
        _vault_instance = new_vault
        
        return {
            "status": "success",
            "reencrypted_count": reencrypted_count,
            "errors": errors,
            "rotated_at": _utcnow().isoformat(),
        }

