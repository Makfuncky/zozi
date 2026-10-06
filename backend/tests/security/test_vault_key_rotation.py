"""Fail-before + paired tests for P0 — vault key rotation misses enc:: values.

Law 275: AES-256-GCM encryption at rest.
Law 277: Key rotation every 90 days, zero downtime.
§10.1 Key Rule 1: Secrets NEVER stored in plain text.

The defect: rotate_key() only detects the v1: (Fernet) prefix. Values
encrypted with the current EncryptedString TypeDecorator carry an enc::
prefix and are silently skipped — treated as plaintext — leaving them
unrotated or worse, written back as if they were plaintext.

Run: pytest backend/tests/security/test_vault_key_rotation.py -v
"""
from __future__ import annotations

import os
import sys
import contextlib

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# Encryption env vars must be set before any module that imports
# infrastructure.security.encryption is loaded (field_encryptor is created
# at module-import time from the env var).
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "x" * 64)
os.environ.setdefault("FIELD_ENCRYPTION_SALT", "a" * 64)
os.environ.setdefault("ZOZI_VAULT_MASTER_KEY", "v" * 64)

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from infrastructure.security.encryption import _ENCRYPTED_PREFIX, field_encryptor
from infrastructure.security.vault import (
    VaultError,
    VaultService,
    get_vault,
    rotate_key,
    _VAULT_PREFIX,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_enc_value(plaintext: str) -> str:
    """Create an enc:: value using the current field_encryptor."""
    assert field_encryptor is not None, "field_encryptor must be set for tests"
    return field_encryptor.encrypt(plaintext)


def _make_vault_value(vault_service: VaultService, plaintext: str) -> str:
    """Create a v1: value using the given vault service."""
    return vault_service.encrypt(plaintext)


def _reset_vault_singleton():
    """Reset the module-level vault singleton for test isolation."""
    import infrastructure.security.vault as vault_mod
    vault_mod._vault_instance = None


@contextlib.contextmanager
def _isolated_db():
    """Create an isolated in-memory SQLite database with payment_gateway_connections table."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE payment_gateway_connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_code TEXT NOT NULL,
                gateway_name TEXT NOT NULL,
                secret_key TEXT,
                webhook_secret TEXT,
                extra_config_json TEXT
            )
        """))
        conn.commit()

    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    import infrastructure.database.database as db_mod

    # Patch SessionLocal so get_db(), get_db_sync(), etc. all return
    # sessions bound to our isolated engine.
    original_session_local = db_mod.SessionLocal
    db_mod.SessionLocal = SessionLocal

    try:
        yield engine
    finally:
        db_mod.SessionLocal = original_session_local
        engine.dispose()


# ---------------------------------------------------------------------------
# Test 1: is_encrypted must recognise both v1: and enc:: prefixes
# ---------------------------------------------------------------------------

class TestIsEncryptedDetectsBothFormats:

    def test_detects_v1_prefix(self):
        _reset_vault_singleton()
        vault = get_vault()
        assert vault.is_encrypted("v1:gAAAAA...") is True

    def test_detects_enc_prefix(self):
        _reset_vault_singleton()
        vault = get_vault()
        assert vault.is_encrypted(_ENCRYPTED_PREFIX + "abc123") is True

    def test_passes_through_plaintext(self):
        _reset_vault_singleton()
        vault = get_vault()
        assert vault.is_encrypted("plaintext-secret") is False

    def test_passes_through_none(self):
        _reset_vault_singleton()
        vault = get_vault()
        assert vault.is_encrypted(None) is False

    def test_passes_through_empty(self):
        _reset_vault_singleton()
        vault = get_vault()
        assert vault.is_encrypted("") is False


# ---------------------------------------------------------------------------
# Test 2: rotate_key re-encrypts enc:: values under the new key
# ---------------------------------------------------------------------------

