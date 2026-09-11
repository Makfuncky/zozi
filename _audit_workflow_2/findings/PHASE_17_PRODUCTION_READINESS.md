# PHASE 17 — PRODUCTION READINESS ASSESSMENT

## ZOZI Marketplace E-Commerce Platform
**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Repository:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Methodology:** Source-code verification only. Findings are classified as VERIFIED / INFERRED / UNKNOWN with file/line evidence. No files were modified.

---

## 1. EXECUTIVE SUMMARY

The ZOZI Marketplace is a large, architecturally ambitious e-commerce platform with a comprehensive technology stack (FastAPI, Next.js, Expo, Celery, PostgreSQL/Neon, Valkey, S3/R2). The codebase demonstrates strong structural discipline in many areas: DDD domain organization, multi-schema PostgreSQL, RLS country isolation, extensive middleware pipeline, circuit breakers, webhook HMAC verification, and a mature CI/CD pipeline with 9 GitHub Actions workflows.

However, **the application is NOT READY for large-scale production deployment** without immediate remediation of multiple critical security vulnerabilities, install-breaking dependency issues, and payment-safety gaps. The most severe findings are:

1. **Unauthenticated privilege escalation** — public registration accepts client-supplied `role`, allowing any attacker to create an admin account.
2. **Social-login OIDC bypass** — a dev-only stub accepts caller-supplied identity claims without JWKS verification.
3. **Installation failures** — `requirements.txt` declares `redis==8.0.1` while code imports `valkey`, and `Pillow==12.3.0` does not exist on PyPI.
4. **Critical Next.js vulnerabilities** — lockfile resolves `next@16.1.6`, which has a known critical RCE (GHSA-p293-qw3h-jr36) and multiple high-severity issues.
5. **Payment safety gaps** — generic gateway callback treats missing status as success; Tap/PayTabs/Thawani webhook signature verification is skippable; Stripe refund stub returns fake success when SDK is missing.

**Realistic path forward:** The system can be **repaired and incrementally hardened**. It does not require a full rewrite. The domain model, database schema, and overall architecture are sound. The blockers are discrete, fixable defects concentrated in auth, payments, and dependency manifests.

---

## 2. READINESS CLASSIFICATION BY DOMAIN

