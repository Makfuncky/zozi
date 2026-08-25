"""Security domain — AXIS 3 feature atoms (permission catalog seed).

Single-sourced here; aggregated by ``rbac/catalog.py``. The strings below are the
canonical permission atoms for the security domain. CI must fail on any
``require_feature("security.*")`` literal that is not present in this map.

Service-level features for fraud detection and threat monitoring subsystems.
"""

from __future__ import annotations

FEATURES: dict[str, dict] = {
    "fraud.detection.view": {
        "label": "View Fraud Detection",
        "risk": "medium",
        "actions": ["read"],
        "description": "View fraud detection alerts, risk scores, and investigation queues.",
    },
    "fraud.detection.manage": {
        "label": "Manage Fraud Detection",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Configure fraud rules, manage detection models, and override risk decisions.",
    },
    "fraud.investigation": {
        "label": "Fraud Investigation",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Investigate fraud cases, add case notes, and resolve investigations.",
    },
    "threat.monitoring.view": {
        "label": "View Threat Monitoring",
        "risk": "medium",
        "actions": ["read"],
        "description": "View threat intelligence feeds, active threats, and security dashboards.",
    },
    "threat.monitoring.manage": {
        "label": "Manage Threat Monitoring",
        "risk": "high",
        "actions": ["read", "create", "update", "delete"],
        "description": "Configure threat detection rules, manage threat feeds, and respond to incidents.",
    },
    "threat.response": {
        "label": "Threat Response",
        "risk": "high",
        "actions": ["read", "update"],
        "description": "Execute threat response actions: block, quarantine, or escalate threats.",
    },
}


def all_features() -> list[str]:
    return sorted(FEATURES.keys())


def is_known(feature: str) -> bool:
    if feature in FEATURES:
        return True
    if feature.endswith(".*"):
        prefix = feature[:-1]
        return any(f.startswith(prefix) for f in FEATURES)
    return False


__all__ = ["FEATURES", "all_features", "is_known", "encrypt_pii", "decrypt_pii", "verify_user_token", "setup_2fa_for_user", "verify_2fa_code", "screen_entity"]


# ── Provider-wired helpers ──

from providers.auth.jwt import decode_token
from providers.auth.totp import generate_secret, provisioning_uri, verify as verify_totp
from providers.security.encryption import Fernet, PBKDF2HMAC, hashes
from providers.security.watchlist import WatchlistProviderError, screen_watchlist

from infrastructure.utils.config import settings


def _derive_fernet_key(key: str) -> bytes:
    """Derive a 32-byte URL-safe base64 key from a settings string for Fernet encryption."""
    import base64
    derived = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"zozi-security-static-salt",
        iterations=100_000,
    ).derive(key.encode("utf-8", errors="replace"))
    return base64.urlsafe_b64encode(derived)


def encrypt_pii(plaintext: str) -> str:
    """Encrypt PII using the security provider's Fernet primitives."""
    key = settings.field_encryption_key or settings.encryption_key
    return Fernet(_derive_fernet_key(key)).encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_pii(ciphertext: str) -> str:
    """Decrypt PII using the security provider's Fernet primitives."""
    key = settings.field_encryption_key or settings.encryption_key
    return Fernet(_derive_fernet_key(key)).decrypt(ciphertext.encode("utf-8")).decode("utf-8")


def verify_user_token(token: str):
    """Decode and verify a JWT using the auth provider."""
    return decode_token(token, secret=settings.secret_key, algorithms=[settings.jwt_algorithm])


def setup_2fa_for_user(user_email: str):
    """Generate a TOTP secret and provisioning URI via the auth provider."""
    secret = generate_secret()
    uri = provisioning_uri(secret, name=user_email, issuer_name="ZOZI")
    return {"secret": secret, "provisioning_uri": uri}


def verify_2fa_code(secret: str, code: str) -> bool:
    """Verify a TOTP 2FA code against a user's secret using the auth provider."""
    return verify_totp(secret, code)


def screen_entity(name: str, country_code: str):
    """Screen an entity against watchlists using the security provider."""
    try:
        return screen_watchlist(
            employee_code="",
            full_name=name,
            country_code=country_code,
        )
    except WatchlistProviderError as exc:
        return {"status": "error", "score": 0.0, "details": str(exc), "flagged_categories": []}
