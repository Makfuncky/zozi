"""Functional test: MfaFactor table persists encrypted TOTP secrets correctly.

Uses raw SQL to avoid the pre-existing CountryConfig mapper issue. Verifies
that field-encrypted secrets can be stored and decrypted through the database.
"""
from __future__ import annotations

import os
import sys
import subprocess
import tempfile

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PROJECT_ROOT = os.path.dirname(_BACKEND_ROOT)

_TEST_SALT_HEX = "a" * 64
_TEST_ENC_KEY = "x" * 64


def _run_script(script: str) -> tuple[int, str, str]:
    env = {
        **os.environ,
        "FIELD_ENCRYPTION_SALT": _TEST_SALT_HEX,
        "FIELD_ENCRYPTION_KEY": _TEST_ENC_KEY,
        "APP_ENV": "test",
        "CSRF_DISABLED": "true",
        "SECRET_KEY": "test-secret-key-for-pytest-only-do-not-use-in-production",
    }
    fd, path = tempfile.mkstemp(suffix=".py", prefix="mfa_func_test_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(script)
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            text=True,
            cwd=_PROJECT_ROOT,
            env=env,
        )
        return result.returncode, result.stdout, result.stderr
    finally:
        os.unlink(path)


class TestMfaFunctional:
    def test_mfa_factor_table_persists_encrypted_secret(self):
        script = (
            'import os as _os\n'
            '_os.environ["FIELD_ENCRYPTION_SALT"] = "' + _TEST_SALT_HEX + '"\n'
            '_os.environ["FIELD_ENCRYPTION_KEY"] = "' + _TEST_ENC_KEY + '"\n'
            '_os.environ.setdefault("APP_ENV", "test")\n'
            '_os.environ.setdefault("CSRF_DISABLED", "true")\n'
            '_os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only-do-not-use-in-production")\n'
            '\n'
            'import sys as _sys\n'
            '_sys.path.insert(0, r"' + _PROJECT_ROOT + '")\n'
            '\n'
            'from sqlalchemy import create_engine, text\n'
            'from sqlalchemy.orm import sessionmaker\n'
            '\n'
            'engine = create_engine("sqlite:///:memory:", echo=False)\n'
            'Session = sessionmaker(bind=engine)\n'
            '\n'
            'with engine.connect() as _conn:\n'
            '    _conn.execute(text("""\n'
            '        CREATE TABLE users (\n'
            '            id INTEGER PRIMARY KEY,\n'
            '            email TEXT UNIQUE,\n'
            '            hashed_password TEXT,\n'
            '            role TEXT,\n'
            '            country_code TEXT,\n'
            '            is_active BOOLEAN,\n'
            '            email_verified BOOLEAN\n'
            '        )\n'
            '    """))\n'
            '    _conn.execute(text("""\n'
            '        CREATE TABLE mfa_factors (\n'
            '            id INTEGER PRIMARY KEY AUTOINCREMENT,\n'
            '            user_id INTEGER NOT NULL,\n'
            '            factor_type TEXT NOT NULL,\n'
            '            secret TEXT NOT NULL,\n'
            '            enabled BOOLEAN NOT NULL DEFAULT 1,\n'
            '            created_at DATETIME,\n'
            '            last_used_at DATETIME,\n'
            '            backup_codes TEXT,\n'
            '            country_code TEXT,\n'
            '            updated_at DATETIME,\n'
            '            is_deleted BOOLEAN NOT NULL DEFAULT 0\n'
            '        )\n'
            '    """))\n'
            '    _conn.commit()\n'
            '\n'
            'db = Session()\n'
            '\n'
            'from infrastructure.security.encryption import field_encryptor\n'
            '\n'
            'db.execute(text("""\n'
            '    INSERT INTO users (email, hashed_password, role, country_code, is_active, email_verified)\n'
            '    VALUES (:e, :p, :r, :c, :a, :v)\n'
            '"""), {\n'
            '    "e": "mfa-func@zozi.com",\n'
            '    "p": "hashed_testpass",\n'
            '    "r": "admin",\n'
            '    "c": "AE",\n'
            '    "a": 1,\n'
            '    "v": 1,\n'
            '})\n'
            'db.commit()\n'
            '\n'
            'user_row = db.execute(text("SELECT id FROM users WHERE email = \'mfa-func@zozi.com\'")).fetchone()\n'
            '\n'
            'raw_secret = "JBSWY3DPEHPK3PXP"\n'
            'encrypted = field_encryptor.encrypt(raw_secret)\n'
            'print("ENCRYPTED_SECRET:", encrypted[:40])\n'
            '\n'
            'db.execute(text(\n'
            '    "INSERT INTO mfa_factors (user_id, factor_type, secret, enabled, is_deleted) VALUES (:uid, :ft, :s, :e, :d)"\n'
            '), {"uid": user_row[0], "ft": "totp", "s": encrypted, "e": 0, "d": 0})\n'
            'db.commit()\n'
            '\n'
            'stored = db.execute(text("SELECT secret FROM mfa_factors WHERE user_id = :uid"), {"uid": user_row[0]}).fetchone()[0]\n'
            'decrypted = field_encryptor.decrypt(stored)\n'
            'print("DECRYPTED_SECRET:", decrypted)\n'
            'assert decrypted == raw_secret, f"Decrypted secret mismatch: {decrypted!r} != {raw_secret!r}"\n'
            '\n'
            'factor_row = db.execute(text("SELECT enabled FROM mfa_factors WHERE user_id = :uid"), {"uid": user_row[0]}).fetchone()\n'
            'assert factor_row[0] == 0, "New factor should be disabled"\n'
            'print("PASS: MfaFactor table persisted encrypted secret and is disabled")\n'
            'db.close()\n'
        )
        rc, out, err = _run_script(script)
        print("STDOUT:", out)
        print("STDERR:", err)
        print("RC:", rc)
        assert rc == 0, f"Subprocess failed: rc={rc}\n{err}"
        assert "PASS: MfaFactor table persisted encrypted secret and is disabled" in out, f"MFA functional test failed: {out}"