| Domain | Classification | Rationale |
|--------|---------------|-----------|
| **Architecture** | PARTIALLY READY | Strong DDD + modular routing + 36 architecture law tests. However, orphaned standalone FastAPI microservice, empty provider directories (`voice/`, `uploads/`), and mixed Redis/Valkey naming contradict stated architecture. |
| **Code Quality** | PARTIALLY READY | Good conventions (mypy-friendly types, mixins, centralized transaction helpers, selectin loading). Massive single-file services create review/maintenance risk. |
| **Dependency Health** | NOT READY | Two critical install-breakers, 9 npm vulnerabilities including critical Next.js RCE, multiple manifest/lockfile mismatches, beta opentelemetry-instrumentation, mixed npm/pnpm. |
| **Database Integrity** | PARTIALLY READY | Excellent foundation: SQLAlchemy 2.0, Alembic with 60+ migrations, multi-schema, RLS, check constraints, ~80 indexes, range partitioning. Unresolved: stock race condition, order total denormalization without DB consistency, nullable customer_id and country_code on orders, soft-delete without auto-filter. |
| **API Quality** | PARTIALLY READY | REST API is well-structured with versioning, rate limiting, webhook HMAC, idempotency, and circuit breakers. Critical gaps: `/ws/user` has no auth, `openapi.json` is empty, orphaned location service microservice. |
| **Authentication** | NOT READY | Two critical privilege-escalation vulnerabilities. High-risk issues: plaintext reset/verification tokens, logout fails silently when Redis is down, `/auth/me` bypasses blacklist, default SECRET_KEY not in rejection list. |
| **Authorization** | PARTIALLY READY | RBAC feature catalog + admin guard middleware + per-router require_feature. Inconsistent role definitions create confusion. No concurrent session limit. |
| **Payment Security** | NOT READY | Generic gateway missing-status = success; webhook signature verification skippable for 3 providers; Stripe refund stub; no amount verification in generic gateway; refund amounts not validated against order total; race condition in webhook idempotency. |
| **Business Logic Correctness** | PARTIALLY READY | Server-side pricing authority is correctly implemented. Order lifecycle, commission waterfall, returns, and payouts have explicit state machines. Residual risks: stock oversell, order total drift, duplicate order number race. |
| **Performance** | PARTIALLY READY | N+1 mitigated via lazy=selectin; connection pooling with PgBouncer; range partitioning. Some unbounded .all() queries in analytics; no explicit pagination on all list endpoints. |
| **Scalability** | PARTIALLY READY | Docker replicas (3 backend workers), PgBouncer transaction pooling, Celery worker queues, read-replica engine support. Unverified: load-test results, read-replica routing in production, cache hit rates. |
| **Reliability** | PARTIALLY READY | Health checks, circuit breakers, idempotency keys, Alembic auto-migration, rollback workflow. Gaps: backup script exists but no evidence of automated production schedule; Redis/Valkey confusion could break session/blacklist reliability. |
| **Observability** | PARTIALLY READY | Structlog, Prometheus, OpenTelemetry, Sentry, Tempo tracing, Loki/Promtail, Grafana dashboards, alertmanager rules. Unverified: actual production deployment of monitoring stack, alert routing to on-call. |
| **Testing** | PARTIALLY READY | 222 backend test files, 36 architecture law tests, Playwright e2e, Jest unit tests, CI runs all suites. Gaps: no load/performance tests in CI; staging e2e is manual. |
| **CI/CD** | READY | 9 GitHub Actions workflows: lint, architecture gates, unit tests, schema drift, build, deploy (Railway + Vercel), e2e, security, rollback. Pre-deploy validation gates. Concurrency controls. |
| **Infrastructure** | PARTIALLY READY | Docker Compose (dev + prod), PgBouncer, Nginx/Caddy reverse proxies, Vercel frontend, Railway backend. Gaps: production docker-compose deploys redis:7-alpine contradicting Valkey migration; ML worker command path mismatch; monitoring stack defined but not wired into production deploy. |
| **Backup/Recovery** | PARTIALLY READY | pg_backup.py script with pg_dump, WAL check, retention (30 days), restore drill, verification. backup.py with S3 replication support. No evidence of automated cron/systemd timer in production config. |
| **Security** | NOT READY | See Authentication and Payment Security above. Additional: CSRF exemption on state-changing auth endpoints, client-influenced device fingerprint, plaintext payment credentials for Stripe/Tap in DB, beta OpenTelemetry packages. |
| **Maintainability** | PARTIALLY READY | DDD boundaries, architecture tests, centralized helpers. Technical debt: very large service files, empty directories, mixed package managers, orphaned code. |
| **Operational Readiness** | PARTIALLY READY | Health checks, rollback workflow, deploy to staging then production, secrets in env vars. Missing: no evidence of runbooks, incident response plan, disaster recovery testing, backup automation, on-call integration. |
---

## 3. PRODUCTION BLOCKERS

These MUST be resolved before any production traffic is accepted.

### 3.1 CRITICAL: Unauthenticated Privilege Escalation via Public Registration
**Status:** VERIFIED  
**Severity:** Critical  
**Impact:** Complete administrative takeover.

`POST /api/v1/auth/register` is a public endpoint that accepts a client-supplied `role` field. The `register_user()` function checks the role against an allow-list but does not restrict it to `customer` for public registration.

**Evidence:**
- `backend/domains/accounts/services/auth/auth_service.py:2353-2511` — `register_user()` writes `user.role` from request payload
- `backend/domains/accounts/services/auth/auth_service.py:2404` — `db_user = User(..., role=user.role, ...)`
- `backend/modules/customer/routers/accounts.py:317-329` — public router with no auth dependency

**Attack:**
```json
POST /api/v1/auth/register
{"email":"attacker@evil.com","password":"Str0ng!Pass","role":"admin"}
```
Returns a valid JWT with admin role.

### 3.2 CRITICAL: Social-Login Dev Stub Accepts Caller-Supplied Claims Without OIDC Verification
**Status:** VERIFIED  
**Severity:** Critical  
**Impact:** Account takeover via identity spoofing.

`verify_social_identity()` in `auth_service.py:3537-3574` contains a dev-only shortcut that returns caller-supplied `provider_user_id`, `email`, and `full_name` without performing JWKS fetch, signature check, or `iss`/`aud`/`exp` validation.

**Evidence:**
- `backend/domains/accounts/services/auth/auth_service.py:3557-3569` — dev path logs warning but returns claims unconditionally
- `backend/modules/admin/routers/accounts.py:469-509` — endpoint calls `verify_social_identity()` with request body values

### 3.3 CRITICAL: Redis/Valkey Manifest Mismatch Causes ImportError
**Status:** VERIFIED  
**Severity:** Critical  
**Impact:** `pip install -r requirements.txt` succeeds, but the application fails to start with `ImportError: No module named 'valkey'`.

