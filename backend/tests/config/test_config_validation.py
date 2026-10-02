"""Tests for backend/config.py validation findings CONFIG-003 through CONFIG-009."""
from __future__ import annotations

import os
import sys

import pytest
from pathlib import Path

# Ensure backend package root is importable.
_BACKEND_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

# Set required env vars before importing config.py so the module-level
# `settings = Settings()` instantiation succeeds.
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "a" * 64
os.environ["FIELD_ENCRYPTION_KEY"] = "a" * 64
os.environ["FIELD_ENCRYPTION_SALT"] = "a" * 32
os.environ["AUDIT_CHAIN_KEY"] = "a" * 32

from pydantic import ValidationError
from config import Settings


def _production_base(**overrides: object) -> dict:
    """Return a minimal set of values that pass the production validator."""
    base = {
        "app_env": "production",
        "secret_key": "a" * 64,
        "database_url": "postgresql+asyncpg://user:pass@localhost/db",
        "database_url_direct": "postgresql+asyncpg://user:pass@localhost/db",
        "valkey_url": "valkey://localhost:6379",
        "sentry_dsn": "https://example@glitchtip.example.com/1",
        "field_encryption_salt": "a" * 32,
        "stripe_secret_key": "sk_test",
        "stripe_publishable_key": "pk_test",
        "stripe_webhook_secret": "whsec_test",
        "tap_secret_key": "sk_test",
        "tap_webhook_secret": "whsec_test",
        "tap_api_base_url": "https://api.tap.company.com",
        "cors_origins": "https://example.com",
        "debug": False,
        "otel_exporter_otlp_endpoint": "http://localhost:4318",
        "trusted_proxy_ips": "10.0.0.0/8",
        "r2_bucket": "bucket",
        "r2_endpoint_url": "https://s3.example.com",
        "r2_access_key_id": "key",
        "r2_secret_access_key": "secret",
        "frontend_url": "https://example.com",
        "backend_url": "https://api.example.com",
        "hash_salt": "a" * 32,
        "kms_encryption_key": "a" * 64,
        "audit_chain_key": "a" * 32,
        "field_encryption_key": "a" * 64,
        "media_storage_base": "/tmp",
        "sso_client_id": "client",
        "celery_broker_url": "valkey://localhost:6379/0",
        "celery_result_backend": "valkey://localhost:6379/1",
        "hf_api_token": "token",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_user": "user",
        "smtp_password": "pass",
        "twilio_account_sid": "sid",
        "twilio_auth_token": "token",
        "whatsapp_account_sid": "sid",
        "whatsapp_auth_token": "token",
        "whatsapp_from_number": "+1234567890",
        "resend_api_key": "key",
        "resend_webhook_secret": "secret",
        "google_client_id": "id",
        "google_client_secret": "secret",
        "facebook_client_id": "id",
        "facebook_client_secret": "secret",
        "stripe_publishable_key": "pk_test",
        "stripe_webhook_secret": "whsec_test",
        "paypal_secret": "secret",
        "paypal_client_id": "id",
        "paypal_webhook_secret": "secret",
        "paytabs_server_key": "key",
        "paytabs_webhook_secret": "secret",
        "paytabs_api_base_url": "https://api.tap.company.com",
        "thawani_secret_key": "key",
        "thawani_publishable_key": "pk",
        "thawani_api_base_url": "https://api.thawani.com",
        "thawani_webhook_secret": "secret",
    }
    base.update(overrides)
    return base


class TestSecretKeyMinLength:
    """CONFIG-004: secret_key min_length should be 64, not 32."""

    def test_secret_key_rejects_32_chars(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_production_base(secret_key="a" * 32))
        errors = exc_info.value.errors()
        assert any("SECRET_KEY must be at least 64 characters" in str(e.get("msg", "")) for e in errors)

    def test_secret_key_accepts_64_chars(self):
        settings = Settings(**_production_base(secret_key="a" * 64))
        assert len(settings.secret_key) == 64


class TestDatabaseUrlScheme:
    """CONFIG-005: database_url must enforce postgresql+asyncpg:// scheme in production."""

    def test_database_url_rejects_wrong_scheme_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(database_url="postgresql://user:pass@localhost/db"),
            )
        errors = exc_info.value.errors()
        assert any("DATABASE_URL must use the 'postgresql+asyncpg://' scheme" in str(e.get("msg", "")) for e in errors)

    def test_database_url_accepts_asyncpg_scheme_in_production(self):
        settings = Settings(
            **_production_base(database_url="postgresql+asyncpg://user:pass@localhost/db"),
        )
        assert settings.database_url.startswith("postgresql+asyncpg://")


class TestValkeyUrlScheme:
    """CONFIG-006: valkey_url must enforce valkey:// scheme in production."""

    def test_valkey_url_rejects_wrong_scheme_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(valkey_url="redis://localhost:6379"),
            )
        errors = exc_info.value.errors()
        assert any("VALKEY_URL must use the 'valkey://' scheme" in str(e.get("msg", "")) for e in errors)

    def test_valkey_url_accepts_valkey_scheme_in_production(self):
        settings = Settings(
            **_production_base(valkey_url="valkey://localhost:6379"),
        )
        assert settings.valkey_url.startswith("valkey://")


class TestAuditChainKeyMinLength:
    """CONFIG-007: audit_chain_key must have min_length=32 in production."""

    def test_audit_chain_key_rejects_short_value_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(audit_chain_key="short"),
            )
        errors = exc_info.value.errors()
        assert any("AUDIT_CHAIN_KEY must be at least 32 characters" in str(e.get("msg", "")) for e in errors)

    def test_audit_chain_key_accepts_32_chars_in_production(self):
        settings = Settings(
            **_production_base(audit_chain_key="a" * 32),
        )
        assert len(settings.audit_chain_key) == 32


class TestFieldEncryptionKeyMinLength:
    """CONFIG-008: field_encryption_key must have min_length=64 in production."""

    def test_field_encryption_key_rejects_short_value_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(field_encryption_key="a" * 32),
            )
        errors = exc_info.value.errors()
        assert any("FIELD_ENCRYPTION_KEY must be at least 64 characters" in str(e.get("msg", "")) for e in errors)

    def test_field_encryption_key_accepts_64_chars_in_production(self):
        settings = Settings(
            **_production_base(field_encryption_key="a" * 64),
        )
        assert len(settings.field_encryption_key) == 64


class TestDatabaseUrlDirectInProduction:
    """CONFIG-003 and CONFIG-009: database_url_direct must be in production validator with constraints."""

    def test_database_url_direct_required_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_production_base(database_url_direct="          "))
        errors = exc_info.value.errors()
        assert any("DATABASE_URL_DIRECT is required in production" in str(e.get("msg", "")) for e in errors)

    def test_database_url_direct_rejects_sqlite_in_production(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(database_url_direct="sqlite:///test.db"),
            )
        errors = exc_info.value.errors()
        assert any("SQLite is not allowed" in str(e.get("msg", "")) for e in errors)

    def test_database_url_direct_has_min_length_constraint(self):
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                **_production_base(database_url_direct="short"),
            )
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("database_url_direct",) and e["type"] == "string_too_short" for e in errors)

    def test_database_url_direct_accepts_valid_value_in_production(self):
        settings = Settings(
            **_production_base(database_url_direct="postgresql+asyncpg://user:pass@localhost/db"),
        )
        assert settings.database_url_direct.startswith("postgresql+asyncpg://")