class TestRotateKeyReencryptsEncPrefix:

    def test_rotate_decrypts_and_reencrypts_enc_value(self):
        """FAIL-BEFORE: rotate_key() skips enc:: values — they remain enc::."""
        _reset_vault_singleton()
        get_vault()  # initialise singleton with env key
        old_plaintext = "sk_test_rotation_survives_12345"

        # Build an enc:: ciphertext the way EncryptedString TypeDecorator does
        enc_ciphertext = _make_enc_value(old_plaintext)
        assert enc_ciphertext.startswith(_ENCRYPTED_PREFIX)

        with _isolated_db() as engine:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO payment_gateway_connections (provider_code, gateway_name, secret_key) "
                         "VALUES (:pc, :gn, :sk)"),
                    {"pc": "stripe", "gn": "Stripe Rotation Test", "sk": enc_ciphertext},
                )
                conn.commit()

                # Verify the row has enc:: before rotation
                raw_before = conn.execute(
                    text("SELECT secret_key FROM payment_gateway_connections WHERE provider_code = :pc"),
                    {"pc": "stripe"},
                ).scalar_one_or_none()
                assert raw_before is not None
                assert raw_before.startswith(_ENCRYPTED_PREFIX), (
                    f"Setup error: expected enc:: prefix, got: {raw_before!r}"
                )

            # Rotate to a new key
            new_key = "new_vault_master_key_99999999999999999999"
            result = rotate_key(new_master_key=new_key)
            assert result["status"] == "success", f"rotate_key failed: {result}"

            # Read back via raw SQL — the same path rotate_key() uses
            with engine.connect() as conn:
                raw_after = conn.execute(
                    text("SELECT secret_key FROM payment_gateway_connections WHERE provider_code = :pc"),
                    {"pc": "stripe"},
                ).scalar_one_or_none()

            # After rotation, the value must be under the NEW key (v1: prefix)
            # and decrypt back to the original plaintext
            assert raw_after is not None, "Row was lost after rotation"
            assert raw_after.startswith(_VAULT_PREFIX), (
                f"FAIL-BEFORE REPRODUCED: enc:: value was not re-encrypted under new key. "
                f"Still has enc:: prefix: {raw_after[:50]!r}"
            )
            assert raw_after != enc_ciphertext, (
                "Value was not changed by rotation"
            )

            # The new vault must be able to decrypt the rotated value
            new_vault = get_vault()
            recovered = new_vault.decrypt(raw_after)
            assert recovered == old_plaintext, (
                f"Decryption under new key failed: {recovered!r} != {old_plaintext!r}"
            )


# ---------------------------------------------------------------------------
# Test 3: rotate_key re-encrypts v1: values (old-format) as well
# ---------------------------------------------------------------------------

class TestRotateKeyReencryptsV1Prefix:

    def test_rotate_decrypts_and_reencrypts_v1_value(self):
        """v1: (Fernet) values must also survive rotation."""
        _reset_vault_singleton()
        vault = get_vault()
        old_plaintext = "whsec_old_fernet_webhook_67890"

        v1_ciphertext = _make_vault_value(vault, old_plaintext)
        assert v1_ciphertext.startswith(_VAULT_PREFIX)

        with _isolated_db() as engine:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO payment_gateway_connections (provider_code, gateway_name, webhook_secret) "
                         "VALUES (:pc, :gn, :whs)"),
                    {"pc": "paypal", "gn": "PayPal V1 Rotation Test", "whs": v1_ciphertext},
                )
                conn.commit()

            new_key = "new_vault_key_for_v1_rotation_88888888888"
            result = rotate_key(new_master_key=new_key)
            assert result["status"] == "success", f"rotate_key failed: {result}"

            with engine.connect() as conn:
                raw_after = conn.execute(
                    text("SELECT webhook_secret FROM payment_gateway_connections WHERE provider_code = :pc"),
                    {"pc": "paypal"},
                ).scalar_one_or_none()

            assert raw_after is not None
            assert raw_after.startswith(_VAULT_PREFIX), (
                f"v1: value was not re-encrypted under new key: {raw_after[:50]!r}"
            )
            assert raw_after != v1_ciphertext

            new_vault = get_vault()
            recovered = new_vault.decrypt(raw_after)
            assert recovered == old_plaintext


# ---------------------------------------------------------------------------
# Test 4: mixed-format rows all survive rotation
# ---------------------------------------------------------------------------

