"""Profile guards for backend/config.py — per-environment configuration.

Companion to the frozen `test_config_validation.py` (14/14, untouched). This file
covers the FILE-2 contract behaviours:

  * ``test_dev_default_rejected_in_production``   — a development default that
    would otherwise survive into production is rejected (Law 86, Law 83).
  * ``test_required_secret_still_raises_when_blanked`` — every production-required
    variable still fails closed when blanked (Law 83). This is the regression
    test the contract asks for: it must FAIL if a future edit weakens
    ``_validate_production``.
  * ``test_staging_profile_does_not_inherit_dev_paths`` — staging is a real
    deployment (Law 205, Law 220) and inherits nothing from development
    (Law 86).

No secret value appears here. Every literal is a synthetic throwaway placeholder
that exists only inside the test process.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from config import BASE_DIR, Settings, _finalize_settings  # noqa: E402


_A64 = "a" * 64
_A32 = "a" * 32

# The exact frontend/backend base URLs the development profile defaults to.
DEV_FRONTEND_URL = "http://localhost:3000"
DEV_BACKEND_URL = "http://localhost:8000"


def _production_base(**overrides: object) -> dict:
    """A complete, valid production profile (every required variable set)."""
    base = {
        "app_env": "production",
        "secret_key": _A64,
        "field_encryption_key": _A64,
        "field_encryption_salt": _A32,
        "audit_chain_key": _A32,
        "database_url": "postgresql+asyncpg://u:p@db.example.invalid/zozi",
        "database_url_direct": "postgresql+asyncpg://u:p@db.example.invalid/zozi",
        "valkey_url": "valkey://valkey.example.invalid:6379/0",
        "sentry_dsn": "https://key@glitchtip.example.invalid/1",
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
        "hf_api_token": "probe-token",
        "smtp_host": "smtp.example.invalid",
        "smtp_port": 587,
        "smtp_user": "probe-user",
        "smtp_password": "probe-pass",
        "twilio_account_sid": "probe-sid",
        "twilio_auth_token": "probe-token",
        "whatsapp_account_sid": "probe-sid",
        "whatsapp_auth_token": "probe-token",
        "whatsapp_from_number": "+10000000000",
        "resend_api_key": "probe-key",
        "resend_webhook_secret": "probe-secret",
        "google_client_id": "probe-id",
        "google_client_secret": "probe-secret",
        "facebook_client_id": "probe-id",
        "facebook_client_secret": "probe-secret",
        "paypal_secret": "probe-secret",
        "paypal_client_id": "probe-id",
        "paypal_webhook_secret": "probe-secret",
        "paytabs_server_key": "probe-key",
        "paytabs_webhook_secret": "probe-secret",
        "paytabs_api_base_url": "https://paytabs.example.invalid",
        "thawani_secret_key": "probe-key",
        "thawani_publishable_key": "probe-pub",
        "thawani_api_base_url": "https://thawani.example.invalid",
        "thawani_webhook_secret": "probe-secret",
        "r2_bucket": "probe-bucket",
        "r2_endpoint_url": "https://r2.example.invalid",
        "r2_access_key_id": "probe-id",
        "r2_secret_access_key": "probe-secret",
        "storage_backend": "r2",
        "kms_encryption_key": _A64,
        "hash_salt": _A32,
        "stripe_secret_key": "probe-key",
        "stripe_publishable_key": "probe-pub",
        "stripe_webhook_secret": "probe-secret",
        "tap_secret_key": "probe-key",
        "tap_webhook_secret": "probe-secret",
        "tap_api_base_url": "https://api.tap.example.invalid",
    }
    base.update(overrides)
    return base


# Every variable `_validate_production` is required to police. The contract's
# third-pass probe blanked 21 named variables (with R2_*/CELERY_*/SMTP_*/GOOGLE_*
# expanded to their members); this list is that set, expanded to 28 individual
# variables so the probe is stricter than the original.
REQUIRED_PRODUCTION_VARIABLES = [
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


def _messages(exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        return " | ".join(str(err.get("msg", "")) for err in exc.errors())
    return str(exc)


class TestDevDefaultsRejectedInProduction:
    """Law 86 / Law 83 — the development profile must not leak into production."""

    def test_dev_default_rejected_in_production(self):
        """Both base URLs left at their development defaults must be rejected.

        This is the demonstrated defect: middleware/security_headers.py builds the
        production CSP `connect-src` from FRONTEND_URL alone, so a
        `http://localhost:3000` default published `ws://localhost:3000` as an
        allowed WebSocket origin and blocked every realtime connection.
        """
        payload = _production_base()
        # Drop the overrides entirely so the declared development defaults apply.
        payload.pop("frontend_url")
        payload.pop("backend_url")

        with pytest.raises(ValidationError) as exc_info:
            Settings(**payload)

        assert "must not point at loopback in production" in _messages(exc_info.value)

    @pytest.mark.parametrize(
        "override",
        [
            {"frontend_url": DEV_FRONTEND_URL},
            {"frontend_url": "http://127.0.0.1:3000"},
            {"frontend_url": "https://localhost:3000"},
            {"backend_url": DEV_BACKEND_URL},
            {"backend_url": "http://0.0.0.0:8000"},
        ],
    )
    def test_each_dev_shaped_base_url_is_rejected(self, override):
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_production_base(**override))
        assert "must not point at loopback in production" in _messages(exc_info.value)

    def test_public_base_urls_are_accepted(self):
        settings = Settings(**_production_base())
        assert settings.frontend_url == "https://www.example.invalid"
        assert settings.backend_url == "https://api.example.invalid"

    @pytest.mark.parametrize(
        ("variable", "bad_value"),
        [
            ("celery_broker_url", "sqlite:///zozi.db"),
            ("celery_result_backend", "sqlite:///zozi.db"),
            ("celery_broker_url", "amqp://guest:guest@rabbitmq:5672//"),
            ("celery_result_backend", "amqp://guest:guest@rabbitmq:5672//"),
        ],
    )
    def test_celery_urls_must_be_valkey_in_production(self, variable, bad_value):
        """A bare non-emptiness check used to accept a SQLite Celery broker."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(**_production_base(**{variable: bad_value}))
        message = _messages(exc_info.value)
        assert "CELERY_BROKER_URL must" in message or "CELERY_RESULT_BACKEND must" in message
        assert "Valkey" in message or "valkey://" in message


