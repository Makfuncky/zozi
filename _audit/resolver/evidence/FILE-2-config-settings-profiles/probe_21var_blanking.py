"""21-variable (expanded to 28 individual) blanking probe for backend/config.py.

Builds a COMPLETE, valid production profile, asserts it constructs cleanly, then
blanks each variable one at a time and asserts a ValidationError is raised.

No secret value is printed: every literal below is a synthetic throwaway
placeholder that exists only in this probe process.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from pydantic import ValidationError  # noqa: E402
from config import Settings  # noqa: E402

A64 = "a" * 64
A32 = "a" * 32

BASE: dict[str, object] = {
    "app_env": "production",
    "secret_key": A64,
    "field_encryption_key": A64,
    "field_encryption_salt": A32,
    "audit_chain_key": A32,
    "database_url": "postgresql+asyncpg://u:p@db.example.invalid/zozi",
    "database_url_direct": "postgresql+asyncpg://u:p@db.example.invalid/zozi",
    "database_replica_url": "postgresql+asyncpg://u:p@db.example.invalid/zozi_ro",
    "valkey_url": "valkey://valkey.example.invalid:6379/0",
    "sentry_dsn": "https://key@glitchtip.example.invalid/1",
    "stripe_secret_key": "sk_probe",
    "stripe_publishable_key": "pk_probe",
    "stripe_webhook_secret": "whsec_probe",
    "tap_secret_key": "sk_probe",
    "tap_webhook_secret": "whsec_probe",
    "tap_api_base_url": "https://api.tap.example.invalid",
    "kms_encryption_key": A64,
    "hash_salt": A32,
    "cors_origins": "https://www.example.invalid",
    "debug": False,
    "otel_exporter_otlp_endpoint": "https://otel.example.invalid:4318",
    "trusted_proxy_ips": "10.0.0.0/8",
    "frontend_url": "https://www.example.invalid",
    "backend_url": "https://api.example.invalid",
    "media_storage_base": "https://media.example.invalid",
    "sso_client_id": "probe-sso",
    "celery_broker_url": "valkey://valkey.example.invalid:6379/1",
    "celery_result_backend": "valkey://valkey.example.invalid:6379/2",
    "hf_api_token": "hf_probe",
    "smtp_host": "smtp.example.invalid",
    "smtp_port": 587,
    "smtp_user": "probe_user",
    "smtp_password": "probe_pass",
    "twilio_account_sid": "probe_sid",
    "twilio_auth_token": "probe_token",
    "whatsapp_account_sid": "probe_sid",
    "whatsapp_auth_token": "probe_token",
    "whatsapp_from_number": "+10000000000",
    "resend_api_key": "re_probe",
    "resend_webhook_secret": "re_probe_wh",
    "google_client_id": "probe_gid",
    "google_client_secret": "probe_gsec",
    "facebook_client_id": "probe_fid",
    "facebook_client_secret": "probe_fsec",
    "paypal_secret": "probe_psec",
    "paypal_client_id": "probe_pcid",
    "paypal_webhook_secret": "probe_pwh",
    "paytabs_server_key": "probe_pt",
    "paytabs_webhook_secret": "probe_ptwh",
    "paytabs_api_base_url": "https://paytabs.example.invalid",
    "thawani_secret_key": "probe_th",
    "thawani_publishable_key": "probe_thpub",
    "thawani_api_base_url": "https://thawani.example.invalid",
    "thawani_webhook_secret": "probe_thwh",
    "r2_bucket": "probe-bucket",
    "r2_endpoint_url": "https://r2.example.invalid",
    "r2_access_key_id": "probe_r2id",
    "r2_secret_access_key": "probe_r2sec",
    "storage_backend": "r2",
    # non-dev shapes so production dev-default guards do not pre-empt the probe
    "ollama_base_url": "https://ollama.example.invalid:11434",
    "sms_mode": "live",
    "push_mode": "live",
    "upload_dir": "/srv/zozi/uploads",
    "backup_dir": "/srv/zozi/backups",
    "backup_enabled": False,
}

BLANKED: list[str] = [
    "SENTRY_DSN",
    "FIELD_ENCRYPTION_KEY",
    "STRIPE_SECRET_KEY",
    "TAP_SECRET_KEY",
    "KMS_ENCRYPTION_KEY",
    "HASH_SALT",
    "DATABASE_URL",
    "DATABASE_URL_DIRECT",
    "VALKEY_URL",
    "FRONTEND_URL",
    "BACKEND_URL",
    "AUDIT_CHAIN_KEY",
    "TRUSTED_PROXY_IPS",
    "R2_BUCKET",
    "R2_ENDPOINT_URL",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "SSO_CLIENT_ID",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    "HF_API_TOKEN",
    "MEDIA_STORAGE_BASE",
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
]


def _first_message(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        for err in exc.errors():
            return str(err.get("msg", ""))[:120]
        return "<no errors>"
    return str(exc)[:120]


def main() -> int:
    # Sanity: the un-blanked production profile must construct.
    Settings(**BASE)
    print("BASELINE production profile: constructs OK (no raise)")

    failures: list[str] = []
    for var in BLANKED:
        payload = dict(BASE)
        payload[var.lower()] = ""
        try:
            Settings(**payload)
        except (ValidationError, ValueError) as exc:
            print(f"  RAISED  {var:<24} {_first_message(exc)}")
            continue
        failures.append(var)
        print(f"  NO-RAISE {var:<24} <-- LAW 83 REGRESSION")

    print()
    print(f"probed={len(BLANKED)}  raised={len(BLANKED) - len(failures)}  "
          f"did_not_raise={len(failures)}")
    if failures:
        print("FAILED_VARIABLES=" + ",".join(failures))
        return 1
    print("RESULT: PASS - every blanked production variable still fails closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())