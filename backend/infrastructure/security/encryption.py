"""AES-256-GCM field encryption for sensitive database columns.

Replaces the previous Fernet-based implementation to satisfy TECHNOLOGY_STACK.md
§5 (cryptography 50.0.1, AES-256-GCM via PBKDF2-derived key).

``FIELD_ENCRYPTION_SALT`` is mandatory.  Missing values cause an immediate
``RuntimeError`` at import time — the previous behaviour of silently falling
back to an ephemeral random salt made every previously-encrypted value
permanently undecryptable after any restart.

Zero-downtime key rotation (ARCHITECTURE_STACK.md Law 277)
--------------------------------------------------------
The ``enc::`` ciphertext format carries no key identifier, so a reader cannot
tell *which* key produced a value.  A single-key encryptor therefore has exactly
one failure mode after ``FIELD_ENCRYPTION_KEY`` changes: ``decrypt`` cannot
authenticate the token and returns the raw ciphertext to the caller, which then
receives ``enc::AbCd...`` where it expected a phone number or a bank account.

``FieldEncryptor`` therefore accepts a KEYRING: one primary key, used for every
new encryption, plus zero or more fallback keys used only for decryption.  A
rotation registers the outgoing key as a fallback, so for the whole migration
window BOTH keys are accepted and no existing row is unreadable at any instant.
Once ``rotate_encryption_key`` has finished, the outgoing key can be dropped.

The KDF cost is NEVER reduced to buy speed: ``_KDF_ITERATIONS`` is fixed and the
fallback chain only changes how many candidate keys are tried, never how hard
each one is to derive.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable, Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from infrastructure.utils.config import settings

logger = logging.getLogger(__name__)

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

_ENCRYPTED_PREFIX = "enc::"
_KDF_ITERATIONS = 600_000

# ---------------------------------------------------------------------------
# Law 277 — key rotation policy
# ---------------------------------------------------------------------------
# Law 277 states the interval verbatim: "Every 90 days. Zero-downtime." These are
# the policy numbers, named so they are auditable rather than buried in a literal
# (Law 66). They are deliberately NOT configurable from the environment: a
# rotation interval that an operator can raise past the legal/compliance limit is
# not a control, it is a suggestion.
KEY_ROTATION_INTERVAL_DAYS = 90
#: Warn this many days before the deadline so a rotation can be scheduled.
KEY_ROTATION_WARN_THRESHOLD_DAYS = 75
#: Rotation-state filename. Holds timestamps and one-way key FINGERPRINTS only —
#: never key material (Law 32, Law 282).
KEY_ROTATION_STATE_FILENAME = ".field_encryption_key_rotation.json"
#: Fingerprint length in hex chars. 16 hex chars = 64 bits, enough to tell two
#: keys apart in an operational log without being usable as key material.
_KEY_FINGERPRINT_HEX_CHARS = 16
#: Status values returned by check_key_rotation(), shaped for /health/deps.
KEY_ROTATION_STATUS_OK = "ok"
KEY_ROTATION_STATUS_DUE_SOON = "due_soon"
KEY_ROTATION_STATUS_OVERDUE = "overdue"
KEY_ROTATION_STATUS_UNKNOWN = "unknown"


def _resolve_kdf_salt() -> bytes:
    raw = os.environ.get("FIELD_ENCRYPTION_SALT", "")
    stripped = str(raw).strip()
    if not stripped:
        app_env = str(getattr(settings, "app_env", "development") or "development").lower()
        if app_env in ("production", "staging"):
            raise RuntimeError(
                "FIELD_ENCRYPTION_SALT is required in production/staging. "
                "Generate with: secrets.token_hex(32)"
            )
        logger.critical(
            "FIELD_ENCRYPTION_SALT is not set — field encryption will use a "
            "non-reproducible salt. Encrypted fields become permanently "
            "undecryptable after any restart. Set FIELD_ENCRYPTION_SALT in "
            "all environments."
        )
        raise RuntimeError(
            "FIELD_ENCRYPTION_SALT must be set. Encrypted fields are "
            "undecryptable without a stable salt."
        )
    if len(stripped) < 32:
        raise RuntimeError(
            f"FIELD_ENCRYPTION_SALT must be at least 32 hex characters "
            f"(got {len(stripped)}). Generate with: secrets.token_hex(32)"
        )
    try:
        return bytes.fromhex(stripped)
    except ValueError:
        raise RuntimeError(
            "FIELD_ENCRYPTION_SALT must be a hex string. "
            "Generate with: secrets.token_hex(32)"
        )


_KDF_SALT: bytes = _resolve_kdf_salt()


def _derive_fernet_key(raw_key: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_KDF_SALT,
        iterations=_KDF_ITERATIONS,
    )
    derived = kdf.derive(raw_key.encode("utf-8"))
    return base64.urlsafe_b64encode(derived)


def _aes256_gcm_encrypt(plaintext: str, key: bytes) -> str:
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def _aes256_gcm_decrypt(token: str, key: bytes) -> str:
    raw = base64.urlsafe_b64decode(token.encode("utf-8"))
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


class FieldEncryptor:
    """AES-256-GCM encryptor with an optional decryption KEYRING.

    ``raw_key`` is the primary key: every value produced by :meth:`encrypt` uses
    it.  ``fallback_keys`` are additional raw keys accepted ONLY by
    :meth:`decrypt`, which is what makes a rotation zero-downtime (Law 277).

    With no fallback keys the behaviour is byte-identical to the previous
    single-key implementation, so every existing caller is unaffected.
    """

    def __init__(self, raw_key: str, fallback_keys: Iterable[str] = ()):
        self._aes_key: bytes | None = None
        if raw_key:
            self._aes_key = _derive_fernet_key(raw_key)[:32]
        self._primary_raw_key: str = raw_key or ""
        # Fallbacks are kept as derived keys only. The raw material is dropped
        # immediately after derivation so it is not retained in memory for the
        # lifetime of the process (Law 32).
        self._fallback_keys: list[bytes] = []
        self.set_fallback_keys(fallback_keys)

    # ------------------------------------------------------------------ keyring
    def set_fallback_keys(self, raw_keys: Iterable[str]) -> None:
        """Replace the decryption keyring. The primary key is never a fallback."""
        derived: list[bytes] = []
        for candidate in raw_keys or ():
            if not candidate:
                continue
            try:
                key = _derive_fernet_key(candidate)[:32]
            except Exception as exc:  # pragma: no cover - defensive
                # Law 59: never swallow silently. A key that cannot be derived is
                # logged, not ignored, because ignoring it silently reduces the
                # set of ciphertexts this process can still read.
                logger.warning(
                    "field_encryption: could not derive a fallback key: %s", exc
                )
                continue
            if key not in derived:
                derived.append(key)
        self._fallback_keys = derived

    def add_fallback_key(self, raw_key: str) -> None:
        """Add one decryption key without disturbing the current ones."""
        if not raw_key:
            return
        try:
            key = _derive_fernet_key(raw_key)[:32]
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("field_encryption: could not derive fallback key: %s", exc)
            return
        if key not in self._fallback_keys:
            self._fallback_keys.append(key)

    def fallback_key_count(self) -> int:
        """How many extra keys this encryptor can still decrypt with."""
        return len(self._fallback_keys)

    def primary_key_fingerprint(self) -> str:
        """One-way fingerprint of the primary key. Safe to log and persist."""
        if not self._primary_raw_key:
            return ""
        return hashlib.sha256(
            self._primary_raw_key.encode("utf-8")
        ).hexdigest()[:_KEY_FINGERPRINT_HEX_CHARS]

    # ----------------------------------------------------------------- crypto
    def is_encrypted(self, value: Any) -> bool:
        return isinstance(value, str) and value.startswith(_ENCRYPTED_PREFIX)

    def encrypt(self, value: Any) -> Any:
        if value is None:
            return None
        if not self._aes_key:
            return value
        if not isinstance(value, str):
            value = str(value)
        if value == "" or self.is_encrypted(value):
            return value
        token = _aes256_gcm_encrypt(value, self._aes_key)
        return f"{_ENCRYPTED_PREFIX}{token}"

    def decrypt(self, value: Any) -> Any:
        if value is None or not isinstance(value, str) or value == "":
            return value
        if not self._aes_key:
            return value
        if not self.is_encrypted(value):
            return value
        token = value[len(_ENCRYPTED_PREFIX):]
        for candidate in (self._aes_key, *self._fallback_keys):
            try:
                return _aes256_gcm_decrypt(token, candidate)
            except Exception:
                # This key did not open it. Try the next one -- during a rotation
                # window the value may legitimately be under the outgoing key.
                continue
        # Every candidate failed. Preserve the pre-existing behaviour exactly:
        # return the raw value and say so in the log (Law 59).
        logger.warning("Encountered unreadable encrypted field; returning raw value")
        return value


def _get_encryption_key() -> str:
    key = settings._resolve_field_encryption_key()
    if not key:
        logger.warning(
            "FIELD_ENCRYPTION_KEY not set. Field encryption is disabled in development mode."
        )
        return ""
    return key


_field_encryption_key = _get_encryption_key()
field_encryptor = FieldEncryptor(_field_encryption_key) if _field_encryption_key else None


# ---------------------------------------------------------------------------
# Rotation-state persistence (Law 277)
# ---------------------------------------------------------------------------
# The sidecar holds ONLY: when the current key was put in service, a one-way
# fingerprint of it, and the fingerprints of any keys still accepted for
# decryption. No key material, no salt, no derived key (Law 32, Law 282).
_MEMORY_KEY_ROTATION_STATE: dict[str, Any] = {}


def _default_key_rotation_state_path() -> Path:
    """Where the rotation sidecar lives.

    Anchored on the backend root (the same place config.py anchors BASE_DIR) so
    the file sits with the application rather than inside an importable package,
    and so a container bind-mount can point at it without code changes.
    """
    return Path(__file__).resolve().parent.parent.parent / KEY_ROTATION_STATE_FILENAME


def key_rotation_state_path(state_path: Optional[Path | str] = None) -> Path:
    return Path(state_path) if state_path else _default_key_rotation_state_path()


def _read_key_rotation_state(state_path: Optional[Path | str] = None) -> dict[str, Any]:
    path = key_rotation_state_path(state_path)
    if path.exists():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                return loaded
            logger.warning(
                "field_encryption: rotation state at %s is not an object; ignoring",
                path.name,
            )
        except Exception as exc:
            logger.warning(
                "field_encryption: rotation state at %s is unreadable: %s",
                path.name,
                exc,
            )
    return dict(_MEMORY_KEY_ROTATION_STATE)


def record_key_rotation(
    rotated_at: Optional[datetime] = None,
    state_path: Optional[Path | str] = None,
    fallback_fingerprints: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Persist the current key's in-service date. Returns the stored state.

    Never raises: a rotation must not fail because its bookkeeping could not be
    written. On a write failure the state is kept in memory and a WARNING is
    logged (Law 30, Law 59).
    """
    moment = rotated_at or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    state = {
        "rotated_at": moment.astimezone(timezone.utc).isoformat(),
        "interval_days": KEY_ROTATION_INTERVAL_DAYS,
        "key_fingerprint": (
            field_encryptor.primary_key_fingerprint() if field_encryptor else ""
        ),
        "fallback_fingerprints": list(fallback_fingerprints or []),
    }
    path = key_rotation_state_path(state_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic write: a torn sidecar would report a bogus rotation date, which
        # is worse than no date at all.
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=str(path.parent),
            prefix=path.name, suffix=".tmp", delete=False,
        ) as handle:
            json.dump(state, handle, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
            tmp_name = handle.name
        os.replace(tmp_name, path)
    except Exception as exc:
        logger.warning(
            "field_encryption: could not persist rotation state to %s (%s); "
            "keeping it in memory only",
            path.name,
            exc,
        )
    _MEMORY_KEY_ROTATION_STATE.clear()
    _MEMORY_KEY_ROTATION_STATE.update(state)
    logger.info(
        "field_encryption_key_rotation_recorded",
        extra={
            "rotated_at": state["rotated_at"],
            "interval_days": KEY_ROTATION_INTERVAL_DAYS,
            # Fingerprints only - never key material (Law 32, Law 282).
            "key_fingerprint": state["key_fingerprint"],
            "fallback_key_count": len(state["fallback_fingerprints"]),
        },
    )
    return dict(state)


def get_key_rotation_state(
    now: Optional[datetime] = None,
    state_path: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Compute the age of the current field-encryption key.

    Returns a dict suitable for a health payload::

        {
            "status": "ok" | "due_soon" | "overdue" | "unknown",
            "rotated_at": "<iso8601>" | "",
            "age_days": <int> | None,
            "interval_days": 90,
            "days_until_due": <int> | None,   # negative once overdue
            "warn_threshold_days": 75,
            "overdue": bool,
            "key_fingerprint": "<16 hex chars>",
            "fallback_key_count": <int>,
        }
    """
    moment = now or datetime.now(timezone.utc)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)

    state = _read_key_rotation_state(state_path)
    rotated_at_raw = str(state.get("rotated_at") or "").strip()
    rotated_at: Optional[datetime] = None
    if rotated_at_raw:
        try:
            rotated_at = datetime.fromisoformat(rotated_at_raw)
            if rotated_at.tzinfo is None:
                rotated_at = rotated_at.replace(tzinfo=timezone.utc)
        except ValueError:
            rotated_at = None

    result: dict[str, Any] = {
        "status": KEY_ROTATION_STATUS_UNKNOWN,
        "rotated_at": rotated_at.isoformat() if rotated_at else "",
        "age_days": None,
        "interval_days": KEY_ROTATION_INTERVAL_DAYS,
        "days_until_due": None,
        "warn_threshold_days": KEY_ROTATION_WARN_THRESHOLD_DAYS,
        "overdue": False,
        "key_fingerprint": str(state.get("key_fingerprint") or ""),
        "fallback_key_count": len(state.get("fallback_fingerprints") or []),
    }
    if rotated_at is None:
        # An unverifiable rotation policy is not a satisfied rotation policy.
        result["status"] = KEY_ROTATION_STATUS_UNKNOWN
        return result

    age = moment - rotated_at
    age_days = age.days
    days_until_due = KEY_ROTATION_INTERVAL_DAYS - age_days
    result["age_days"] = age_days
    result["days_until_due"] = days_until_due
    if days_until_due <= 0:
        # Law 277: "Every 90 days." A key that has REACHED 90 days has met its
        # limit, so the deadline day itself counts as overdue rather than as a
        # grace period nobody asked for.
        result["status"] = KEY_ROTATION_STATUS_OVERDUE
        result["overdue"] = True
    elif days_until_due <= KEY_ROTATION_INTERVAL_DAYS - KEY_ROTATION_WARN_THRESHOLD_DAYS:
        result["status"] = KEY_ROTATION_STATUS_DUE_SOON
    else:
        result["status"] = KEY_ROTATION_STATUS_OK
    return result


def check_key_rotation(
    now: Optional[datetime] = None,
    state_path: Optional[Path | str] = None,
    log: bool = True,
) -> dict[str, Any]:
    """Rotation-age check WITH an operational signal.

    Logs CRITICAL when the key is past the Law 277 deadline and WARNING when it
    is inside the warn window or when its age cannot be established. The return
    value is shaped for ``/health/deps`` (Law 299) so it can be surfaced without
    further translation; the wiring itself lives in main.py, which is outside
    this contract's allowed files.
    """
    state = get_key_rotation_state(now=now, state_path=state_path)
    if not log:
        return state

    status = state["status"]
    if status == KEY_ROTATION_STATUS_OVERDUE:
        logger.critical(
            "field_encryption_key_rotation_overdue",
            extra={
                "age_days": state["age_days"],
                "days_overdue": -(state["days_until_due"] or 0),
                "interval_days": KEY_ROTATION_INTERVAL_DAYS,
                "key_fingerprint": state["key_fingerprint"],
            },
        )
    elif status == KEY_ROTATION_STATUS_DUE_SOON:
        logger.warning(
            "field_encryption_key_rotation_due",
            extra={
                "age_days": state["age_days"],
                "days_until_due": state["days_until_due"],
                "interval_days": KEY_ROTATION_INTERVAL_DAYS,
                "key_fingerprint": state["key_fingerprint"],
            },
        )
    elif status == KEY_ROTATION_STATUS_UNKNOWN:
        logger.warning(
            "field_encryption_key_rotation_age_unknown",
            extra={
                "interval_days": KEY_ROTATION_INTERVAL_DAYS,
                "detail": (
                    "no rotation state recorded; the Law 277 deadline cannot be "
                    "verified. Call record_key_rotation() after the next rotation."
                ),
            },
        )
    return state


def register_previous_field_encryption_key(raw_key: str) -> int:
    """Add an outgoing key to the live encryptor's decryption keyring.

    This is the zero-downtime mechanism (Law 277). Call it BEFORE switching
    FIELD_ENCRYPTION_KEY so that every value written under the old key stays
    readable for the whole migration window. Returns the resulting keyring size,
    or 0 when field encryption is disabled.
    """
    if not raw_key:
        return 0
    if field_encryptor is None:
        logger.warning(
            "field_encryption: cannot register a previous key because "
            "FIELD_ENCRYPTION_KEY is not configured; field encryption is disabled"
        )
        return 0
    field_encryptor.add_fallback_key(raw_key)
    count = field_encryptor.fallback_key_count()
    logger.warning(
        "field_encryption_previous_key_registered",
        extra={
            "fallback_key_count": count,
            "detail": (
                "the previous key is accepted for DECRYPTION ONLY until the "
                "rotation completes; new writes use the current key"
            ),
        },
    )
    return count


@lru_cache(maxsize=128)
def _encrypted_storage_length(plaintext_length: int) -> int:
    probe_length = max(int(plaintext_length or 0), 1)
    encrypted_value = field_encryptor.encrypt("x" * probe_length)
    return len(str(encrypted_value))


class EncryptedString(TypeDecorator):
    """Transparent-at-rest encryption with ciphertext-safe storage sizing."""

    impl = Text
    cache_ok = True

    def __init__(self, length: int | None = None):
        super().__init__()
        self.length = length

    def load_dialect_impl(self, dialect):  # type: ignore[override]
        if self.length and field_encryptor:
            return dialect.type_descriptor(String(_encrypted_storage_length(self.length)))
        return dialect.type_descriptor(Text())

    def process_bind_param(self, value: Any, dialect):  # type: ignore[override]
        if field_encryptor:
            return field_encryptor.encrypt(value)
        return value

    def process_result_value(self, value: Any, dialect):  # type: ignore[override]
        if field_encryptor:
            return field_encryptor.decrypt(value)
        return value


def decrypt_secret(value: Optional[str]) -> Optional[str]:
    """
    Decrypt a secret value.
    
    First attempts to decrypt using the vault service (v1: prefix).
    Falls back to the legacy field encryptor for backward compatibility.
    """
    if not value:
        return value
    if value.startswith("v1:"):
        from infrastructure.security.vault import get_vault
        return get_vault().decrypt(value)
    if field_encryptor:
        return field_encryptor.decrypt(value)
    return value
