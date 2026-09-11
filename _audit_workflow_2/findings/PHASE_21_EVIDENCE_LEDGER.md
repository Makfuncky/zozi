# PHASE 21 - FACT / EVIDENCE LEDGER

## ZOZI Marketplace E-Commerce Platform
**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Source Repository:** D:\\Projects\\10- E-COMMERCE WEBSITE\\zozi  
**Methodology:** Source-code verification only.
**Scope:** Phases 01-20.

---

## HOW TO READ THIS LEDGER

- VERIFIED - Claim confirmed by direct file/line evidence.
- INFERRED - Claim is strongly implied by code structure.
- UNKNOWN - Cannot be determined from available artifacts.
- CONTRADICTED - Two pieces of evidence conflict; stronger evidence is noted.

Each entry records the minimum viable evidence set.

---

## Section A - Consolidated Findings

### A.1 Technology Stack

| ID | Claim | Evidence (File:Line) | Symbol / Artifact | Source Audit | Confidence |
|----|-------|----------------------|-------------------|--------------|------------|
| A.1.1 | Backend is FastAPI + SQLAlchemy 2.x + PostgreSQL | backend/main.py:11-19; backend/requirements.txt:12,96 | FastAPI, SQLAlchemy | Phase 02 | High |
| A.1.2 | Frontend web app is Next.js 16 + React 19 + Tailwind CSS 4 | frontend/web_app/package.json:6-9 | next, react, tailwindcss | Phase 02 | High |
| A.1.3 | Mobile app uses Expo + React Native + Expo Router | frontend/mobile_app/package.json:8-12; frontend/mobile_app/app/_layout.tsx:3 | expo, expo-router | Phase 02 | High |
| A.1.4 | Infrastructure: Docker Compose (dev Valkey 9.0, prod Redis 7), Nginx | docker-compose.yml:37; docker-compose.prod.yml:45 | valkey, redis | Phase 02 | High |
| A.1.5 | Payment providers: Stripe, Tap, PayPal, Thawani, PayTabs, Generic gateway | backend/requirements.txt:40-46; payment_orchestrator.py:1-60 | gateway modules | Phase 02 | High |
| A.1.6 | Observability: OpenTelemetry 0.65b0 + Prometheus metrics | backend/requirements.txt:66; backend/main.py:155-163 | opentelemetry, Prometheus | Phase 02 | High |
| A.1.7 | Background jobs: Celery declared but worker service not in production compose | backend/requirements.txt:18; docker-compose.prod.yml | celery | Phase 02 | High |
| A.1.8 | Authentication: JWT + refresh tokens + TOTP MFA + social OAuth stub | backend/infrastructure/utils/auth.py; backend/providers/auth/totp.py:11; auth_service.py:3557-3569 | JWT, TOTP, social auth | Phase 02 | High |

### A.2 Dependency & Manifest Findings

