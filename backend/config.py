"""Flexible application settings used across mixed recovery-era modules."""
from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import warnings
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
    _app_env = os.environ.get("APP_ENV", "development")
    # Skip .env loading when running tests so test fixtures have clean
    # env state; .env dummy values would otherwise leak into tests via the
    # module-level side-effect below (c.f. test_payments_providers "empty" tests).
    # APP_ENV=test is set by conftest.py before any test imports, so it is a
    # reliable signal even during test collection, unlike PYTEST_CURRENT_TEST
    # which is only set when a test body is actually executing.
    _in_pytest = bool(os.environ.get("PYTEST_CURRENT_TEST"))
    if _app_env == "development" and not _in_pytest:
        ROOT = Path(__file__).resolve().parent.parent
        load_dotenv(ROOT / ".env", override=False)
except ImportError:
    pass

# NOTE(CFG-008): the legacy `_BOOL_KEYS` / `_INT_KEYS` / `_FLOAT_KEYS` coercion
# dicts that used to live here were removed. They were declared and never read:
# a repo-wide grep found zero consumers by name, zero through the
# `from config import *` shim in infrastructure/utils/config.py (underscore
# names are excluded from `__all__` at the bottom of this file), and zero via
# getattr. Typed coercion is pydantic-settings' job (Law 84 / Law 203).
# `_S3_TO_R2` below is the contrasting example of a module dict that IS live —
# it is consumed by `_migrate_s3_to_r2`.
_S3_TO_R2 = {
    "s3_bucket": "r2_bucket",
    "s3_region": "r2_region",
    "s3_endpoint_url": "r2_endpoint_url",
    "s3_cdn_base": "r2_cdn_base",
    "s3_access_key_id": "r2_access_key_id",
    "s3_secret_access_key": "r2_secret_access_key",
    "s3_presign_ttl_seconds": "r2_presign_ttl_seconds",
}

# Hosts that mean "this machine". A deployed profile (staging/production) must
# never be configured to talk to itself where a real peer is required: the
# frontend in production is Cloudflare Pages (Law 216), and a loopback
# FRONTEND_URL is what silently produced a `ws://localhost:3000` connect-src in
# the production CSP (Law 36 / Law 285) and killed every WebSocket (Law 114).
_LOOPBACK_HOST_TOKENS = ("localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1")


def _contains_loopback_host(value: str) -> bool:
    """True when a URL or DSN points at the local machine.

    Substring matching on purpose, so it matches the sibling CORS check at
    `_validate_production` (`"localhost" in cors_origins`) rather than inventing
    a second, stricter parser that would disagree with it.
    """
    lowered = str(value or "").lower()
    return any(token in lowered for token in _LOOPBACK_HOST_TOKENS)


