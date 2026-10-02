"""Empirical check of constraint (d) in the resolver log, section 5 NOTE-B.

Loads a SCRATCH copy of backend/config.py (sys.path[0] = the scratch dir) that
carries the candidate production dev-shape guards, then replays the 14
constructions that backend/tests/config/test_config_validation.py performs and
reports which of them would flip from pass to fail.

The real backend/config.py is never imported and never modified by this script.
"""
from __future__ import annotations

import sys
from pathlib import Path

SCRATCH = Path(r"C:\Users\user\AppData\Local\Temp\opencode\scratch_cfg")
sys.path.insert(0, str(SCRATCH))

from pydantic import ValidationError  # noqa: E402
import config  # noqa: E402

assert Path(config.__file__).parent == SCRATCH, f"wrong config loaded: {config.__file__}"
print(f"loaded scratch config from: {config.__file__}")

A64 = "a" * 64
A32 = "a" * 32

# Verbatim copy of _production_base() from the frozen test (read-only use).
BASE = {
    "app_env": "production", "secret_key": A64,
    "database_url": "postgresql+asyncpg://user:pass@localhost/db",
    "database_url_direct": "postgresql+asyncpg://user:pass@localhost/db",
    "valkey_url": "valkey://localhost:6379", "sentry_dsn": "https://example@glitchtip.example.com/1",
    "field_encryption_salt": A32, "stripe_secret_key": "sk_test", "stripe_publishable_key": "pk_test",
    "stripe_webhook_secret": "whsec_test", "tap_secret_key": "sk_test", "tap_webhook_secret": "whsec_test",
    "tap_api_base_url": "https://api.tap.company.com", "cors_origins": "https://example.com",
    "debug": False, "otel_exporter_otlp_endpoint": "http://localhost:4318",
    "trusted_proxy_ips": "10.0.0.0/8", "r2_bucket": "bucket", "r2_endpoint_url": "https://s3.example.com",
    "r2_access_key_id": "key", "r2_secret_access_key": "secret",
    "frontend_url": "https://example.com", "backend_url": "https://api.example.com",
    "hash_salt": A32, "kms_encryption_key": A64, "audit_chain_key": A32, "field_encryption_key": A64,
    "media_storage_base": "/tmp", "sso_client_id": "client",
    "celery_broker_url": "valkey://localhost:6379/0", "celery_result_backend": "valkey://localhost:6379/1",
    "hf_api_token": "token", "smtp_host": "smtp.example.com", "smtp_port": 587,
    "smtp_user": "user", "smtp_password": "pass", "twilio_account_sid": "sid",
    "twilio_auth_token": "token", "whatsapp_account_sid": "sid", "whatsapp_auth_token": "token",
    "whatsapp_from_number": "+1234567890", "resend_api_key": "key", "resend_webhook_secret": "secret",
    "google_client_id": "id", "google_client_secret": "secret", "facebook_client_id": "id",
    "facebook_client_secret": "secret", "paypal_secret": "secret", "paypal_client_id": "id",
    "paypal_webhook_secret": "secret", "paytabs_server_key": "key", "paytabs_webhook_secret": "secret",
    "paytabs_api_base_url": "https://api.tap.company.com", "thawani_secret_key": "key",
    "thawani_publishable_key": "pk", "thawani_api_base_url": "https://api.thawani.com",
    "thawani_webhook_secret": "secret",
}

ACCEPT_TESTS = [
    ("test_secret_key_accepts_64_chars", {"secret_key": A64}),
    ("test_database_url_accepts_asyncpg_scheme_in_production", {"database_url": "postgresql+asyncpg://user:pass@localhost/db"}),
    ("test_valkey_url_accepts_valkey_scheme_in_production", {"valkey_url": "valkey://localhost:6379"}),
    ("test_audit_chain_key_accepts_32_chars_in_production", {"audit_chain_key": A32}),
    ("test_field_encryption_key_accepts_64_chars_in_production", {"field_encryption_key": A64}),
    ("test_database_url_direct_accepts_valid_value_in_production", {"database_url_direct": "postgresql+asyncpg://user:pass@localhost/db"}),
]

REJECT_TESTS = [
    ("test_secret_key_rejects_32_chars", {"secret_key": "a" * 32}, "SECRET_KEY must be at least 64 characters"),
    ("test_database_url_rejects_wrong_scheme_in_production", {"database_url": "postgresql://user:pass@localhost/db"}, "DATABASE_URL must use the 'postgresql+asyncpg://' scheme"),
    ("test_valkey_url_rejects_wrong_scheme_in_production", {"valkey_url": "redis://localhost:6379"}, "VALKEY_URL must use the 'valkey://' scheme"),
    ("test_audit_chain_key_rejects_short_value_in_production", {"audit_chain_key": "short"}, "AUDIT_CHAIN_KEY must be at least 32 characters"),
    ("test_field_encryption_key_rejects_short_value_in_production", {"field_encryption_key": "a" * 32}, "FIELD_ENCRYPTION_KEY must be at least 64 characters"),
    ("test_database_url_direct_required_in_production", {"database_url_direct": "          "}, "DATABASE_URL_DIRECT is required in production"),
    ("test_database_url_direct_rejects_sqlite_in_production", {"database_url_direct": "sqlite:///test.db"}, "SQLite is not allowed"),
    ("test_database_url_direct_has_min_length_constraint", {"database_url_direct": "short"}, "string_too_short"),
]


def run(name, overrides, expect_msg=None):
    payload = dict(BASE)
    payload.update(overrides)
    try:
        config.Settings(**payload)
        raised = []
    except (ValidationError, ValueError) as exc:
        raised = [str(e.get("msg", "")) for e in exc.errors()] if isinstance(exc, ValidationError) else [str(exc)]
    if expect_msg is None:
        return name, (not raised), ""
    return name, (expect_msg in " | ".join(raised)), ""


print()
print("=== the 6 'accepts_*' tests (must construct cleanly) ===")
flipped = []
for name, ov in ACCEPT_TESTS:
    ok = run(name, ov)[1]
    print(f"  {'OK  ' if ok else 'FLIP'}  {name}")
    if not ok:
        flipped.append(name)

print()
print("=== the 8 'rejects_*' tests (must still raise with the expected message) ===")
for name, ov, msg in REJECT_TESTS:
    ok = run(name, ov, msg)[1]
    print(f"  {'OK  ' if ok else 'FLIP'}  {name}")
    if not ok:
        flipped.append(name)

print()
print(f"FLIPPED_COUNT={len(flipped)} / 14")
print("FLIPPED=" + ", ".join(flipped) if flipped else "FLIPPED=<none>")