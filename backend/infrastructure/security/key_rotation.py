"""
Key Rotation Utility — re-encrypts all EncryptedString fields with a new
FIELD_ENCRYPTION_KEY without exposing plaintext values to application logs.

Usage:
    from infrastructure.security.key_rotation import rotate_encryption_key
    result = rotate_encryption_key(old_key, new_key, db)

The function:
1. Registers *old_key* on the live field encryptor's decryption keyring, so no
   existing ciphertext becomes unreadable at any instant (Law 277,
   "zero-downtime").
2. Decrypts every encrypted column using *old_key*.
3. Re-encrypts the plaintext using *new_key*.
4. Writes the updated rows in batches of BATCH_SIZE and commits after each
   batch to keep the transaction size manageable.
5. Returns a summary dict with row counts and any per-table errors.
6. Records the new key's in-service date so the 90-day deadline can be
   enforced (Law 277).

Step 1 is the one that makes the whole operation safe. The ``enc::`` ciphertext
format carries no key identifier, so a single-key encryptor cannot tell "wrong
key" from "corrupt value" — it just returns the ciphertext to the caller. By
widening the keyring for the duration of the migration, a partially-completed
rotation (including rows written concurrently while the migration runs) still
decrypts correctly, because the outgoing key remains accepted.

SEC2-027 — rotation-age enforcement
-----------------------------------
There was no enforcement of any kind. ``_KDF_ITERATIONS`` lives in
``infrastructure/security/encryption.py``, not in this file (the orchestrator's
"MIS-CITED" record was correct about the location), and the only
rotation timestamp anywhere in the codebase was the ``rotated_at`` RETURN VALUE
of the *vault* master-key rotation in ``infrastructure/security/vault.py`` — a
different key, in a different file, handed back to the caller and discarded.

The policy now lives next to the key derivation it protects, in
``infrastructure.security.encryption``, and is re-exported here:

    KEY_ROTATION_INTERVAL_DAYS  90          Law 277, stated verbatim
    get_key_rotation_state(...)  age / days_until_due / overdue
    check_key_rotation(...)      the same dict PLUS a WARNING/CRITICAL log line
    key_rotation_health(...)     shaped for /health/deps (Law 299)

Wiring ``key_rotation_health()`` into ``main.py``'s ``/health/deps`` is a one-line
change in a file outside this contract's allowed set, so it is documented rather
than applied.

Law 1 compliance: this module declares its encrypted-column registry as a
plain ``(table_name, [column_names])`` list — no domain ORM imports.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from infrastructure.security.encryption import (
    KEY_ROTATION_INTERVAL_DAYS,
    KEY_ROTATION_WARN_THRESHOLD_DAYS,
    FieldEncryptor,
    check_key_rotation,
    get_key_rotation_state,
    record_key_rotation,
    register_previous_field_encryption_key,
)
from infrastructure.utils.encryption import FieldEncryptor as _LegacyFieldEncryptor

logger = logging.getLogger(__name__)

BATCH_SIZE = 200

#: Compatibility guard. `infrastructure/utils/encryption.py` re-exports
#: `FieldEncryptor` from this module's canonical home, and
#: `infrastructure/utils/key_rotation.py` re-exports this whole module
#: wholesale. Both historical import paths must keep resolving to the SAME
#: class, otherwise a caller could end up encrypting with one keyring and
#: decrypting with another.
if _LegacyFieldEncryptor is not FieldEncryptor:  # pragma: no cover - import guard
    raise RuntimeError(
        "FieldEncryptor import-path divergence: infrastructure.utils.encryption "
        "and infrastructure.security.encryption must expose the same class"
    )

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

    Zero-downtime guarantee (Law 277): *old_raw_key* is registered on the live
    field encryptor's decryption keyring BEFORE any row is rewritten, so a value
    that this migration does not reach -- including one written concurrently
    while it runs -- is still decryptable. The rotation records the new key's
    in-service date so the 90-day deadline becomes enforceable.

    Returns::

        {
            "status": "ok" | "partial",
            "tables": {
                "users": {"rows_processed": 42, "rows_updated": 40, "errors": 0},
                ...
            },
            "total_updated": 123,
            "total_errors": 2,
            "previous_key_registered": <int>,   # keyring size during migration
            "rotation_state": {...},            # the recorded Law 277 state
        }
    """
    if not old_raw_key:
        raise ValueError("old_raw_key is required; refusing to rotate without the outgoing key")
    if not new_raw_key:
        raise ValueError("new_raw_key is required; refusing to rotate onto an empty key")
    if old_raw_key == new_raw_key:
        raise ValueError("new_raw_key equals old_raw_key; refusing a no-op rotation")

    # Law 277 zero-downtime. Registered FIRST, so that every subsequent failure
    # mode of this function still leaves old ciphertext readable.
    previous_keys_registered = register_previous_field_encryption_key(old_raw_key)

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
            from sqlalchemy import bindparam, column, select, table, update
            from sqlalchemy.sql import quoted_name

            safe_table = quoted_name(table_name, quote=True)
            safe_pk = quoted_name(pk_col, quote=True)
            safe_cols = [quoted_name(c, quote=True) for c in columns]

            # WHY Core constructs, not string SQL: a column name cannot be a
            # bind parameter, so the dialect compiler must emit the
            # identifiers. lim/off are the only values, and stay bound.
            select_stmt = (
                select(*(column(c) for c in [safe_pk] + safe_cols))
                .select_from(table(safe_table))
                .order_by(column(safe_pk))
                .limit(bindparam("lim"))
                .offset(bindparam("off"))
            )

            while True:
                rows = db.execute(
                    select_stmt,
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
                        values_dict = {col_name: bindparam(col_name) for col_name in updates if col_name != pk_col}
                        tbl = table(safe_table, *(column(c) for c in updates.keys()))
                        stmt = (
                            update(tbl)
                            .where(column(safe_pk) == bindparam(pk_col))
                            .values(values_dict)
                        )
                        db.execute(stmt, updates)
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

    # Law 277: the 90-day clock starts now. Recorded even when the migration was
    # partial, because the key IS in service either way; the keyring registered
    # above is what keeps the unmigrated rows readable.
    rotation_state = record_key_rotation()

    result = {
        "status": "ok" if total_errors == 0 else "partial",
        "tables": summary,
        "total_updated": total_updated,
        "total_errors": total_errors,
        "previous_key_registered": previous_keys_registered,
        "rotation_state": rotation_state,
    }
    if total_errors:
        failed = sorted(t for t, s in summary.items() if s["errors"])
        logger.error(
            "key_rotation: PARTIAL rotation - %d row(s) across %s could not be "
            "re-encrypted. The previous key is still accepted for decryption, so "
            "those values remain readable, but the migration must be re-run "
            "before the previous key is retired.",
            total_errors,
            ", ".join(failed) or "unknown",
        )
    else:
        logger.info(
            "key_rotation: rotation complete, %d row(s) re-encrypted; the "
            "previous key stays accepted for decryption until it is explicitly "
            "retired",
            total_updated,
        )
    return result


def key_rotation_health(now: Any = None, state_path: Any = None) -> dict:
    """Rotation-age health block for ``/health/deps`` (Law 299).

    Returns ``{"status": ..., "law": "277", "interval_days": 90, ...}``. The
    field is intentionally a plain dict so a caller can splat it into a health
    payload without importing anything from this module.
    """
    state = check_key_rotation(now=now, state_path=state_path)
    return {
        "field_encryption_key": {
            "status": state["status"],
            "law": "277",
            "rotated_at": state["rotated_at"],
            "age_days": state["age_days"],
            "interval_days": state["interval_days"],
            "days_until_due": state["days_until_due"],
            "overdue": state["overdue"],
            # Fingerprint only -- never key material (Law 32, Law 282).
            "key_fingerprint": state["key_fingerprint"],
            "fallback_key_count": state["fallback_key_count"],
        }
    }