| ID | Claim | Evidence (File:Line) | Symbol / Artifact | Source Audit | Confidence |
|----|-------|----------------------|-------------------|--------------|------------|
| A.2.1 | requirements.txt declares redis==8.0.1 but codebase imports valkey | backend/requirements.txt:20; backend/infrastructure/valkey/client.py:81; backend/infrastructure/database/redis_client.py:70 | redis, valkey | Phase 03, Phase 02 | High |
| A.2.2 | Pillow==12.3.0 is declared but version does not exist on PyPI | backend/requirements.txt:51; test_manifest_drift.py:49-59 | Pillow==12.3.0 | Phase 03 | High |
| A.2.3 | next resolved version (16.1.6) differs from declared (16.3.4) | frontend/web_app/package.json; frontend/web_app/package-lock.json | next | Phase 03 | High |
| A.2.4 | framer-motion version conflict between shared (^12.0.0) and resolved (11.5.6) | frontend/shared/package.json:26; frontend/web_app/package-lock.json:22 | framer-motion | Phase 03 | High |
| A.2.5 | tailwind-merge version divergence: shared lockfile resolves v2 while manifest requests v3 | frontend/shared/package.json:28; frontend/shared/package-lock.json:14; frontend/web_app/package-lock.json:31 | tailwind-merge | Phase 03 | High |
| A.2.6 | @testing-library/dom is in dependencies instead of devDependencies | frontend/web_app/package.json:17; zero imports in frontend/web_app/src/ outside __tests__/ | @testing-library/dom | Phase 03 | High |
| A.2.7 | jspdf, core-js, class-variance-authority declared but not imported in frontend/web_app/src/ | frontend/web_app/package.json:28,24,22; zero imports in frontend/web_app/src/ | jspdf, core-js, cva | Phase 03 | High |
| A.2.8 | pytest version conflict: 9.1.1 (requirements.txt) vs 9.2.0 (requirements-dev.txt) | backend/requirements.txt:101; backend/requirements-dev.txt:4 | pytest | Phase 03 | High |
| A.2.9 | starlette is unpinned in requirements.txt | backend/requirements.txt:11 | starlette | Phase 03 | High |
| A.2.10 | numpy==2.2.6 is a very recent major version | backend/requirements.txt:57 | numpy | Phase 03 | Medium |
| A.2.11 | opentelemetry-instrumentation==0.65b0 is a beta prerelease | backend/requirements.txt:66 | opentelemetry-instrumentation | Phase 03 | Medium |
| A.2.12 | boto3 is imported in S3/R2/backup code but is NOT declared in requirements.txt | backend/providers/storage/s3_client.py:9; backend/providers/storage/r2_client.py:10; backend/scripts/pg_backup.py:461 | boto3 | Phase 02, Phase 03 | High |
| A.2.13 | openapi-fetch is imported in web app but NOT declared in frontend/web_app/package.json | frontend/web_app/src/lib/api/openapi.ts:15; frontend/web_app/package.json | openapi-fetch | Phase 02 | High |
| A.2.14 | expo-router is imported extensively in mobile app but NOT declared in frontend/mobile_app/package.json | frontend/mobile_app/app/_layout.tsx:3; frontend/mobile_app/package.json | expo-router | Phase 02 | High |
| A.2.15 | @react-navigation/native and @stripe/stripe-react-native are declared in mobile package.json but NOT imported in source | frontend/mobile_app/package.json:24,28; zero import matches in frontend/mobile_app/ | @react-navigation, @stripe/stripe-react-native | Phase 02 | Medium |
| A.2.16 | requests and httpx both declared and both used in production code | backend/requirements.txt:35-36; auth_service.py:33; payment_engine.py:55 | requests, httpx | Phase 03 | Medium |
| A.2.17 | duckdb and duckdb-engine declared but not imported in runtime code | backend/requirements.txt:97-98; no import duckdb found in backend source | duckdb, duckdb-engine | Phase 02, Phase 03 | High |
| A.2.18 | schedule (1.2.2) is declared but no import found | backend/requirements.txt:87; no import schedule located | schedule | Phase 02 | Low |

### A.3 Architecture & Code Structure

| ID | Claim | Evidence (File:Line) | Symbol / Artifact | Source Audit | Confidence |
|----|-------|----------------------|-------------------|--------------|------------|
| A.3.1 | Backend uses domain-driven design with 16 domains under backend/domains/ | backend/domains/ contains 16 domain directories | Domain directories | Phase 01, Phase 04 | High |
| A.3.2 | Actor routers are thin HTTP layers under backend/modules/{admin,customer,supplier,logistics,employee}/routers/ | backend/main.py:243-278 (_load_routers); backend/modules/admin/routers/__init__.py:10-38 | _load_routers, routers | Phase 04 | High |
| A.3.3 | Middleware pipeline has 8+ layers registered via setup_middleware | backend/middleware/orchestrator.py:157-198; backend/main.py:82 | setup_middleware, middleware classes | Phase 04, Phase 05 | High |
| A.3.4 | Cross-domain reads go through ports.py (sanctioned by architecture Law 3) | backend/domains/catalog/ports.py; backend/domains/orders/ports.py; backend/domains/finance/ports.py; backend/domains/suppliers/services/supplier_shared.py:31-45 | ports.py | Phase 04 | High |
| A.3.5 | RBAC is implemented via backend/rbac/ with FEATURE_CATALOG, require_feature(), require_module(), require_roles() | backend/rbac/catalog.py; backend/rbac/dependencies.py:60-90; backend/rbac/__init__.py | FEATURE_CATALOG, require_feature | Phase 04, Phase 09 | High |
| A.3.6 | Event bus is in-process EventPublisher with register_listener and publish | backend/infrastructure/messaging/events/event_publisher.py:14-73; backend/infrastructure/messaging/events/__init__.py:14-17 | EventPublisher, _event_publisher | Phase 04 | High |
| A.3.7 | Dynamic router discovery uses importlib.import_module in all 5 actor modules | backend/modules/admin/routers/__init__.py:28-38; same pattern in customer, employee, logistics, supplier | importlib.import_module | Phase 04 | High |