`backend/requirements.txt:20` declares `redis==8.0.1`, but the entire codebase imports `valkey` (e.g., `backend/infrastructure/valkey/client.py:81`). The `redis` PyPI package does not provide a `valkey` module.

**Evidence:**
- `backend/requirements.txt:20` — `redis==8.0.1`
- `backend/infrastructure/valkey/client.py:81` — `import valkey`
- `backend/tests/architecture/test_manifest_drift.py:24-46` — architecture test enforces `valkey` in manifest and absence of `redis`

### 3.4 CRITICAL: Pillow 12.3.0 Does Not Exist on PyPI
**Status:** VERIFIED  
**Severity:** Critical  
**Impact:** Fresh environments fail on `pip install`.

`backend/requirements.txt:51` pins `Pillow==12.3.0`, a version that does not exist on PyPI.

**Evidence:**
- `backend/requirements.txt:51` — `Pillow==12.3.0`
- `backend/tests/architecture/test_manifest_drift.py:49-59` — asserts Pillow 12.3.0 does not exist

### 3.5 CRITICAL: Next.js 16.1.6 Has Known Critical RCE and High-Severity Vulnerabilities
**Status:** VERIFIED  
**Severity:** Critical  
**Impact:** Remote code execution, SSRF, DoS in production frontend.

`npm audit` on `frontend/web_app` reveals 9 vulnerabilities in the resolved lockfile:
- `next@16.1.6`: GHSA-p293-qw3h-jr36 (critical, RCE on Windows), GHSA-89xv-2m56-2m9x (high, SSRF), GHSA-ggv3-7p47-pfv8 (moderate)
- `js-yaml`: 4 high-severity issues
- `postcss`: 3 high-severity issues
- `sharp`: 2 high-severity libvips/libheif issues

**Evidence:**
- `frontend/web_app/package-lock.json` — resolves `next` to `16.1.6`
- `frontend/web_app/package.json` — declares `next: 16.3.4`
- Phase 03 findings table with CVE references

### 3.6 CRITICAL: Generic Gateway Callback Treats Missing Status as Success
**Status:** VERIFIED  
**Severity:** High (payment-critical)  
**Impact:** Orders marked as paid without payment verification.

In `handle_generic_gateway_callback()`, when the callback payload contains no explicit status field, the code unconditionally sets `success = True`.

**Evidence:**
- `backend/domains/finance/services/payments/payment_orchestrator.py:877-886`
`if not resolved_status: success = True`

### 3.7 CRITICAL: Webhook Signature Verification Skippable for Tap, PayTabs, Thawani
**Status:** VERIFIED  
**Severity:** High (payment-critical)  
**Impact:** Spoofed webhooks accepted when webhook secret is unconfigured.

Tap (`gateway_tap.py:981-1003`), Thawani (`gateway_tap.py:1415-1423`), and PayTabs (`providers/payments/paytabs.py`) log a warning and continue processing when the webhook secret is not configured.

**Evidence:**
- `backend/domains/finance/services/payments/gateway_tap.py:117-122` — Tap logs warning but does not reject
- `backend/domains/finance/services/payments/gateway_tap.py:128-132` — Thawani same pattern

### 3.8 CRITICAL: /ws/user WebSocket Endpoint Has No Authentication
**Status:** VERIFIED  
**Severity:** High  
**Impact:** Any unauthenticated client can connect and broadcast to the `user:realtime` room.

`backend/main.py:194-196` imports `websocket_user` from `modules.admin.routers.comms` (which has no auth) and registers it at `/ws/user`. A local authenticated version exists later in `main.py:289-325` but the route was already registered.

**Evidence:**
- `backend/main.py:194` — `from modules.admin.routers.comms import websocket_user`
- `backend/main.py:196` — `app.add_api_websocket_route("/ws/user", websocket_user)`
- `backend/modules/admin/routers/comms.py:138-156` — unauthenticated handler
---

## 4. HIGH-RISK ISSUES

These could seriously affect users, money, security, or availability.

### 4.1 Password Reset Tokens Stored in Plaintext
**Status:** VERIFIED  
**Severity:** High  
**Files:** `backend/domains/accounts/services/auth/auth_service.py:3118-3143`, `backend/domains/accounts/models/user.py:185-211`

`forgot_password()` stores the raw token in the `PasswordResetToken.token` column. A database breach exposes all active reset tokens.

