"""SEC2-027 — Law 277 key-rotation enforcement and the zero-downtime guarantee.

The absolute constraint this file exists to protect: **existing ciphertext must
remain decryptable after a rotation.** A rotation that invalidates old data is a
data-loss incident, not a security improvement.

What is locked in:

  1. ``_KDF_ITERATIONS`` is never reduced. The KDF cost is asserted by value,
     because lowering it is the tempting way to "speed up" a rotation and it
     silently weakens every ciphertext ever written.
  2. encrypt(A) -> rotate(A, B) -> decrypt still returns the original plaintext,
     including for rows the migration did NOT reach and for a value written
     under the old key *during* the rotation window.
  3. The 90-day deadline is computed and signalled, not merely documented.
  4. Nothing written to disk or to a log is key material — only one-way
     fingerprints and timestamps (Law 32, Law 282).

Tests that need a specific ``FIELD_ENCRYPTION_KEY`` run in a subprocess so they
cannot leak a key into the ambient test session. Every policy test passes an
explicit ``state_path`` into ``tmp_path``, so nothing writes to the
application-wide rotation sidecar.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

_SALT_HEX = "a" * 64
_KEY_A = "A" * 64
_KEY_B = "b" * 64


def _run(body: str, *, key: str = _KEY_A) -> tuple[int, str, str]:
    """Execute a snippet in a subprocess with a controlled key + salt."""
    env = {
        **os.environ,
        "FIELD_ENCRYPTION_SALT": _SALT_HEX,
        "FIELD_ENCRYPTION_KEY": key,
    }
    code = f"import sys\nsys.path.insert(0, {str(_BACKEND_ROOT)!r})\n" + textwrap.dedent(body)
    proc = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=str(_BACKEND_ROOT),
        env=env,
    )
    return proc.returncode, proc.stdout, proc.stderr


# ---------------------------------------------------------------------------
# 1. The KDF cost is never reduced  (contract section 3, item 1)
# ---------------------------------------------------------------------------

def test_kdf_iterations_unchanged():
    """_KDF_ITERATIONS must still be 600_000."""
    rc, out, err = _run(
        """
        import infrastructure.security.encryption as enc
        print("KDF", enc._KDF_ITERATIONS)
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "KDF 600000" in out, (
        f"Law 277 / contract s3: the KDF work factor must not be reduced. Got: {out!r}"
    )


def test_derivation_uses_the_module_constant():
    """PBKDF2 must read _KDF_ITERATIONS, and the cost must have ONE source."""
    source = (
        _BACKEND_ROOT / "infrastructure" / "security" / "encryption.py"
    ).read_text(encoding="utf-8")
    assert "iterations=_KDF_ITERATIONS" in source, (
        "PBKDF2HMAC must take the module constant so the cost has one source of truth"
    )
    assert source.count("600_000") == 1, (
        "the KDF cost must appear exactly once, as the named constant"
    )


# ---------------------------------------------------------------------------
# 2. encrypt -> rotate -> decrypt  (the absolute constraint)
# ---------------------------------------------------------------------------