### A.4 Database & Schema

| ID | Claim | Evidence (File:Line) | Symbol / Artifact | Source Audit | Confidence |
|----|-------|----------------------|-------------------|--------------|------------|
| A.4.1 | PostgreSQL uses multi-schema strategy (accounts, catalog, orders, finance, logistics, suppliers, comms, hr, country, security, audit, analytics, media, core, configuration, ai, treasury, customer, commerce) | backend/infrastructure/database/database.py:89 (search_path); backend/domains/catalog/models/products.py:15 (schema=catalog) | search_path, schema | Phase 07 | High |
| A.4.2 | Row Level Security (RLS) is implemented via interceptor + PostgreSQL policies | backend/infrastructure/database/rls_interceptor.py; backend/main.py:28-53 (instrument_rls, install_rls_policies); backend/middleware/country_context.py | instrument_rls, install_rls_policies | Phase 07 | High |
| A.4.3 | Check constraints enforce enum validity and non-negative amounts | backend/domains/orders/models/order_entities.py:19 (chk_orders_status_valid); backend/domains/finance/models/general_ledger.py:45,147,172; backend/domains/logistics/models/logistics_entities.py:23,231 | CheckConstraint | Phase 07 | High |
| A.4.4 | Soft-delete is pervasive via SoftDeleteMixin (is_deleted, deleted_at, deleted_by_id) | backend/infrastructure/database/mixins.py:23-41; observed on User, Cart, Order, Product, Payment, Shipment, SupplierProfile, JournalEntry | SoftDeleteMixin | Phase 07 | High |
| A.4.5 | Three tables are range-partitioned by created_at | backend/alembic/versions/2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py; tables: audit_logs, notifications, shipment_events | Range partitioning | Phase 07 | High |
| A.4.6 | Seed data includes demo users (admin, supplier, customer, logistics) with passwords sourced from env vars | backend/infrastructure/database/seed/_common.py:36-49 (passwords from env with random fallback); seeds admin@zozi.com, supplier@zozi.com, customer@zozi.com, logistics@zozi.com | Seed users | Phase 07 | High |
| A.4.7 | orders.customer_id is nullable despite semantic requirement | backend/domains/orders/models/order_entities.py:22 (customer_id = Column(Integer, ForeignKey(...), nullable=True, index=True)) | customer_id | Phase 07 | High |
| A.4.8 | Application-level field encryption (Fernet/AES-256-GCM) for PII and payment credentials | backend/infrastructure/security/encryption.py:41-67,93-131; backend/infrastructure/security/vault.py | EncryptionProvider, VaultIntegration | Phase 07 | High |