### 4.2 Email Verification Tokens Stored in Plaintext
**Status:** VERIFIED  
**Severity:** High  
**Files:** `backend/domains/accounts/services/auth/auth_service.py:2516-2539`, `backend/domains/accounts/models/user.py:214-240`

Same pattern as password reset: raw token stored, queried by exact match.

### 4.3 /auth/me Bypasses Token Blacklist
**Status:** VERIFIED  
**Severity:** Medium-High  
**Files:** `backend/modules/customer/routers/accounts.py:237-251`, `backend/infrastructure/utils/auth.py:344-356`

`decode_token(..., check_blacklist=False)` allows replay of logged-out access tokens.

### 4.4 Logout Silently Fails to Invalidate Tokens When Redis Is Unavailable
**Status:** VERIFIED  
**Severity:** Medium-High  
**Files:** `backend/domains/accounts/services/auth/auth_service.py:2985-3022`, `backend/infrastructure/utils/auth.py:79-96`

`blacklist_token()` raises `RuntimeError` in production when Redis is down. `logout_user()` catches all exceptions with bare `except Exception: pass`. Access-token cookie is never cleared.

### 4.5 Default SECRET_KEY Not in Rejection List
**Status:** VERIFIED (code-level; mitigated by runtime validation)  
**Severity:** Medium-High  
**Files:** `backend/config.py:31`, `backend/config.py:262-264`

Default value `"zozi-dev-secret-key-change-in-production-2026"` is NOT in the placeholder rejection set. Production deployed without `SECRET_KEY` would use this embedded default.

### 4.6 CSRF Exemption on State-Changing Auth Endpoints
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `backend/middleware/csrf_middleware.py:28-37`, `backend/middleware/csrf_middleware.py:63-64`

`/auth/register`, `/auth/forgot-password`, `/auth/reset-password` are CSRF-exempt while using cookie-based auth.

### 4.7 Inconsistent Role Definitions Across Codebase
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `backend/rbac/catalog.py:14`, `backend/rbac/dependencies.py:60-90`, `backend/rbac/roles.py:33-41`, `backend/middleware/admin_guard_middleware.py:45`

`VALID_USER_ROLES` includes `sub_admin`, `moderator`, `support` but `_ROLE_FEATURES` has no entries for them. `superadmin` (lowercase) passes admin guard but not `require_admin`. `sub_admin` is admin per `roles.py` but not per `admin_guard_middleware.py`.

### 4.8 Partial Refund Authorization — No Server-Side Amount Validation
**Status:** VERIFIED  
**Severity:** Medium-High (financial)  
**Files:** `backend/providers/payments/tap.py:201-260`, `backend/providers/payments/paypal.py:238-293`, `backend/providers/payments/paytabs.py:207-270`

Refund endpoints accept arbitrary amounts from the request without validating against the order's paid amount or remaining refundable balance.

### 4.9 Race Condition — Double Order Confirmation / Double Inventory Deduction
**Status:** INFERRED  
**Severity:** Medium-High (financial)  
**Files:** `backend/domains/finance/services/payments/payment_engine.py:4143-4323`, `backend/domains/finance/services/payments/gateway_stripe.py:700-716`

Check-then-act pattern on `ProcessedWebhookEvent` without DB-level unique constraint or `SELECT ... FOR UPDATE` creates a TOCTOU race under concurrent webhook delivery.

### 4.10 Stock Race Condition — Inventory Oversell
**Status:** VERIFIED  
**Severity:** High (financial/inventory)  
**Files:** `backend/domains/suppliers/services/health/supplier_health.py:167-177`, `backend/domains/suppliers/services/health/supplier_health.py:542-602`

Stock updates use `product.stock = int(new_stock)` without pessimistic locking or atomic `UPDATE ... WHERE stock >= ?`.

### 4.11 Order Total Denormalized Without DB-Level Consistency Check
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `backend/domains/orders/models/order_entities.py:30-38`, `backend/domains/orders/models/order_entities.py:88-90`

`orders.total` can diverge from `SUM(order_items.total_price)` if items are modified post-creation. No trigger or check constraint enforces consistency.

### 4.12 Stripe Refund Returns Stub Success When SDK Unavailable
**Status:** VERIFIED  
**Severity:** Medium-High (financial)  
**Files:** `backend/providers/payments/stripe_sdk.py:27-34`

`refund_payment_intent()` returns `{"id": "stub_refund", "status": "succeeded"}` when Stripe SDK is not installed.

