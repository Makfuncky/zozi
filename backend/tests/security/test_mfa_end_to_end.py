"""Paired regression test for P1 — MFA enrollment persists nothing end to end.

Law 283: TOTP for admin/employee. Store TOTP secrets encrypted (AES-256-GCM), not bcrypt-hashed.
TECH §5 pyotp: Store the TOTP secret encrypted (AES-256-GCM), never bcrypt-hashed.

The defect (before fix): setup_totp() calls setattr(user, "totp_secret", secret) on an
unmapped Python attribute — the secret is silently discarded and never reaches the database.

Strategy: Run tests in subprocesses with FIELD_ENCRYPTION_KEY set before imports.
Uses SQLAlchemy core insert() to create users (avoids declarative constructor issues
in subprocess contexts). Mocks `_aes256_gcm_encrypt` to prove the encryption path
is invoked when setup_totp persists the secret.
"""
from __future__ import annotations

import os
import sys
import subprocess
import textwrap

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_BACKEND_ROOT)

_TEST_SALT_HEX = "a" * 64
_TEST_ENC_KEY = "x" * 64


def _run_test_code(code: str) -> tuple[int, str, str]:
    """Run Python code in a subprocess with encryption env vars at import time."""
    env = {
        **os.environ,
        "FIELD_ENCRYPTION_SALT": _TEST_SALT_HEX,
        "FIELD_ENCRYPTION_KEY": _TEST_ENC_KEY,
        "APP_ENV": "test",
        "CSRF_DISABLED": "true",
        "SECRET_KEY": "test-secret-key-for-pytest-only-do-not-use-in-production",
    }
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


# Minimal boilerplate: set env vars FIRST, then import only what's needed.
# Avoids _preload_all_models() which triggers full app loading.
_SUBPROCESS_BOILERPLATE = r"""
import os as _os
_os.environ["FIELD_ENCRYPTION_SALT"] = "__SALT__"
_os.environ["FIELD_ENCRYPTION_KEY"] = "__KEY__"
_os.environ.setdefault("APP_ENV", "test")
_os.environ.setdefault("CSRF_DISABLED", "true")
_os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")

import sys
sys.path.insert(0, r"__PROJECT_ROOT__")

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from infrastructure.database.base import Base
_SCHEMAS = {t.schema for t in Base.metadata.tables.values() if t.schema}
_SCHEMA_TRANSLATE_MAP = {s: None for s in _SCHEMAS}


def _remove_broken_fk_tables(Base):
    for _pass in range(10):
        broken = set()
        existing = {t.name for t in Base.metadata.tables.values()}
        for table in list(Base.metadata.tables.values()):
            for fk in table.foreign_key_constraints:
                try:
                    target = fk.referred_table
                except Exception:
                    broken.add(table.fullname)
                    continue
                if target is None or target.name not in existing:
                    broken.add(table.fullname)
        if not broken:
            break
        for name in broken:
            try:
                Base.metadata.remove(Base.metadata.tables[name])
            except KeyError:
                pass


# Import models AFTER env vars are set so the full metadata is registered.
# Broken FK tables must be removed BEFORE create_all().
from domains.accounts.models.user import User  # noqa: F401
from domains.accounts.models.mfa_factor import MfaFactor  # noqa: F401
from domains.accounts.services.auth.auth_service import setup_totp  # noqa: F401
_remove_broken_fk_tables(Base)

engine = create_engine(
    "sqlite://",
    echo=False,
    execution_options={"schema_translate_map": _SCHEMA_TRANSLATE_MAP},
)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine)
""".replace("__SALT__", _TEST_SALT_HEX).replace("__KEY__", _TEST_ENC_KEY).replace("__PROJECT_ROOT__", _PROJECT_ROOT).replace("{{", "{").replace("}}", "}")


def _make_user(db, email: str, role: str = "admin") -> "User":
    """Create a user using SQLAlchemy core insert, bypassing any __init__ issues."""
    from sqlalchemy import insert
    from domains.accounts.models.user import User
    from infrastructure.utils.auth import get_password_hash
    result = db.execute(
        insert(User).values(
            email=email,
            hashed_password=get_password_hash("testpass123"),
            role=role,
            country_code="AE",
            is_active=True,
            email_verified=True,
        )
    )
    db.flush()
    user = db.query(User).filter(User.email == email).first()
    return user