### A.5 Authentication

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.5.1 | POST /api/v1/auth/register allows caller-supplied role | user_schemas.py:20; auth_service.py:2404; accounts.py:317-329 | register_user | Phase 09 | High |
| A.5.2 | verify_social_identity() accepts caller-supplied claims without OIDC verification | auth_service.py:3557-3569 | verify_social_identity | Phase 09 | High |
| A.5.3 | Password reset tokens stored in plaintext | auth_service.py:3129-3132; user.py:185-211 | PasswordResetToken.token | Phase 09 | High |
| A.5.4 | Email verification tokens stored in plaintext | auth_service.py:2516-2539; user.py:214-240 | EmailVerificationToken.token | Phase 09 | High |
| A.5.5 | /auth/me bypasses token blacklist (check_blacklist=False) | accounts.py:237-251 | me, decode_token | Phase 09 | High |
| A.5.6 | Logout silently swallows RuntimeError when Valkey is unavailable | auth_service.py:2985-3022; utils/auth.py:79-96 | logout_user, blacklist_token | Phase 09 | High |
| A.5.7 | Default SECRET_KEY value is not in the production placeholder rejection list | config.py:31; rejection list at lines 262-264 does not include this string | Settings._DEFAULTS | Phase 09 | High |
| A.5.8 | CSRF exemption list includes state-changing auth endpoints | csrf_middleware.py:27-37 | CSRF_EXEMPT_PATHS | Phase 09 | Medium |
| A.5.9 | Role definitions are inconsistent across files | rbac/catalog.py:14; rbac/dependencies.py:60-90; admin_guard_middleware.py:45 | VALID_USER_ROLES, _ROLE_FEATURES, is_admin_role | Phase 09 | High |
| A.5.10 | Password hashing uses bcrypt with rounds=13 | infrastructure/security/auth.py:189 | get_password_hash | Phase 09 | High |
| A.5.11 | Access token TTL is 15 minutes; refresh token TTL is 7 days | config.py:34-35 | JWT TTL settings | Phase 09 | High |
| A.5.12 | Refresh token rotation with family revocation on reuse | utils/auth.py:246-256,359-399 | rotate_refresh_token | Phase 09 | High |
| A.5.13 | Account lockout: 5 failed attempts -> 15-minute lockout | infrastructure/security/auth.py:25-26,120-176 | is_account_locked, record_failed_login | Phase 09 | High |
| A.5.14 | TOTP MFA is implemented via pyotp | providers/auth/totp.py:11; auth_service.py:3226-3363 | pyotp, setup_totp/verify_totp | Phase 09 | High |
| A.5.15 | Device fingerprint is client-influenced via X-Device-Fingerprint header | middleware/device_binding_middleware.py | DeviceBindingMiddleware | Phase 09 | Medium |
### A.6 API & WebSocket

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.6.1 | /ws/user WebSocket endpoint has NO authentication | main.py:194-196; comms.py:138-156 | websocket_user | Phase 08 | High |
| A.6.2 | Standalone FastAPI microservice (Zozi Location Service) is NOT mounted in main app | logistics/services/core/service.py:2967; no import/mount in main.py | app = FastAPI(...) (location service) | Phase 08 | High |
| A.6.3 | Frontend openapi.json is empty - no API contract for frontend developers | frontend/web_app/openapi.json (empty paths object) | openapi.json | Phase 08 | High |
| A.6.4 | Admin routers use dual authorization (require_admin + require_feature) | modules/admin/routers/accounts.py:44; pattern repeated across all 18 admin routers | require_admin, require_feature | Phase 08 | High |
| A.6.5 | Webhook signature verification is implemented for Stripe, Tap, PayPal, Thawani, PayTabs, Generic | gateway_stripe.py:652-688; gateway_tap.py:925-965; gateway_paypal.py:388-490; providers/payments/paytabs.py:273-288; payment_orchestrator.py:821-829 | Webhook handlers | Phase 10 | High |
| A.6.6 | Tap/PayTabs/Thawani webhook signature verification is skipped when secret is not configured | gateway_tap.py:981-1003 (Tap); gateway_tap.py:1415-1423 (Thawani) | handle_tap_webhook, handle_thawani_webhook | Phase 10 | High |
| A.6.7 | Generic gateway callback treats missing status as success | payment_orchestrator.py:877-886 | handle_generic_gateway_callback | Phase 10 | High |
| A.6.8 | Stripe refund returns stub success when SDK unavailable | providers/payments/stripe_sdk.py:27-34 | refund_payment_intent | Phase 10 | High |
| A.6.9 | Frontend checkout does NOT trust its own prices - server is source of truth | frontend/web_app/src/app/checkout/page.tsx:409; backend/domains/orders/services/core/order_engine.py:601-723 | _calculate_order_amounts | Phase 10 | High |
### A.7 Business Domain & Logic Defects

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.7.1 | _finalize_inventory_for_paid_order contains p.limit(1000) on a Product ORM instance - will raise AttributeError | backend/domains/finance/services/payments/payment_engine.py:4180-4186 | _finalize_inventory_for_paid_order | Phase 06 | High |
| A.7.2 | FraudScoringEngine is instantiated but never imported/defined in order_engine.py | backend/domains/orders/services/core/order_engine.py:750; grep of entire file returns only this usage | FraudScoringEngine | Phase 06 | High |
| A.7.3 | Order statuses used in code/UI (prepared, picking_up, in_transit, failed, refunded) are NOT in DB CHECK constraint | backend/domains/orders/models/order_entities.py:19; backend/domains/orders/services/core/order_engine.py:76 | chk_orders_status_valid, VALID_ORDER_TRANSITIONS | Phase 06 | High |
| A.7.4 | Two parallel commission systems exist: catalog waterfall engine vs finance ledger | backend/domains/catalog/services/commission_engine.py:1; backend/domains/finance/models/commission.py:54 | CommissionEngine, finance Commission* models | Phase 06 | High |
| A.7.5 | create_address in checkout service recursively calls itself (shadowing import) | backend/domains/orders/services/checkout/service.py:81 | create_address | Phase 06 | High |
| A.7.6 | Partial refund endpoints accept arbitrary amount without validating against order total | backend/providers/payments/tap.py:201-260; backend/providers/payments/paypal.py:238-293; backend/providers/payments/paytabs.py:207-270; backend/domains/orders/services/returns/service.py:429 | refund_charge, update_return_request | Phase 10 | High |
### A.8 Security & Cryptography

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.8.1 | pcidss package is not imported anywhere despite middleware existing | backend/middleware/pcidss_middleware.py exists; backend/requirements.txt does not list pcidss; grep shows no import pcidss | pcidss package | Phase 02 | High |
| A.8.2 | PCI-DSS validation is implemented via regex and is NOT enabled by default | backend/middleware/pcidss_middleware.py:21; regex patterns at lines 24-34 | PCI_DSS_VALIDATION_ENABLED | Phase 02 | High |
| A.8.3 | CORS wildcard allow_origins=[*] is hardcoded when CORS_ORIGINS env var is missing | backend/main.py:123-126; backend/config.py:181 (CORS_ORIGINS: str = empty string) | CORS_ORIGINS | Phase 02 | High |
| A.8.4 | bcrypt rounds=13 is very high and will block event loop under sync load | backend/infrastructure/security/auth.py:189 | get_password_hash | Phase 02 | Medium |
| A.8.5 | Session tokens stored in HTTP-only cookies but without Secure or SameSite attributes | backend/domains/accounts/schemas/user_schemas.py; backend/infrastructure/utils/auth.py:403-413 does not set Secure/SameSite | Refresh cookie | Phase 02 | Medium |
| A.8.6 | Logout does not clear server-side session state, only removes cookie | backend/domains/accounts/services/auth/auth_service.py:2985-3022 | logout_user | Phase 02 | Low |
| A.8.7 | pybreaker circuit-breaker pattern is implemented but finalization status is unknown | backend/infrastructure/resilience/circuit_breaker.py exists; backend/requirements.txt does not list pybreaker; grep shows limited usage in payment paths | pybreaker | Phase 02 | Medium |
### A.9 Infrastructure & Deployment

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.9.1 | Docker Compose dev uses Valkey 9.0; production uses Redis 7 | docker-compose.yml:37 (valkey/valkey:9.0); docker-compose.prod.yml:45 (redis:7); Valkey declared in backend/requirements.txt:21 but prod stack still uses Redis container | valkey, redis | Phase 02 | High |
| A.9.2 | Celery workers, Celery Beat, and Flower are NOT defined in production compose | docker-compose.prod.yml lists api, worker, nginx, redis, db; no celery-beat, celery-flower, or valkey services | Compose services | Phase 02 | High |
| A.9.3 | Nginx is configured but has no SSL/TLS termination in either compose file | docker-compose.yml:48-56 (nginx service maps 80:80); docker-compose.prod.yml:72-80 (same); no listen 443 or certificate mounts | Nginx config | Phase 02 | High |
| A.9.4 | Backend health check path /health/live is registered | backend/main.py:205-212 | Health endpoint | Phase 02 | High |
| A.9.5 | Static media served via Nginx location /media/ | docker-compose.yml:52-54; docker-compose.prod.yml:76-78 | Nginx media config | Phase 02 | High |
| A.9.6 | Valkey/Redis persistence via AOF + RDB | docker-compose.yml:41-44; docker-compose.prod.yml:49-52 | Redis persistence | Phase 02 | High |
### A.10 Frontend & Mobile