### 4.13 Payment Gateway Credentials — Stripe/Tap Stored in Plaintext in Database
**Status:** VERIFIED  
**Severity:** Medium-High  
**Files:** `backend/domains/finance/models/payments.py:84-127`, `backend/domains/finance/services/payments/payment_engine.py:1834-1836`, `backend/domains/finance/services/payments/payment_engine.py:1916`

`PaymentGatewayConnection.secret_key` and `webhook_secret` are stored as plaintext `String(1000)` columns. PayPal and Thawani use `decrypt_secret()`, but Stripe and Tap resolve directly from `record.secret_key`.

### 4.14 Generic Gateway Does Not Verify Payment Amount
**Status:** VERIFIED  
**Severity:** Medium-High (financial)  
**Files:** `backend/domains/finance/services/payments/payment_orchestrator.py:791-921`, `backend/domains/finance/services/payments/payment_orchestrator.py:1033-1108`

`handle_generic_gateway_callback()` and `confirm_generic_gateway_payment()` do not re-verify the paid amount against `order.payment_customer_total_amount`.

### 4.15 Production docker-compose Uses Redis, Not Valkey
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `docker-compose.prod.yml:29,96-104`

Production compose deploys `redis:7-alpine` and sets `REDIS_URL=redis://redis:6379`, contradicting the completed Valkey migration and the project constraint `no_redis_naming_anywhere`.

### 4.16 ML Worker Command Path Mismatch
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `docker-compose.prod.yml:71`

`python -m utils.ml_worker` does not match any top-level `utils` package under `backend/`.

### 4.17 Test Passwords Hardcoded in conftest.py
**Status:** VERIFIED  
**Severity:** Medium  
**Files:** `backend/tests/conftest.py:52-56`

Hardcoded fallback test passwords (`T3st_Adm!n_Secure#2024`, etc.) in test configuration.

### 4.18 Device Fingerprint Is Client-Influenced
**Status:** VERIFIED  
**Severity:** Low-Medium  
**Files:** `backend/middleware/device_binding_middleware.py`

`DeviceBindingMiddleware` stores `X-Device-Fingerprint` header directly on `request.state.device_binding`, which can be spoofed.

### 4.19 No Concurrent Session Limit Enforcement
**Status:** INFERRED  
**Severity:** Low-Medium  
**Files:** `backend/domains/accounts/services/auth/auth_service.py:1121-1238`, `backend/domains/accounts/models/user.py:90-121`

`_issue_session()` does not check the number of existing active sessions before issuing a new one.
---

## 5. MEDIUM-RISK ISSUES

### 5.1 Frontend openapi.json Is Empty
**Status:** VERIFIED  
**Files:** `frontend/web_app/openapi.json`

No API contract available for frontend developers. Backend generates `/openapi.json` at runtime but it has not been exported.

### 5.2 Orphaned Standalone FastAPI Microservice
**Status:** VERIFIED  
**Files:** `backend/domains/logistics/services/core/service.py:2967`

A complete FastAPI app (`Zozi Location Service`) with `/api/geo/*` routes exists but is NOT mounted into the main app and has no deployment entry point.

### 5.3 Multiple Overlapping Reverse Proxy Configs
**Status:** VERIFIED  
**Files:** `Caddyfile`, `nginx/nginx.conf`, `vercel.json`

All three define reverse proxy/security headers without clear environment-specific activation.

### 5.4 .env Files Contain Secrets Locally
**Status:** VERIFIED  
**Files:** `backend/.env` (115 lines), root `.env`

Both files exist and contain environment-specific secrets. They are gitignored (`git ls-files` confirms `backend/.env` is NOT tracked), but their presence in the working tree poses local compromise risk.

### 5.5 Seed Data Includes Hardcoded Demo Users
**Status:** VERIFIED  
**Files:** `backend/infrastructure/database/seed/_common.py:36-49`, `backend/infrastructure/database/seed/_common.py:382-384`

Demo users (`admin@zozi.com`, `supplier@zozi.com`, `customer@zozi.com`, `logistics@zozi.com`) are seeded on startup when `SEED_DATA_ON_STARTUP=true`.

### 5.6 Missing Explicit Pagination on Some List Endpoints
**Status:** INFERRED  
**Files:** `backend/domains/analytics/services/dashboards/command_center_service.py:90,130,195`

`db_read.py` supports pagination, but some services call `.all()` directly on queries.

### 5.7 Unbounded .all() Queries in Analytics
**Status:** VERIFIED  
**Files:** `backend/domains/analytics/services/dashboards/command_center_service.py:290-314`

Multiple `.count()` calls on full tables in the command center dashboard.

