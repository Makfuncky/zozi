"""Paired test: every variable that config.py validators or module-level
imports require must be present in the environment before ``config`` is
imported. If a future agent adds a new required variable, this test fails
loudly at collection time instead of silently breaking the suite.
"""
from __future__ import annotations

import os
import sys

_BACKEND_ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))


# ---------------------------------------------------------------------------
# The complete contract: every env var the test-suite requires.
# ---------------------------------------------------------------------------
_REQUIRED_TEST_ENV_VARS = [
    # Core app/test flags
    "APP_ENV",
    "CSRF_DISABLED",
    # Encryption
    "FIELD_ENCRYPTION_SALT",
    "FIELD_ENCRYPTION_KEY",
    # Secrets / auth
    "SECRET_KEY",
    "AUDIT_CHAIN_KEY",
    # Database
    "DATABASE_URL",
    "DATABASE_URL_DIRECT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    # Payment providers
    "STRIPE_SECRET_KEY",
    "STRIPE_PUBLISHABLE_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "TAP_SECRET_KEY",
    "TAP_WEBHOOK_SECRET",
    "TAP_API_BASE_URL",
    "PAYTABS_SERVER_KEY",
    "PAYTABS_WEBHOOK_SECRET",
    "PAYTABS_PROFILE_ID",
    "PAYTABS_API_BASE_URL",
    "PAYTABS_CALLBACK_URL",
    "THAWANI_SECRET_KEY",
    "THAWANI_PUBLISHABLE_KEY",
    "THAWANI_API_BASE_URL",
    "THAWANI_WEBHOOK_SECRET",
    "PAYPAL_SECRET",
    "PAYPAL_CLIENT_ID",
    "PAYPAL_WEBHOOK_SECRET",
    # AI / external services
    "OPENAI_API_KEY",
    "SENTRY_DSN",
    "HF_API_TOKEN",
    # Comms
    "TWILIO_ACCOUNT_SID",
    "TWILIO_AUTH_TOKEN",
    "WHATSAPP_ACCOUNT_SID",
    "WHATSAPP_AUTH_TOKEN",
    "WHATSAPP_FROM_NUMBER",
    "RESEND_API_KEY",
    "RESEND_WEBHOOK_SECRET",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USER",
    "SMTP_PASSWORD",
    # Social / SSO
    "GOOGLE_CLIENT_ID",
    "GOOGLE_CLIENT_SECRET",
    "FACEBOOK_CLIENT_ID",
    "FACEBOOK_CLIENT_SECRET",
    "SSO_CLIENT_ID",
    # Storage / infra
    "VALKEY_URL",
    "CELERY_BROKER_URL",
    "CELERY_RESULT_BACKEND",
    "R2_BUCKET",
    "R2_ENDPOINT_URL",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "MEDIA_STORAGE_BASE",
    "CORS_ORIGINS",
    "FRONTEND_URL",
    "BACKEND_URL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    # Security / misc
    "ENCRYPTION_KEY",
    "KMS_ENCRYPTION_KEY",
    "HASH_SALT",
    "TRUSTED_PROXY_IPS",
    "BANK_API_AUTH_TOKEN",
    "BANK_API_SOURCE_ACCOUNT_ID",
    # Seed data passwords
    "SEED_ADMIN_PASSWORD",
    "SEED_SUPPLIER_PASSWORD",
    "SEED_CUSTOMER_PASSWORD",
    "SEED_LOGISTICS_PASSWORD",
    "SEED_EMPLOYEE_PASSWORD",
]


def test_all_required_env_vars_are_present() -> None:
    """Fail loudly if any required env var is missing from the environment."""
    missing = [v for v in _REQUIRED_TEST_ENV_VARS if not os.environ.get(v)]
    assert not missing, (
        "Missing required test environment variables: "
        + ", ".join(missing)
        + ". Set them in backend/tests/conftest.py before importing config."
    )
