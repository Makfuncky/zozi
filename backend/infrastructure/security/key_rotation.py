"""
Key Rotation Utility — re-encrypts all EncryptedString fields with a new
FIELD_ENCRYPTION_KEY without exposing plaintext values to application logs.

Usage:
    from infrastructure.security.key_rotation import rotate_encryption_key
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

Law 1 compliance: this module declares its encrypted-column registry as a
plain ``(table_name, [column_names])`` list — no domain ORM imports.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.utils.encryption import FieldEncryptor

logger = logging.getLogger(__name__)

BATCH_SIZE = 200

# Schema-contract registry: (table_name, [encrypted_column_names]).
# Keep in sync with the EncryptedString usages across the domain models.
_ENCRYPTED_TABLES: list[tuple[str, list[str]]] = [
    ("users", ["phone", "address_book"]),
    ("orders", ["shipping_address", "customer_phone"]),
    ("shipments", ["shipping_address"]),
    ("shipment_events", ["location"]),
    ("supplier_profiles", [
        "bank_account_number", "bank_routing_number",
        "national_id", "tax_id",
    ]),
    ("logistics_partners", ["contact_email", "contact_phone"]),
]

_VALID_TABLES = {t for t, _ in _ENCRYPTED_TABLES}
_VALID_COLUMNS: dict[str, set[str]] = {
    t: set(cols) for t, cols in _ENCRYPTED_TABLES
}
_VALID_PK_COLS = {"id"}


def _validate_table(table_name: str) -> None:
    if table_name not in _VALID_TABLES:
        raise ValueError(f"Refusing to interpolate non-allowlisted table '{table_name}'")


def _validate_columns(table_name: str, columns: list[str]) -> None:
    allowed = _VALID_COLUMNS.get(table_name, set())
    for col in columns:
        if col not in allowed:
            raise ValueError(f"Column '{col}' not in allowlist for table '{table_name}'")


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
    old_enc = FieldEncryptor(old_raw_key)
    new_enc = FieldEncryptor(new_raw_key)

    summary: dict[str, dict] = {}
    total_updated = 0
    total_errors = 0

    for table_name, columns in _ENCRYPTED_TABLES:
        rows_processed = 0
        rows_updated = 0
        errors = 0

        try:
            offset = 0
            _validate_table(table_name)
            _validate_columns(table_name, columns)
            # Determine the primary key column once (default to ``id``).
            pk_col = "id"
            if pk_col not in _VALID_PK_COLS:
                raise ValueError(f"Primary key column '{pk_col}' not in allowlist")
            from sqlalchemy.sql import quoted_name
            safe_table = quoted_name(table_name, quote=True)
            safe_pk = quoted_name(pk_col, quote=True)
            safe_cols = [quoted_name(c, quote=True) for c in columns]
            select_cols_sql = ", ".join([safe_pk] + safe_cols)

            while True:
                rows = db.execute(
                    text(
                        f"SELECT {select_cols_sql} FROM {safe_table} "
                        f"ORDER BY {safe_pk} LIMIT :lim OFFSET :off"
                    ),
                    {"lim": BATCH_SIZE, "off": offset},
                ).mappings().all()
                if not rows:
                    break

                for row in rows:
                    rows_processed += 1
                    changed = False
                    updates: dict[str, Any] = {}
                    for col in columns:
                        raw = row.get(col)
                        if raw is None:
                            continue
                        try:
                            plaintext = old_enc.decrypt(raw)
                            if plaintext is None:
                                continue
                            if plaintext != raw or old_enc.is_encrypted(raw):
                                new_val = new_enc.encrypt(plaintext)
                                updates[col] = new_val
                                changed = True
                        except Exception as col_err:
                            logger.warning(
                                "key_rotation: failed column %s.%s id=%s: %s",
                                table_name, col, row.get(pk_col), col_err,
                            )
                            errors += 1
                    if changed:
                        updates[pk_col] = row.get(pk_col)
                        safe_update_cols = [quoted_name(c, quote=True) for c in updates.keys() if c != pk_col]
                        set_clause = ", ".join([f"{c} = :{c}" for c in safe_update_cols])
                        db.execute(
                            text(f"UPDATE {safe_table} SET {set_clause} WHERE {safe_pk} = :{pk_col}"),
                            updates,
                        )
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