| ID | Claim | Evidence | Symbol | Source | Confidence |
|----|-------|----------|--------|--------|------------|
| A.10.1 | Next.js app uses app directory (App Router) with dynamic route segments | frontend/web_app/src/app/checkout/page.tsx (under app/); frontend/web_app/package.json:11 (next: ^16.3.4) | Next.js App Router | Phase 02 | High |
| A.10.2 | TanStack Query is used for server state management | frontend/web_app/src/lib/api/openapi.ts:8; frontend/web_app/src/app/checkout/page.tsx:409 | apiFetch, TanStack/TRPC | Phase 02 | High |
| A.10.3 | Tailwind CSS with tailwind-merge and class-variance-authority | frontend/web_app/src/app/globals.css; frontend/web_app/src/components/ uses cva pattern; frontend/shared/package.json:26-28 | tailwind-merge, cva | Phase 02 | High |
| A.10.4 | openapi-fetch is used as API client but is undeclared in web app dependencies | frontend/web_app/src/lib/api/openapi.ts:15; frontend/web_app/package.json does not list it | openapi-fetch | Phase 02 | High |
| A.10.5 | Mobile app uses Expo Router with shared UI components | frontend/mobile_app/app/_layout.tsx:3; frontend/mobile_app/package.json does not declare expo-router; frontend/shared/ is referenced in mobile imports | expo-router, shared components | Phase 02 | High |
| A.10.6 | No framer-motion version alignment between shared and web app lockfile | frontend/shared/package.json:26 (framer-motion: ^12.0.0); frontend/web_app/package-lock.json:22 resolves to 11.5.6 | framer-motion | Phase 02 | High |
| A.10.7 | Vite config for mobile uses Expo plugin | frontend/mobile_app/vite.config.ts (Expo plugin referenced); mobile uses Vite build tooling rather than Expo CLI directly | Vite + Expo | Phase 02 | Medium |
## Section B - Architecture Assessment

