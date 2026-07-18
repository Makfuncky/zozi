"""
Key Rotation Utility — re-encrypts all EncryptedString fields with a new
FIELD_ENCRYPTION_KEY without exposing plaintext values to application logs.

Usage:
    from utils.key_rotation import rotate_encryption_key
    result = rotate_encryption_key(old_key, new_key, db)

The function:
1. Decrypts every encrypted column using *old_key*.
2. Re-encrypts the plaintext using *new_key*.
3. Writes the updated rows in batches of BATCH_SIZE and commits after each
   batch to keep the transaction size manageable.
4. Returns a summary dict with row counts and any per-table errors.

After a successful rotation the caller must update the FIELD_ENCRYPTION_KEY
environment variable / secret-store entry so that the running singleton
``field_encryptor`` in utils/encryption.py is also refreshed (typically
requires an app restart or a hot-reload of the config).
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from utils.encryption import FieldEncryptor

logger = logging.getLogger(__name__)

BATCH_SIZE = 200

# Registry: (Model, [encrypted_column_attribute_names])
# Keep this in sync with db/models.py EncryptedString usages.
_ENCRYPTED_COLUMNS: list[tuple[Any, list[str]]] = []


def _build_registry():
    """Lazy import so that circular imports are avoided."""
    if _ENCRYPTED_COLUMNS:
        return
    from models import (
        User, Order, Shipment, ShipmentEvent,
        SupplierProfile, LogisticsPartner,
    )
    _ENCRYPTED_COLUMNS.extend([
        (User, ["phone", "address_book"]),
        (Order, ["shipping_address", "customer_phone"]),
        (Shipment, ["shipping_address"]),
        (ShipmentEvent, ["location"]),
        (SupplierProfile, [
            "bank_account_number", "bank_routing_number",
            "national_id", "tax_id",
        ]),
        (LogisticsPartner, ["contact_email", "contact_phone"]),
    ])


def rotate_encryption_key(old_raw_key: str, new_raw_key: str, db: Session) -> dict:
    """Re-encrypt every EncryptedString column from *old_raw_key* to *new_raw_key*.

    Returns::

        {
            "status": "ok" | "partial",
            "tables": {
                "users": {"rows_processed": 42, "rows_updated": 40, "errors": 0},
                ...
            },
            "total_updated": 123,
            "total_errors": 2,
        }
    """
    _build_registry()
    old_enc = FieldEncryptor(old_raw_key)
    new_enc = FieldEncryptor(new_raw_key)

    summary: dict[str, dict] = {}
    total_updated = 0
    total_errors = 0

    for Model, columns in _ENCRYPTED_COLUMNS:
        table_name = Model.__tablename__
        rows_processed = 0
        rows_updated = 0
        errors = 0

        try:
            offset = 0
            while True:
                batch = db.query(Model).offset(offset).limit(BATCH_SIZE).all()
                if not batch:
                    break
                for row in batch:
                    rows_processed += 1
                    changed = False
                    for col in columns:
                        raw = getattr(row, col, None)
                        if raw is None:
                            continue
                        try:
                            # Decrypt with old key; will return raw value if not encrypted
                            plaintext = old_enc.decrypt(raw)
                            if plaintext is None:
                                continue
                            # Re-encrypt with new key only when the value was actually
                            # encrypted (i.e. decryption changed it).
                            if plaintext != raw or old_enc.is_encrypted(raw):
                                new_val = new_enc.encrypt(plaintext)
                                setattr(row, col, new_val)
                                changed = True
                        except Exception as col_err:
                            logger.warning(
                                "key_rotation: failed column %s.%s id=%s: %s",
                                table_name, col, getattr(row, "id", "?"), col_err,
                            )
                            errors += 1
                    if changed:
                        rows_updated += 1
                db.commit()
                offset += BATCH_SIZE

        except Exception as tbl_err:
            logger.error("key_rotation: table %s failed: %s", table_name, tbl_err)
            db.rollback()
            errors += 1

        summary[table_name] = {
            "rows_processed": rows_processed,
            "rows_updated": rows_updated,
            "errors": errors,
        }
        total_updated += rows_updated
        total_errors += errors

    return {
        "status": "ok" if total_errors == 0 else "partial",
        "tables": summary,
        "total_updated": total_updated,
        "total_errors": total_errors,
    }