class TestRotateKeyHandlesMixedFormats:

    def test_enc_and_v1_and_plaintext_all_survive(self):
        """Law 277 zero-downtime: mixed enc::, v1:, and plaintext rows must
        all be handled correctly in a single rotation pass."""
        _reset_vault_singleton()
        vault = get_vault()

        enc_plain = "sk_enc_mixed_abc"
        v1_plain = "whsec_v1_mixed_xyz"
        plain_plain = "sk_plain_mixed_legacy"

        enc_val = _make_enc_value(enc_plain)
        v1_val = _make_vault_value(vault, v1_plain)

        with _isolated_db() as engine:
            with engine.connect() as conn:
                for pc, field, val in [
                    ("gateway_a", "secret_key", enc_val),
                    ("gateway_b", "webhook_secret", v1_val),
                    ("gateway_c", "secret_key", plain_plain),
                ]:
                    conn.execute(
                        text(f"INSERT INTO payment_gateway_connections "
                             f"(provider_code, gateway_name, {field}) "
                             f"VALUES (:pc, :gn, :val)"),
                        {"pc": pc, "gn": f"{pc} Mixed Test", "val": val},
                    )
                conn.commit()

            new_key = "mixed_format_rotation_key_777777777777777"
            result = rotate_key(new_master_key=new_key)
            assert result["status"] == "success", f"rotate_key failed: {result}"
            assert result["errors"] == [], f"Unexpected errors: {result['errors']}"

            new_vault = get_vault()

            with engine.connect() as conn:
                # enc:: row → now v1: with correct plaintext
                raw_a = conn.execute(
                    text("SELECT secret_key FROM payment_gateway_connections WHERE provider_code = 'gateway_a'"),
                ).scalar_one_or_none()
                assert raw_a is not None
                assert raw_a.startswith(_VAULT_PREFIX), (
                    f"enc:: row not rotated: {raw_a[:60]!r}"
                )
                assert new_vault.decrypt(raw_a) == enc_plain

                # v1: row → still v1: with correct plaintext
                raw_b = conn.execute(
                    text("SELECT webhook_secret FROM payment_gateway_connections WHERE provider_code = 'gateway_b'"),
                ).scalar_one_or_none()
                assert raw_b is not None
                assert raw_b.startswith(_VAULT_PREFIX), (
                    f"v1: row not rotated: {raw_b[:60]!r}"
                )
                assert new_vault.decrypt(raw_b) == v1_plain

                # plaintext row → still plaintext (untouched)
                raw_c = conn.execute(
                    text("SELECT secret_key FROM payment_gateway_connections WHERE provider_code = 'gateway_c'"),
                ).scalar_one_or_none()
                assert raw_c is not None
                assert raw_c == plain_plain, (
                    f"Plaintext row was mutated during rotation: {raw_c!r}"
                )


# ---------------------------------------------------------------------------
# Test 5: rotate_key fails closed when no new key is provided
# ---------------------------------------------------------------------------

class TestRotateKeyFailsClosedWithNoNewKey:

    def test_rotate_without_new_key_raises(self):
        _reset_vault_singleton()
        get_vault()  # initialise singleton
        # Unset the env var so the fallback also returns nothing
        old_env = os.environ.pop("ZOZI_VAULT_MASTER_KEY", None)
        try:
            with pytest.raises(VaultError):
                rotate_key(new_master_key=None)
        finally:
            if old_env is not None:
                os.environ["ZOZI_VAULT_MASTER_KEY"] = old_env


# ---------------------------------------------------------------------------
# Test 6: no secret value ever appears in a log or exception message
# ---------------------------------------------------------------------------

class TestNoSecretLeakInErrors:

    def test_encryption_error_does_not_contain_plaintext(self):
        """Error messages from rotate_key must never contain the secret value."""
        _reset_vault_singleton()
        vault = get_vault()
        secret = "super-secret-key-value-42"

        # Insert an enc:: value
        enc_val = _make_enc_value(secret)

        with _isolated_db() as engine:
            with engine.connect() as conn:
                conn.execute(
                    text("INSERT INTO payment_gateway_connections (provider_code, gateway_name, secret_key) "
                         "VALUES (:pc, :gn, :sk)"),
                    {"pc": "leak_test", "gn": "Leak Test", "sk": enc_val},
                )
                conn.commit()

            # Rotate with a new key — should succeed, but check error list is clean
            new_key = "no_leak_key_999999999999999999999999999"
            result = rotate_key(new_master_key=new_key)
            assert result["status"] == "success"

            # No error message may contain the plaintext secret
            for err in result.get("errors", []):
                assert secret not in err, (
                    f"Secret leaked in error message: {err!r}"
                )