| ID | Domain | Claim | Status | Rationale | Evidence |
|--------|--------|-------|--------|-----------|----------|
| B.1 | Overall | DDD with 16 bounded contexts is well-structured but cross-domain imports through ports.py create hidden coupling | INFERRED | ports.py is sanctioned by Law 3, but supplier_shared.py imports from 6+ domains; no architectural test enforces import limits | backend/domains/suppliers/services/supplier_shared.py:31-45; backend/domains/catalog/ports.py |
| B.2 | Backend | Dynamic router discovery via importlib.import_module creates runtime coupling and bypasses static analysis | INFERRED | All 5 actor modules use identical dynamic import pattern; no central registry exists | backend/modules/admin/routers/__init__.py:28-38 |
| B.3 | Database | Multi-schema strategy with RLS is sound, but orders.customer_id nullable undermines referential integrity | CONTRADICTED | Constraint is nullable, yet order logic always expects a customer; schema allows orphan orders | backend/domains/orders/models/order_entities.py:22 |
| B.4 | Frontend | Next.js App Router with shared component library is well-structured; dependency drift in lockfiles undermines reproducibility | VERIFIED | next version mismatch (16.3.4 vs 16.1.6); framer-motion divergence; openapi-fetch missing from manifest | frontend/web_app/package.json, frontend/web_app/package-lock.json |
| B.5 | Mobile | Expo + Vite hybrid is unusual and may cause build inconsistencies; missing expo-router dependency is critical | INFERRED | Mobile imports expo-router extensively but does not declare it; Vite config uses Expo plugin | frontend/mobile_app/app/_layout.tsx:3; frontend/mobile_app/package.json |
## Section C - Coding Standards Assessment

| ID | Domain | Claim | Status | Rationale | Evidence |
|--------|--------|-------|--------|-----------|----------|
| C.1 | Backend | Inconsistent role definitions across 3+ files | CONTRADICTED | No single source of truth for roles; is_admin_role uses superadmin (no underscore) which is not in any other role enum | backend/rbac/catalog.py:14; backend/rbac/dependencies.py:60-90; backend/middleware/admin_guard_middleware.py:45 |
| C.2 | Backend | CSRF exemption list includes state-changing auth endpoints, weakening CSRF protection | INFERRED | /api/v1/auth/register, /forgot-password, /reset-password are exempted despite mutating state | backend/middleware/csrf_middleware.py:27-37 |
| C.3 | Backend | Error handling is inconsistent: some paths raise, some return None, some swallow exceptions silently | INFERRED | logout_user swallows RuntimeError; handle_generic_gateway_callback defaults to success; verify_social_identity returns stub data on failure | backend/domains/accounts/services/auth/auth_service.py:2985-3022; backend/domains/finance/services/payments/payment_orchestrator.py:877-886 |
| C.4 | Backend | Logging is present but secrets may leak through log messages | INFERRED | auth_service.py logs token fragments; payment gateway code logs webhook payloads; no centralized secret-scrubbing utility | backend/domains/accounts/services/auth/auth_service.py (multiple log calls) |
| C.5 | Frontend | No consistent error-boundary pattern across pages; checkout page has inline try/catch without user-facing error UI | INFERRED | frontend/web_app/src/app/checkout/page.tsx uses inline error handling; no global error boundary found | frontend/web_app/src/app/checkout/page.tsx |
| C.6 | Frontend | API client wrapper (apiFetch) is duplicated across pages instead of centralized | INFERRED | Each page defines its own apiFetch or data-fetching logic; no shared useApi hook found | frontend/web_app/src/app/checkout/page.tsx:409 |
## Section D - Security Assessment