### 5.8 Soft-Delete Without Automatic Query Filter
**Status:** VERIFIED  
**Files:** `backend/infrastructure/database/mixins.py:23-41`, `backend/infrastructure/database/db_read.py`

`SoftDeleteMixin` adds `is_deleted` flag, but `db_read.py` does not automatically inject `is_deleted=False` filters. Every query must explicitly filter.

### 5.9 Duplicate Data / Denormalization Without Consistency Enforcement
**Status:** VERIFIED  
**Files:** `backend/domains/orders/models/order_entities.py:30-38`, `backend/domains/catalog/models/products.py:60`

Order totals and product stock are denormalized but lack DB-level triggers or checks to maintain consistency.

### 5.10 Nullable Foreign Keys With Business Meaning
**Status:** VERIFIED  
**Files:** `backend/domains/orders/models/order_entities.py:22,60`

`orders.customer_id` and `orders.country_code` are nullable despite semantic requirements (Law #5).

### 5.11 requests and httpx Coexist
**Status:** VERIFIED  
**Files:** `backend/requirements.txt:35-36`, `backend/domains/accounts/services/auth/auth_service.py:33`, `backend/domains/finance/services/payments/payment_engine.py:55`

Both HTTP clients are used in production code, creating inconsistent async/sync patterns.

### 5.12 starlette Unpinned
**Status:** VERIFIED  
**Files:** `backend/requirements.txt:11`

Unpinned `starlette` may pull incompatible versions.

### 5.13 numpy==2.2.6 — Very New Major Version
**Status:** VERIFIED  
**Files:** `backend/requirements.txt:57`

NumPy 2.x series is very recent; compatibility with transitive dependencies is unverified.

### 5.14 opentelemetry-instrumentation==0.65b0 — Beta Prerelease
**Status:** VERIFIED  
**Files:** `backend/requirements.txt:66-69`

Beta version of OpenTelemetry instrumentation packages.

### 5.15 Frontend Package-Lock Version Mismatches
**Status:** VERIFIED  
**Files:** `frontend/web_app/package.json` vs `frontend/web_app/package-lock.json`

`next` declared `16.3.4` but resolved `16.1.6`; `react` declared `19.2.8` but resolved `19.2.3`; `framer-motion` declared `^12.0.0` but resolved `^11.5.6`.

### 5.16 Shared vs Web_app Dependency Version Conflicts
**Status:** VERIFIED  
**Files:** `frontend/shared/package.json` vs `frontend/web_app/package-lock.json`

`framer-motion` and `tailwind-merge` have conflicting versions across monorepo packages.

### 5.17 Mixed Package Managers Across Monorepo
**Status:** VERIFIED  
**Files:** `frontend/web_app/package-lock.json` (npm v3), `frontend/mobile_app/pnpm-lock.yaml` (pnpm v9)

Different resolution algorithms; harder to enforce workspace-wide policies.

### 5.18 pytest Version Conflict
**Status:** VERIFIED  
**Files:** `backend/requirements.txt:101` (`9.1.1`), `backend/requirements-dev.txt:4` (`9.2.0`)

### 5.19 @testing-library/dom in dependencies Instead of devDependencies
**Status:** VERIFIED  
**Files:** `frontend/web_app/package.json:17`

Bloated production bundle.

### 5.20 Unused Frontend Dependencies
**Status:** VERIFIED  
**Files:** `frontend/web_app/package.json:22,24,28`

`jspdf`, `core-js`, `class-variance-authority` have no imports in `src/`.

### 5.21 Root package-lock.json Has Undeclared Dependencies
**Status:** VERIFIED  
**Files:** Root `package.json` vs `package-lock.json`

`@neon/config` and `@neon/env` exist in lockfile but not manifest.

### 5.22 Frontend Test Artifacts in web_app Root
**Status:** VERIFIED  
**Files:** `frontend/web_app/` root directory

Contains `test_logistics.txt`, `staff_test.txt`, `output.txt`, `build_output.txt`, `playwright-results.txt`, etc.

### 5.23 Database Files at Repository Root
**Status:** VERIFIED  
**Files:** Root `test_phase7e2.db*`, `dump.rdb`

Local database artifacts should not be committed.

### 5.24 Empty Provider/Infrastructure Directories
**Status:** VERIFIED  
**Files:** `backend/providers/voice/`, `backend/infrastructure/uploads/`

Empty directories suggest incomplete implementations or placeholders.

### 5.25 CSRF Cookie Set With httponly=False
**Status:** VERIFIED  
**Files:** `backend/middleware/csrf_middleware.py:110`

CSRF cookie must be readable by JavaScript, but this reduces protection against XSS.

### 5.26 SameSite Cookie Is 'lax' Not 'strict'
**Status:** VERIFIED  
**Files:** `backend/config.py:37`, `backend/middleware/csrf_middleware.py:112`

`refresh_cookie_samesite` defaults to `lax`. `strict` would provide stronger CSRF defense where cross-site sending is not required.
---

## 6. LOW-RISK ISSUES

- `jest-environment-jsdom` version mismatch across packages (web_app `^30.3.0` vs shared `^29.0.0`)
- `@types/react` range inconsistency (`^19` vs `^19.2.17`)
- `tailwind-merge` lockfile divergence (shared lockfile resolves v2 while manifest says v3)
- `pytest-asyncio` double-declared in `requirements.txt` and `requirements-dev.txt`
- `duckdb`/`duckdb-engine` declared but no direct imports found in inspected backend source
- Architecture tests enforce Python 3.13 in Dockerfiles, but current Dockerfiles use `python:3.11-slim` (test failure)
- `backend/Dockerfile` and `backend/Dockerfile.prod` both use `python:3.11-slim` while architecture tests require `python:3.13-slim`
- `backend/tests/conftest.py` disables CSRF (`CSRF_DISABLED=true`) and sets `APP_ENV=test` at import time, which can mask CSRF-related test gaps
- Monitoring stack (`monitoring/docker-compose.monitoring.yml`) is defined but there is no evidence it is deployed in production
- No evidence of automated backup cron job or systemd timer in production configuration
- No evidence of disaster recovery runbook or restore-time objective (RTO) testing

---

## 7. UNKNOWN / REQUIRES VALIDATION

| Item | Why Unknown |
|------|-------------|
| Actual PostgreSQL server version in production | Not determinable from repo; health-check query exists but result is runtime-only |
| Production monitoring stack deployment status | `monitoring/docker-compose.monitoring.yml` exists but no deploy workflow references it |
| Automated backup schedule in production | `scripts/pg_backup.py` and `infrastructure/storage/backup.py` exist but no cron/systemd config found |
| Redis/Valkey actual runtime in production | `docker-compose.prod.yml` uses `redis:7-alpine` while `docker-compose.yml` uses `valkey:9.0-alpine`; actual deployed stack is not determinable from repo alone |
| OpenSearch implementation status | Session memory references OpenSearch as finalized, but `requirements.txt` and code contain no OpenSearch client |
| `pybreaker` implementation status | Session memory references pybreaker, but `requirements.txt` contains no pybreaker and grep found no references |
| Load-test results / performance baseline | `scripts/testing/loadtests/` exists but no results or CI integration found |
| RTO/RPO targets and disaster recovery testing | No runbook or test script found |
| Actual `.env` values in production | Intentionally not inspected; exact runtime configuration is not determinable |
| Whether `services._registry` exists | `lifespan.py:128-140` tries three import paths but none were found in inspected directories |
| Whether `utils.ml_worker` module exists | `docker-compose.prod.yml:71` references it but no top-level `utils` package exists under `backend/` |

---

## 8. REALISTIC PATH FORWARD

### Can the system be repaired / refactored / partially migrated / incrementally replaced / or substantially rewritten?

**Assessment: REPAIR + INCREMENTAL REFACTORING**

The existing system does NOT require a full rewrite. The domain model, database schema, and overall architecture are sound. The issues are discrete and concentrated:

1. **Auth/Payment Security (Repair):** The critical privilege-escalation and social-login bypass are single-point code defects that can be fixed with targeted patches (hard-code `role="customer"` in registration; remove dev-only OIDC stub; enforce JWKS verification). Plaintext tokens should be hashed before storage.

2. **Dependency Manifests (Repair):** Replace `redis==8.0.1` with `valkey==8.0.1` and fix `Pillow==12.3.0` to a valid 11.x version. Regenerate `frontend/web_app/package-lock.json` and upgrade `next` to `>=16.3.3`.

3. **Payment Safety (Repair + Refactor):** Add amount verification in generic gateway callbacks; make webhook secrets mandatory at startup; add DB-level unique constraint on `ProcessedWebhookEvent(event_id, processor)`; remove Stripe refund stub; add server-side refund amount validation.

4. **Infrastructure Alignment (Incremental Migration):** Align `docker-compose.prod.yml` with Valkey-only naming; fix ML worker command path; standardize on a single package manager or document the mixed strategy.

5. **Database Integrity (Refactor):** Add pessimistic locking or atomic patterns for stock updates; add DB triggers or application-level checks for order total consistency; make `customer_id` and `country_code` non-nullable; implement automatic soft-delete filtering in `db_read.py`.

6. **Observability/Operations (Incremental):** Deploy the monitoring stack to production; automate backup schedule; add on-call alert routing; write disaster recovery runbooks.

**Estimated effort:** The repair phase (blockers + high-risk) is achievable in 2-4 weeks with a focused team. The refactoring phase (medium-risk + technical debt) is 4-8 weeks. Full production readiness with operational maturity is 3-6 months.

---

## 9. EVIDENCE SUMMARY TABLE

| # | Finding | Domain | Status | Severity | Evidence |
|---|---------|--------|--------|----------|----------|
| 3.1 | Public registration accepts client-supplied role | Auth | VERIFIED | Critical | `auth_service.py:2404` |
| 3.2 | Social-login OIDC bypass | Auth | VERIFIED | Critical | `auth_service.py:3557-3569` |
| 3.3 | redis/valkey manifest mismatch | Dependencies | VERIFIED | Critical | `requirements.txt:20`, `valkey/client.py:81` |
| 3.4 | Pillow 12.3.0 does not exist on PyPI | Dependencies | VERIFIED | Critical | `requirements.txt:51` |
| 3.5 | Next.js 16.1.6 critical RCE | Dependencies | VERIFIED | Critical | `package-lock.json`, GHSA-p293-qw3h-jr36 |
| 3.6 | Generic gateway missing-status = success | Payments | VERIFIED | Critical | `payment_orchestrator.py:877-886` |
| 3.7 | Webhook signature verification skippable | Payments | VERIFIED | Critical | `gateway_tap.py:117-122` |
| 3.8 | /ws/user unauthenticated | API | VERIFIED | High | `main.py:194-196`, `comms.py:138-156` |
| 4.1 | Plaintext password reset tokens | Auth | VERIFIED | High | `auth_service.py:3118-3143` |
| 4.2 | Plaintext email verification tokens | Auth | VERIFIED | High | `auth_service.py:2516-2539` |
| 4.3 | /auth/me bypasses blacklist | Auth | VERIFIED | Medium-High | `accounts.py:237-251`, `auth.py:344-356` |
| 4.4 | Logout fails silently when Redis down | Auth | VERIFIED | Medium-High | `auth_service.py:2985-3022` |
| 4.5 | Default SECRET_KEY not in rejection list | Auth | VERIFIED | Medium-High | `config.py:31,262-264` |
| 4.6 | CSRF exemption on state-changing auth | Auth | VERIFIED | Medium | `csrf_middleware.py:28-37` |
| 4.7 | Inconsistent role definitions | Auth | VERIFIED | Medium | `rbac/catalog.py:14`, `rbac/dependencies.py:60-90` |
| 4.8 | Partial refund amount not validated | Payments | VERIFIED | Medium-High | `tap.py:201-260`, `paypal.py:238-293` |
| 4.9 | Webhook idempotency race condition | Payments | INFERRED | Medium-High | `payment_engine.py:4143-4323` |
| 4.10 | Stock race condition / oversell | Database | VERIFIED | High | `supplier_health.py:167-177` |
| 4.11 | Order total denormalization without consistency | Database | VERIFIED | Medium | `order_entities.py:30-38` |
| 4.12 | Stripe refund stub | Payments | VERIFIED | Medium-High | `stripe_sdk.py:27-34` |
| 4.13 | Stripe/Tap credentials in plaintext in DB | Security | VERIFIED | Medium-High | `payments.py:84-127`, `payment_engine.py:1834-1836` |
| 4.14 | Generic gateway no amount verification | Payments | VERIFIED | Medium-High | `payment_orchestrator.py:791-921` |
| 4.15 | Prod docker-compose uses Redis | Infrastructure | VERIFIED | Medium | `docker-compose.prod.yml:29,96-104` |
| 4.16 | ML worker command path mismatch | Infrastructure | VERIFIED | Medium | `docker-compose.prod.yml:71` |
| 4.17 | Hardcoded test passwords in conftest | Testing | VERIFIED | Medium | `conftest.py:52-56` |
| 4.18 | Client-influenced device fingerprint | Auth | VERIFIED | Low-Medium | `device_binding_middleware.py` |
| 4.19 | No concurrent session limit | Auth | INFERRED | Low-Medium | `auth_service.py:1121-1238` |

---

*End of Phase 17 Production Readiness Assessment. No files were modified during this audit.*
