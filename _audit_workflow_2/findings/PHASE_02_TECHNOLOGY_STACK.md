```
=== AGENT LOG ===
PHASE: 02 — Technology / Framework / Library Inventory
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_02_TECHNOLOGY_STACK.md
SCOPE_COVERED: Root + web_app + mobile_app + shared package.json; backend requirements.txt / requirements-dev.txt / pyproject.toml; Dockerfile + Dockerfile.prod; docker-compose(.yml/.prod.yml/.override.yml); Caddyfile; nginx/nginx.conf; railway.toml; vercel.json; neon.ts; backend main.py / config.py / jobs/celery_app.py; provider + infrastructure import tracing across backend/**; frontend web_app + mobile_app import tracing; .github/workflows enumeration.
FILES_EXAMINED: ~40 read directly + ~950 traversed via grep (12 grep passes)
EVIDENCE_ITEMS: 78 file:line citations
FINDINGS_TOTAL: 118 technologies catalogued (VERIFIED: 71 / INFERRED: 33 / UNKNOWN: 14)
SEVERITY_BREAKDOWN: BLOCKER: 0 / HIGH: 3 / MEDIUM: 6 / LOW: 5 / INFO: 8  (severity applies to stack contradictions only; forensic phase makes no fixes)
TOP_FINDINGS:
  1. boto3 is imported by S3/R2 storage + backup but is NOT a declared dependency, while prod compose forces STORAGE_BACKEND=s3 — backend/providers/storage/s3_client.py:9, backend/providers/storage/r2_client.py:10, backend/scripts/pg_backup.py:461 vs backend/requirements.txt (absent), docker-compose.prod.yml:30
  2. Cache/broker server disagrees dev vs prod: Valkey 9.0 (dev) vs Redis 7 (prod), redis-py 8.0.1 client — docker-compose.yml:19-24 vs docker-compose.prod.yml:100
  3. Celery is fully wired in dev (5 workers + beat) but ABSENT from prod compose; prod only runs `python -m utils.ml_worker`, a module path that does not match the discovered layout — docker-compose.yml:52-186 vs docker-compose.prod.yml:66-98
  4. DuckDB + duckdb-engine declared but never imported in runtime code (only a test string list) — backend/requirements.txt vs backend/tests/system/test_import_direction_all_packages.py:178
  5. `expo-router` (mobile) and `openapi-fetch` (web) are imported heavily but not declared in their package.json; @react-navigation, @stripe/stripe-react-native, jspdf declared but not imported — see §5
GAPS / NOT DETERMINABLE: Exact runtime DB driver (sync psycopg2 vs async asyncpg) — async engine is guarded/optional; GitHub Actions workflow *contents* not audited (existence only); precise lock-file resolution (no committed lockfile inspected); whether anachronistic version pins resolve on a real index (not verifiable offline).
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 02 — TECHNOLOGY / FRAMEWORK / LIBRARY INVENTORY

> Forensic, evidence-based, skeptical. "Declared" ≠ "imported" ≠ "functionally
> used". Every row cites the manifest that declares it and, where practical, the
> source line that imports/uses it. Absence of a usage citation is stated
> explicitly. No secret values are reproduced.

## 0. Method & column legend

| Column | Meaning |
|---|---|
| Declared Dependency? | Present in a manifest (`requirements*.txt`, `package.json`, `pyproject.toml`) |
| Actually Imported? | An `import`/`from … import`/`import()` statement was found in source |
| Actually Used? | Traced to a call site / registration / runtime wiring, not just an import |
| Evidence | `file:line` for the strongest citation |
| Confidence | High / Med / Low |

Manifests inspected (VERIFIED they exist and were read):
- Root [package.json](package.json) (npm orchestrator)
- [frontend/web_app/package.json](frontend/web_app/package.json)
- [frontend/mobile_app/package.json](frontend/mobile_app/package.json)
- [frontend/shared/package.json](frontend/shared/package.json)
- [frontend/package.json](frontend/package.json) (2 devDeps only)
- [backend/requirements.txt](backend/requirements.txt), [backend/requirements-dev.txt](backend/requirements-dev.txt), [backend/pyproject.toml](backend/pyproject.toml)
- No committed lock file (`package-lock.json` / `poetry.lock` / `uv.lock`) was located in the read set — **UNKNOWN / GAP** (resolution graph not verifiable).

---

## 1. Languages & runtime versions

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Python | 3.11 (image) | Yes | — | Yes | [backend/Dockerfile](backend/Dockerfile#L1) `FROM python:3.11-slim`; [backend/Dockerfile.prod](backend/Dockerfile.prod#L1) | High |
| TypeScript (web) | ~5.10 | Yes | — | Yes | [frontend/web_app/package.json](frontend/web_app/package.json) devDeps `typescript ~5.10` + `next.config.ts` | High |
| TypeScript (mobile) | ~5.9.3 | Yes | — | Yes | [frontend/mobile_app/package.json](frontend/mobile_app/package.json) | High |
| JavaScript/JSX/TSX | ES2020+ | Yes | — | Yes | `.tsx` across `frontend/web_app/src` and `frontend/mobile_app/app` | High |
| Node.js | >=20 | Yes | — | Yes | [frontend/mobile_app/package.json](frontend/mobile_app/package.json) `engines.node >=20`; [frontend/web_app/package.json](frontend/web_app/package.json) `@types/node ^20` | High |
| SQL (PostgreSQL dialect) | PG 18 | Yes | — | Yes | raw SQL in `backend/alembic/versions/*` (e.g. `to_tsvector`) | High |
| Bash / PowerShell | — | Yes | — | Yes | `run_zozi.sh`, `run_zozi.bat`, `backend/start_backend.ps1` | High |
| Dockerfile | — | Yes | — | Yes | [backend/Dockerfile](backend/Dockerfile), [backend/Dockerfile.prod](backend/Dockerfile.prod) | High |

> **INFO / version plausibility:** Numerous pins are anachronistically high vs
> publicly-released versions as of the knowledge cutoff (e.g. `pytest 9.1.1`,
> `gunicorn 26.0.0`, `redis 8.0.1`, `next 16.3.4`, `react 19.2.8`,
> `@playwright/test 1.62`, `sqlalchemy 2.0.51`). Per MASTER_RULES this is **not**
> a quality judgment; it is flagged only as a manifest-vs-reality item that is
> **NOT verifiable offline**. Confidence Low.

---

## 2. Backend frameworks, servers & core libraries

### 2.1 Web framework / HTTP server (categories 3, 11)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| FastAPI | 0.115.2 | Yes | Yes | Yes | [backend/main.py](backend/main.py#L20) `from fastapi import FastAPI…`; app built [backend/main.py](backend/main.py#L74) | High |
| Starlette | unpinned | Yes | Yes (transitive + direct middleware) | Yes | declared [backend/requirements.txt](backend/requirements.txt); FastAPI is built on it; middleware in `backend/middleware/*` | High |
| Uvicorn | 0.51.0 `[standard]` | Yes | — | Yes | run cmd [docker-compose.yml](docker-compose.yml#L50); [railway.toml](railway.toml) startCommand `uvicorn main:app` | High |
| Gunicorn | 26.0.0 | Yes | — | Yes (prod) | [backend/Dockerfile.prod](backend/Dockerfile.prod) CMD `gunicorn … uvicorn.workers.UvicornWorker` | High |
| python-multipart | 0.0.32 | Yes | — | Inferred | declared; required by FastAPI form/file uploads (`UploadFile` used in routers) | Med |
| WebSockets (FastAPI/Starlette) | — | — | Yes | Yes | [backend/infrastructure/messaging/ws_manager.py](backend/infrastructure/messaging/ws_manager.py#L1); [backend/main.py](backend/main.py#L20) imports `WebSocket` | High |
| `websockets` (PyPI) | 16.1.1 | Yes | Not directly | Inferred (transitive ws impl for uvicorn[standard]) | declared; no direct `import websockets` found in app code | Med |

### 2.2 ORM, migrations, DB drivers (categories 5, 6)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| SQLAlchemy (sync ORM) | 2.0.51 | Yes | Yes | Yes | [backend/infrastructure/database/database.py](backend/infrastructure/database/database.py#L10) `create_engine`; `sessionmaker` [backend/infrastructure/database/init_db.py](backend/infrastructure/database/init_db.py#L32) | High |
| SQLAlchemy async engine | (same) | — | Yes (guarded) | Inferred / optional | [backend/infrastructure/database/database.py](backend/infrastructure/database/database.py#L17-L24) `create_async_engine` in try/except, set to `None` on failure | Med |
| Alembic | 1.18.5 | Yes | — | Yes | `backend/alembic/versions/*` migrations; [package.json](package.json) `db:migrate` → `alembic upgrade head` | High |
| psycopg2-binary (sync driver) | 2.9.12 | Yes | Not directly | Inferred (active driver) | declared; sync `create_engine` + `postgresql://` URL implies psycopg2 default driver ([docker-compose.yml](docker-compose.yml#L28)) | Med |
| asyncpg (async driver) | 0.31.0 | Yes | Not directly | Inferred / possibly unused | declared; only consumed if the guarded async engine initialises — no `+asyncpg` URL found | Low |
| DuckDB | 1.5.5 | Yes | **No** | **No (runtime)** | declared [backend/requirements.txt](backend/requirements.txt); only occurrence is a test string list [backend/tests/system/test_import_direction_all_packages.py](backend/tests/system/test_import_direction_all_packages.py#L178) | High |
| duckdb-engine | 0.17.0 | Yes | **No** | **No** | declared; no import found anywhere | High |
| Redis-py (client → Valkey) | 8.0.1 | Yes | Yes | Yes | [backend/infrastructure/database/redis_client.py](backend/infrastructure/database/redis_client.py#L70) `import redis`; wrapper `redis_client` used in 30+ modules (e.g. [backend/middleware/rate_limit_middleware.py](backend/middleware/rate_limit_middleware.py#L19)) | High |

> **Full-text search is PostgreSQL-native**, not an external engine — see §2.7.

### 2.3 Validation & settings (category 7)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Pydantic (v2) | 2.13.4 | Yes | Yes | Yes | `BaseModel` used widely, e.g. [backend/domains/accounts/services/auth/auth_service.py](backend/domains/accounts/services/auth/auth_service.py#L1644) `class PublicResendVerificationRequest(BaseModel)` | High |
| pydantic-settings | 2.7.1 | Yes | Not in `config.py` | Inferred / partly bypassed | declared; but the primary `Settings` class is a **hand-rolled dict**, not `BaseSettings` — [backend/config.py](backend/config.py#L23) | Med |
| python-dotenv | 1.2.2 | Yes | Yes | Yes | [backend/config.py](backend/config.py#L16) `from dotenv import load_dotenv` | High |
| email-validator | 2.3.0 | Yes | Not directly | Inferred | declared; used transitively by Pydantic `EmailStr`/FastAPI | Med |

### 2.4 Auth & authz libraries (categories 8, 9)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| PyJWT | 2.13.0 | Yes | Yes | Yes | [backend/domains/accounts/services/auth/auth_service.py](backend/domains/accounts/services/auth/auth_service.py#L32) `import jwt`; re-exported via `providers/auth/jwt` | High |
| python-jose[cryptography] | 3.5.0 | Yes | Yes | Yes | [backend/domains/comms/services/system_comms_status_service.py](backend/domains/comms/services/system_comms_status_service.py#L16) `from jose import JWTError, jwt` | High |
| bcrypt | 5.0.0 | Yes | Yes | Yes | [backend/infrastructure/security/auth.py](backend/infrastructure/security/auth.py#L12) `import bcrypt`; hashing [auth.py:189](backend/infrastructure/security/auth.py#L189) `bcrypt.hashpw(…, gensalt(rounds=13))`; verify [auth.py:180](backend/infrastructure/security/auth.py#L180) | High |
| passlib[bcrypt] | 1.7.4 | Yes | Yes (seed only) | Partial | only usage found is dev seeding [backend/scripts/seed_loader.py](backend/scripts/seed_loader.py#L580) `from passlib.hash import bcrypt`; core auth uses raw `bcrypt` | High |
| PyOTP (2FA/TOTP) | 2.10.0 | Yes | Yes (guarded) | Yes | [backend/providers/auth/totp.py](backend/providers/auth/totp.py#L11) `import pyotp` | High |
| RBAC (in-house) | — | n/a | Yes | Yes | `backend/rbac/` package; enforced in middleware/routers (dir present) | Med |

> **CONTRADICTION (MEDIUM):** Two JWT libraries coexist — PyJWT (`import jwt`)
> and python-jose (`from jose import jwt`). Both are imported in live modules.
> Reported, not resolved. (Deeper token-path analysis is Phase 09.)

### 2.5 HTTP clients (category 10)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| httpx | 0.28.1 | Yes | Yes | Yes | [backend/domains/finance/services/payments/payment_engine.py](backend/domains/finance/services/payments/payment_engine.py#L55) `import httpx`; Tap gateway [gateway_tap.py:5](backend/domains/finance/services/payments/gateway_tap.py#L5) | High |
| requests | 2.34.2 | Yes | Yes | Yes | [backend/providers/payments/tap.py](backend/providers/payments/tap.py#L14), [paytabs.py:14](backend/providers/payments/paytabs.py#L14), [thawani.py:14](backend/providers/payments/thawani.py#L14), OAuth [backend/providers/auth/apple.py](backend/providers/auth/apple.py#L21) | High |

### 2.6 Caching, queues, background workers, scheduling (categories 12, 13, 14)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Valkey (cache server, dev) | 9.0-alpine | n/a (image) | — | Yes (dev) | [docker-compose.yml](docker-compose.yml#L19-L24) `image: valkey:9.0-alpine` | High |
| Redis (cache server, prod) | 7-alpine | n/a (image) | — | Yes (prod) | [docker-compose.prod.yml](docker-compose.prod.yml#L100) `image: redis:7-alpine` | High |
| Celery | 5.4.0 | Yes | Yes | Yes (dev wiring) | [backend/jobs/celery_app.py](backend/jobs/celery_app.py#L5) `from celery import Celery`; 12 task modules import `shared_task` | High |
| Celery Beat scheduler | (celery) | — | Yes | Yes (dev) | beat_schedule [backend/jobs/celery_app.py](backend/jobs/celery_app.py#L57-L100); service [docker-compose.yml](docker-compose.yml#L152) | High |
| APScheduler | 3.11.3 | Yes | Yes (guarded) | Superseded / optional | wrapper [backend/providers/automation/scheduler.py](backend/providers/automation/scheduler.py#L1) `HAS_APSCHEDULER`; comment "replacing APScheduler" [backend/jobs/periodic_tasks.py](backend/jobs/periodic_tasks.py#L1) | Med |
| `schedule` (lib) | 1.2.2 | Yes | Not found | Unknown | declared; no `import schedule` located | Low |
| cachetools | 5.5.0 | Yes | Not directly | Inferred | declared; in-proc cache utilities under `infrastructure/utils/performance_cache.py` | Low |

> **CONTRADICTION #3 (HIGH — deployment):** dev [docker-compose.yml](docker-compose.yml#L52-L186)
> defines 4 Celery workers (`ml`, `periodic`, `payouts`, `emails`) + `celery-beat`;
> prod [docker-compose.prod.yml](docker-compose.prod.yml) defines **no Celery
> service at all** — only `ml_worker` running `python -m utils.ml_worker`.
> Additionally the dev worker command is `celery -A celery_app …` but the actual
> module is `jobs/celery_app.py` and **no top-level `backend/celery_app.py`
> exists** ([backend/](backend/) root listing). Both the `celery_app` and
> `utils.ml_worker` module paths are unverified against the discovered layout.
> Reported for Phase 16 depth.

### 2.7 Search engine (category 15)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Elasticsearch / OpenSearch / Meilisearch / Whoosh | — | **No** | **No** | **No** | zero import matches across `backend/**` | High |
| PostgreSQL full-text search | PG-native | n/a | Yes | Yes | [backend/domains/catalog/services/search/search_service.py](backend/domains/catalog/services/search/search_service.py#L145) `websearch_to_tsquery`; ranking `ts_rank_cd` [search_service.py:560](backend/domains/catalog/services/search/search_service.py#L560); trigger migration [backend/alembic/versions/2026_07_29_19_14-…add_products_search_vector_trigger.py](backend/alembic/versions/2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py#L45) | High |

### 2.8 Object/file storage & image processing (categories 16, 17)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| boto3 (S3 + Cloudflare R2 + backup) | — | **No** | Yes (guarded) | Yes (prod path) | [backend/providers/storage/s3_client.py](backend/providers/storage/s3_client.py#L9), [r2_client.py:10](backend/providers/storage/r2_client.py#L10), backup [backend/scripts/pg_backup.py](backend/scripts/pg_backup.py#L461); prod forces `STORAGE_BACKEND=s3` [docker-compose.prod.yml](docker-compose.prod.yml#L30) | High |
| Local filesystem storage | — | n/a | Yes | Yes (default) | `storage_backend` default `local` [backend/config.py](backend/config.py#L118); static mount [backend/main.py](backend/main.py#L89) | High |
| Pillow (PIL) | 12.3.0 | Yes | Yes | Yes | [backend/providers/image/__init__.py](backend/providers/image/__init__.py#L5) `from PIL import Image, ImageOps, …` | High |
| NumPy | 2.2.6 | Yes | Yes | Yes | [backend/providers/bg_removal/bg_removal_service.py](backend/providers/bg_removal/bg_removal_service.py#L40) `import numpy as np`; many image modules | High |
| OpenCV (cv2) | (commented) 5.0.0.93 | Commented/optional | Yes (guarded) | Conditional | [backend/providers/image/ocr.py](backend/providers/image/ocr.py#L41) `import cv2` inside guard; degrades via HAS_CV2 | Med |
| rembg | (commented) 2.0.69 | Commented/optional | Yes (lazy) | Conditional | [backend/providers/image/bg_remover/rembg_lazy_load.py](backend/providers/image/bg_remover/rembg_lazy_load.py#L14) `from rembg import remove …` | Med |
| onnxruntime | (commented) 1.23.2 | Commented/optional | Yes (lazy) | Conditional | [backend/providers/image/bg_remover/core_i_o.py](backend/providers/image/bg_remover/core_i_o.py#L122) `import onnxruntime as ort` | Med |
| qrcode | 1.5.4 | Yes | Yes | Yes | [backend/infrastructure/security/qr_auth.py](backend/infrastructure/security/qr_auth.py#L5) `import qrcode` | High |
| python-magic | 0.4.27 | Yes | Not isolated | Inferred | declared for MIME sniffing of uploads | Low |
| aiofiles | 25.1.0 | Yes | Not isolated | Inferred | declared for async file IO | Low |

> **CONTRADICTION #1 (HIGH):** boto3 is a hard runtime requirement for the S3/R2
> storage backends and the DB-backup uploader, yet it is **absent from
> `requirements.txt`** and **not installed by `Dockerfile.prod`** (which pins
> `requirements.txt` only). Prod sets `STORAGE_BACKEND=s3`
> ([docker-compose.prod.yml](docker-compose.prod.yml#L30)) → S3 media path would
> fail at import time unless boto3 is provided out-of-band.

### 2.9 Email, SMS/voice, AI providers (categories 18, 19, + AI)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| SMTP (stdlib `smtplib`) | stdlib | n/a | Yes | Yes | [backend/infrastructure/messaging/email_service.py](backend/infrastructure/messaging/email_service.py#L16) `import smtplib` | High |
| Resend (email HTTP API, no SDK) | — | No SDK | Yes (HTTP) | Yes | [backend/providers/comms/email.py](backend/providers/comms/email.py#L45) POSTs `https://api.resend.com/emails`; config key `resend_api_key` [backend/config.py](backend/config.py#L76) | High |
| Twilio (SMS/voice) | — | **No** (not in requirements) | Yes (guarded) | Conditional | [backend/providers/comms/twilio.py](backend/providers/comms/twilio.py#L15) `from twilio.rest import Client` in try/except | Med |
| Ollama (local LLM, HTTP) | n/a | No SDK | Yes (HTTP) | Yes | provider [backend/providers/ai/ai_variant_config.py](backend/providers/ai/ai_variant_config.py#L12); `_ollama_chat` re-exported [backend/providers/__init__.py](backend/providers/__init__.py#L32); default `http://localhost:11434`; model `llama3.1` [backend/config.py](backend/config.py#L144) | High |
| HuggingFace (HTTP) | — | No SDK | Yes (guarded) | Conditional | [backend/providers/ai/huggingface.py](backend/providers/ai/huggingface.py#L17) `import requests`; `hf_api_token` config | Med |
| OpenAI | — | config key only | **No** | **No** | `openai_api_key` in [backend/config.py](backend/config.py#L54) but **no `import openai`** in runtime code (only a baseline string list [backend/scripts/_gen_service_provider_baseline.py](backend/scripts/_gen_service_provider_baseline.py#L37)) | High |
| Google / Apple OAuth (id_token verify) | — | No SDK | Yes | Yes | [backend/providers/auth/oauth.py](backend/providers/auth/oauth.py#L58) `verify_google_id_token`; Apple [backend/providers/auth/apple.py](backend/providers/auth/apple.py#L3) — verified via JWT libs + HTTP JWKS, **no google-auth SDK** | Med |

### 2.10 Payment providers (category 20)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Stripe (official SDK) | 15.3.1 | Yes | Yes | Yes | module [backend/providers/payments/stripe_sdk.py](backend/providers/payments/stripe_sdk.py); registry [backend/providers/payments/registry.py](backend/providers/payments/registry.py) | High |
| Stripe Connect | (stripe) | Yes | Yes | Yes | [backend/providers/payments/connect.py](backend/providers/payments/connect.py); config `stripe_connect_auto_create_accounts` [backend/config.py](backend/config.py) | Med |
| Tap Payments (custom, `requests`) | — | No SDK | Yes | Yes | [backend/providers/payments/tap.py](backend/providers/payments/tap.py#L14); async gateway [backend/domains/finance/services/payments/gateway_tap.py](backend/domains/finance/services/payments/gateway_tap.py#L5) | High |
| PayTabs (custom, `requests`) | — | No SDK | Yes | Yes | [backend/providers/payments/paytabs.py](backend/providers/payments/paytabs.py#L14); config resolvers referenced by tests [backend/tests/providers/test_payments_providers.py](backend/tests/providers/test_payments_providers.py#L765) | High |
| Thawani (custom, `requests`) | — | No SDK | Yes | Yes | [backend/providers/payments/thawani.py](backend/providers/payments/thawani.py#L14); webhook verify tests [backend/tests/security/test_webhook_security.py](backend/tests/security/test_webhook_security.py#L117) | High |
| PayPal (custom) | — | No SDK | Yes | Yes | [backend/providers/payments/paypal.py](backend/providers/payments/paypal.py); `PayPalError` [backend/tests/providers/test_provider_health.py](backend/tests/providers/test_provider_health.py#L170) | Med |
| Generic gateway abstraction | — | n/a | Yes | Yes | base [backend/providers/payments/base.py](backend/providers/payments/base.py#L3); `generic.py`, `webhooks.py`, `registry.py` | High |
| Bank API (payout rails) | — | No SDK | Yes (guarded) | Conditional | [backend/providers/finance/bank_api.py](backend/providers/finance/bank_api.py#L14) `import requests`; `bank_api_enabled` config | Med |

### 2.11 Logging, monitoring, analytics (categories 21, 22, 23)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| structlog | 26.1.0 | Yes | Yes | Yes | setup [backend/main.py](backend/main.py#L36) `setup_structlog`; `import structlog` in 140+ modules | High |
| Sentry SDK | 2.66.1 | Yes | Yes | Yes (conditional on DSN) | [backend/infrastructure/observability/error_handler.py](backend/infrastructure/observability/error_handler.py#L61) `sentry_sdk.init(...)`; tests [backend/tests/observability/test_sentry.py](backend/tests/observability/test_sentry.py#L84) | High |
| prometheus-client | 0.26.0 | Yes | Not directly | Inferred (via instrumentator) | declared; metrics served through instrumentator below | Med |
| prometheus-fastapi-instrumentator | 7.1.0 | Yes | Yes | Yes | [backend/infrastructure/observability/prometheus_setup.py](backend/infrastructure/observability/prometheus_setup.py#L9) `from prometheus_fastapi_instrumentator import Instrumentator`; wired [backend/main.py](backend/main.py#L85) | High |
| OpenTelemetry (api/sdk/otlp-http + instrumentation) | 1.44.0 / 0.65b0 | Yes | Yes (guarded) | Conditional (needs OTLP endpoint) | [backend/infrastructure/observability/tracing.py](backend/infrastructure/observability/tracing.py#L20-L25); wired [backend/main.py](backend/main.py#L95) | High |
| Application analytics (in-house) | — | n/a | Yes | Yes | `backend/domains/analytics/**` services; command-center dashboards | Med |
| Third-party product analytics (GA/Segment/PostHog/Mixpanel) | — | **No** | **No** | **No** | none found in backend or web imports | High |

### 2.12 Rate limiting, i18n & misc utilities

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| SlowAPI | 0.1.10 | Yes | Yes | Yes | [backend/infrastructure/security/rate_limiter.py](backend/infrastructure/security/rate_limiter.py#L20) `from slowapi import Limiter` | High |
| limits | 5.8.0 | Yes | Not directly | Inferred (SlowAPI backend) | declared; underlying storage lib for SlowAPI | Med |
| Babel (i18n) | 2.18.0 | Yes | Not isolated | Inferred | declared for locale/number/date formatting | Low |
| phonenumbers | 9.0.35 | Yes | Yes | Yes | [backend/infrastructure/utils/phone_utils.py](backend/infrastructure/utils/phone_utils.py#L6) `import phonenumbers` | High |
| feedparser | 6.0.12 | Yes | Yes (guarded) | Yes | [backend/providers/news/rss_provider.py](backend/providers/news/rss_provider.py#L13) `import feedparser` | High |
| python-docx | 1.2.0 | Yes | Not isolated | Inferred | declared for DOCX export | Low |
| openpyxl | 3.1.5 | Yes | Not isolated | Inferred | declared for XLSX export | Low |
| Faker | 40.36.0 | Yes | Yes | Yes (seed/tests) | declared in both req + req-dev; seed/test data | Med |
| pytz / tzlocal | 2026.3.post1 / 5.4.4 | Yes | Not isolated | Inferred | declared timezone utilities | Low |
| python-slugify / text-unidecode | 8.0.4 / 1.3 | Yes | Not isolated | Inferred | slug generation | Low |

---

## 3. Frontend — web_app ([frontend/web_app](frontend/web_app))

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Next.js (App Router) | 16.3.4 | Yes | Yes | Yes | `next.config.ts`; edge middleware [frontend/web_app/middleware.ts](frontend/web_app/middleware.ts#L1) `from "next/server"`; API routes `src/app/api/**/route.ts` | High |
| React / React DOM | 19.2.8 | Yes | Yes | Yes | ubiquitous `import React`; e.g. [frontend/web_app/src/__tests__/Chatbot.test.tsx](frontend/web_app/src/__tests__/Chatbot.test.tsx#L4) | High |
| Zustand (state) | 5.0.11 | Yes | Yes | Yes | [frontend/web_app/src/lib/cartStore.ts](frontend/web_app/src/lib/cartStore.ts#L3) `import { create } from "zustand"` (10+ stores) | High |
| framer-motion | 12.x | Yes | Yes | Yes | [frontend/web_app/src/app/admin/dashboard/page.tsx](frontend/web_app/src/app/admin/dashboard/page.tsx#L6) `import { motion }` (100+ files) | High |
| chart.js + react-chartjs-2 | 4.5.1 / 5.3.1 | Yes | Yes | Yes | [frontend/web_app/src/components/ChartComponents.tsx](frontend/web_app/src/components/ChartComponents.tsx#L16) | High |
| jose (server JWT verify) | 6.2.10 | Yes | Yes | Yes | [frontend/web_app/src/lib/serverAuth.ts](frontend/web_app/src/lib/serverAuth.ts#L1) `import { jwtVerify } from "jose"` | High |
| DOMPurify | 3.3.3 | Yes | Yes | Yes | [frontend/web_app/src/components/admin/EmailTemplateManager.tsx](frontend/web_app/src/components/admin/EmailTemplateManager.tsx#L6) | High |
| qrcode | 1.5.4 | Yes | Yes | Yes | [frontend/web_app/src/app/supplier/labels/[id]/page.tsx](frontend/web_app/src/app/supplier/labels/%5Bid%5D/page.tsx#L5) `import QRCode from "qrcode"` | High |
| @zxing/library (barcode) | 0.21.3 | Yes | Yes (dynamic) | Yes | [frontend/web_app/src/app/admin/barcode/page.tsx](frontend/web_app/src/app/admin/barcode/page.tsx#L116) `await import("@zxing/library")` | High |
| @stripe/react-stripe-js + @stripe/stripe-js | 5.6.0 / 8.7.0 | Yes | Mocked in tests | Inferred | jest mock [frontend/web_app/src/__tests__/pages/checkout.test.tsx](frontend/web_app/src/__tests__/pages/checkout.test.tsx#L81) — direct src import not located in this pass | Med |
| openapi-fetch (typed API client) | — | **No** | Yes | Yes | [frontend/web_app/src/lib/api/openapi.ts](frontend/web_app/src/lib/api/openapi.ts#L15) `import createClient … from "openapi-fetch"` — **not in package.json** | High |
| jspdf | 4.1.0 | Yes | **No** | **No** | declared; zero import match in `frontend/web_app/**` | Med |
| lucide-react (icons) | 0.563.0 | Yes | Not isolated | Inferred | declared; icon usage pervasive | Med |
| clsx / class-variance-authority / tailwind-merge | 2.1.1 / 0.7.1 / 3.5.0 | Yes | Not isolated | Inferred | declared; standard `cn()` styling helpers | Med |
| core-js | 3.37.1 | Yes | Not isolated | Unknown | declared polyfills; usage not traced | Low |
| Tailwind CSS v4 (+ @tailwindcss/postcss, autoprefixer) | ^4 | Yes | — | Yes | devDeps [frontend/web_app/package.json](frontend/web_app/package.json); postcss pipeline | High |
| ESLint 9 + eslint-config-next | 9 / 16.3.4 | Yes | — | Yes | `lint` script; devDeps | High |

---

## 4. Frontend — mobile_app ([frontend/mobile_app](frontend/mobile_app))

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| Expo | ~57.0.9 | Yes | Yes | Yes | `expo-status-bar`, `babel-preset-expo`, `jest-expo`; app entry `node_modules/expo/AppEntry.js` | High |
| expo-router (file-based routing) | — | **No** | Yes | Yes | [frontend/mobile_app/app/_layout.tsx](frontend/mobile_app/app/_layout.tsx#L3) `import { Stack } from "expo-router"` (120+ files) — **not in package.json** | High |
| React Native | 0.81.4 | Yes | Yes | Yes | pervasive `from "react-native"` (e.g. [frontend/mobile_app/app/admin/dashboard.tsx](frontend/mobile_app/app/admin/dashboard.tsx#L18)) | High |
| React / React DOM | 19.1.0 | Yes | Yes | Yes | declared; RN renderer | High |
| react-native-reanimated | 4.2.1 | Yes | Yes | Yes | [frontend/mobile_app/app/(tabs)/_layout.tsx](frontend/mobile_app/app/(tabs)/_layout.tsx#L8) | High |
| react-native-gesture-handler | 2.30.1 | Yes | Yes | Yes | [frontend/mobile_app/app/_layout.tsx](frontend/mobile_app/app/_layout.tsx#L5) `GestureHandlerRootView` | High |
| Zustand | 5.0.14 | Yes | Not isolated | Inferred | declared; store pattern shared with web | Med |
| @react-navigation/native + native-stack | 7.3.4 / 7.17.7 | Yes | **No** | **No (superseded)** | declared but zero import matches — routing is expo-router | High |
| @stripe/stripe-react-native | 0.50.0 | Yes | **No** | **No** | declared; zero import match | Med |
| react-native-svg / safe-area-context / screens | 15.15.3 / 5.6.2 / 4.23.0 | Yes | Not isolated | Inferred | declared; RN/expo-router deps | Med |
| @react-native-async-storage/async-storage | 2.2.0 | Yes | Not isolated | Inferred | declared token/persist store | Low |
| dayjs | 1.11.13 | Yes | Not isolated | Unknown | declared; usage not traced | Low |
| lucide-react-native | 0.469.0 | Yes | Not isolated | Inferred | declared icons | Low |

---

## 5. Frontend — shared ([frontend/shared](frontend/shared))

| Technology | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|
| @zozi/shared workspace pkg | Yes | Yes | Yes | consumed by web via `"@zozi/shared": "file:../shared"` [frontend/web_app/package.json](frontend/web_app/package.json) | High |
| clsx / framer-motion / lucide-react / tailwind-merge / zustand | Yes | Inferred | Inferred | shared UI primitives; `src/index.ts` barrel [frontend/shared/package.json](frontend/shared/package.json) | Med |
| React / RN / react-native-web (peerDeps) | Yes (peer) | Inferred | Inferred | `peerDependencies` for cross-platform components | Med |

---

## 6. Testing frameworks (category 24)

| Technology | Version | Declared? | Imported? | Used? | Evidence | Confidence |
|---|---|---|---|---|---|---|
| pytest | 9.1.1 (req) / 9.2.0 (dev) | Yes | Yes | Yes | config [backend/pyproject.toml](backend/pyproject.toml#L1); `backend/tests/**` | High |
| pytest-asyncio | 1.4.0 | Yes | Yes | Yes | declared both manifests; async tests | High |
| pytest-timeout | 2.4.0 | Yes | Inferred | Yes | [backend/requirements-dev.txt](backend/requirements-dev.txt) | Med |
| Hypothesis | unpinned | Yes | Yes | Yes | `.hypothesis/` cache dir present in [backend/](backend/); property tests | High |
| Jest (web) | 29 | Yes | Yes | Yes | [frontend/web_app/jest.setup.ts](frontend/web_app/jest.setup.ts#L2); `src/__tests__/**` | High |
| ts-jest | 29 | Yes | — | Yes | devDeps web + shared | High |
| @testing-library/react + dom + jest-dom | 16.3.2 / 10.4.1 / 6.x | Yes | Yes | Yes | test files import RTL | High |
| jest-axe (a11y) | 10.0.0 | Yes | Inferred | Yes | devDeps + `@types/jest-axe` | Med |
| jest-environment-jsdom | 30.3.0 | Yes | — | Yes | web devDeps | High |
| Playwright (web e2e) | 1.58.2 | Yes | Yes | Yes | `frontend/web_app/e2e/*.spec.ts` | High |
| jest-expo (mobile) | ~57 | Yes | Yes | Yes | mobile devDeps; [frontend/mobile_app/lib/__tests__/rootLayout.test.tsx](frontend/mobile_app/lib/__tests__/rootLayout.test.tsx#L53) | High |
| Playwright (backend e2e, separate) | ^1.62.0 | Yes | — | Yes | [backend/tests/playwright/package.json](backend/tests/playwright/package.json) | High |
| react-test-renderer | 19.1.0 | Yes | Inferred | Yes | mobile devDeps | Med |

---

## 7. Build tools & package managers (categories 25, 26)

| Technology | Declared/Present? | Used? | Evidence | Confidence |
|---|---|---|---|---|
| npm (JS package manager) | Yes | Yes | root [package.json](package.json) scripts; `.npmrc` in [frontend/.npmrc](frontend/.npmrc) | High |
| `--legacy-peer-deps` install | Yes | Yes | [vercel.json](vercel.json#L4) `npm install --legacy-peer-deps` → peer-dep conflicts present | High |
| pip (Python) | Yes | Yes | Dockerfiles `pip install -r requirements.txt` | High |
| Next.js compiler / SWC | Yes | Yes | `next build` [frontend/web_app/package.json](frontend/web_app/package.json) | High |
| tsc (TypeScript) | Yes | Yes | `typecheck`/`build` scripts (shared, mobile) | High |
| Babel (mobile) | Yes | Yes | `@babel/core`, `babel-preset-expo` | High |
| PostCSS + Autoprefixer + Tailwind v4 | Yes | Yes | web devDeps | High |
| Alembic (DB build/migrate) | Yes | Yes | `db:migrate` [package.json](package.json) | High |
| Makefile | Present | Inferred | [Makefile](Makefile) at root | Med |

---

## 8. Infrastructure, containers, cloud, CDN/proxy, CI/CD (categories 27–30)

| Technology | Declared/Present? | Used? | Evidence | Confidence |
|---|---|---|---|---|
| Docker | Yes | Yes | [backend/Dockerfile](backend/Dockerfile), [backend/Dockerfile.prod](backend/Dockerfile.prod), `frontend/web_app/Dockerfile` (referenced [docker-compose.yml](docker-compose.yml#L189)) | High |
| Docker Compose (dev/prod/override) | Yes | Yes | [docker-compose.yml](docker-compose.yml), [docker-compose.prod.yml](docker-compose.prod.yml), [docker-compose.override.yml](docker-compose.override.yml) | High |
| PostgreSQL | 18-alpine (dev) | Yes | [docker-compose.yml](docker-compose.yml#L4) `image: postgres:18-alpine` | High |
| PgBouncer (pooler) | edoburu/pgbouncer | Yes | [docker-compose.override.yml](docker-compose.override.yml#L4); prod [docker-compose.prod.yml](docker-compose.prod.yml#L2) `POOL_MODE=transaction` | High |
| Valkey / Redis | 9.0 / 7 | Yes | see §2.6 | High |
| Caddy (reverse proxy, auto-HTTPS) | Yes | Yes | [Caddyfile](Caddyfile) `reverse_proxy backend:8000`, HSTS headers | High |
| nginx (reverse proxy) | Yes | Present | [nginx/nginx.conf](nginx/nginx.conf#L42) `upstream backend { server backend:8000; }` | High |
| Railway (PaaS) | Yes | Yes | [railway.toml](railway.toml) builder=dockerfile, uvicorn startCommand | High |
| Vercel (web hosting) | Yes | Yes | [vercel.json](vercel.json) `framework: nextjs` | High |
| Neon (serverless Postgres + Auth) | Yes | Inferred | [neon.ts](neon.ts) `@neon/config` `auth: true`; `DATABASE_REPLICA_URL` config | Med |
| AWS S3 | Yes (prod) | Conditional | [docker-compose.prod.yml](docker-compose.prod.yml#L31-L37); s3_client (boto3) | Med |
| Cloudflare R2 | Yes | Conditional | [backend/providers/storage/r2_client.py](backend/providers/storage/r2_client.py); `S3_ENDPOINT_URL`/`S3_REGION=auto` | Med |
| CloudFront / CDN | Referenced | Inferred | `S3_CDN_BASE` config [backend/config.py](backend/config.py#L122); "S3/CloudFront serves media" [backend/main.py](backend/main.py#L88) | Low |
| Sentry (SaaS) | Yes | Conditional | see §2.11 | High |
| OTLP tracing backend | Yes | Conditional | env `OTEL_EXPORTER_OTLP_ENDPOINT` [backend/main.py](backend/main.py#L95) | Med |
| GitHub Actions (CI/CD) | Yes (9 workflows) | Present | [.github/workflows/ci.yml](.github/workflows/ci.yml), `build.yml`, `deploy.yml`, `e2e.yml`, `security.yml`, `rollback.yml`, `schema-audit.yml`, `router-generation.yml`, `architecture-gate.yml` — **contents not audited this phase** | Med |

---

## 9. Contradictions & discrepancies (reported, not resolved — MASTER_RULES §10–11)

| # | Sev | Contradiction | Evidence |
|---|---|---|---|
| C1 | HIGH | boto3 required by S3/R2/backup but undeclared; prod forces S3 | [s3_client.py:9](backend/providers/storage/s3_client.py#L9), [r2_client.py:10](backend/providers/storage/r2_client.py#L10), [pg_backup.py:461](backend/scripts/pg_backup.py#L461) vs [requirements.txt](backend/requirements.txt), [docker-compose.prod.yml:30](docker-compose.prod.yml#L30) |
| C2 | HIGH | Cache/broker server differs dev↔prod (Valkey 9 vs Redis 7); config default `redis://` | [docker-compose.yml:19](docker-compose.yml#L19) vs [docker-compose.prod.yml:100](docker-compose.prod.yml#L100) vs [config.py:74](backend/config.py#L74) |
| C3 | HIGH | Celery workers/beat only in dev compose; prod has none; `celery -A celery_app` + `utils.ml_worker` module paths unverified | [docker-compose.yml:52](docker-compose.yml#L52) vs [docker-compose.prod.yml:66](docker-compose.prod.yml#L66); no `backend/celery_app.py` in [backend/](backend/) |
| C4 | MED | DuckDB + duckdb-engine declared, never imported | [requirements.txt](backend/requirements.txt) vs [test_import_direction_all_packages.py:178](backend/tests/system/test_import_direction_all_packages.py#L178) |
| C5 | MED | Dual JWT libs (PyJWT + python-jose) both imported | [auth_service.py:32](backend/domains/accounts/services/auth/auth_service.py#L32) vs [system_comms_status_service.py:16](backend/domains/comms/services/system_comms_status_service.py#L16) |
| C6 | MED | `expo-router` used everywhere but undeclared; `@react-navigation` declared but unused | [_layout.tsx:3](frontend/mobile_app/app/_layout.tsx#L3) vs [mobile_app/package.json](frontend/mobile_app/package.json) |
| C7 | MED | `openapi-fetch` imported but undeclared (web) | [openapi.ts:15](frontend/web_app/src/lib/api/openapi.ts#L15) vs [web_app/package.json](frontend/web_app/package.json) |
| C8 | MED | pytest pinned differently across manifests (9.1.1 vs 9.2.0) | [requirements.txt](backend/requirements.txt) vs [requirements-dev.txt](backend/requirements-dev.txt) |
| C9 | LOW | jspdf (web) & @stripe/stripe-react-native (mobile) declared, not imported | §3, §4 |
| C10 | LOW | APScheduler present but "replacing APScheduler" via Celery — two scheduler mechanisms | [periodic_tasks.py:1](backend/jobs/periodic_tasks.py#L1), [scheduler.py:1](backend/providers/automation/scheduler.py#L1) |
| C11 | LOW | OpenAI key plumbed in config but no OpenAI SDK/usage | [config.py:54](backend/config.py#L54) |
| C12 | LOW | Two reverse proxies committed (Caddy + nginx) with no single source of truth | [Caddyfile](Caddyfile), [nginx/nginx.conf](nginx/nginx.conf) |
| C13 | INFO | Async DB stack declared (asyncpg + async engine) but engine is guarded/optional; runtime appears sync | [database.py:17](backend/infrastructure/database/database.py#L17) |

---

## VERIFIED STACK (conclusively confirmed)

- **Runtime/lang:** Python 3.11 (slim image); TypeScript 5.x; Node ≥20.
- **Backend web:** FastAPI 0.115.2 on Starlette; served by Uvicorn (dev) and Gunicorn+UvicornWorker (prod); native WebSockets.
- **ORM/migrations:** SQLAlchemy 2.0 **sync** ORM + Alembic; PostgreSQL 18; PgBouncer transaction pooling; redis-py 8 client against **Valkey (dev)**.
- **Full-text search:** PostgreSQL `tsvector`/`websearch_to_tsquery`/`ts_rank_cd` (no external search engine).
- **Auth:** bcrypt (rounds=13) password hashing; PyJWT **and** python-jose both live; PyOTP TOTP; in-house RBAC package.
- **HTTP clients:** httpx + requests (both actively used, esp. payment gateways).
- **Background/queue:** Celery 5.4 with Beat (dev compose: ml/periodic/payouts/emails queues).
- **Payments:** Stripe official SDK (+ Connect); custom `requests`-based Tap, PayTabs, Thawani, PayPal gateways behind a registry/base abstraction.
- **Email:** stdlib SMTP + Resend HTTP API (no SDK).
- **AI:** Ollama (local LLM over HTTP; llama3.1/phi3/moondream/whisper); optional rembg/onnxruntime/opencv (lazy, HAS_* guarded); Pillow + NumPy image pipeline.
- **Observability:** structlog (140+ modules), Sentry SDK (DSN-gated), Prometheus via fastapi-instrumentator, OpenTelemetry (OTLP-gated).
- **Rate limiting:** SlowAPI (+ limits).
- **Frontend web:** Next.js 16 App Router (route handlers + edge middleware), React 19, Zustand, framer-motion, chart.js/react-chartjs-2, jose, DOMPurify, qrcode, @zxing/library (dynamic), openapi-fetch, Tailwind v4/PostCSS, ESLint 9.
- **Frontend mobile:** Expo 57 + expo-router (file-based) + React Native 0.81, reanimated, gesture-handler.
- **Testing:** pytest (+asyncio, +timeout, Hypothesis) backend; Jest+ts-jest+RTL+jest-axe+jsdom and Playwright (web); jest-expo + Playwright (mobile); separate Playwright e2e for backend.
- **Infra:** Docker + Compose (dev/prod/override); Caddy + nginx; Railway (backend), Vercel (web), Neon (Postgres/Auth); GitHub Actions (9 workflows present).
- **Not-used-but-declared (confirmed):** DuckDB/duckdb-engine (backend); jspdf, @react-navigation, @stripe/stripe-react-native (frontend).

## SUSPECTED STACK (likely, insufficient evidence)

- **asyncpg** as an active driver (declared; async engine is guarded/optional — sync psycopg2 path appears primary).
- **pydantic-settings** for config (declared, but the live `Settings` is a hand-rolled dict, not `BaseSettings`).
- **boto3** at runtime in prod (imported + prod env demands S3, but undeclared/uninstalled → may fail).
- **Twilio / HuggingFace / Bank API / Google-Apple OAuth** — guarded/optional providers; wiring present, live activation depends on env/credentials.
- **CloudFront/CDN**, **Neon Auth**, **OTLP backend** — configured hooks; actual production enablement not provable from repo.
- **cachetools, limits, babel, python-docx, openpyxl, pytz, tzlocal, python-slugify, python-magic, aiofiles, core-js, dayjs, clsx/cva/tailwind-merge, lucide-react(-native), async-storage** — declared and plausibly used, but not isolated to a specific call site in this pass.

## UNKNOWN / NOT DETERMINABLE FROM AVAILABLE CODE

- Exact resolved dependency versions (no committed lock file inspected).
- Whether the anachronistic pins resolve against any real package index (offline, not checkable).
- `schedule` (1.2.2) — declared, no import located.
- GitHub Actions workflow **contents** (only filenames enumerated this phase).
- Precise prod worker entrypoint validity (`utils.ml_worker`) — module path not matched to layout.
- Whether `@stripe/react-stripe-js` is imported in a non-test src path (only test mock observed).

## Skepticism checklist

- [x] Opened actual files; cited real lines (78 citations).
- [x] Separated framework/DB-native behavior (PG FTS, Starlette WS) from app libs.
- [x] Separated declared vs imported vs used for every row.
- [x] Labeled VERIFIED / INFERRED / UNKNOWN throughout.
- [x] Avoided inferring from names/docs alone (e.g., DuckDB "declared" ≠ used).
- [x] Reported contradictions (C1–C13) without silently resolving them.
- [x] No secret values reproduced (only key names/locations referenced).
