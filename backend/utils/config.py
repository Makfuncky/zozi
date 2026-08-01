"""Flexible application settings used across mixed recovery-era modules."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent.parent
logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).resolve().parent.parent


try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass


class Settings:
    _DEFAULTS: dict[str, Any] = {
        "app_name": "ZOZI Marketplace",
        "app_version": "1.0.0",
        "debug": False,
        "env": "development",
        "app_env": os.getenv("APP_ENV", "development"),
        "runtime_profile": os.getenv("RUNTIME_PROFILE", "standard"),
        "secret_key": os.getenv("SECRET_KEY", "") or ("alembic-dev-key" if os.environ.get("ALEMBIC_MODE") == "true" else ""),
        "algorithm": "HS256",
        "jwt_algorithm": "HS256",
        "access_token_expire_minutes": 60,
        "refresh_token_expire_days": 7,
        "refresh_token_cookie_name": "refresh_token",
        "refresh_cookie_samesite": "lax",
        "cors_origins": "http://localhost:3000,http://127.0.0.1:3000",
        "database_url": os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'zozi.db')}"),
        "db_pool_size": int(os.getenv("DB_POOL_SIZE", "20")),
        "db_max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "30")),
        "db_pool_recycle": int(os.getenv("DB_POOL_RECYCLE", "1800")),
        "db_connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
        "db_statement_timeout": int(os.getenv("DB_STATEMENT_TIMEOUT", "60000")),
        "stripe_secret_key": "",
        "stripe_publishable_key": "",
        "stripe_webhook_secret": "",
        "stripe_api_version": "",
        "tap_secret_key": "",
        "tap_webhook_secret": "",
        "tap_webhook_url": "",
        "openai_api_key": "",
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "email_from": "noreply@zozi.com",
        "frontend_url": "http://localhost:3000",
        "backend_url": "http://localhost:8000",
        "upload_dir": str(BASE_DIR / "uploads"),
        "max_upload_size_mb": 10,
        "backup_dir": str(BASE_DIR / "uploads" / "backups"),
        "max_backups": 48,
        "backup_max_files": 48,
        "backup_interval_minutes": 30,
        "backup_enabled": True,
        "encryption_key": "",
        "twilio_account_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
        "twilio_auth_token": os.getenv("TWILIO_AUTH_TOKEN", ""),
        "redis_url": "redis://localhost:6379",
        "default_currency": "OMR",
        "resend_api_key": "",
        "resend_webhook_secret": "",
        "google_client_id": "",
        "google_client_secret": "",
        "facebook_client_id": "",
        "facebook_client_secret": "",
        "customer_email_verification_mode": "auto",
        "readiness_require_redis": False,
        "readiness_require_email": False,
        "readiness_require_payments": False,
        "email_scheduler_enabled": False,
        "background_job_workers": 2,
        "background_job_ttl_seconds": 3600,
        "background_jobs_enabled": False,
        "bootstrap_schema_on_startup": False,
        "run_legacy_migrations_on_startup": False,
        "seed_data_on_startup": True,
        "loadtest_profile_enabled": False,
        "vat_rate": 0.0,
        "zozi_commission_rate": 0.1,
        "payout_holding_days": 7,
        "finance_auto_reconcile_batch_limit": 100,
        "finance_scheduler_enabled": False,
        "finance_scheduler_process_payouts": False,
        "finance_scheduler_dispatch_provider": "",
        "finance_scheduler_dispatch_payouts": False,
        "finance_scheduler_dispatch_dry_run": True,
        "bank_api_enabled": False,
        "bank_api_base_url": "",
        "bank_api_batch_path": "",
        "bank_api_auth_token": "",
        "bank_api_source_account_id": "",
        "bank_api_timeout_seconds": 30,
        "media_storage_base": "",
        "storage_backend": os.getenv("STORAGE_BACKEND", "local"),
        "s3_bucket": os.getenv("S3_BUCKET", ""),
        "s3_region": os.getenv("S3_REGION", "auto"),
        "s3_endpoint_url": os.getenv("S3_ENDPOINT_URL", ""),
        "s3_cdn_base": os.getenv("S3_CDN_BASE", ""),
        "s3_access_key_id": os.getenv("S3_ACCESS_KEY_ID", ""),
        "s3_secret_access_key": os.getenv("S3_SECRET_ACCESS_KEY", ""),
        "s3_presign_ttl_seconds": int(os.getenv("S3_PRESIGN_TTL_SECONDS", "900")),
        "presigned_uploads_enabled": str(os.getenv("PRESIGNED_UPLOADS_ENABLED", "false")).lower() in {"1", "true", "yes", "on"},
        "hf_api_token": "",
        "stripe_connect_auto_create_accounts": False,
        "sentry_dsn": "",
        "field_encryption_key": "",
        "field_encryption_key_from_env": "",
        "field_encryption_key_file": "",
        "field_encryption_key_source": "auto",
        "field_encryption_key_vault_addr": "",
        "field_encryption_key_vault_token": "",
        "field_encryption_key_vault_path": "",
        "field_encryption_key_vault_field": "field_encryption_key",
        "field_encryption_key_aws_ssm_parameter": "",
        "field_encryption_key_aws_region": "",
        "security_headers_enabled": True,
        "hsts_enabled": True,
        "cookie_secure": True,
        "rate_limit_enabled": True,
        "country_ai_enabled": str(os.getenv("COUNTRY_AI_ENABLED", "true")).lower() in {"1", "true", "yes", "on"},
        "country_ai_ollama_model": os.getenv("COUNTRY_AI_OLLAMA_MODEL", "llama3.1"),
        "country_ai_cache_ttl_seconds": int(os.getenv("COUNTRY_AI_CACHE_TTL_SECONDS", "86400")),
        "country_ai_web_search_enabled": str(os.getenv("COUNTRY_AI_WEB_SEARCH_ENABLED", "true")).lower() in {"1", "true", "yes", "on"},
        "country_ai_max_concurrent_jobs": int(os.getenv("COUNTRY_AI_MAX_CONCURRENT_JOBS", "5")),
    }

    _BOOL_KEYS = {
        "debug",
        "backup_enabled",
        "readiness_require_redis",
        "readiness_require_email",
        "readiness_require_payments",
        "email_scheduler_enabled",
        "bootstrap_schema_on_startup",
        "run_legacy_migrations_on_startup",
        "seed_data_on_startup",
        "loadtest_profile_enabled",
        "finance_scheduler_enabled",
        "finance_scheduler_process_payouts",
        "finance_scheduler_dispatch_payouts",
        "finance_scheduler_dispatch_dry_run",
        "bank_api_enabled",
        "stripe_connect_auto_create_accounts",
        "security_headers_enabled",
        "hsts_enabled",
        "cookie_secure",
        "rate_limit_enabled",
        "presigned_uploads_enabled",
        "country_ai_enabled",
        "country_ai_web_search_enabled",
    }
    _INT_KEYS = {
        "access_token_expire_minutes",
        "refresh_token_expire_days",
        "smtp_port",
        "max_upload_size_mb",
        "max_backups",
        "backup_max_files",
        "backup_interval_minutes",
        "background_job_workers",
        "background_job_ttl_seconds",
        "payout_holding_days",
        "finance_auto_reconcile_batch_limit",
        "bank_api_timeout_seconds",
        "db_pool_size",
        "db_max_overflow",
        "db_pool_recycle",
        "db_connect_timeout",
        "db_statement_timeout",
        "s3_presign_ttl_seconds",
        "country_ai_cache_ttl_seconds",
        "country_ai_max_concurrent_jobs",
        "finance_ai_timeout",
    }
    _FLOAT_KEYS = {"vat_rate", "zozi_commission_rate"}

    def __init__(self, **values: Any) -> None:
        object.__setattr__(self, "_overrides", {})
        object.__setattr__(self, "_field_encryption_key_cache", None)

        # Compatibility with pydantic-settings style construction used in tests.
        values.pop("_env_file", None)
        values.pop("_env_file_encoding", None)
        for key, value in values.items():
            object.__getattribute__(self, "_overrides")[self._normalize(key)] = value

        app_env = str(self._resolve("app_env")).strip().lower()
        secret_key = str(self._resolve("secret_key") or "").strip()
        if not secret_key:
            # Allow empty for alembic migration commands when ALEMBIC_MODE is set
            if os.environ.get('ALEMBIC_MODE') == 'true':
                secret_key = 'alembic-dev-key'
            else:
                raise ValueError(
                    "SECRET_KEY must be set to a strong random value. "
                    "Every restart with an ephemeral key invalidates all existing JWT tokens."
                )

        cookie_secure = self._resolve("cookie_secure")
        refresh_cookie_samesite = str(self._resolve("refresh_cookie_samesite") or "lax").lower()
        if cookie_secure and refresh_cookie_samesite == "lax":
            app_env = str(self._resolve("app_env")).lower()
            if app_env == "production":
                refresh_cookie_samesite = "none"
            object.__setattr__(self, "_overrides", dict(object.__getattribute__(self, "_overrides"), refresh_cookie_samesite=refresh_cookie_samesite))
        if cookie_secure and refresh_cookie_samesite == "none":
            import warnings
            warnings.warn(
                "cookie_secure=True with SameSite=none requires HTTPS. "
                "Ensure SSL certificates are properly configured in production.",
                UserWarning,
                stacklevel=2,
            )

        runtime_profile = str(self._resolve("runtime_profile") or "standard").strip().lower()
        if runtime_profile == "loadtest":
            object.__setattr__(self, "_overrides", dict(object.__getattribute__(self, "_overrides"), loadtest_profile_enabled=True))

        # Production-only validation
        if app_env == "production":
            sentry_dsn = str(self._resolve("sentry_dsn") or "").strip()
            if not sentry_dsn:
                raise ValueError("SENTRY_DSN is required in production")

            field_key = str(self._resolve_field_encryption_key() or "").strip()
            if not field_key:
                raise ValueError("FIELD_ENCRYPTION_KEY is required in production")

            stripe_key = str(self._resolve("stripe_secret_key") or "").strip()
            if not stripe_key:
                raise ValueError("STRIPE_SECRET_KEY is required in production")

            tap_key = str(self._resolve("tap_secret_key") or "").strip()
            if not tap_key:
                raise ValueError("TAP_SECRET_KEY is required in production")

            database_url = str(self._resolve("database_url") or "").strip()
            if not database_url:
                raise ValueError("DATABASE_URL is required in production")
            if database_url.startswith("sqlite"):
                raise ValueError("SQLite is not allowed in production; use PostgreSQL")
            
            pool_size = int(self._resolve("db_pool_size") or "20")
            if pool_size < 1 or pool_size > 100:
                raise ValueError("DB_POOL_SIZE must be between 1 and 100")

    def __getattribute__(self, name: str) -> Any:
        if name.startswith("_"):
            return object.__getattribute__(self, name)

        overrides = object.__getattribute__(self, "_overrides")
        key = object.__getattribute__(self, "_normalize")(name)
        if key == "field_encryption_key":
            return object.__getattribute__(self, "_resolve_field_encryption_key")()
        if key in overrides:
            return overrides[key]

        try:
            return object.__getattribute__(self, name)
        except AttributeError:
            return object.__getattribute__(self, "_resolve")(name)

    def _normalize(self, name: str) -> str:
        return name.lower()

    def _env_value(self, key: str) -> str | None:
        for env_name in {key.upper(), key, key.replace("__", "_").upper()}:
            value = os.getenv(env_name)
            if value is not None:
                return value
        return None

    def _coerce(self, key: str, value: Any) -> Any:
        if isinstance(value, str):
            if key in self._BOOL_KEYS:
                return value.strip().lower() in {"1", "true", "yes", "on"}
            if key in self._INT_KEYS:
                try:
                    return int(value)
                except ValueError:
                    return self._DEFAULTS.get(key, 0)
            if key in self._FLOAT_KEYS:
                try:
                    return float(value)
                except ValueError:
                    return self._DEFAULTS.get(key, 0.0)
        return value

    def _raw_value(self, key: str) -> Any:
        normalized = self._normalize(key)
        overrides = object.__getattribute__(self, "_overrides")
        if normalized in overrides:
            return overrides[normalized]

        env_value = self._env_value(normalized)
        if env_value is not None:
            return self._coerce(normalized, env_value)

        return self._DEFAULTS.get(normalized, "")

    def _resolve_local_field_encryption_key(self) -> str:
        direct_key = str(self._raw_value("field_encryption_key") or "").strip()
        if direct_key:
            return direct_key

        legacy_key = str(self._raw_value("encryption_key") or "").strip()
        if legacy_key:
            return legacy_key

        env_alias = str(self._raw_value("field_encryption_key_from_env") or "").strip()
        if env_alias:
            indirect = str(os.getenv(env_alias, "") or "").strip()
            if indirect:
                return indirect

        secret_file = str(self._raw_value("field_encryption_key_file") or "").strip()
        if secret_file:
            try:
                value = Path(secret_file).read_text(encoding="utf-8").strip()
                if value:
                    return value.splitlines()[0].strip()
            except OSError:
                return ""

        return ""

    def _load_field_encryption_key_from_vault(self) -> str:
        vault_addr = str(self._raw_value("field_encryption_key_vault_addr") or "").strip()
        vault_token = str(self._raw_value("field_encryption_key_vault_token") or "").strip()
        vault_path = str(self._raw_value("field_encryption_key_vault_path") or "").strip()
        vault_field = str(self._raw_value("field_encryption_key_vault_field") or "field_encryption_key").strip()

        if not vault_addr or not vault_token or not vault_path:
            return ""

        endpoint = f"{vault_addr.rstrip('/')}/v1/{vault_path.lstrip('/')}"
        try:
            from urllib.request import Request, urlopen

            request = Request(endpoint, headers={"X-Vault-Token": vault_token})
            with urlopen(request, timeout=3) as response:  # nosec B310 - URL is controlled by runtime configuration
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
        parameter_name = str(self._raw_value("field_encryption_key_aws_ssm_parameter") or "").strip()
        region = str(self._raw_value("field_encryption_key_aws_region") or "").strip()
        if not parameter_name:
            return ""

        try:
            import boto3

            kwargs: dict[str, Any] = {}
            if region:
                kwargs["region_name"] = region
            client = boto3.client("ssm", **kwargs)
            response = client.get_parameter(Name=parameter_name, WithDecryption=True)
            value = response.get("Parameter", {}).get("Value")
            if isinstance(value, str):
                return value.strip()
        except Exception:
            return ""
        return ""

    def _resolve_field_encryption_key(self) -> str:
        cached_key = object.__getattribute__(self, "_field_encryption_key_cache")
        if isinstance(cached_key, str) and cached_key:
            return cached_key

        overrides = object.__getattribute__(self, "_overrides")
        has_explicit_local_directive = any(
            key in overrides
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
                object.__setattr__(self, "_field_encryption_key_cache", resolved)
                return resolved

        source = str(self._raw_value("field_encryption_key_source") or "auto").strip().lower()
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

        if resolved:
            object.__setattr__(self, "_field_encryption_key_cache", resolved)
        return resolved

    def _resolve(self, name: str) -> Any:
        key = self._normalize(name)
        if key == "field_encryption_key":
            return self._resolve_field_encryption_key()
        overrides = object.__getattribute__(self, "_overrides")
        if key in overrides:
            return overrides[key]
        if key == "cors_origins_list":
            origins = str(self._resolve("cors_origins"))
            return [item.strip() for item in origins.split(",") if item.strip()]
        if key == "should_secure_cookies":
            return str(self._resolve("app_env")).lower() == "production"
        if key == "env":
            return self._resolve("app_env")
        if key == "backup_max_files":
            return self._coerce(key, self._env_value(key) or self._resolve("max_backups"))
        value = self._env_value(key)
        if value is not None:
            return self._coerce(key, value)
        if key in self._DEFAULTS:
            return self._DEFAULTS[key]
        if key.endswith(("_enabled", "_required", "_configured", "_secure", "_live")):
            return False
        if key.endswith(("_minutes", "_days", "_seconds", "_limit", "_workers", "_ttl")):
            return 0
        if key.endswith("_rate"):
            return 0.0
        return ""

    def __getattr__(self, name: str) -> Any:
        key = self._normalize(name)
        if key in self._DEFAULTS:
            logger.warning(
                "Accessing undefined setting '%s' — returning default value. "
                "This setting may not exist.", name
            )
        return self._resolve(name)

def __setattr__(self, name: str, value: Any) -> None:
    key = self._normalize(name)
    overrides = object.__getattribute__(self, "_overrides")
    overrides[key] = value
    if key.startswith("field_encryption_key") or key == "encryption_key":
        object.__setattr__(self, "_field_encryption_key_cache", None)


settings = Settings()

for _key in (
    "stripe_secret_key",
    "stripe_webhook_secret",
    "stripe_api_version",
    "tap_secret_key",
    "tap_webhook_secret",
    "tap_webhook_url",
    "frontend_url",
):
    object.__setattr__(settings, _key, settings._resolve(_key))

