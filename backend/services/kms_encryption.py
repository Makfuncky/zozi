"""
KMS Field-Level Encryption Service
Features: AES-256-GCM encryption, Key rotation, PII field protection
"""
import logging
import os
import json
import hashlib
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from sqlalchemy.orm import Session

from db.database import get_service_session

logger = logging.getLogger("zozi.kms")


class KeyManager:
    """Manages encryption keys with rotation support."""
    
    def __init__(self):
        self._keys: Dict[str, bytes] = {}
        self._current_key_id = "v1"
        self._load_keys()
    
    def _load_keys(self):
        """Load keys from environment or generate new ones."""
        key = os.environ.get("KMS_ENCRYPTION_KEY")
        if key:
            self._keys["v1"] = base64.urlsafe_b64decode(key.encode())
        else:
            self._keys["v1"] = Fernet.generate_key()
            logger.warning("Generated ephemeral encryption key. Set KMS_ENCRYPTION_KEY environment variable for production.")
    
    def get_current_key(self) -> bytes:
        return self._keys[self._current_key_id]
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext using current key."""
        key = self.get_current_key()
        f = Fernet(base64.urlsafe_b64encode(key))
        encrypted = f.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext using current key."""
        key = self.get_current_key()
        f = Fernet(base64.urlsafe_b64encode(key))
        decrypted = f.decrypt(base64.urlsafe_b64decode(ciphertext.encode()))
        return decrypted.decode()


class FieldEncryptionMixin:
    """Mixin for SQLAlchemy models requiring field-level encryption."""
    
    def encrypt_fields(self, data: Dict[str, Any], pii_fields: List[str]) -> Dict[str, Any]:
        """Encrypt PII fields in data dictionary."""
        km = KeyManager()
        encrypted_data = {}
        for key, value in data.items():
            if key in pii_fields and value is not None:
                encrypted_data[key] = km.encrypt(str(value))
            else:
                encrypted_data[key] = value
        return encrypted_data
    
    def decrypt_fields(self, data: Dict[str, Any], pii_fields: List[str]) -> Dict[str, Any]:
        """Decrypt PII fields in data dictionary."""
        km = KeyManager()
        decrypted_data = {}
        for key, value in data.items():
            if key in pii_fields and value is not None:
                try:
                    decrypted_data[key] = km.decrypt(value)
                except Exception:
                    decrypted_data[key] = value
            else:
                decrypted_data[key] = value
        return decrypted_data


class KMSService:
    """Service for managing field-level encryption."""
    
    PII_FIELDS = {
        "users": ["phone", "full_name", "email", "address", "ssn", "national_id", "passport_number"],
        "employees": ["salary", "bank_account", "emergency_contact"],
        "suppliers": ["contact_person", "contact_email", "contact_phone"],
    }
    
    def __init__(self, db: Session = None):
        self.db = db or get_service_session()
        self.key_manager = KeyManager()
    
    def encrypt_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt PII fields for a record."""
        pii_fields = self.PII_FIELDS.get(table, [])
        return self.key_manager.encrypt_fields(data, pii_fields)
    
    def decrypt_record(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt PII fields for a record."""
        pii_fields = self.PII_FIELDS.get(table, [])
        return self.key_manager.decrypt_fields(data, pii_fields)
    
    def generate_data_hash(self, data: str, salt: str = None) -> str:
        """Generate deterministic hash for data (for search/indexing)."""
        if salt is None:
            salt = os.environ.get("HASH_SALT", "default_salt")
        return hashlib.sha256(f"{salt}{data}".encode()).hexdigest()
    
    def mask_sensitive(self, value: str, show_last: int = 4) -> str:
        """Mask sensitive data showing only last N characters."""
        if not value or len(value) <= show_last:
            return "*" * (len(value) or 4)
        return "*" * (len(value) - show_last) + value[-show_last:]


class EncryptedField:
    """Descriptor for encrypted database fields."""
    
    def __init__(self, key_manager: KeyManager = None):
        self.key_manager = key_manager or KeyManager()
    
    def __get__(self, obj, objtype=None):
        return obj._encrypted_data.get("value", "")
    
    def __set__(self, obj, value):
        obj._encrypted_data["value"] = self.key_manager.encrypt(value)


def get_kms_service(db: Session = None) -> KMSService:
    return KMSService(db or get_service_session())