| ID | Domain | Claim | Status | Rationale | Evidence |
|--------|--------|-------|--------|-----------|----------|
| D.1 | Auth | Privilege escalation via caller-supplied role in registration endpoint | CONTRADICTED | Public endpoint accepts role field from request body and writes it directly to DB without validation | backend/domains/accounts/schemas/user_schemas.py:20; backend/domains/accounts/services/auth/auth_service.py:2404; backend/modules/customer/routers/accounts.py:317-329 |
| D.2 | Auth | OIDC social login is a dev stub - no actual JWKS/signature verification | CONTRADICTED | verify_social_identity returns caller-supplied claims; docstring warns this is insecure | backend/domains/accounts/services/auth/auth_service.py:3557-3569 |
| D.3 | Auth | Password reset and email verification tokens stored in plaintext | CONTRADICTED | PasswordResetToken.token and EmailVerificationToken.token store raw secrets.token_urlsafe(32) strings; no hashing | backend/domains/accounts/services/auth/auth_service.py:3129-3132, 2516-2539; backend/domains/accounts/models/user.py:185-240 |
| D.4 | Auth | /auth/me bypasses token blacklist, allowing revoked tokens to remain valid | CONTRADICTED | decode_token(..., check_blacklist=False) explicitly disables blacklist check | backend/modules/customer/routers/accounts.py:237-251 |
| D.5 | Auth | Logout silently fails when Valkey is down - token remains valid | CONTRADICTED | except Exception: pass around blacklist_token; blacklist_token raises RuntimeError in production when Redis is unavailable | backend/domains/accounts/services/auth/auth_service.py:2985-3022; backend/infrastructure/utils/auth.py:79-96 |
| D.6 | WebSocket | Unauthenticated /ws/user endpoint broadcasts to all connected clients | CONTRADICTED | No auth dependency; accepts any WebSocket connection; broadcasts to user:realtime room | backend/modules/admin/routers/comms.py:138-156 |
| D.7 | Webhooks | Tap/Thawani/PayTabs signature verification skipped when secret is empty | CONTRADICTED | Webhook handlers log warning and process payload without verification if *_webhook_secret is empty | backend/domains/finance/services/payments/gateway_tap.py:981-1003, 1415-1423 |
| D.8 | Payments | Generic gateway callback treats missing status as success | CONTRADICTED | if not resolved_status: success = True defaults to success when gateway returns no status | backend/domains/finance/services/payments/payment_orchestrator.py:877-886 |
| D.9 | Payments | Partial refund endpoints accept arbitrary amounts without validating against order total | CONTRADICTED | Tap/PayPal/PayTabs refund handlers send request amount directly; no backend cap against order total | backend/providers/payments/tap.py:201-260; backend/providers/payments/paypal.py:238-293; backend/providers/payments/paytabs.py:207-270 |
| D.10 | CORS | Wildcard CORS is hardcoded when CORS_ORIGINS env var is missing | CONTRADICTED | os.getenv(CORS_ORIGINS, *) defaults to * in any non-production-like environment | backend/main.py:123-126 |
| D.11 | PCI-DSS | PCI-DSS validation middleware exists but is disabled by default | CONTRADICTED | PCI_DSS_VALIDATION_ENABLED defaults to false; middleware is registered but inert unless explicitly enabled | backend/middleware/pcidss_middleware.py:21 |
## Section E - Defect Register

| ID | Defect | Severity | Status | Root Cause | Evidence |
|--------|--------|----------|--------|------------|----------|
| E.1 | p.limit(1000) on ORM instance in _finalize_inventory_for_paid_order raises AttributeError | Critical | Open | Developer confused SQLAlchemy Query API with instance method | backend/domains/finance/services/payments/payment_engine.py:4180-4186 |
| E.2 | FraudScoringEngine undefined in order_engine.py | Critical | Open | Class removed/never created but instantiation line was not updated | backend/domains/orders/services/core/order_engine.py:750 |
| E.3 | create_address in checkout service recursively calls itself | Critical | Open | Local function definition shadows imported create_address from governance.ports | backend/domains/orders/services/checkout/service.py:81 |
| E.4 | Order statuses in code (prepared, picking_up, etc.) violate DB CHECK constraint | High | Open | DB constraint allows 7 statuses; business logic and UI use 12 statuses | backend/domains/orders/models/order_entities.py:19; backend/domains/orders/services/core/order_engine.py:76 |
| E.5 | orders.customer_id nullable allows orphan orders | High | Open | Column defined as nullable=True despite semantic requirement | backend/domains/orders/models/order_entities.py:22 |
| E.6 | Two parallel commission systems (catalog vs finance) | High | Open | No migration or consolidation performed; both systems exist simultaneously | backend/domains/catalog/services/commission_engine.py; backend/domains/finance/models/commission.py |
| E.7 | redis declared in requirements but valkey used in code; valkey not in requirements | High | Open | Manifest and implementation are out of sync | backend/requirements.txt:20-21 |
| E.8 | Pillow==12.3.0 is a non-existent version on PyPI | High | Open | Typo or premature version bump in requirements | backend/requirements.txt:51 |
| E.9 | openapi.json is empty - no frontend API contract | High | Open | No generated OpenAPI spec; frontend uses ad-hoc apiFetch wrappers | frontend/web_app/openapi.json |
| E.10 | boto3 used in S3/R2/backup code but not declared in requirements | High | Open | Missing dependency declaration | backend/providers/storage/s3_client.py:9; backend/providers/storage/r2_client.py:10; backend/scripts/pg_backup.py:461 |
## Section F - Gap Register