class Settings(BaseSettings):
    # NOTE: env_ignore_empty lets an explicitly-empty env var (e.g.
    # `FIELD_ENCRYPTION_KEY=`) fall back to the default instead of tripping the
    # min_length/secret Field constraints below.
    model_config = SettingsConfigDict(env_prefix="", extra="ignore", env_ignore_empty=True)

    app_name: str = Field(default="ZOZI Marketplace")
    app_version: str = Field(default="1.0.0")
    log_level: str = Field(default="INFO")
    debug: bool = Field(default=False)
    app_env: str = Field(default="development")
    runtime_profile: str = Field(default="standard")
    secret_key: str = Field(default="", min_length=32, secret=True, validate_default=False)
    algorithm: str = Field(default="HS256")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=7)
    refresh_token_cookie_name: str = Field(default="refresh_token")
    # NOTE(e2e-fix): the Next.js middleware authenticates server-side requests by
    # reading an `access_token` COOKIE:
    #     frontend/web_app/src/lib/serverAuth.ts:16
    #         rawToken = authHeader?.startsWith("Bearer ") ? ... : accessCookie
    #         -> cookieList.get("access_token")
    #     frontend/web_app/middleware.ts:57,65-75 -> role gate for
    #         /admin, /supplier, /logistics-partner
    # Browser navigations never send an Authorization header, so without this
    # cookie `getVerifiedToken()` always returned null and EVERY guarded route
    # redirected to /login?callbackUrl=... even for a valid session — the whole
    # admin/supplier/logistics area was unreachable. The token-issuing paths only
    # set the refresh cookie, so define the name here and set both.
    access_token_cookie_name: str = Field(default="access_token")
    refresh_cookie_samesite: str = Field(default="lax")
    cors_origins: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")
    database_url: str = Field(
        default="",
        pattern=r"^(?:|postgres(?:ql)?(?:\+[A-Za-z0-9_]+)?://.*|sqlite(?:\+[A-Za-z0-9_]+)?://.*)$",
    )
    database_url_direct: str = Field(default="", min_length=10)
    database_replica_url: str = Field(default="")
    postgres_db: str = Field(default="")
    postgres_user: str = Field(default="")
    postgres_password: str = Field(default="")
    db_ssl_mode: str = Field(default="")
    field_encryption_salt: str = Field(default="")
    seed_admin_password: str = Field(default="")
    seed_customer_password: str = Field(default="")
    seed_supplier_password: str = Field(default="")
    seed_logistics_password: str = Field(default="")
    seed_employee_password: str = Field(default="")
    db_pool_size: int = Field(default=50, ge=1, le=100)
    db_max_overflow: int = Field(default=40, ge=30, le=1000)
    db_pool_recycle: int = Field(default=1800)
    db_connect_timeout: int = Field(default=30)
    db_statement_timeout: int = Field(default=60000)
    stripe_secret_key: str = Field(default="")
    stripe_publishable_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")
    stripe_api_version: str = Field(default="")
    tap_secret_key: str = Field(default="")
    tap_webhook_secret: str = Field(default="")
    tap_webhook_url: str = Field(default="")
    tap_api_base_url: str = Field(default="")
    paytabs_server_key: str = Field(default="")
    paytabs_webhook_secret: str = Field(default="")
    paytabs_profile_id: str = Field(default="")
    paytabs_api_base_url: str = Field(default="")
    paytabs_callback_url: str = Field(default="")
    thawani_secret_key: str = Field(default="")
    thawani_publishable_key: str = Field(default="")
    thawani_api_base_url: str = Field(default="")
    thawani_webhook_secret: str = Field(default="")
    paypal_mode: str = Field(default="sandbox")
    openai_api_key: str = Field(default="")
    smtp_host: str = Field(default="")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    email_from: str = Field(default="")
    whatsapp_min_delay: float = Field(default=3.0)
    frontend_url: str = Field(default="http://localhost:3000")
    backend_url: str = Field(default="http://localhost:8000")
    upload_dir: str = Field(default=str(BASE_DIR / "uploads"))
    max_upload_size_mb: int = Field(default=10)
    backup_dir: str = Field(default=str(BASE_DIR / "uploads" / "backups"))
    max_backups: int = Field(default=48)
    backup_max_files: int = Field(default=48)
    backup_interval_minutes: int = Field(default=30)
    backup_enabled: bool = Field(default=True)
    backup_verify_on_create: bool = Field(default=False)
    backup_cloud_enabled: bool = Field(default=False)
    backup_cloud_provider: str = Field(default="")
    backup_s3_bucket: str = Field(default="")
    backup_s3_prefix: str = Field(default="")
    backup_s3_region: str = Field(default="")
    backup_s3_endpoint_url: str = Field(default="")
    backup_s3_access_key_id: str = Field(default="")
    backup_s3_secret_access_key: str = Field(default="")
    encryption_key: str = Field(default="")
    kms_encryption_key: str = Field(default="")
    hash_salt: str = Field(default="")
    twilio_account_sid: str = Field(default="")
    twilio_auth_token: str = Field(default="")
    valkey_url: str = Field(
        default="",
        pattern=r"^(?:|valkey://.*|rediss?://.*|unix://.*)$",
    )
    default_currency: str = Field(default="OMR")
    resend_api_key: str = Field(default="")
    resend_webhook_secret: str = Field(default="")
    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    facebook_client_id: str = Field(default="")
    facebook_client_secret: str = Field(default="")
    sso_client_id: str = Field(default="")
    customer_email_verification_mode: str = Field(default="auto")
    readiness_require_valkey: bool = Field(default=False, alias="readiness_require_valkey")
    readiness_require_email: bool = Field(default=False)
    readiness_require_payments: bool = Field(default=False)
    email_scheduler_enabled: bool = Field(default=False)
    background_job_workers: int = Field(default=2)
    background_job_ttl_seconds: int = Field(default=3600)
    background_jobs_enabled: bool = Field(default=False)
    celery_broker_url: str = Field(default="valkey://localhost:6379/1")
    celery_result_backend: str = Field(default="valkey://localhost:6379/2")
    celery_task_always_eager: bool = Field(default=False)
    ml_workers: int = Field(default=2)
    bootstrap_schema_on_startup: bool = Field(default=False)
    run_legacy_migrations_on_startup: bool = Field(default=False)
    seed_data_on_startup: bool = Field(default=True)
    loadtest_profile_enabled: bool = Field(default=False)
    vat_rate: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0"), le=Decimal("1"))
    zozi_commission_rate: Decimal = Field(default=Decimal("0.10"), ge=Decimal("0"), le=Decimal("1"))
    default_commission_rate_pct: float = Field(default=15.0)
    payout_holding_days: int = Field(default=7)
    finance_auto_reconcile_batch_limit: int = Field(default=100)
    finance_ai_timeout: int = Field(default=30)
    finance_scheduler_enabled: bool = Field(default=False)
    finance_scheduler_process_payouts: bool = Field(default=False)
    finance_scheduler_dispatch_provider: str = Field(default="")
    finance_scheduler_dispatch_payouts: bool = Field(default=False)
    finance_scheduler_dispatch_dry_run: bool = Field(default=True)
    bank_api_enabled: bool = Field(default=False)
    bank_api_base_url: str = Field(default="")
    bank_api_batch_path: str = Field(default="")
    bank_api_auth_token: str = Field(default="")
    bank_api_source_account_id: str = Field(default="")
    bank_api_timeout_seconds: int = Field(default=30)
    media_storage_base: str = Field(default="")
    storage_backend: str = Field(default="local")
    r2_bucket: str = Field(default="")
    r2_region: str = Field(default="auto")
    r2_endpoint_url: str = Field(default="")
    r2_cdn_base: str = Field(default="")
    r2_access_key_id: str = Field(default="")
    r2_secret_access_key: str = Field(default="")
    r2_presign_ttl_seconds: int = Field(default=900)
    presigned_uploads_enabled: bool = Field(default=False)
    hf_api_token: str = Field(default="")
    stripe_connect_auto_create_accounts: bool = Field(default=False)
    sentry_dsn: str = Field(default="")
    field_encryption_key: str = Field(default="", min_length=64, secret=True, validate_default=False)
    field_encryption_key_from_env: str = Field(default="")
    field_encryption_key_file: str = Field(default="")
    field_encryption_key_source: str = Field(default="auto")
    field_encryption_key_vault_addr: str = Field(default="")
    field_encryption_key_vault_token: str = Field(default="")
    field_encryption_key_vault_path: str = Field(default="")
    field_encryption_key_vault_field: str = Field(default="field_encryption_key")
    field_encryption_key_aws_ssm_parameter: str = Field(default="")
    field_encryption_key_aws_region: str = Field(default="")
    security_headers_enabled: bool = Field(default=True)
    hsts_enabled: bool = Field(default=True)
    cookie_secure: bool = Field(default=True)
    rate_limit_enabled: bool = Field(default=True)
    trusted_proxy_ips: str = Field(default="")
    fraud_proxy_seed_ips: str = Field(default="")
    audit_chain_key: str = Field(default="", min_length=32, secret=True, validate_default=False)
    location_cors_origins: str = Field(default="")
    default_accounts_json: str = Field(default="")
    login_lockout_ttl: int = Field(default=900)
    country_ai_enabled: bool = Field(default=True)
    country_ai_ollama_model: str = Field(default="llama3.1")
    country_ai_cache_ttl_seconds: int = Field(default=86400)
    country_ai_web_search_enabled: bool = Field(default=True)
    country_ai_max_concurrent_jobs: int = Field(default=5)
    zozi_retention_delete_archived: bool = Field(default=False)
    whatsapp_account_sid: str = Field(default="")
    whatsapp_auth_token: str = Field(default="")
    whatsapp_from_number: str = Field(default="")
    otel_exporter_otlp_endpoint: str = Field(default="")
    otp_ttl_seconds: int = Field(default=300)
    otp_max_attempts: int = Field(default=5)
    paypal_webhook_secret: str = Field(default="")
    paypal_client_id: str = Field(default="")
    paypal_secret: str = Field(default="")
    tap_api_base_url: str = Field(default="")
    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="moondream:latest")
    ollama_text_model: str = Field(default="phi3:mini")
    bg_max_concurrent: int = Field(default=2)
    bg_max_session_cache: int = Field(default=2)
    bg_max_image_dim: int = Field(default=1024)
    bg_lite_max_dim: int = Field(default=1024)
    bg_memory_warn_mb: int = Field(default=256)
    bg_skip_heavy_models: bool = Field(default=True)
    default_country: str = Field(default="US")
    location_http_timeout: float = Field(default=4.0)
    location_cache_ttl: int = Field(default=3600)
    location_user_agent: str = Field(default="zozi-location-service/1.0")
    sms_mode: str = Field(default="dev")
    sms_serial_port: str = Field(default="COM3")
    sms_serial_baud: int = Field(default=9600)
    sms_android_url: str = Field(default="")
    sms_retry_attempts: int = Field(default=3)
    sms_retry_delay: int = Field(default=2)
    push_mode: str = Field(default="dev")
    fcm_server_key: str = Field(default="")
    fcm_project_id: str = Field(default="")
    log_retention_days: int = Field(default=30)

    env: str = Field(default="development", alias="app_env")
    cors_origins_list: list[str] = Field(default=[])
    should_secure_cookies: bool = Field(default=False)

    def __init__(self, **values: Any) -> None:
        normalized_values = {}
        for key, value in values.items():
            normalized_values[key.lower()] = value

        normalized_values.pop("_env_file", None)
        normalized_values.pop("_env_file_encoding", None)

        app_env = str(
            normalized_values.get("app_env", os.environ.get("APP_ENV", "development"))
        ).strip().lower()
        if app_env == "test":
            normalized_values.setdefault(
                "secret_key",
                "test-secret-key-for-unit-tests-only-" + "a" * 32,
            )
            if "DATABASE_URL" not in os.environ:
                normalized_values.setdefault("database_url", "sqlite:///:memory:")
            if "DATABASE_URL_DIRECT" not in os.environ:
                normalized_values.setdefault("database_url_direct", "sqlite:///:memory:")
            normalized_values.setdefault(
                "field_encryption_salt",
                "test-salt-for-unit-tests-only",
            )
            normalized_values.setdefault(
                "field_encryption_key",
                "test-field-encryption-key-for-unit-tests-only-" + "a" * 32,
            )
            normalized_values.setdefault(
                "audit_chain_key",
                "test-audit-chain-key-for-unit-tests-only-" + "a" * 16,
            )

        super().__init__(**normalized_values)

        object.__setattr__(self, "_field_encryption_key_cache", None)

    @model_validator(mode="before")
    @classmethod
    def _validate_db_pool_size(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        pool_size_value = data.get("db_pool_size")
        if pool_size_value is not None:
            try:
                pool_size = int(pool_size_value)
            except (TypeError, ValueError):
                raise ValidationError.from_exception_data(
                    "Settings",
                    [{"type": "int_parsing", "loc": ("db_pool_size",), "input": pool_size_value}],
                )
            if pool_size < 1 or pool_size > 100:
                raise ValidationError.from_exception_data(
                    "Settings",
                    [{"type": "greater_than", "loc": ("db_pool_size",), "input": pool_size, "ctx": {"gt": 0}}],
                )
        return data

    @model_validator(mode="before")
    @classmethod
    def _validate_db_max_overflow(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        overflow_value = data.get("db_max_overflow")
        if overflow_value is not None:
            try:
                max_overflow = int(overflow_value)
            except (TypeError, ValueError):
                raise ValidationError.from_exception_data(
                    "Settings",
                    [{"type": "int_parsing", "loc": ("db_max_overflow",), "input": overflow_value}],
                )
            if max_overflow < 30:
                raise ValidationError.from_exception_data(
                    "Settings",
                    [{"type": "greater_than", "loc": ("db_max_overflow",), "input": max_overflow, "ctx": {"gt": 29}}],
                )
        return data

    @model_validator(mode="before")
    @classmethod
    def _validate_key_lengths(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        app_env = str(data.get("app_env", "development") or "development").strip().lower()
        if app_env != "production":
            return data

        secret_key = str(data.get("secret_key", "") or "").strip()
        if secret_key and len(secret_key) < 64:
            raise ValueError("SECRET_KEY must be at least 64 characters")

        audit_chain_key = str(data.get("audit_chain_key", "") or "").strip()
        if audit_chain_key and len(audit_chain_key) < 32:
            raise ValueError("AUDIT_CHAIN_KEY must be at least 32 characters")

        field_encryption_key = str(data.get("field_encryption_key", "") or "").strip()
        if field_encryption_key and len(field_encryption_key) < 64:
            raise ValueError("FIELD_ENCRYPTION_KEY must be at least 64 characters")

        return data

    @model_validator(mode="after")
    def _validate_required_secrets_in_non_production(self) -> "Settings":
        app_env = str(self.app_env or "development").strip().lower()
        if app_env == "production":
            _required_secrets = [
                "secret_key",
                "database_url",
                "database_url_direct",
                "postgres_db",
                "postgres_user",
                "postgres_password",
                "field_encryption_salt",
                "stripe_secret_key",
                "stripe_publishable_key",
                "stripe_webhook_secret",
                "tap_secret_key",
                "tap_webhook_secret",
                "tap_api_base_url",
                "paytabs_server_key",
                "paytabs_webhook_secret",
                "paytabs_profile_id",
                "paytabs_api_base_url",
                "paytabs_callback_url",
                "thawani_secret_key",
                "thawani_publishable_key",
                "thawani_api_base_url",
                "thawani_webhook_secret",
                "openai_api_key",
                "encryption_key",
                "kms_encryption_key",
                "hash_salt",
                "sentry_dsn",
                "twilio_account_sid",
                "twilio_auth_token",
                "whatsapp_account_sid",
                "whatsapp_auth_token",
                "whatsapp_from_number",
                "resend_api_key",
                "resend_webhook_secret",
                "google_client_id",
                "google_client_secret",
                "facebook_client_id",
                "facebook_client_secret",
                "sso_client_id",
                "audit_chain_key",
                "trusted_proxy_ips",
                "r2_bucket",
                "r2_endpoint_url",
                "r2_access_key_id",
                "r2_secret_access_key",
                "bank_api_auth_token",
                "bank_api_source_account_id",
                "hf_api_token",
                "paypal_secret",
                "paypal_client_id",
                "paypal_webhook_secret",
            ]
        else:
            _required_secrets = [
                "secret_key",
                "database_url",
                "database_url_direct",
                "postgres_db",
                "postgres_user",
                "postgres_password",
                "field_encryption_salt",
            ]
        missing = [
            key for key in _required_secrets
            if not str(getattr(self, key, "") or "").strip()
        ]
        if missing:
            raise ValueError(
                f"Required secret settings are not configured: {', '.join(missing)}. "
                f"Set them in .env or the environment. APP_ENV={app_env!r}"
            )
        return self

    @model_validator(mode="before")
    @classmethod
    def _migrate_s3_to_r2(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        for old, new in _S3_TO_R2.items():
            if new not in data and old in data:
                data[new] = data.pop(old)
        s3_env_map = {
            "S3_BUCKET": "r2_bucket",
            "S3_REGION": "r2_region",
            "S3_ENDPOINT_URL": "r2_endpoint_url",
            "S3_CDN_BASE": "r2_cdn_base",
            "S3_ACCESS_KEY_ID": "r2_access_key_id",
            "S3_SECRET_ACCESS_KEY": "r2_secret_access_key",
            "S3_PRESIGN_TTL_SECONDS": "r2_presign_ttl_seconds",
        }
        return data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        key = name.lower()
        logger.warning(
            "Accessing undefined setting '%s' — raising AttributeError. "
            "Define this setting explicitly or use getattr(settings, '%s', default).",
            name, name,
        )
        raise AttributeError(f"Settings has no attribute '{name}'")

    @property
    def has_smtp_config(self) -> bool:
        """True when a usable SMTP relay is configured.

        NOTE(e2e-fix): `infrastructure/messaging/email_service.py:121` reads
        `settings.has_smtp_config`, but no such attribute was ever defined, so
        `__getattr__` raised `AttributeError: Settings has no attribute
        'has_smtp_config'`. That call sits on the CUSTOMER login path:

            auth_service.json_login_user (:2750)
              -> is_customer_email_verification_required (:1673)
                -> has_live_email_delivery (email_service.py:328)
                  -> get_email_delivery_status (:310)
                    -> _get_runtime_email_config (:297)
                      -> _load_environment_email_config (:121)
                        -> settings.has_smtp_config   <-- AttributeError -> HTTP 500

        Because the branch is gated on `role == "customer"`, only customer
        logins failed with a 500 while admin/supplier/logistics succeeded.
        Defining the property makes the check work and the failure disappear.
        """
        return bool(str(self.smtp_host or "").strip())

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        key = name.lower()
        if key.startswith("field_encryption_key") or key == "encryption_key":
            object.__setattr__(self, "_field_encryption_key_cache", None)
        object.__setattr__(self, key, value)

    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        secret_key = str(self.secret_key or "").strip()
        if not secret_key:
            raise ValueError(
                "SECRET_KEY must be set to a strong random value. "
                "Every restart with an ephemeral key invalidates all existing JWT tokens."
            )
        if secret_key.lower() in {"change-me-in-production", "change-me", "changeme", "secret", "secret-key", "default"}:
            raise ValueError(
                "SECRET_KEY must not be a placeholder value. "
                "Generate one, e.g. python -c \"import secrets; secrets.token_hex(32)\""
            )
        return self

    @model_validator(mode="after")
    def _validate_cookie_secure(self) -> "Settings":
        cookie_secure = self.cookie_secure
        refresh_cookie_samesite = str(self.refresh_cookie_samesite or "lax").lower()
        if cookie_secure and refresh_cookie_samesite == "lax":
            app_env = str(self.app_env or "").lower()
            if app_env == "production":
                self.refresh_cookie_samesite = "none"
        if cookie_secure and self.refresh_cookie_samesite == "none":
            warnings.warn(
                "cookie_secure=True with SameSite=none requires HTTPS. "
                "Ensure SSL certificates are properly configured in production.",
                UserWarning,
                stacklevel=2,
            )
        return self

    @model_validator(mode="after")
    def _validate_runtime_profile(self) -> "Settings":
        runtime_profile = str(self.runtime_profile or "standard").strip().lower()
        if runtime_profile == "loadtest":
            self.loadtest_profile_enabled = True
        return self

    @model_validator(mode="after")
    def _compute_dynamic_fields(self) -> "Settings":
        origins = str(self.cors_origins or "").strip()
        self.cors_origins_list = [item.strip() for item in origins.split(",") if item.strip()]
        self.should_secure_cookies = str(self.app_env or "").lower() == "production"
        object.__setattr__(self, "env", self.app_env)
        if not self.backup_max_files:
            self.backup_max_files = self.max_backups
        return self

    @model_validator(mode="after")
    def _validate_database_url_scheme(self) -> "Settings":
        app_env = str(self.app_env or "").lower()
        if app_env != "production":
            return self
        database_url = str(self.database_url or "").strip()
        if database_url and not database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' scheme in production. "
                f"Current value: {database_url!r}"
            )
        return self

    @model_validator(mode="after")
    def _validate_valkey_url_scheme(self) -> "Settings":
        app_env = str(self.app_env or "").lower()
        if app_env != "production":
            return self
        valkey_url = str(self.valkey_url or "").strip()
        if valkey_url and not valkey_url.startswith("valkey://"):
            raise ValueError(
                "VALKEY_URL must use the 'valkey://' scheme in production. "
                f"Current value: {valkey_url!r}"
            )
        return self

    @model_validator(mode="after")
    def _sync_jwt_algorithm(self) -> "Settings":
        algorithm = str(self.algorithm or "HS256").strip()
        object.__setattr__(self, "jwt_algorithm", algorithm)
        return self

    @model_validator(mode="after")
    def _validate_production(self) -> "Settings":
        app_env = str(self.app_env or "").lower()
        if app_env != "production":
            return self

        sentry_dsn = str(self.sentry_dsn or "").strip()
        if not sentry_dsn:
            raise ValueError("SENTRY_DSN is required in production")

        field_key = str(self._resolve_field_encryption_key() or "").strip()
        if not field_key:
            raise ValueError("FIELD_ENCRYPTION_KEY is required in production")

        stripe_key = str(self.stripe_secret_key or "").strip()
        if not stripe_key:
            raise ValueError("STRIPE_SECRET_KEY is required in production")

        tap_key = str(self.tap_secret_key or "").strip()
        if not tap_key:
            raise ValueError("TAP_SECRET_KEY is required in production")

        kms_key = str(self.kms_encryption_key or "").strip()
        if not kms_key:
            raise ValueError("KMS_ENCRYPTION_KEY must be set in production")

        hash_salt = str(self.hash_salt or "").strip()
        if not hash_salt:
            raise ValueError("HASH_SALT must be set in production")

        database_url = str(self.database_url or "").strip()
        if not database_url:
            raise ValueError("DATABASE_URL is required in production")
        if database_url.startswith("sqlite"):
            raise ValueError("SQLite is not allowed in production; use PostgreSQL")
        if not database_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL must use the 'postgresql+asyncpg://' scheme in production. "
                f"Current value: {database_url!r}"
            )

        database_url_direct = str(self.database_url_direct or "").strip()
        if not database_url_direct:
            raise ValueError("DATABASE_URL_DIRECT is required in production")
        if database_url_direct.startswith("sqlite"):
            raise ValueError("SQLite is not allowed in production; use PostgreSQL")
        if not database_url_direct.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL_DIRECT must use the 'postgresql+asyncpg://' scheme in production. "
                f"Current value: {database_url_direct!r}"
            )

        pool_size = int(self.db_pool_size or 20)
        if pool_size < 1 or pool_size > 100:
            raise ValueError("DB_POOL_SIZE must be between 1 and 100")

        cors_origins = str(self.cors_origins or "").strip()
        if not cors_origins:
            raise ValueError("CORS_ORIGINS must be set in production")
        if "localhost" in cors_origins or "127.0.0.1" in cors_origins:
            raise ValueError("CORS_ORIGINS must not contain localhost/127.0.0.1 in production")

        if self.debug:
            raise ValueError("debug must be False in production")

        otel_endpoint = str(self.otel_exporter_otlp_endpoint or "").strip()
        if not otel_endpoint:
            raise ValueError("OTEL_EXPORTER_OTLP_ENDPOINT is required in production")

        smtp_host = str(self.smtp_host or "").strip()
        smtp_port = int(self.smtp_port or 0)
        smtp_user = str(self.smtp_user or "").strip()
        smtp_password = str(self.smtp_password or "").strip()
        if not smtp_host or not smtp_port or not smtp_user or not smtp_password:
            raise ValueError("SMTP (smtp_host, smtp_port, smtp_user, smtp_password) is required in production")

        twilio_account_sid = str(self.twilio_account_sid or "").strip()
        twilio_auth_token = str(self.twilio_auth_token or "").strip()
        whatsapp_account_sid = str(self.whatsapp_account_sid or "").strip()
        whatsapp_auth_token = str(self.whatsapp_auth_token or "").strip()
        whatsapp_from_number = str(self.whatsapp_from_number or "").strip()
        if not twilio_account_sid or not twilio_auth_token:
            raise ValueError("TWILIO (twilio_account_sid, twilio_auth_token) is required in production")
        if not whatsapp_account_sid or not whatsapp_auth_token or not whatsapp_from_number:
            raise ValueError("WHATSAPP (whatsapp_account_sid, whatsapp_auth_token, whatsapp_from_number) is required in production")

        resend_api_key = str(self.resend_api_key or "").strip()
        resend_webhook_secret = str(self.resend_webhook_secret or "").strip()
        if not resend_api_key or not resend_webhook_secret:
            raise ValueError("RESEND (resend_api_key, resend_webhook_secret) is required in production")

        google_client_id = str(self.google_client_id or "").strip()
        google_client_secret = str(self.google_client_secret or "").strip()
        if not google_client_id or not google_client_secret:
            raise ValueError("GOOGLE (google_client_id, google_client_secret) is required in production")

        facebook_client_id = str(self.facebook_client_id or "").strip()
        facebook_client_secret = str(self.facebook_client_secret or "").strip()
        if not facebook_client_id or not facebook_client_secret:
            raise ValueError("FACEBOOK (facebook_client_id, facebook_client_secret) is required in production")

        sso_client_id = str(self.sso_client_id or "").strip()
        if not sso_client_id:
            raise ValueError("SSO (sso_client_id) is required in production")

        valkey_url = str(self.valkey_url or "").strip()
        if not valkey_url:
            raise ValueError("VALKEY (valkey_url) is required in production")

        celery_broker_url = str(self.celery_broker_url or "").strip()
        celery_result_backend = str(self.celery_result_backend or "").strip()
        if not celery_broker_url or not celery_result_backend:
            raise ValueError("CELERY (celery_broker_url, celery_result_backend) is required in production")
        # The check above is non-emptiness only, so a SQLite broker (forbidden as
        # a Celery broker — TECHNOLOGY_STACK §20) used to pass it. Enforce the
        # scheme the technology stack mandates. Values are deliberately NOT
        # echoed in the message: a broker URL can carry a password (Law 82).
        for celery_var, celery_url in (
            ("CELERY_BROKER_URL", celery_broker_url),
            ("CELERY_RESULT_BACKEND", celery_result_backend),
        ):
            if celery_url.startswith("sqlite"):
                raise ValueError(
                    f"{celery_var} must be a Valkey URL in production; SQLite is "
                    "forbidden as a Celery broker or result backend"
                )
            if not celery_url.startswith(("valkey://", "redis://", "rediss://")):
                raise ValueError(
                    f"{celery_var} must use the 'valkey://' scheme in production"
                )

        bank_api_enabled = bool(self.bank_api_enabled)
        if bank_api_enabled:
            bank_api_base_url = str(self.bank_api_base_url or "").strip()
            bank_api_auth_token = str(self.bank_api_auth_token or "").strip()
            bank_api_source_account_id = str(self.bank_api_source_account_id or "").strip()
            if not bank_api_base_url or not bank_api_auth_token or not bank_api_source_account_id:
                raise ValueError("BANK_API (bank_api_base_url, bank_api_auth_token, bank_api_source_account_id) is required in production when enabled")

        media_storage_base = str(self.media_storage_base or "").strip()
        if not media_storage_base:
            raise ValueError("MEDIA_STORAGE (media_storage_base) is required in production")

        hf_api_token = str(self.hf_api_token or "").strip()
        if not hf_api_token:
            raise ValueError("HF_API_TOKEN is required in production")

        stripe_publishable_key = str(self.stripe_publishable_key or "").strip()
        stripe_webhook_secret = str(self.stripe_webhook_secret or "").strip()
        if not stripe_publishable_key or not stripe_webhook_secret:
            raise ValueError("STRIPE_PUBLISHABLE_KEY and STRIPE_WEBHOOK_SECRET are required in production")

        tap_webhook_secret = str(self.tap_webhook_secret or "").strip()
        tap_api_base_url = str(self.tap_api_base_url or "").strip()
        if not tap_webhook_secret or not tap_api_base_url:
            raise ValueError("TAP_WEBHOOK_SECRET and TAP_API_BASE_URL are required in production")

        paypal_secret = str(self.paypal_secret or "").strip()
        paypal_client_id = str(self.paypal_client_id or "").strip()
        paypal_webhook_secret = str(self.paypal_webhook_secret or "").strip()
        if not paypal_secret or not paypal_client_id or not paypal_webhook_secret:
            raise ValueError("PAYPAL_SECRET, PAYPAL_CLIENT_ID, and PAYPAL_WEBHOOK_SECRET are required in production")

        paytabs_server_key = str(self.paytabs_server_key or "").strip()
        paytabs_webhook_secret = str(self.paytabs_webhook_secret or "").strip()
        paytabs_api_base_url = str(self.paytabs_api_base_url or "").strip()
        if not paytabs_server_key or not paytabs_webhook_secret or not paytabs_api_base_url:
            raise ValueError("PAYTABS (paytabs_server_key, paytabs_webhook_secret, paytabs_api_base_url) are required in production")

        thawani_secret_key = str(self.thawani_secret_key or "").strip()
        thawani_publishable_key = str(self.thawani_publishable_key or "").strip()
        thawani_api_base_url = str(self.thawani_api_base_url or "").strip()
        thawani_webhook_secret = str(self.thawani_webhook_secret or "").strip()
        if not thawani_secret_key or not thawani_publishable_key or not thawani_api_base_url or not thawani_webhook_secret:
            raise ValueError("THAWANI (thawani_secret_key, thawani_publishable_key, thawani_api_base_url, thawani_webhook_secret) are required in production")

        audit_chain_key = str(self.audit_chain_key or "").strip()
        if not audit_chain_key:
            raise ValueError("AUDIT_CHAIN_KEY is required in production")

        trusted_proxy_ips = str(self.trusted_proxy_ips or "").strip()
        if not trusted_proxy_ips:
            raise ValueError("TRUSTED_PROXY_IPS is required in production")

        r2_bucket = str(self.r2_bucket or "").strip()
        r2_endpoint_url = str(self.r2_endpoint_url or "").strip()
        r2_access_key_id = str(self.r2_access_key_id or "").strip()
        r2_secret_access_key = str(self.r2_secret_access_key or "").strip()
        if not r2_bucket or not r2_endpoint_url or not r2_access_key_id or not r2_secret_access_key:
            raise ValueError("R2_BUCKET, R2_ENDPOINT_URL, R2_ACCESS_KEY_ID, and R2_SECRET_ACCESS_KEY are required in production")

        frontend_url = str(self.frontend_url or "").strip()
        backend_url = str(self.backend_url or "").strip()
        if not frontend_url or not backend_url:
            raise ValueError("FRONTEND_URL and BACKEND_URL are required in production")
        # Non-emptiness is not enough. middleware/security_headers.py builds the
        # production CSP connect-src from FRONTEND_URL alone, so a loopback value
        # published `ws://localhost:3000` as an allowed WebSocket origin and
        # silently blocked every realtime connection in production (Law 36,
        # Law 114, Law 285). Values are NOT echoed: a base URL can carry
        # credentials (Law 82).
        if _contains_loopback_host(frontend_url) or _contains_loopback_host(backend_url):
            raise ValueError(
                "FRONTEND_URL and BACKEND_URL must not point at loopback in production. "
                "The development defaults (http://localhost:3000 / :8000) must not "
                "survive into the production profile (Law 86); set the public "
                "Cloudflare Pages / API URLs."
            )

        return self

    @model_validator(mode="after")
    def _validate_staging(self) -> "Settings":
        app_env = str(self.app_env or "").lower()
        if app_env != "staging":
            return self

        if self.debug:
            raise ValueError("debug must be False in staging")

        cors_origins = str(self.cors_origins or "").strip()
        if "localhost" in cors_origins or "127.0.0.1" in cors_origins:
            raise ValueError("CORS_ORIGINS must not contain localhost/127.0.0.1 in staging")

        database_url = str(self.database_url or "").strip()
        if database_url.startswith("sqlite"):
            raise ValueError("SQLite is not allowed in staging; use PostgreSQL")

        # Staging is a real shared deployment (Law 205, Law 220) that signs its
        # WORM chain and serves real traffic. It must not inherit the development
        # base URLs any more than production must (Law 86).
        frontend_url = str(self.frontend_url or "").strip()
        backend_url = str(self.backend_url or "").strip()
        if _contains_loopback_host(frontend_url) or _contains_loopback_host(backend_url):
            raise ValueError(
                "FRONTEND_URL and BACKEND_URL must not point at loopback in staging; "
                "the staging profile must not inherit the development defaults (Law 86)."
            )

        return self

    def _resolve_local_field_encryption_key(self) -> str:
        direct_key = str(getattr(self, "field_encryption_key", "") or "").strip()
        if direct_key:
            return direct_key

        legacy_key = str(getattr(self, "encryption_key", "") or "").strip()
        if legacy_key:
            return legacy_key

        env_alias = str(getattr(self, "field_encryption_key_from_env", "") or "").strip()
        if env_alias:
            indirect = str(os.environ.get(env_alias, "") or "").strip()
            if indirect:
                return indirect

        secret_file = str(getattr(self, "field_encryption_key_file", "") or "").strip()
        if secret_file:
            try:
                value = Path(secret_file).read_text(encoding="utf-8").strip()
                if value:
                    return value.splitlines()[0].strip()
            except OSError:
                return ""

        return ""

    def _load_field_encryption_key_from_vault(self) -> str:
        vault_addr = str(getattr(self, "field_encryption_key_vault_addr", "") or "").strip()
        vault_token = str(getattr(self, "field_encryption_key_vault_token", "") or "").strip()
        vault_path = str(getattr(self, "field_encryption_key_vault_path", "") or "").strip()
        vault_field = str(getattr(self, "field_encryption_key_vault_field", "field_encryption_key") or "field_encryption_key").strip()

        if not vault_addr or not vault_token or not vault_path:
            return ""

        endpoint = f"{vault_addr.rstrip('/')}/v1/{vault_path.lstrip('/')}"
        try:
            from urllib.request import Request, urlopen
            request = Request(endpoint, headers={"X-Vault-Token": vault_token})
            with urlopen(request, timeout=3) as response:  # nosec B310
                payload = json.loads(response.read().decode("utf-8"))
        except Exception:
            return ""

        if not isinstance(payload, dict):
            return ""

        primary_data = payload.get("data")
        if isinstance(primary_data, dict):
            nested_data = primary_data.get("data")
            if isinstance(nested_data, dict):
                value = nested_data.get(vault_field)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            value = primary_data.get(vault_field)
            if isinstance(value, str) and value.strip():
                return value.strip()

        value = payload.get(vault_field)
        if isinstance(value, str) and value.strip():
            return value.strip()
        return ""

    def _load_field_encryption_key_from_aws_ssm(self) -> str:
        parameter_name = str(getattr(self, "field_encryption_key_aws_ssm_parameter", "") or "").strip()
        region = str(getattr(self, "field_encryption_key_aws_region", "") or "").strip()
        if not parameter_name:
            return ""

        try:
            from providers.storage import create_ssm_client
            client = create_ssm_client(region)
            response = client.get_parameter(Name=parameter_name, WithDecryption=True)
            value = response.get("Parameter", {}).get("Value")
            if isinstance(value, str):
                return value.strip()
        except Exception:
            return ""
        return ""

    def _resolve_field_encryption_key(self) -> str:
        try:
            cached_key = object.__getattribute__(self, "_field_encryption_key_cache")
        except AttributeError:
            object.__setattr__(self, "_field_encryption_key_cache", None)
            cached_key = None
        if isinstance(cached_key, str) and cached_key:
            return cached_key

        has_explicit_local_directive = any(
            key in self.__dict__
            for key in (
                "field_encryption_key",
                "encryption_key",
                "field_encryption_key_from_env",
                "field_encryption_key_file",
            )
        )
        if has_explicit_local_directive:
            resolved = self._resolve_local_field_encryption_key()
            if resolved:
                salt = str(getattr(self, "field_encryption_salt", "") or "").strip()
                if salt:
                    resolved = hashlib.sha256((resolved + salt).encode()).hexdigest()
                object.__setattr__(self, "_field_encryption_key_cache", resolved)
                return resolved

        source = str(getattr(self, "field_encryption_key_source", "auto") or "auto").strip().lower()
        if source not in {"auto", "env", "vault", "aws_ssm"}:
            source = "auto"

        resolved = ""
        if source == "env":
            resolved = self._resolve_local_field_encryption_key()
        elif source == "vault":
            resolved = self._load_field_encryption_key_from_vault()
            if not resolved:
                resolved = self._resolve_local_field_encryption_key()
        elif source == "aws_ssm":
            resolved = self._load_field_encryption_key_from_aws_ssm()
            if not resolved:
                resolved = self._resolve_local_field_encryption_key()
        else:
            resolved = self._resolve_local_field_encryption_key()
        if not resolved and source == "auto":
            resolved = self._load_field_encryption_key_from_vault()
        if not resolved and source == "auto":
            resolved = self._load_field_encryption_key_from_aws_ssm()

        if isinstance(resolved, str) and resolved:
            salt = str(getattr(self, "field_encryption_salt", "") or "").strip()
            if salt:
                resolved = hashlib.sha256((resolved + salt).encode()).hexdigest()

        if resolved:
            object.__setattr__(self, "_field_encryption_key_cache", resolved)
        return resolved


def _validate_deployed_profile(instance: Settings) -> None:
    """Law 86 for the values a `Settings` validator cannot police.

    `_finalize_settings` runs on the process-wide singleton, i.e. on the actual
    boot path, exactly like the pre-existing `storage_backend != "r2"` guard.
    That placement is deliberate: these rules are requirements on a DEPLOYMENT's
    configuration, and putting them on every `Settings(...)` construction would
    make them assertions about every ad-hoc instantiation too.

    development and test keep the in-repo defaults. staging and production must
    choose deliberately:
      * a backup path under the deployment tree is inside the container image and
        is destroyed on every redeploy, so `backup_enabled=True` would report
        backups as on while silently persisting none (Law 232, Law 307);
      * a local upload_dir is only meaningful when the storage backend is local —
        production pins STORAGE_BACKEND=r2 (see `_finalize_settings`);
      * an AI endpoint without a scheme is a typo the client cannot use (Law 84).
    """
    app_env = str(instance.app_env or "").strip().lower()
    if app_env not in ("staging", "production"):
        return

    deployment_root = str(BASE_DIR).lower()

    if instance.backup_enabled:
        backup_dir = str(instance.backup_dir or "").strip()
        if not backup_dir or deployment_root in backup_dir.lower():
            raise ValueError(
                f"BACKUP_DIR must be an explicit path outside the deployment tree while "
                f"BACKUP_ENABLED is true in {app_env}. The built-in default "
                f"'{BASE_DIR / 'uploads' / 'backups'}' is a development path and is "
                "ephemeral inside a container, so backups written there are lost on every "
                "redeploy. Set BACKUP_DIR to a durable mount, or set BACKUP_ENABLED=false. "
                "(Law 86, Law 232, Law 307)"
            )

    if str(instance.storage_backend or "").strip().lower() != "r2":
        upload_dir = str(instance.upload_dir or "").strip()
        if not upload_dir or deployment_root in upload_dir.lower():
            raise ValueError(
                f"UPLOAD_DIR must be an explicit path outside the deployment tree while "
                f"STORAGE_BACKEND is '{instance.storage_backend}' in {app_env}. The built-in "
                "default is a development path. Set UPLOAD_DIR to a durable mount, or set "
                "STORAGE_BACKEND=r2. (Law 86, TECHNOLOGY_STACK §20)"
            )

    ollama_base_url = str(instance.ollama_base_url or "").strip()
    if not ollama_base_url.startswith(("http://", "https://")):
        raise ValueError(
            f"OLLAMA_BASE_URL must be an absolute http(s) URL in {app_env}; the "
            "configured value does not start with a scheme. (Law 84)"
        )


def _finalize_settings(instance: Settings) -> Settings:
    if instance.app_env == "production" and instance.storage_backend != "r2":
        raise ValueError(
            "STORAGE_BACKEND must be 'r2' in production. "
            f"Current value: {instance.storage_backend!r}"
        )

    _validate_deployed_profile(instance)

    for _key in (
        "stripe_secret_key",
        "stripe_webhook_secret",
        "stripe_api_version",
        "tap_secret_key",
        "tap_webhook_secret",
        "tap_webhook_url",
        "frontend_url",
    ):
        object.__setattr__(instance, _key, getattr(instance, _key))
    return instance


def get_settings() -> Settings:
    """Return the process-wide Settings singleton, built on first access.

    Instantiating ``Settings`` at import time made ``import backend.config``
    fail (env/secrets validation) before callers could configure anything, so
    the singleton is created lazily on first ``settings`` attribute access.
    """
    existing = globals().get("settings")
    if existing is not None:
        return existing
    instance = _finalize_settings(Settings())
    globals()["settings"] = instance
    return instance


def __getattr__(name: str) -> Any:
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [name for name in list(globals()) if not name.startswith("_")]
if "settings" not in __all__:
    __all__.append("settings")
