# Audit Dimension 11: Environmental / Config

| Check | Description | Status | Evidence | project_completion_blocker |
|---|---|---|---|---|
| 1 | All env vars from TECHNOLOGY_STACK.md read in config | PASS | `backend/config.py` defines pydantic-settings fields for every env var in `_most_imp_docx/TECHNOLOGY_STACK.md` env-var table (APP_ENV, DATABASE_URL, DATABASE_URL_DIRECT, DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE, CORS_ORIGINS, FRONTEND_URL, BACKEND_URL, STRIPE_*, TAP_*, TWILIO_*, SMTP_*, RESEND_*, GOOGLE_*, FACEBOOK_*, CELERY_*, R2_*, OPENAI_API_KEY, HF_API_TOKEN, OLLAMA_*, BG_*, FIELD_ENCRYPTION_KEY, AUDIT_CHAIN_KEY, TRUSTED_PROXY_IPS, FRAUD_PROXY_SEED_IPS, COUNTRY_AI_*, SENTRY_DSN, etc.). `backend/providers/config.py` additionally reads HF/OPENAI/OLLAMA/BG via `os.environ.get`. | no |
| 2 | Required env vars validated at startup; missing = immediate failure | PARTIAL | `settings = Settings()` at module level triggers `model_validator(mode="after")` chain at import. Production profile (`_validate_production_environments`) raises `ValueError` for missing required vars. Development/test skip most production-only checks, so missing vars do not fail fast in dev. | no |
| 3 | No default credentials in fallbacks | PASS | No hardcoded API keys, tokens, or passwords found in any config file. Secrets default to empty string `""` and are enforced by validators in production. | no |
| 4 | APP_ENV selects correct profile (development, staging, production) | PASS | `app_env` field (alias `APP_ENV`) defaults to `"development"`. `_compute_dynamic_fields` and `_validate_production_environments` gate behavior (debug, CORS, cookie secure, validation strictness) on `app_env in ("production", "staging")`. | no |
| 5 | RUNTIME_PROFILE switches between standard and loadtest | PASS | `runtime_profile` field defaults to `"standard"`. `_validate_runtime_profile` sets `loadtest_profile_enabled = True` when `runtime_profile == "loadtest"`. | no |
| 6 | Feature flags typed via pydantic-settings | PASS | `backend/config.py` uses `pydantic_settings.BaseSettings` with explicit typed fields (`bool`, `int`, `Decimal`, `list[str]`) for all feature flags (`loadtest_profile_enabled`, `background_jobs_enabled`, `presigned_uploads_enabled`, `readiness_require_*`, `country_ai_*`, etc.). | no |
| 7 | No raw `os.getenv()` in production code | FAIL | `backend/config.py` contains raw `os.getenv()` at lines 47 (pre-bootstrap APP_ENV), 329–330 (S3→R2 migration), and 663 (indirect field-encryption-key lookup). `backend/providers/config.py` uses `os.environ.get()` for all AI/BG vars. `backend/providers/payments/config.py` uses `os.getenv()` for all payment vars. | no |
| 8 | DATABASE_URL and DATABASE_URL_DIRECT configured | PASS | `database_url` and `database_url_direct` fields are defined (defaults `""`). `_validate_production_environments` raises `ValueError` if either is missing in production/staging. | no |
| 9 | DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_RECYCLE configured | PASS | `db_pool_size` (default 50, ge=1, le=100), `db_max_overflow` (default 100, ge=1, le=200), `db_pool_recycle` (default 1800, ge=60, le=3600) are all defined and validated. | no |
| 10 | CORS_ORIGINS: empty in prod, correct in dev | FAIL | Default is `"http://localhost:3000,http://127.0.0.1:3000"` (dev-correct). However, `_validate_production_environments` **requires** `CORS_ORIGINS` to be set and explicitly rejects any value containing `localhost` or `127.0.0.1`. `TECHNOLOGY_STACK.md` states CORS should be "empty or correct production origins in prod" and is "only used in dev." The validator contradicts the documented production expectation of emptiness. | no |
| 11 | FRONTEND_URL and BACKEND_URL set | PASS | `frontend_url` (default `http://localhost:3000`) and `backend_url` (default `http://localhost:8000`) are defined. Production validator raises `ValueError` if either is missing. | no |
| 12 | Payment keys: STRIPE, TAP, PayPal | PASS | `stripe_secret_key`, `stripe_publishable_key`, `stripe_webhook_secret`, `stripe_api_version`, `tap_secret_key`, `tap_webhook_secret`, `tap_webhook_url`, `tap_api_base_url`, `paypal_mode`, `paypal_client_id`, `paypal_secret`, `paypal_webhook_secret` are all defined. Production requires STRIPE and TAP secrets; PayPal/Tap/Paytabs/Thawani are validated when partially set. | no |
| 13 | SMS/WhatsApp: TWILIO | PASS | `twilio_account_sid`, `twilio_auth_token` are defined. Production validator enforces both-or-none. `whatsapp_account_sid`, `whatsapp_auth_token`, `whatsapp_from_number` also exist for self-hosted WhatsApp. | no |
| 14 | Email: SMTP, RESEND | PASS | `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password`, `email_from` are defined. `resend_api_key`, `resend_webhook_secret` are defined. Production validator enforces SMTP completeness when any SMTP field is set, and RESEND completeness when any RESEND field is set. | no |
| 15 | OAuth: GOOGLE, FACEBOOK | PASS | `google_client_id`, `google_client_secret`, `facebook_client_id`, `facebook_client_secret` are defined. Production validator enforces both-or-none for each provider. | no |
| 16 | Celery/Valkey: CELERY_BROKER_URL, CELERY_RESULT_BACKEND | PASS | `celery_broker_url`, `celery_result_backend`, `valkey_url` are defined. Production validator raises `ValueError` if Celery URLs or Valkey URL are missing. | no |
| 17 | Storage/R2: R2_* vars | PASS | `r2_bucket`, `r2_region`, `r2_endpoint_url`, `r2_cdn_base`, `r2_access_key_id`, `r2_secret_access_key`, `r2_presign_ttl_seconds` are defined. Production validator requires all core R2 vars. | no |
| 18 | AI/ML: OPENAI_API_KEY, HF_API_TOKEN, OLLAMA_* | PASS | `openai_api_key`, `hf_api_token`, `ollama_base_url`, `ollama_model`, `ollama_text_model`, `country_ai_ollama_model` are defined in `config.py`. `backend/providers/config.py` duplicates some via `os.environ.get`. Production validator requires `HF_API_TOKEN`. | no |
| 19 | Background removal: BG_* vars | PASS | `bg_max_concurrent`, `bg_max_session_cache`, `bg_max_image_dim`, `bg_lite_max_dim`, `bg_memory_warn_mb`, `bg_skip_heavy_models` are defined in `config.py`. `backend/providers/config.py` also reads them via `os.environ.get`. | no |
| 20 | Field encryption: FIELD_ENCRYPTION_KEY | PASS | `field_encryption_key`, `field_encryption_salt`, and legacy `encryption_key` are defined. `_resolve_field_encryption_key` supports env/file/vault/AWS-SSM resolution. Production validator requires a resolved key ≥64 chars and `FIELD_ENCRYPTION_SALT`. | no |
| 21 | Audit: AUDIT_CHAIN_KEY | PASS | `audit_chain_key` is defined. Production validator raises `ValueError` if missing and enforces minimum length of 32 characters. | no |
| 22 | Trusted proxy: TRUSTED_PROXY_IPS | PASS | `trusted_proxy_ips` is defined. Production validator raises `ValueError` if missing. | no |
| 23 | Fraud: FRAUD_PROXY_SEED_IPS | PASS | `fraud_proxy_seed_ips` is defined. | no |
| 24 | Country AI: COUNTRY_AI_* vars | PASS | `country_ai_enabled`, `country_ai_ollama_model`, `country_ai_cache_ttl_seconds`, `country_ai_web_search_enabled`, `country_ai_max_concurrent_jobs` are all defined. | no |
| 25 | Observability: SENTRY_DSN | PASS | `sentry_dsn` is defined. Production validator raises `ValueError` if missing. | no |