class TestMfaEndToEnd:
    """Paired test: enrollment persists an encrypted TOTP secret and verification works."""

    def test_enrollment_persists_encrypted_secret_in_mfa_factor(self):
        """After setup_totp(), an MfaFactor record must exist.

        Proves encryption is invoked by mocking _aes256_gcm_encrypt (Law 283).
        """
        code = f"""
{_SUBPROCESS_BOILERPLATE}
from unittest import mock
from sqlalchemy import insert as sa_insert

# Import models AFTER boilerplate sets up engine
from domains.accounts.models.user import User
from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.services.auth.auth_service import setup_totp
from infrastructure.utils.auth import get_password_hash

db = Session()

# Create user via core insert (avoids __init__ constructor issues)
user = db.execute(
    sa_insert(User).values(
        email="mfa-mock@zozi.com",
        hashed_password=get_password_hash("testpass123"),
        role="admin",
        country_code="AE",
        is_active=True,
        email_verified=True,
    )
).inserted_primary_key[0]
db.flush()
user_obj = db.query(User).filter(User.email == "mfa-mock@zozi.com").first()
user_id = user_obj.id
print("USER_ID:", user_id)

current_user = {{"id": user_id, "role": "admin"}}

# Mock _aes256_gcm_encrypt to prove encryption is invoked on persist
with mock.patch(
    "infrastructure.security.encryption._aes256_gcm_encrypt",
    side_effect=lambda plaintext, key: f"enc::MOCKED{{plaintext[:8]}}",
) as mock_enc:
    result = setup_totp(current_user, db)
    db.commit()

print("ENCRYPT_CALL_COUNT:", mock_enc.call_count)
assert mock_enc.call_count >= 1, f"Expected >=1 encrypt call, got {{mock_enc.call_count}}"

# Verify MfaFactor was created
factors = db.query(MfaFactor).filter(
    MfaFactor.user_id == user_id,
    MfaFactor.factor_type == "TOTP",
).all()
print("FACTOR_COUNT:", len(factors))
assert len(factors) == 1, f"Expected 1 MfaFactor, got {{len(factors)}}"

f = factors[0]
print("ENABLED:", f.enabled)
assert f.enabled == False
print("PERSISTED_AND_ENCRYPTED: OK")
db.close()
"""
        rc, out, err = _run_test_code(code)
        print("STDOUT:", out)
        print("STDERR:", err[:1000] if err else "")
        print("RC:", rc)
        assert rc == 0, f"Subprocess failed: rc={rc}\n{err}"
        assert "PERSISTED_AND_ENCRYPTED: OK" in out, f"MFA must persist and encrypt: {out}"

    def test_valid_totp_code_verifies_after_enrollment(self):
        """A valid TOTP code must verify via enable_totp."""
        code = f"""
{_SUBPROCESS_BOILERPLATE}
import pyotp
from sqlalchemy import insert as sa_insert
from domains.accounts.models.user import User
from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.services.auth.auth_service import setup_totp, enable_totp
from infrastructure.utils.auth import get_password_hash
from infrastructure.security.encryption import field_encryptor

db = Session()

user = db.query(User).filter(User.email == "mfa-verify-diag@zozi.com").first()
if not user:
    user = db.execute(
        sa_insert(User).values(
            email="mfa-verify-diag@zozi.com",
            hashed_password=get_password_hash("testpass123"),
            role="admin",
            country_code="AE",
            is_active=True,
            email_verified=True,
        )
    ).inserted_primary_key[0]
    db.flush()
    user = db.query(User).filter(User.email == "mfa-verify-diag@zozi.com").first()

current_user = {{"id": user.id, "role": "admin"}}
setup_result = setup_totp(current_user, db)
db.commit()

factor = db.query(MfaFactor).filter(
    MfaFactor.user_id == user.id,
    MfaFactor.factor_type == "TOTP",
).first()
assert factor is not None, "No MfaFactor found"

stored_secret = field_encryptor.decrypt(getattr(factor, "secret"))
print("STORED_SECRET_DECRYPTED:", stored_secret)
assert stored_secret == setup_result.get("secret", ""), "Decrypted secret must match"

totp = pyotp.TOTP(stored_secret)
valid_code = totp.now()
print("VALID_CODE:", valid_code)

enable_result = enable_totp(current_user, db, valid_code)
db.commit()
print("ENABLE_RESULT:", enable_result.get("detail", ""))

factor_after = db.query(MfaFactor).filter(
    MfaFactor.user_id == user.id,
    MfaFactor.factor_type == "TOTP",
).first()
print("FACTOR_ENABLED:", factor_after.enabled)
print("RECOVERY_CODES:", len(enable_result.get("recovery_codes", [])))
db.close()
"""
        rc, out, err = _run_test_code(code)
        print("STDOUT:", out)
        print("STDERR:", err[:1000] if err else "")
        print("RC:", rc)
        assert rc == 0, f"Subprocess failed: rc={rc}\n{err}"
        assert "FACTOR_ENABLED: True" in out, f"MfaFactor should be enabled: {out}"
        assert "RECOVERY_CODES: 8" in out, f"8 recovery codes expected: {out}"

    def test_invalid_totp_code_is_rejected(self):
        """An invalid TOTP code must raise HTTPException 400."""
        code = f"""
{_SUBPROCESS_BOILERPLATE}
from sqlalchemy import insert as sa_insert
from domains.accounts.models.user import User
from domains.accounts.services.auth.auth_service import setup_totp, enable_totp
from fastapi import HTTPException
from infrastructure.utils.auth import get_password_hash

db = Session()

user = db.query(User).filter(User.email == "mfa-invalid-diag@zozi.com").first()
if not user:
    user = db.execute(
        sa_insert(User).values(
            email="mfa-invalid-diag@zozi.com",
            hashed_password=get_password_hash("testpass123"),
            role="admin",
            country_code="AE",
            is_active=True,
            email_verified=True,
        )
    ).inserted_primary_key[0]
    db.flush()
    user = db.query(User).filter(User.email == "mfa-invalid-diag@zozi.com").first()

current_user = {{"id": user.id, "role": "admin"}}
setup_totp(current_user, db)
db.commit()

try:
    enable_totp(current_user, db, "000000")
    print("RESULT: NOT_REJECTED")
except HTTPException as e:
    print("RESULT: REJECTED status_code=", e.status_code, "detail=", e.detail)
db.close()
"""
        rc, out, err = _run_test_code(code)
        print("STDOUT:", out)
        print("STDERR:", err[:1000] if err else "")
        print("RC:", rc)
        assert rc == 0, f"Subprocess failed: rc={rc}\n{err}"
        assert "RESULT: REJECTED" in out, f"Invalid code should be rejected: {out}"
        assert "400" in out, f"Expected 400 status code: {out}"

    def test_secret_never_returned_in_get_totp_status(self):
        """get_totp_status must not include the raw TOTP secret."""
        code = f"""
{_SUBPROCESS_BOILERPLATE}
from sqlalchemy import insert as sa_insert
from domains.accounts.models.user import User
from domains.accounts.models.mfa_factor import MfaFactor
from domains.accounts.services.auth.auth_service import setup_totp, get_totp_status
from infrastructure.utils.auth import get_password_hash

db = Session()

user = db.query(User).filter(User.email == "mfa-leak-diag@zozi.com").first()
if not user:
    user = db.execute(
        sa_insert(User).values(
            email="mfa-leak-diag@zozi.com",
            hashed_password=get_password_hash("testpass123"),
            role="admin",
            country_code="AE",
            is_active=True,
            email_verified=True,
        )
    ).inserted_primary_key[0]
    db.flush()
    user = db.query(User).filter(User.email == "mfa-leak-diag@zozi.com").first()

current_user = {{"id": user.id, "role": "admin"}}
setup_result = setup_totp(current_user, db)
db.commit()
raw_secret = setup_result.get("secret", "")
print("RAW_SECRET_SETUP:", bool(raw_secret))

status = get_totp_status(current_user, db)
print("STATUS:", status)
assert "secret" not in str(status).lower()
assert "totp_secret" not in str(status).lower()
print("NO_LEAK: OK")
db.close()
"""
        rc, out, err = _run_test_code(code)
        print("STDOUT:", out)
        print("STDERR:", err[:1000] if err else "")
        print("RC:", rc)
        assert rc == 0, f"Subprocess failed: rc={rc}\n{err}"
        assert "NO_LEAK: OK" in out, f"Secret must not leak: {out}"