class TestRequiredSecretStillRaisesWhenBlanked:
    """Law 83 — required env vars validated at startup; missing = immediate failure.

    Regression test: if any entry in REQUIRED_PRODUCTION_VARIABLES stops raising,
    this test fails and Law 83 has been weakened.
    """

    def test_unblanked_production_profile_is_valid(self):
        """Guard against a vacuous probe: the baseline must construct."""
        assert Settings(**_production_base()).app_env == "production"

    @pytest.mark.parametrize("variable", REQUIRED_PRODUCTION_VARIABLES)
    def test_required_secret_still_raises_when_blanked(self, variable):
        payload = _production_base(**{variable.lower(): ""})
        with pytest.raises((ValidationError, ValueError)) as exc_info:
            Settings(**payload)
        assert _messages(exc_info.value), f"{variable} blanked but nothing was reported"


class TestStagingProfileDoesNotInheritDevPaths:
    """Law 86 + Law 205 + Law 220 — staging is a deployment, not development."""

    @staticmethod
    def _staging_base(**overrides: object) -> dict:
        """A staging profile with every non-production required secret present."""
        base = _production_base(app_env="staging")
        base.update(
            {
                "cors_origins": "https://staging.example.invalid",
                "database_url": "postgresql+asyncpg://u:p@staging-db.example.invalid/zozi",
                "database_url_direct": "postgresql+asyncpg://u:p@staging-db.example.invalid/zozi",
                "frontend_url": "https://staging.example.invalid",
                "backend_url": "https://api.staging.example.invalid",
                "valkey_url": "valkey://valkey.example.invalid:6379/0",
                "storage_backend": "r2",
                # the remainder of `_validate_required_secrets_in_non_production`
                "postgres_db": "zozi",
                "postgres_user": "zozi",
                "postgres_password": "probe-pass",
                "paytabs_profile_id": "probe-profile",
                "paytabs_callback_url": "https://api.staging.example.invalid/cb",
                "openai_api_key": "probe-key",
                "encryption_key": _A64,
                "bank_api_auth_token": "probe-token",
                "bank_api_source_account_id": "probe-account",
            }
        )
        base.update(overrides)
        return base

    def test_staging_profile_does_not_inherit_dev_paths(self):
        """A staging profile must not silently keep the development base URLs."""
        base = self._staging_base()
        base.pop("frontend_url")
        base.pop("backend_url")

        with pytest.raises(ValidationError) as exc_info:
            Settings(**base)

        assert "must not point at loopback in staging" in _messages(exc_info.value)

    def test_staging_profile_accepts_configured_base_urls(self):
        settings = Settings(**self._staging_base())
        assert settings.frontend_url == "https://staging.example.invalid"

    def test_staging_backup_dir_must_not_be_the_development_path(self):
        """A backup written inside the deployment tree is lost on every redeploy."""
        instance = Settings(**self._staging_base(backup_enabled=True))
        assert instance.backup_dir == str(BASE_DIR / "uploads" / "backups")

        with pytest.raises(ValueError) as exc_info:
            _finalize_settings(instance)
        assert "BACKUP_DIR must be an explicit path outside the deployment tree" in str(exc_info.value)

    def test_staging_backup_dir_on_a_durable_mount_is_accepted(self):
        instance = Settings(**self._staging_base(backup_enabled=True, backup_dir="/srv/zozi/backups"))
        assert _finalize_settings(instance) is instance

    def test_staging_backups_can_be_turned_off_explicitly(self):
        instance = Settings(**self._staging_base(backup_enabled=False))
        assert _finalize_settings(instance) is instance

    def test_production_requires_an_explicit_backup_location(self):
        """Law 86 — production must not inherit the in-repo backup path.

        `infrastructure/storage/backup.py` and `lifespan.py` both honour
        `backup_enabled`, so an in-container backup path would report backups as
        on while persisting none across a redeploy (Law 232, Law 307).
        """
        instance = Settings(**_production_base(backup_enabled=True))
        assert instance.backup_dir == str(BASE_DIR / "uploads" / "backups")
        with pytest.raises(ValueError) as exc_info:
            _finalize_settings(instance)
        assert "BACKUP_DIR must be an explicit path outside the deployment tree" in str(exc_info.value)

    def test_production_backup_on_a_durable_mount_is_accepted(self):
        instance = Settings(**_production_base(backup_enabled=True, backup_dir="/srv/zozi/backups"))
        assert _finalize_settings(instance) is instance

    def test_production_backups_can_be_turned_off_explicitly(self):
        instance = Settings(**_production_base(backup_enabled=False))
        assert _finalize_settings(instance) is instance

    def test_production_upload_dir_rule_is_scoped_to_local_storage(self):
        """STORAGE_BACKEND=r2 is mandated in production, so the local upload_dir
        requirement must not fire there — assert the rule stays scoped."""
        instance = Settings(**_production_base(storage_backend="r2", backup_enabled=False))
        assert instance.upload_dir == str(BASE_DIR / "uploads")
        assert _finalize_settings(instance) is instance

    def test_development_profile_keeps_the_development_defaults(self):
        """The dev profile is unchanged: no new requirement in development/test."""
        instance = Settings(
            app_env="development",
            secret_key=_A64,
            field_encryption_key=_A64,
            field_encryption_salt=_A32,
            audit_chain_key=_A32,
        )
        assert instance.frontend_url == DEV_FRONTEND_URL
        assert instance.backend_url == DEV_BACKEND_URL
        assert instance.ollama_base_url == "http://localhost:11434"
        assert instance.backup_dir == str(BASE_DIR / "uploads" / "backups")
        assert _finalize_settings(instance) is instance


class TestAuditChainKeyFloorIsUniform:
    """AUDIT_CHAIN_KEY had a 16-char declarative floor and a 32-char prod floor.

    Staging signs its WORM chain (Law 96) with the same key, so both floors must
    agree at 32.
    """

    def test_audit_chain_key_below_32_is_rejected_in_staging(self):
        payload = TestStagingProfileDoesNotInheritDevPaths._staging_base(
            audit_chain_key="a" * 16
        )
        with pytest.raises(ValidationError) as exc_info:
            Settings(**payload)
        assert "at least 32 characters" in _messages(exc_info.value)

    def test_audit_chain_key_of_32_is_accepted_in_staging(self):
        payload = TestStagingProfileDoesNotInheritDevPaths._staging_base(
            audit_chain_key="a" * 32
        )
        assert len(Settings(**payload).audit_chain_key) == 32