## Summary

- **PASS**: 22 / 25
- **PARTIAL**: 1 / 25
- **FAIL**: 2 / 25
- **project_completion_blocker = yes**: 0

## Findings

### Finding ENV-01 — Raw `os.getenv()` / `os.environ.get()` in production code
- **Files**: `backend/config.py`, `backend/providers/config.py`, `backend/providers/payments/config.py`
- **Description**: Rule 7 states "No raw os.getenv() in production code." `backend/config.py` uses `os.getenv()` for pre-Settings bootstrap (line 47), S3→R2 alias migration (lines 329–330), and indirect field-encryption resolution (line 663). `backend/providers/config.py` and `backend/providers/payments/config.py` use `os.environ.get()` / `os.getenv()` for every AI, background-removal, and payment variable instead of the canonical `settings` object.
- **Impact**: Circumvents pydantic-settings validation, type coercion, and secret masking. Increases risk of reading stale or misspelled env vars.
- **Recommendation**: Migrate `backend/providers/config.py` and `backend/providers/payments/config.py` to consume the canonical `Settings` instance. Isolate the three raw `os.getenv()` calls in `backend/config.py` behind a clearly marked internal `_bootstrap` helper and document why they cannot use pydantic-settings.

### Finding ENV-02 — CORS_ORIGINS production requirement contradicts TECHNOLOGY_STACK.md
- **File**: `backend/config.py`
- **Description**: Rule 10 expects CORS_ORIGINS to be empty in production (Next.js proxy handles CORS per `TECHNOLOGY_STACK.md`). The `_validate_production_environments` validator instead **requires** `CORS_ORIGINS` to be set and rejects any value containing `localhost` or `127.0.0.1`.
- **Impact**: Operators may set CORS origins in production unnecessarily, contradicting the documented architecture where Next.js is the sole ingress and CORS is handled at the proxy layer.
- **Recommendation**: Align `_validate_production_environments` with `TECHNOLOGY_STACK.md` — allow empty `CORS_ORIGINS` in production, or remove the production CORS requirement entirely if the Next.js proxy is authoritative.

### Finding ENV-06 — Hardcoded secrets in docker-compose.monitoring.yml
- **File**: `monitoring/docker-compose.monitoring.yml`
- **Description**: `SENTRY_SECRET_KEY` hardcoded as `sentry-secret-key-change-in-production` (line 96) and `SENTRY_DB_PASSWORD` hardcoded as `sentry-password` (line 101) instead of `${VAR:?}` references. Rule 32 states "No hardcoded secrets: JWT keys, API keys, passwords from env vars or secrets manager only."
- **Impact**: Attackers who clone the repo obtain valid Sentry secret key and database password placeholders; accidental deployment with default values bypasses secret management.
- **Recommendation**: Replace hardcoded values with `${SENTRY_SECRET_KEY:?}` and `${SENTRY_DB_PASSWORD:?}` env var references.
- **Status**: RESOLVED