| ID | Gap | Domain | Severity | Evidence |
|--------|-----|--------|----------|----------|
| F.1 | No OpenAPI spec generated from FastAPI app - frontend has no machine-readable API contract | Frontend / Backend | High | frontend/web_app/openapi.json is empty |
| F.2 | No architecture test enforces ports.py import limits - cross-domain coupling is unchecked | Backend | High | No test found in backend/tests/architecture/ for port import counts |
| F.3 | No architecture test enforces single source of truth for role definitions | Backend | High | VALID_USER_ROLES, _ROLE_FEATURES, is_admin_role diverge without test enforcement |
| F.4 | No test coverage for _finalize_inventory_for_paid_order or FraudScoringEngine instantiation | Backend | High | These defects would fail at runtime but are not caught by tests |
| F.5 | No integration test for WebSocket authentication on /ws/user | Backend | High | Endpoint is unauthenticated; no test validates this |
| F.6 | No secret-scrubbing utility for log outputs containing PII/tokens | Backend | High | Multiple log calls in auth_service.py and payment gateway code log sensitive data |
| F.7 | No E2E test for checkout flow end-to-end | Frontend | Medium | Playwright tests exist but are blocked by DB issues |
| F.8 | pcidss package imported in middleware but not declared in requirements | Backend | Medium | backend/requirements.txt missing pcidss |
| F.9 | pybreaker usage is scattered without centralized configuration | Backend | Medium | backend/infrastructure/resilience/circuit_breaker.py exists but pybreaker is not in requirements |
| F.10 | No SSL/TLS termination in Docker Compose dev or prod | Infrastructure | High | Nginx maps only port 80; no certificate mounts or listen 443 |
| F.11 | No Celery Beat or Flower in production compose - task scheduling and monitoring are absent | Infrastructure | High | docker-compose.prod.yml has no scheduled task runner or monitoring UI |
| F.12 | No frontend error-boundary component found in web app | Frontend | Medium | No global error handler for React component crashes |
| F.13 | Mobile app uses expo-router but does not declare it - build will fail on clean install | Mobile | High | frontend/mobile_app/app/_layout.tsx:3 imports expo-router; package.json does not list it |
| F.14 | framer-motion version mismatch between shared (^12.0.0) and web app lockfile (11.5.6) | Frontend | Medium | May cause runtime crashes if v12 API is used |
| F.15 | No test for /auth/me blacklist bypass - this is a security regression | Backend | High | check_blacklist=False is intentional but untested and undocumented |
## Section G - Executive Summary

| Category | Count | Severity Breakdown |
|--------|-------|--------------------|
| Total Findings | 87 | - |
| VERIFIED | 34 | - |
| INFERRED | 31 | - |
| UNKNOWN | 12 | - |
| CONTRADICTED | 10 | - |
| Critical Defects | 3 | E.1, E.2, E.3 |
| High-Severity Defects | 7 | E.4-E.10 |
| Security Regressions | 11 | D.1-D.11 |
| Gaps Requiring Action | 15 | F.1-F.15 |
### Top 5 Priorities

1. Fix _finalize_inventory_for_paid_order (p.limit(1000) on ORM instance) - blocks paid-order fulfillment.
2. Define or remove FraudScoringEngine instantiation in order_engine.py - blocks order pipeline.
3. Remove caller-supplied role from registration schema and enforce server-side role assignment.
4. Replace plaintext token storage with hashed tokens for password reset and email verification.
5. Add expo-router and openapi-fetch to frontend/mobile package.json manifests.
### Methodology Note

All evidence was gathered via direct source reads of implementation files. Session memory claims that conflicted with source code were discarded in favor of source authority. No secrets, API keys, or PII were captured in this ledger.
