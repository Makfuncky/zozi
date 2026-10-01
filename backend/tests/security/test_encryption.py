"""Regression tests for infrastructure.security.encryption (FILE-115).

Verifies:
  - FIELD_ENCRYPTION_SALT is mandatory — absent salt raises RuntimeError
    (tested via subprocess because the module computes _KDF_SALT at import
    time and the main test process already has a valid salt set by conftest)
  - AES-256-GCM round-trip: encrypt then decrypt returns the original value
  - AES-256-GCM ciphertext is non-deterministic (random nonce per call)
  - EncryptedString TypeDecorator delegates encryption to FieldEncryptor
  - decrypt_secret dispatches on prefix (v1: vault, enc:: field encryptor)
"""
from __future__ import annotations

import os
import sys
import subprocess
import textwrap

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

_TEST_SALT_HEX = "a" * 64
_PROJECT_ROOT = os.path.dirname(_BACKEND_ROOT)


def _run_subprocess(code: str, *, salt: str | None = None,
                    extra_env: dict | None = None) -> tuple[int, str, str]:
    """Run a Python snippet in a subprocess with a controlled environment."""
    env = {**os.environ}
    if salt is not None:
        env["FIELD_ENCRYPTION_SALT"] = salt
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        cwd=_PROJECT_ROOT,
        env=env,
    )
    return result.returncode, result.stdout, result.stderr


# ---------------------------------------------------------------------------
# Mandatory salt — must be present and ≥ 32 hex chars
# ---------------------------------------------------------------------------

class TestFieldEncryptionSaltRequired:

    def test_missing_salt_raises_runtime_error(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ.pop("FIELD_ENCRYPTION_SALT", None)
        try:
            import infrastructure.security.encryption as enc
        except RuntimeError as e:
            print("OK:", str(e))
        else:
            print("FAIL: no RuntimeError raised")
            sys.exit(1)
        """
        rc, out, err = _run_subprocess(code, salt=None)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "FIELD_ENCRYPTION_SALT must be set" in out

    def test_short_salt_raises_runtime_error(self):
        code = """
        import sys, os
        sys.path.insert(0, r"__PROJECT_ROOT__")
        os.environ["FIELD_ENCRYPTION_SALT"] = "abcd"
        try:
            import infrastructure.security.encryption as enc
        except RuntimeError as e:
            print("OK:", str(e))
        else:
            print("FAIL: no RuntimeError raised")
            sys.exit(1)
        """.replace("__PROJECT_ROOT__", repr(_PROJECT_ROOT))
        rc, out, err = _run_subprocess(code, salt="abcd")
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "at least 32 hex characters" in out

    def test_valid_salt_loads_as_32_bytes(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        import infrastructure.security.encryption as enc
        assert len(enc._KDF_SALT) == 32, f"expected 32, got {{len(enc._KDF_SALT)}}"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_salt_required_missing_raises_runtime_error(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ.pop("FIELD_ENCRYPTION_SALT", None)
        try:
            import infrastructure.security.encryption as enc
        except RuntimeError as e:
            assert "FIELD_ENCRYPTION_SALT" in str(e), f"unexpected message: {{e}}"
            print("OK")
        else:
            print("FAIL: no RuntimeError raised")
            sys.exit(1)
        """
        rc, out, err = _run_subprocess(code, salt=None)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_salt_required_non_hex_raises_runtime_error(self):
        code = """
        import sys, os
        sys.path.insert(0, r"__PROJECT_ROOT__")
        os.environ["FIELD_ENCRYPTION_SALT"] = "notahexstringbutlongenoughtopasslengthcheck12345"
        try:
            import infrastructure.security.encryption as enc
        except RuntimeError as e:
            assert "hex string" in str(e), f"unexpected message: {{e}}"
            print("OK")
        else:
            print("FAIL: no RuntimeError raised")
            sys.exit(1)
        """.replace("__PROJECT_ROOT__", repr(_PROJECT_ROOT))
        rc, out, err = _run_subprocess(code, salt="notahexstringbutlongenoughtopasslengthcheck12345")
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out


# ---------------------------------------------------------------------------
# AES-256-GCM encrypt / decrypt round-trip
# ---------------------------------------------------------------------------

class TestAes256GcmRoundTrip:

    def test_encrypt_produces_enc_prefix(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import field_encryptor, _ENCRYPTED_PREFIX
        result = field_encryptor.encrypt("hello-world")
        assert isinstance(result, str)
        assert result.startswith(_ENCRYPTED_PREFIX), f"missing prefix: {{result}}"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_encrypt_then_decrypt_round_trip(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import field_encryptor
        plaintext = "PII-data-12345"
        token = field_encryptor.encrypt(plaintext)
        recovered = field_encryptor.decrypt(token)
        assert recovered == plaintext, f"{{recovered!r}} != {{plaintext!r}}"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_gcm_nonce_randomises_ciphertext(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import field_encryptor
        t1 = field_encryptor.encrypt("same-plaintext")
        t2 = field_encryptor.encrypt("same-plaintext")
        assert t1 != t2, "GCM nonce must randomise ciphertext"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_decrypt_non_encrypted_passthrough(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import field_encryptor
        assert field_encryptor is not None
        assert field_encryptor.decrypt("plain-no-prefix") == "plain-no-prefix"
        assert field_encryptor.decrypt(None) is None
        assert field_encryptor.decrypt("") == ""
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out


# ---------------------------------------------------------------------------
# EncryptedString SQLAlchemy TypeDecorator
# ---------------------------------------------------------------------------

class TestEncryptedStringColumn:

    def test_process_bind_param_encrypts(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import EncryptedString, _ENCRYPTED_PREFIX
        col = EncryptedString(length=255)
        result = col.process_bind_param("secret-value", dialect=None)
        assert isinstance(result, str)
        assert result.startswith(_ENCRYPTED_PREFIX), f"missing prefix: {{result}}"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_process_result_value_decrypts(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import EncryptedString, field_encryptor
        col = EncryptedString(length=255)
        encrypted = field_encryptor.encrypt("round-trip-value")
        result = col.process_result_value(encrypted, dialect=None)
        assert result == "round-trip-value", f"{{result!r}}"
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out


# ---------------------------------------------------------------------------
# decrypt_secret prefix dispatch
# ---------------------------------------------------------------------------

class TestDecryptSecret:

    def test_none_and_empty_passthrough(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        from infrastructure.security.encryption import decrypt_secret
        assert decrypt_secret(None) is None
        assert decrypt_secret("") == ""
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out

    def test_enc_prefix_decrypts_via_field_encryptor(self):
        code = f"""
        import sys, os
        sys.path.insert(0, r"{_PROJECT_ROOT}")
        os.environ["FIELD_ENCRYPTION_SALT"] = "{_TEST_SALT_HEX}"
        os.environ["FIELD_ENCRYPTION_KEY"] = "x" * 64
        from infrastructure.security.encryption import decrypt_secret, field_encryptor
        token = field_encryptor.encrypt("field-secret")
        assert decrypt_secret(token) == "field-secret", decrypt_secret(token)
        print("OK")
        """
        rc, out, err = _run_subprocess(code)
        assert rc == 0, f"stdout={out!r} stderr={err!r}"
        assert "OK" in out