def test_encrypt_rotate_decrypt_returns_original_plaintext():
    """Values encrypted under key A must still decrypt after rotating to key B.

    Three rows are simulated, mirroring what a real migration actually sees:
      * row 1 is re-encrypted by the rotation,
      * row 2 the migration FAILED to reach (the `partial` case),
      * row 3 was written under the old key *during* the rotation window.
    All three must come back as the original plaintext under the new keyring.
    """
    rc, out, err = _run(
        f"""
        from infrastructure.security.encryption import (
            FieldEncryptor, register_previous_field_encryption_key,
        )

        KEY_A = {_KEY_A!r}
        KEY_B = {_KEY_B!r}
        SECRETS = [
            "4111111111111111",          # card-like
            "GB29NWBK60161331926819",    # IBAN-like
            "OM1234567890",              # local account number
        ]

        # --- before the rotation: everything is written under key A ------------
        old = FieldEncryptor(KEY_A)
        ciphertexts = [old.encrypt(s) for s in SECRETS]
        assert all(c.startswith("enc::") for c in ciphertexts), ciphertexts

        # --- Law 277: the outgoing key joins the DECRYPTION keyring FIRST -----
        n = register_previous_field_encryption_key(KEY_A)
        assert n >= 1, "the previous key must be registered before any row is rewritten"

        # --- the new configuration --------------------------------------------
        new = FieldEncryptor(KEY_B, fallback_keys=[KEY_A])

        row1 = new.encrypt(old.decrypt(ciphertexts[0]))  # migrated
        row2 = ciphertexts[1]                             # migration missed it
        row3 = old.encrypt(SECRETS[2])                     # written mid-window

        assert new.decrypt(row1) == SECRETS[0], "migrated row lost its plaintext"
        assert new.decrypt(row2) == SECRETS[1], (
            "UNMIGRATED ROW BECAME UNREADABLE - this is the data-loss incident "
            "the zero-downtime guarantee exists to prevent"
        )
        assert new.decrypt(row3) == SECRETS[2], (
            "a value written under the old key during the window must stay readable"
        )

        # the retired key must NOT be able to read a newly written row
        assert old.decrypt(row1) == row1, (
            "a new row must not be readable by the retired key"
        )
        print("OK")
        """,
        key=_KEY_B,
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


def test_single_key_behaviour_is_unchanged():
    """With no fallback keys the encryptor behaves exactly as it did before."""
    rc, out, err = _run(
        f"""
        from infrastructure.security.encryption import FieldEncryptor
        enc = FieldEncryptor({_KEY_A!r})
        assert enc.fallback_key_count() == 0
        token = enc.encrypt("PII-12345")
        assert enc.decrypt(token) == "PII-12345"
        # passthroughs preserved
        assert enc.decrypt(None) is None
        assert enc.decrypt("") == ""
        assert enc.decrypt("plain") == "plain"
        assert enc.decrypt(12345) == 12345
        # an unreadable token still returns the raw value (unchanged fallback)
        assert enc.decrypt("enc::not-a-real-token") == "enc::not-a-real-token"
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


def test_fallback_keys_are_for_decryption_only():
    """New writes always use the primary key; fallbacks never encrypt."""
    rc, out, err = _run(
        f"""
        from infrastructure.security.encryption import FieldEncryptor
        plain = FieldEncryptor({_KEY_A!r})
        ringed = FieldEncryptor({_KEY_B!r}, fallback_keys=[{_KEY_A!r}])
        value = "same-plaintext"
        # a fallback key can read a primary-key value
        assert ringed.decrypt(plain.encrypt(value)) == value
        # but a key that is NOT in the ring cannot
        stranger = FieldEncryptor("z" * 64)
        assert ringed.decrypt(stranger.encrypt(value)) != value, (
            "the ringed encryptor must not decrypt with a key outside its keyring"
        )
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


def test_fallback_keyring_is_idempotent():
    rc, out, err = _run(
        f"""
        from infrastructure.security.encryption import FieldEncryptor
        enc = FieldEncryptor({_KEY_A!r})
        enc.add_fallback_key({_KEY_B!r})
        enc.add_fallback_key({_KEY_B!r})
        assert enc.fallback_key_count() == 1, enc.fallback_key_count()
        enc.set_fallback_keys([{_KEY_B!r}, {_KEY_B!r}])
        assert enc.fallback_key_count() == 1
        enc.set_fallback_keys([])
        assert enc.fallback_key_count() == 0
        enc.add_fallback_key("")
        assert enc.fallback_key_count() == 0
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


def test_register_previous_key_widens_the_live_keyring():
    """The live singleton must actually gain the key, not just report it."""
    rc, out, err = _run(
        f"""
        import infrastructure.security.encryption as enc
        from infrastructure.security.encryption import register_previous_field_encryption_key
        before = enc.field_encryptor.fallback_key_count()
        n = register_previous_field_encryption_key({_KEY_B!r})
        assert n == before + 1, (n, before)
        assert enc.field_encryptor.fallback_key_count() == n
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


# ---------------------------------------------------------------------------
# 3. Law 277 enforcement — the 90-day deadline
# ---------------------------------------------------------------------------

def test_interval_is_the_law_value():
    rc, out, err = _run(
        """
        from infrastructure.security.encryption import (
            KEY_ROTATION_INTERVAL_DAYS, KEY_ROTATION_WARN_THRESHOLD_DAYS,
        )
        print("INTERVAL", KEY_ROTATION_INTERVAL_DAYS)
        print("WARN", KEY_ROTATION_WARN_THRESHOLD_DAYS)
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "INTERVAL 90" in out, "Law 277 states 'Every 90 days'"
    assert "WARN 75" in out, "the warn window must precede the deadline"


@pytest.fixture()
def policy(tmp_path):
    """The rotation policy module plus a private, throwaway state file."""
    import infrastructure.security.encryption as enc

    enc._MEMORY_KEY_ROTATION_STATE.clear()
    return enc, tmp_path / "rotation.json"


def test_unknown_when_nothing_recorded(policy):
    enc, state_file = policy
    state = enc.get_key_rotation_state(state_path=state_file)
    assert state["status"] == enc.KEY_ROTATION_STATUS_UNKNOWN, (
        "with no recorded rotation the policy must be UNKNOWN, never 'ok' - an "
        "unverifiable rotation policy is not a satisfied one"
    )
    assert state["age_days"] is None
    assert state["overdue"] is False


def test_rotation_state_round_trip(policy):
    enc, state_file = policy
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    enc.record_key_rotation(rotated_at=now, state_path=state_file)

    persisted = json.loads(state_file.read_text(encoding="utf-8"))
    assert persisted["rotated_at"].startswith("2026-10-06T12:00:00")
    assert persisted["interval_days"] == enc.KEY_ROTATION_INTERVAL_DAYS

    fresh = enc.get_key_rotation_state(now=now, state_path=state_file)
    assert fresh["status"] == enc.KEY_ROTATION_STATUS_OK
    assert fresh["age_days"] == 0
    assert fresh["days_until_due"] == enc.KEY_ROTATION_INTERVAL_DAYS
    assert fresh["overdue"] is False


@pytest.mark.parametrize(
    "days_ago,expected_status,expected_overdue",
    [
        (0, "ok", False),
        (10, "ok", False),
        (74, "ok", False),
        (75, "due_soon", False),    # the warn threshold: 15 days left
        (89, "due_soon", False),
        (90, "overdue", True),      # the deadline day itself is already overdue
        (91, "overdue", True),
        (365, "overdue", True),
    ],
)
def test_ninety_day_deadline_is_computed(policy, days_ago, expected_status, expected_overdue):
    enc, state_file = policy
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    enc.record_key_rotation(rotated_at=now - timedelta(days=days_ago), state_path=state_file)

    state = enc.get_key_rotation_state(now=now, state_path=state_file)

    assert state["status"] == expected_status, state
    assert state["overdue"] is expected_overdue, state
    assert state["age_days"] == days_ago, state
    assert state["days_until_due"] == enc.KEY_ROTATION_INTERVAL_DAYS - days_ago, state


def test_check_key_rotation_signals_overdue(policy, caplog):
    enc, state_file = policy
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    enc.record_key_rotation(rotated_at=now - timedelta(days=200), state_path=state_file)

    with caplog.at_level(logging.DEBUG, logger="infrastructure.security.encryption"):
        state = enc.check_key_rotation(now=now, state_path=state_file)

    assert state["overdue"] is True
    assert state["days_until_due"] == -110
    assert "field_encryption_key_rotation_overdue" in caplog.text, (
        "an overdue key must produce a CRITICAL operational signal, not silence"
    )
    assert any(r.levelno >= logging.CRITICAL for r in caplog.records)


def test_check_key_rotation_warns_when_due_soon(policy, caplog):
    enc, state_file = policy
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    enc.record_key_rotation(rotated_at=now - timedelta(days=80), state_path=state_file)

    with caplog.at_level(logging.DEBUG, logger="infrastructure.security.encryption"):
        state = enc.check_key_rotation(now=now, state_path=state_file)

    assert state["status"] == enc.KEY_ROTATION_STATUS_DUE_SOON
    assert "field_encryption_key_rotation_due" in caplog.text
    assert any(r.levelno >= logging.WARNING for r in caplog.records)


def test_check_key_rotation_warns_when_age_unknown(policy, caplog):
    enc, state_file = policy
    with caplog.at_level(logging.DEBUG, logger="infrastructure.security.encryption"):
        state = enc.check_key_rotation(state_path=state_file)

    assert state["status"] == enc.KEY_ROTATION_STATUS_UNKNOWN
    assert "field_encryption_key_rotation_age_unknown" in caplog.text


def test_check_key_rotation_is_silent_when_fresh(policy, caplog):
    enc, state_file = policy
    enc.record_key_rotation(state_path=state_file)
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger="infrastructure.security.encryption"):
        state = enc.check_key_rotation(state_path=state_file)

    assert state["status"] == enc.KEY_ROTATION_STATUS_OK
    assert "rotation_overdue" not in caplog.text
    assert "rotation_age_unknown" not in caplog.text
    assert "rotation_due" not in caplog.text


def test_corrupt_state_file_degrades_to_unknown(policy, caplog):
    enc, state_file = policy
    state_file.write_text("{not json at all", encoding="utf-8")
    with caplog.at_level(logging.DEBUG, logger="infrastructure.security.encryption"):
        state = enc.get_key_rotation_state(state_path=state_file)

    assert state["status"] == enc.KEY_ROTATION_STATUS_UNKNOWN
    assert "unreadable" in caplog.text, (
        "a corrupt sidecar must be reported (Law 59), not silently ignored"
    )


def test_unwritable_state_path_never_raises(policy, tmp_path):
    """A rotation must not fail because its bookkeeping could not be written."""
    enc, _ = policy
    blocker = tmp_path / "blocker"
    blocker.write_text("this is a file, not a directory", encoding="utf-8")

    state = enc.record_key_rotation(state_path=blocker / "nested" / "state.json")

    assert state["rotated_at"], "state must still be returned from memory"


# ---------------------------------------------------------------------------
# 4. No key material is ever persisted or logged  (Law 32, Law 282)
# ---------------------------------------------------------------------------

def test_state_file_contains_no_key_material(policy):
    enc, state_file = policy
    enc.record_key_rotation(state_path=state_file)
    raw = state_file.read_text(encoding="utf-8")

    for secret in (_KEY_A, _KEY_B, _SALT_HEX):
        assert secret not in raw, (
            f"key material leaked into the rotation state file ({secret[:6]}...)"
        )

    parsed = json.loads(raw)
    assert set(parsed) == {
        "rotated_at", "interval_days", "key_fingerprint", "fallback_fingerprints",
    }
    fp = parsed["key_fingerprint"]
    assert fp == "" or (len(fp) == 16 and all(c in "0123456789abcdef" for c in fp))


def test_overdue_log_contains_no_key_material(policy, caplog):
    enc, state_file = policy
    now = datetime(2026, 10, 6, 12, 0, tzinfo=timezone.utc)
    enc.record_key_rotation(rotated_at=now - timedelta(days=400), state_path=state_file)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        enc.check_key_rotation(now=now, state_path=state_file)

    for secret in (_KEY_A, _KEY_B, _SALT_HEX):
        assert secret not in caplog.text, "key material leaked into a log record"


def test_fingerprint_is_one_way_and_stable():
    rc, out, err = _run(
        f"""
        from infrastructure.security.encryption import FieldEncryptor
        a = FieldEncryptor({_KEY_A!r}).primary_key_fingerprint()
        b = FieldEncryptor({_KEY_A!r}).primary_key_fingerprint()
        c = FieldEncryptor({_KEY_B!r}).primary_key_fingerprint()
        print("STABLE", a == b)
        print("DIFFERENT", a != c)
        print("LEN", len(a))
        print("HEX", all(x in "0123456789abcdef" for x in a))
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "STABLE True" in out
    assert "DIFFERENT True" in out
    assert "LEN 16" in out
    assert "HEX True" in out


# ---------------------------------------------------------------------------
# 5. Module wiring (Law 1 / Law 102)
# ---------------------------------------------------------------------------

def test_key_rotation_module_exposes_the_policy():
    rc, out, err = _run(
        """
        import infrastructure.security.key_rotation as k
        import infrastructure.security.encryption as e
        import infrastructure.utils.encryption as legacy
        assert k.KEY_ROTATION_INTERVAL_DAYS == e.KEY_ROTATION_INTERVAL_DAYS == 90
        assert k.FieldEncryptor is e.FieldEncryptor is legacy.FieldEncryptor
        for name in ("get_key_rotation_state", "check_key_rotation",
                     "key_rotation_health", "record_key_rotation",
                     "register_previous_field_encryption_key"):
            assert hasattr(k, name), name
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out


def test_key_rotation_module_imports_nothing_above_infrastructure():
    """Law 1 / Law 102: no domain, module, rbac, jobs or provider imports."""
    import ast

    tree = ast.parse(
        (_BACKEND_ROOT / "infrastructure" / "security" / "key_rotation.py")
        .read_text(encoding="utf-8")
    )
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            roots.add((node.module or "").split(".")[0])
    forbidden = roots & {"domains", "modules", "rbac", "jobs", "middleware", "providers"}
    assert not forbidden, f"Law 1 violation: key_rotation.py imports {forbidden}"


def test_rotation_refuses_degenerate_arguments():
    """A rotation that cannot be correct must fail loudly, not silently no-op."""
    rc, out, err = _run(
        f"""
        import infrastructure.security.key_rotation as k
        for args in (("", {_KEY_B!r}), ({_KEY_A!r}, ""), ({_KEY_A!r}, {_KEY_A!r})):
            try:
                k.rotate_encryption_key(args[0], args[1], None)
            except ValueError:
                continue
            raise AssertionError("expected ValueError for " + repr(args))
        print("OK")
        """
    )
    assert rc == 0, f"stdout={out!r} stderr={err!r}"
    assert "OK" in out