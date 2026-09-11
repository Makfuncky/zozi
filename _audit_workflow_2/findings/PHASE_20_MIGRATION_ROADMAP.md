# TASK 20 - INDUSTRIAL MIGRATION ROADMAP
## ZOZI Marketplace E-Commerce Platform

**Audit Date:** 2026-09-11  
**Auditor:** Kilo (Forensic Technical Audit)  
**Repository:** D:\Projects\10- E-COMMERCE WEBSITE\zozi  
**Source Documents:** PHASE_14_BUGS.md, PHASE_17_PRODUCTION_READINESS.md, PHASE_19_TARGET_ARCHITECTURE.md, PHASE_21_EVIDENCE_LEDGER.md  
**Methodology:** Source-code verification only. Findings classified as VERIFIED / INFERRED / UNKNOWN with file/line evidence.

---

## 1. EXECUTIVE SUMMARY

The ZOZI Marketplace is a modular monolith FastAPI + Next.js + Expo e-commerce platform with a well-structured domain architecture, 16 bounded contexts, multi-schema PostgreSQL with RLS, Valkey caching, Celery workers, and a comprehensive observability stack. The target architecture, as defined in PHASE_19, is **Modular Monolith + Dedicated Workers** — an extension of the current pattern rather than a disruptive microservices rewrite.

The migration from **CURRENT VERIFIED SYSTEM** to **TARGET ARCHITECTURE** requires 16 ordered phases. The system contains discrete, fixable defects concentrated in auth, payments, dependencies, and database integrity. No full rewrite is required. The realistic path is **REPAIR + INCREMENTAL REFACTORING**.

**Estimated effort:**
- Phase 1–5 (blockers + foundation): 2–4 weeks
- Phase 6–11 (core migration): 4–8 weeks
- Phase 12–16 (optimization + cleanup): 2–4 weeks
- Total: 8–16 weeks with a focused team

**Critical path:** Dependency Stabilization → Security Remediation → Database Stabilization → Infrastructure Modernization → Production Validation.

---


## 2. CURRENT STATE VERIFICATION SUMMARY

### 2.1 Verified Critical Defects (from PHASE_14, PHASE_17, PHASE_21)

| # | Defect | Severity | Evidence |
|---|--------|----------|----------|
| 1 | Public registration accepts client-supplied role (privilege escalation) | CRITICAL | auth_service.py:2404, user_schemas.py:20,47, modules/customer/routers/accounts.py:317-329 |
| 2 | Social-login OIDC bypass — dev stub accepts caller-supplied claims | CRITICAL | auth_service.py:3557-3569 |
| 3 | redis==8.0.1 in requirements.txt but code imports valkey | CRITICAL | requirements.txt:20, infrastructure/valkey/client.py:81 |
| 4 | Pillow==12.3.0 does not exist on PyPI | CRITICAL | requirements.txt:51 |
| 5 | Next.js lockfile resolves 16.1.6 (critical RCE GHSA-p293-qw3h-jr36) | CRITICAL | frontend/web_app/package-lock.json, package.json:30 |
| 6 | Generic gateway callback treats missing status as success | CRITICAL | payment_orchestrator.py:877-885 |
| 7 | Webhook signature verification skippable for Tap/Thawani/PayTabs | CRITICAL | gateway_tap.py:981-1003, 1415-1423 |
| 8 | /ws/user WebSocket endpoint has no authentication | HIGH | main.py:194-196, modules/admin/routers/comms.py:138-156 |
| 9 | order.status vs order.status_code — ~30 service files crash | CRITICAL | order_entities.py:24, order_engine.py:897,1020-1021, tracking/service.py:1041, orders_service.py:393 |
| 10 | Infinite recursion in create_address() | CRITICAL | domains/orders/services/checkout/service.py:96 |
| 11 | Duplicate function definitions in finance_service.py (infinite recursion) | CRITICAL | finance_service.py:372-487 |
| 12 | Payment status check constraint allows 4 statuses; code uses 6+ | HIGH | order_entities.py:19, payment_orchestrator.py, gateway_tap.py |
| 13 | Plaintext password reset tokens | HIGH | auth_service.py:3118-3143, user.py:185-211 |
| 14 | Plaintext email verification tokens | HIGH | auth_service.py:2516-2539, user.py:214-240 |
| 15 | Production docker-compose uses redis:7-alpine, not Valkey | MEDIUM | docker-compose.prod.yml:96-104 |
| 16 | ML worker command path mismatch | MEDIUM | docker-compose.prod.yml:71 |
| 17 | Orders with duplicate amount columns (subtotal/subtotal_amount, etc.) | MEDIUM | order_entities.py:30-38 |
| 18 | orders.customer_id nullable despite semantic requirement | HIGH | order_entities.py:22 |
| 19 | Stock race condition — inventory oversell | HIGH | supplier_health.py:167-177, 542-602 |
| 20 | CORS wildcard hardcoded when CORS_ORIGINS env var missing | MEDIUM | main.py:123-126, config.py:181 |

### 2.2 Verified Target Architecture Components (from PHASE_19)

| Component | Current State | Target State | Gap |
|-----------|--------------|--------------|-----|
| Architecture | Modular monolith | Modular monolith + workers | Workers exist but need production alignment |
| Database | Neon PostgreSQL 18 | Neon PostgreSQL 18 + replicas | Replicas configured but not verified in production |
| Cache | Valkey single node (dev), Redis 7 (prod) | Valkey cluster | Production still uses Redis; cluster not configured |
| Workers | 4 Celery queues (ml, periodic, payouts, emails) | Same + production wiring | Not in production compose |
| Observability | OTel + Prometheus + Grafana + Loki | Same + production deployment | Monitoring stack defined but not deployed |
| Security | Multiple critical/high issues | Fixed | Requires discrete patches |
| Frontend | Next.js 16.3.4 (manifest), 16.1.6 (lockfile) | Next.js >=16.3.4 | Lockfile needs regeneration |

---

## 3. MIGRATION PHASES

### PHASE 1: REPOSITORY CLEANUP
**Objective:** Remove non-production artifacts from the repository to reduce attack surface, improve clone times, and eliminate confusion.

**Prerequisites:** None. Can run in parallel with Phase 2.

**Files/components affected:**
- Repository root: test_phase7e2.db, test_phase7e2.db-shm, test_phase7e2.db-wal, dump.rdb
- frontend/web_app/ root: test_logistics.txt, staff_test.txt, output.txt, build_output.txt, playwright-results.txt
- backend/.env (exists in working tree; gitignored but should be removed from developer environments)
- Root .env (same)
- Empty directories: backend/providers/voice/, backend/infrastructure/uploads/

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:** None.

**Testing required:**
- Verify git status shows no tracked database or test artifact files
- Confirm .gitignore covers *.db, dump.rdb, .env, playwright-results/
- Run git ls-files --others --ignored --exclude-standard to confirm ignored files are not tracked

**Deployment strategy:** No deployment. Repository-only change.

**Rollback strategy:** N/A — removal of untracked files is non-breaking.

**Risk:** LOW — no production code affected.

**Exit criteria:**
- [ ] No database files (.db, .rdb) in repository root or subdirectories (except .gitignore)
- [ ] No test artifact files (test_*.txt, output.txt, playwright-results/) in tracked paths
- [ ] Empty directories removed or contain .gitkeep if structurally required
- [ ] .env files confirmed gitignored and absent from tracked history

---

### PHASE 2: DEPENDENCY STABILIZATION
**Objective:** Fix all manifest/lockfile mismatches, missing dependencies, and vulnerable packages so the application installs and starts cleanly.

**Prerequisites:** Phase 1 (repository cleanup).

**Files/components affected:**
- backend/requirements.txt — replace redis==8.0.1 with valkey==8.0.1; fix Pillow==12.3.0 to valid version; add boto3; add pcidss if required; pin starlette
- backend/requirements-dev.txt — align pytest version with requirements.txt
- frontend/web_app/package.json — move @testing-library/dom to devDependencies; add openapi-fetch if missing
- frontend/web_app/package-lock.json — regenerate after fixes; upgrade next to >=16.3.3 to patch GHSA-p293-qw3h-jr36
- frontend/shared/package.json / package-lock.json — align framer-motion and tailwind-merge versions
- frontend/mobile_app/package.json — add expo-router; remove unused @react-navigation/native, @stripe/stripe-react-native if not imported

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:** None.

**Testing required:**
- pip install -r backend/requirements.txt succeeds in clean virtualenv
- pip install -r backend/requirements-dev.txt succeeds
- npm install in frontend/web_app succeeds with no unresolved peer dependencies
- npm install in frontend/shared succeeds
- npm install in frontend/mobile_app succeeds
- npm audit shows no critical/high vulnerabilities in frontend
- Run backend/tests/architecture/test_manifest_drift.py — all assertions pass
- Verify python -c import valkey succeeds

**Deployment strategy:** Use expand/contract pattern for dependency changes.

**Rollback strategy:** Pin previous manifest files in git; revert to previous commit if installation breaks.

**Risk:** MEDIUM — incorrect version pins could break imports. Mitigated by testing in isolated virtualenv.

**Exit criteria:**
- [ ] pip install -r backend/requirements.txt succeeds with no errors
- [ ] pip install -r backend/requirements-dev.txt succeeds
- [ ] All backend tests pass (pytest backend/tests/)
- [ ] Frontend npm run build succeeds for web_app and shared
- [ ] npm audit shows 0 critical, 0 high vulnerabilities
- [ ] test_manifest_drift.py passes all assertions
- [ ] No redis references remain in requirements.txt (except in comments/docs if unavoidable)

---

### PHASE 3: TEST FOUNDATION
**Objective:** Establish a safety net of automated tests covering the critical bugs and security defects identified in Phases 14/17.

**Prerequisites:** Phase 2 (dependencies must be installable for tests to run).

**Files/components affected:**
- backend/tests/ — add new test files for critical paths
- backend/tests/conftest.py — remove hardcoded fallback passwords; use environment variables with secure random defaults

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:** None.

**Testing required:**
- Add tests for register_rejects_admin_role, social_login_requires_oidc, ws_user_requires_auth, password_reset_token_hashed, order_status_code_attribute, create_address_no_recursion, generic_gateway_no_status, webhook_signature_required
- Run full backend test suite: pytest backend/tests/ -x
- Target: >80% pass rate before proceeding to Phase 4

**Deployment strategy:** No deployment. Tests run in CI only.

**Rollback strategy:** N/A — test additions are additive.

**Risk:** LOW — test failures indicate existing bugs, not new regressions.

**Exit criteria:**
- [ ] All new critical-path tests pass
- [ ] Existing test suite passes (or documented failures are pre-existing and tracked)
- [ ] conftest.py no longer contains hardcoded passwords
- [ ] Test coverage report generated for critical domains (auth, payments, orders)

---

### PHASE 4: SECURITY REMEDIATION
**Objective:** Fix all CRITICAL and HIGH security vulnerabilities that block production deployment.

**Prerequisites:** Phase 3 (test foundation must exist to verify fixes).

**Files/components affected:**
- backend/domains/accounts/schemas/user_schemas.py:20,47 — remove role from public registration schemas; enforce server-side role=customer
- backend/domains/accounts/services/auth/auth_service.py:2404 — hardcode role=customer in register_user()
- backend/domains/accounts/services/auth/auth_service.py:3557-3569 — remove dev-only OIDC bypass; enforce JWKS verification or raise 501
- backend/modules/admin/routers/accounts.py:469-509 — remove endpoint that accepts caller-supplied social claims
- backend/domains/accounts/services/auth/auth_service.py:3118-3143 — hash password reset tokens before storage
- backend/domains/accounts/services/auth/auth_service.py:2516-2539 — hash email verification tokens before storage
- backend/domains/accounts/models/user.py:185-240 — update column types to store hashed tokens
- backend/modules/admin/routers/comms.py:138-156 — add authentication dependency to websocket_user
- backend/main.py:194-196 — ensure only authenticated websocket is registered at /ws/user
- backend/domains/finance/services/payments/payment_orchestrator.py:877-885 — require explicit status or reject callback
- backend/domains/finance/services/payments/gateway_tap.py:981-1003, 1415-1423 — reject webhooks when secret is unconfigured
- backend/providers/payments/paytabs.py — same as above
- backend/middleware/csrf_middleware.py:28-37 — remove CSRF exemption for state-changing auth endpoints or add alternative protection
- backend/main.py:123-126 — reject wildcard CORS in non-development environments
- backend/config.py:31,262-264 — add default SECRET_KEY to rejection list
- backend/infrastructure/utils/auth.py:403-413 — add Secure and SameSite=strict to refresh cookie

**Database changes:**
- Alter password_reset_tokens.token column to store bcrypt-hashed values
- Alter email_verification_tokens.token column to store bcrypt-hashed values
- Migration: ALTER TABLE accounts.password_reset_tokens ALTER COLUMN token TYPE VARCHAR(255);
- Migration: ALTER TABLE accounts.email_verification_tokens ALTER COLUMN token TYPE VARCHAR(255);

**API changes:**
- POST /api/v1/auth/register — role field removed from request schema; server assigns customer
- POST /api/v1/auth/social/login — returns 501 when OIDC not configured; no caller-supplied claims accepted
- POST /api/v1/auth/forgot-password — CSRF protection enforced (exemption removed)
- POST /api/v1/auth/reset-password — CSRF protection enforced
- WS /ws/user — requires valid JWT access token
- POST /payments/{gateway}/webhook — returns 401 when webhook secret is missing
- Generic gateway callback — returns 400 when no explicit status in payload

**Infrastructure changes:** None.

**Testing required:**
- All tests from Phase 3 must pass
- Penetration test: attempt privilege escalation via registration → must fail
- Penetration test: attempt social login without valid JWT → must fail
- Penetration test: connect to /ws/user without token → must be rejected
- Penetration test: send unsigned webhook → must be rejected with 401
- Verify existing password reset flow still works after token hashing change

**Deployment strategy:**
- Blue/green deployment for auth endpoints (highest risk):
  1. Deploy to staging with new auth logic
  2. Run penetration tests against staging
  3. Promote to production via blue/green (instant cutover, instant rollback)
- Use feature flag ENFORCE_SECURE_REGISTRATION=true to toggle new registration behavior
- Use feature flag REQUIRE_WEBHOOK_SIGNATURES=true to toggle webhook verification enforcement

**Rollback strategy:**
- Feature flags allow instant rollback without redeployment
- Blue/green: revert traffic to previous green environment
- Database: hashed token migration is additive; old plaintext tokens become invalid (users must request new reset emails — acceptable UX impact for security gain)

**Risk:** HIGH — auth changes affect every user. Mitigated by blue/green deployment and feature flags.

**Exit criteria:**
- [ ] POST /api/v1/auth/register with role=admin returns 400 or assigns customer
- [ ] Social login returns 501 when OIDC not configured
- [ ] /ws/user rejects unauthenticated connections with 4001/401
- [ ] Webhook endpoints return 401 when secret is unconfigured
- [ ] Generic gateway callback rejects payloads without explicit status
- [ ] Password reset tokens stored as bcrypt hashes in DB
- [ ] Email verification tokens stored as bcrypt hashes in DB
- [ ] CSRF exemptions removed for state-changing auth endpoints (or alternative protection added)
- [ ] CORS rejects * wildcard in non-development
- [ ] Default SECRET_KEY rejected at startup
- [ ] Refresh cookie has Secure and SameSite=strict attributes

---

### PHASE 5: DATABASE STABILIZATION
**Objective:** Fix all database-level integrity issues, ORM attribute mismatches, and race conditions that cause runtime crashes or data corruption.

**Prerequisites:** Phase 4 (security fixes) — database migrations for token hashing must be complete.

**Files/components affected:**
- backend/domains/orders/models/order_entities.py:19,24,30-38 — standardize amount columns
- backend/domains/orders/services/core/order_engine.py:897,1020-1021,1047-1048,1235,1244 — update to order.status_code
- backend/domains/orders/services/orders_service.py:338-339,393,409 — update to order.status_code
- backend/domains/orders/services/tracking/service.py:1041,1044,1075,1092,1148,1157,1205,1225,1227,1258,1271,1309,1314,1345-1346,1426,1431-1432,1517,1519,1524 — update to order.status_code
- backend/domains/orders/services/core/dtos.py:75 — update to orm_order.status_code
- backend/domains/orders/services/core/order_admin.py:58,68,122-123,222,307,339,351,360,375 — update to order.status_code
- backend/domains/orders/services/packing/service.py:103-104,124,171-172 — update to order.status_code
- backend/domains/orders/services/core/logistics.py:105,132,4212,4578,4869,4872 — update to order.status_code
- backend/domains/suppliers/services/orders/supplier_orders_service.py:92,230-231,655-656 — update to order.status_code
- backend/domains/suppliers/services/orders/supplier_orders.py:82-83,129,188,194,232-233,256,376,512,514,569 — update to order.status_code
- backend/domains/finance/services/payouts/payout_batch_service.py:1651 — update to order.status_code
- backend/domains/finance/services/payments/payment_orchestrator.py:595,889,905,1039,1051,1075,1083,1103,1107 — update to order.status_code
- backend/domains/finance/services/payments/gateway_tap.py:299,331,345,383,397,460,478,528,644,669,683,721,739,905,1517,1554,1583,1670,1690,1710,1752,1764,1803 — update to order.status_code
- backend/domains/orders/services/checkout/service.py:80-116 — fix infinite recursion
- backend/domains/finance/services/finance_service.py:372-487 — remove duplicate function definitions
- backend/domains/finance/models/payments.py:39-60 — expand check constraint to include all valid statuses
- backend/domains/suppliers/services/health/supplier_health.py:167-177, 542-602 — add pessimistic locking for stock updates
- backend/domains/orders/models/order_entities.py:22 — make customer_id non-nullable (after data cleanup)

**Database changes:**
- Expand chk_orders_status_valid to include all statuses used in code: prepared, picking_up, in_transit, failed, refunded, returned
- Migration: ALTER TABLE orders DROP CONSTRAINT chk_orders_status_valid; ALTER TABLE orders ADD CONSTRAINT chk_orders_status_valid CHECK (status_code IN (...));
- Add UNIQUE CONSTRAINT on ProcessedWebhookEvent(event_id, processor) to prevent duplicate processing
- Add pessimistic locking (SELECT ... FOR UPDATE) or atomic UPDATE for inventory operations
- Add trigger or application-level check for orders.total consistency with SUM(order_items.total_price)
- Migration: ALTER TABLE orders ALTER COLUMN customer_id SET NOT NULL; (after backfilling nulls)

**API changes:** None directly, but all order-related endpoints will now correctly handle status_code.

**Infrastructure changes:** None.

**Testing required:**
- Run full backend test suite after each file change
- Add integration test for order status transitions with expanded check constraint
- Add integration test for stock update with concurrent requests
- Verify all ~30 service files that previously accessed order.status now use order.status_code without AttributeError
- Verify create_address() no longer raises RecursionError
- Verify finance_service.py functions no longer recurse infinitely

**Deployment strategy:**
- Expand/contract database migration for check constraint expansion
- Strangler pattern for order.status fix — deploy changes in batches by domain:
  - Batch 1: order_engine.py, orders_service.py, dtos.py (core order domain)
  - Batch 2: tracking/service.py, packing/service.py, logistics.py (fulfillment domains)
  - Batch 3: supplier_orders_service.py, supplier_orders.py, payout_batch_service.py (supplier/finance domains)
  - Batch 4: payment_orchestrator.py, gateway_tap.py (payment domain)
- Use feature flag USE_STATUS_CODE=true to toggle between old and new attribute names during transition

**Rollback strategy:**
- Database: revert migration via ALTER TABLE orders DROP CONSTRAINT chk_orders_status_valid; and re-add old constraint
- Application: revert to previous git commit
- If customer_id made non-nullable causes issues, temporarily revert to nullable and backfill data

**Risk:** HIGH — order status is core to the entire system. A mistake breaks checkout, tracking, refunds, and admin operations. Mitigated by batch deployment and comprehensive testing.

**Exit criteria:**
- [ ] No order.status references remain in backend source (all use order.status_code)
- [ ] create_address() completes without RecursionError
- [ ] finance_service.py functions defined exactly once each
- [ ] DB check constraint allows all statuses used in code
- [ ] customer_id is non-nullable on orders table
- [ ] Stock updates use atomic/pessimistic locking
- [ ] orders.total consistent with SUM(order_items.total_price) (via trigger or application logic)
- [ ] All backend tests pass

---

### PHASE 6: ARCHITECTURE REFACTORING
**Objective:** Align the codebase with the stated architecture laws, remove orphaned code, and eliminate naming violations.

**Prerequisites:** Phase 5 (database stabilization) — architecture refactoring should not touch unstable database code.

**Files/components affected:**
- backend/infrastructure/valkey/client.py:115-117 — remove redis_client = valkey_client and get_redis = valkey_client aliases
- backend/infrastructure/valkey/client.py:119-121 — remove _NoOpRedis, _NoOpPipeline aliases
- backend/infrastructure/messaging/realtime.py:43 — rename _create_realtime_redis_client() to _create_realtime_valkey_client()
- All files importing from infrastructure.utils.redis_client import redis_client — update to from infrastructure.valkey.client import valkey_client
- backend/infrastructure/observability/error_handler.py:59 — replace sentry_sdk.integrations.redis import with Valkey-compatible integration or remove if unused
- backend/config.py:74,90-91 — replace redis_url with valkey_url; replace redis://localhost:6379 defaults with valkey://localhost:6379
- backend/domains/logistics/services/core/service.py:2967 — either mount the location service into main.py or remove it if not needed
- backend/providers/voice/ — remove empty directory or implement stub
- backend/infrastructure/uploads/ — remove empty directory or implement stub

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:**
- docker-compose.prod.yml:29,96-104 — replace redis:7-alpine service with valkey:9.0-alpine; update REDIS_URL env vars to VALKEY_URL=valkey://valkey:6379
- docker-compose.prod.yml:71 — fix ML worker command from python -m utils.ml_worker to correct module path
- docker-compose.prod.yml — add celery-beat and celery-flower services if required for production

**Testing required:**
- Run full backend test suite after each rename batch
- Verify no redis identifiers remain in source code (except in comments/docs referencing historical context)
- Verify valkey client connects and functions correctly
- Verify Celery broker connects to Valkey

**Deployment strategy:**
- Strangler pattern for naming migration:
  1. Expand: Add new valkey_ prefixed functions/aliases alongside old redis_ ones
  2. Dual-read: Both old and new paths work simultaneously (using same underlying Valkey client)
  3. Contract: Update all callers to use new names; remove old aliases
  4. Cleanup: Remove old aliases in next deployment
- Use feature flag VALKEY_MIGRATION_COMPLETE=true to verify no old code paths are hit in production
- Infrastructure: update docker-compose.prod.yml in a separate deploy from application code changes

**Rollback strategy:**
- Application: git revert to previous commit
- Infrastructure: revert docker-compose.prod.yml and redeploy
- If Valkey connection fails after Redis removal, temporarily restore Redis service while debugging

**Risk:** MEDIUM — renaming core cache client affects auth, sessions, rate limiting, Celery, and realtime. Mitigated by strangler pattern and dual-run period.

**Exit criteria:**
- [ ] No redis identifiers in Python source, config, or docker-compose (except historical comments)
- [ ] valkey is the sole cache client name throughout the codebase
- [ ] docker-compose.prod.yml uses valkey:9.0-alpine container
- [ ] Location service either mounted in main.py or removed with clear documentation
- [ ] Empty provider directories removed or populated
- [ ] All backend tests pass

---

### PHASE 7: API STABILIZATION / VERSIONING
**Objective:** Ensure all API endpoints are backward-compatible, properly versioned, documented, and tested.

**Prerequisites:** Phase 6 (architecture refactoring) — API routes should be stable before versioning.

**Files/components affected:**
- backend/main.py — verify all routers are mounted under versioned prefixes (/api/v1/)
- backend/infrastructure/utils/versioning.py — review versioning strategy
- frontend/web_app/openapi.json — export from backend /openapi.json and commit to frontend
- frontend/web_app/src/lib/api/openapi.ts — ensure uses exported openapi.json
- All list endpoints — add explicit pagination (limit, offset or cursor-based)
- backend/domains/analytics/services/dashboards/command_center_service.py:290-314 — replace unbounded .all() and .count() with paginated queries

**Database changes:** None.

**API changes:**
- Export backend OpenAPI spec to frontend/web_app/openapi.json (CI step)
- Add ?limit=20&offset=0 pagination to all unbounded list endpoints
- Add rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset) to all responses
- Ensure all breaking changes are deployed under /api/v2/ prefix with /api/v1/ maintained

**Infrastructure changes:**
- Add CI step to regenerate and validate frontend/web_app/openapi.json from backend spec
- Add CI gate that fails if frontend API calls use endpoints not in the spec

**Testing required:**
- Run OpenAPI validator against exported spec
- Verify all paginated endpoints return consistent limit/offset/total structure
- Run Playwright e2e tests against paginated endpoints
- Verify rate limiting headers present on all responses

**Deployment strategy:**
- Backward-compatible API versioning:
  1. Deploy new /api/v2/ endpoints alongside existing /api/v1/
  2. Frontend gradually migrates to v2
  3. Deprecate v1 after v2 is stable (with 6-month deprecation window)
- Feature flags for pagination rollout: ENABLE_PAGINATION=true on new endpoints, then flip to default-on

**Rollback strategy:**
- If v2 endpoints have bugs, route traffic back to v1 via reverse proxy or gateway
- Pagination changes are backward-compatible if limit defaults to a high value when omitted

**Risk:** LOW — versioning and pagination are additive changes.

**Exit criteria:**
- [ ] Backend /openapi.json exported and committed to frontend/web_app/openapi.json
- [ ] All list endpoints support pagination
- [ ] No unbounded .all() queries in analytics services
- [ ] Rate limit headers present on all responses
- [ ] API versioning strategy documented
- [ ] All API tests pass

---

### PHASE 8: INFRASTRUCTURE MODERNIZATION
**Objective:** Align production infrastructure with the target architecture (Valkey-only, SSL termination, monitoring, proper worker wiring).

**Prerequisites:** Phase 7 (API stable) — infrastructure changes should not destabilize APIs.

**Files/components affected:**
- docker-compose.prod.yml — replace Redis with Valkey; add Celery Beat, Flower, monitoring services
- docker-compose.yml (dev) — already uses Valkey, verify consistency
- nginx/nginx.conf — add SSL/TLS termination configuration
- Caddyfile — verify SSL configuration (Caddy auto-HTTPS)
- monitoring/docker-compose.monitoring.yml — deploy to production or integrate with existing stack
- backend/config.py — replace all redis:// defaults with valkey://
- railway.toml — verify environment variables match Valkey configuration
- vercel.json — verify reverse proxy and security headers

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:**
- Replace redis:7-alpine service in docker-compose.prod.yml with valkey:9.0-alpine
- Update all REDIS_URL references to VALKEY_URL in production compose and backend config
- Add celery-beat service for scheduled tasks
- Add celery-flower service for worker monitoring
- Deploy monitoring stack (Prometheus + Grafana + Loki + Tempo) to production
- Configure SSL/TLS termination (Nginx or Caddy with Let us Encrypt)
- Add health check endpoints to all services
- Configure log rotation and retention policies

**Testing required:**
- docker-compose -f docker-compose.prod.yml up succeeds
- Valkey responds to PING from backend
- Celery workers connect to Valkey broker
- Health checks pass (/health/live, /health/deps, /health/ready)
- Monitoring dashboards load and display metrics

**Deployment strategy:**
- Blue/green deployment for infrastructure:
  1. Deploy new infrastructure stack to green environment
  2. Run smoke tests against green
  3. Switch traffic from blue to green
  4. Keep blue running for 24 hours before decommissioning
- Canary deployment for individual service changes: deploy to 1 replica first; monitor for 30 minutes
- Use feature flags to disable background jobs during infrastructure migration: BACKGROUND_JOBS_ENABLED=false

**Rollback strategy:**
- Blue/green: instant traffic switch back to blue environment
- If Valkey fails, temporarily restore Redis service while debugging
- Monitoring stack failure does not affect application — rollback is non-breaking

**Risk:** MEDIUM — infrastructure changes affect all services. Mitigated by blue/green deployment.

**Exit criteria:**
- [ ] docker-compose.prod.yml contains no redis services or references
- [ ] All services connect to Valkey successfully
- [ ] Celery Beat and Flower running in production
- [ ] Monitoring stack deployed and dashboards accessible
- [ ] SSL/TLS termination working on all public endpoints
- [ ] Health checks pass for all services
- [ ] Log rotation configured with 10MB/3-file policy

---

### PHASE 9: OBSERVABILITY
**Objective:** Deploy production-grade observability with alerts, dashboards, and on-call integration.

**Prerequisites:** Phase 8 (infrastructure modernized) — monitoring stack must be deployed before it can be configured.

**Files/components affected:**
- monitoring/grafana/ — deploy dashboards
- monitoring/alertmanager.yml — configure alert routing
- backend/infrastructure/observability/ — verify all instrumentation is active
- backend/infrastructure/observability/error_handler.py — verify Sentry integration
- backend/infrastructure/observability/prometheus_setup.py — verify metrics export

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:**
- Deploy Prometheus + Grafana + Loki + Tempo + Alertmanager stack
- Configure synthetic monitors for critical endpoints
- Set up alert routing to on-call (email, Slack, PagerDuty)
- Configure log retention policies (30 days hot, 1 year cold)
- Add business metrics dashboards (order volume, payment success rate, signups)

**Testing required:**
- Verify all metrics appear in Prometheus
- Verify traces appear in Tempo
- Verify logs appear in Loki
- Trigger test alerts and verify they reach on-call
- Verify Sentry captures errors in staging

**Deployment strategy:**
- Deploy monitoring stack via Docker Compose alongside production stack
- Configure alert rules in staging first; tune thresholds before production
- Use canary deployment for alert rules: enable in staging, then gradually enable in production

**Rollback strategy:**
- Monitoring stack is additive — failure does not affect application
- Disable alert rules if they generate noise; do not rollback application

**Risk:** LOW — monitoring is non-blocking.

**Exit criteria:**
- [ ] Prometheus scraping all backend and infrastructure metrics
- [ ] Grafana dashboards display application, database, and infrastructure metrics
- [ ] Loki ingests application logs
- [ ] Tempo ingests distributed traces
- [ ] Alertmanager routes alerts to on-call channels
- [ ] Synthetic monitors pass for all critical endpoints
- [ ] Log retention policies configured

---

### PHASE 10: PERFORMANCE OPTIMIZATION
**Objective:** Optimize query performance, connection pooling, caching, and background job routing for production scale.

**Prerequisites:** Phase 9 (observability) — need metrics to identify bottlenecks.

**Files/components affected:**
- backend/domains/analytics/services/dashboards/command_center_service.py:290-314 — replace unbounded queries with paginated/materialized views
- backend/domains/suppliers/services/health/supplier_health.py:167-177, 542-602 — add atomic stock updates
- backend/infrastructure/database/database.py — tune connection pool settings
- backend/infrastructure/database/db_read.py — add automatic soft-delete filtering
- Alembic migrations — add materialized views for analytics
- PostgreSQL — add missing indexes identified in audit

**Database changes:**
- Create materialized views for analytics dashboards (mv_daily_orders, mv_supplier_health, etc.)
- Add GIN index on JSONB columns used for filtering
- Add trigram index on product search columns
- Migration: Add atomic stock update via UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?

**API changes:**
- Add caching headers (Cache-Control, ETag) to public catalog endpoints
- Implement cache invalidation on product/price changes

**Infrastructure changes:** None.

**Testing required:**
- Load test with simulated traffic (1000 concurrent users)
- Verify p95 latency < 500ms for API endpoints
- Verify p95 latency < 200ms for catalog endpoints
- Verify database connection pool utilization < 80%
- Verify Valkey hit rate > 90%

**Deployment strategy:**
- Canary deployment for performance changes:
  1. Deploy materialized views and new queries to staging
  2. Run load tests against staging
  3. Deploy to 1 production replica; monitor metrics
  4. Scale to full production if metrics are good
- Use feature flag ENABLE_MATERIALIZED_VIEWS=true to toggle new analytics queries

**Rollback strategy:**
- Revert to previous queries if materialized views cause stale data
- Revert connection pool settings if they cause connection exhaustion
- Feature flags allow instant rollback without redeployment

**Risk:** MEDIUM — materialized views add complexity; stale data risk. Mitigated by refresh schedules and feature flags.

**Exit criteria:**
- [ ] All .all() and unbounded .count() queries replaced with paginated versions
- [ ] Materialized views refresh within acceptable staleness window (5 minutes)
- [ ] Stock updates are atomic; no oversell under concurrent load
- [ ] Database connection pool utilization < 80% under load
- [ ] p95 API latency < 500ms
- [ ] p95 catalog latency < 200ms
- [ ] Valkey cache hit rate > 90%

---

### PHASE 11: PAYMENT HARDENING
**Objective:** Fix all payment-safety gaps to prevent financial loss, fraud, and reconciliation errors.

**Prerequisites:** Phase 4 (security remediation for webhook signatures) — must be complete before payment hardening.

**Files/components affected:**
- backend/domains/finance/services/payments/payment_orchestrator.py:791-921 — add amount verification in handle_generic_gateway_callback and confirm_generic_gateway_payment
- backend/domains/finance/services/payments/gateway_tap.py:201-260 — add server-side refund amount validation
- backend/domains/finance/services/payments/paypal.py:238-293 — add server-side refund amount validation
- backend/domains/finance/services/payments/paytabs.py:207-270 — add server-side refund amount validation
- backend/providers/payments/stripe_sdk.py:27-34 — remove stub success; raise error when SDK unavailable
- backend/domains/finance/services/payments/payment_engine.py:4143-4323 — add DB-level unique constraint on ProcessedWebhookEvent(event_id, processor)
- backend/domains/finance/models/payments.py:84-127 — encrypt secret_key and webhook_secret columns (Stripe, Tap)

**Database changes:**
- Add UNIQUE CONSTRAINT on ProcessedWebhookEvent(event_id, processor)
- Migration: ALTER TABLE finance.processed_webhook_events ADD CONSTRAINT uq_event_processor UNIQUE (event_id, processor);
- Encrypt existing plaintext payment credentials (Stripe, Tap) using existing EncryptionProvider
- Migration: Add encrypted_secret_key column; backfill encrypted values; drop old column

**API changes:**
- Generic gateway callback — validates amount against order.payment_customer_total_amount; returns 400 if mismatch
- Refund endpoints — validate requested amount against remaining refundable balance; return 400 if exceeded
- Stripe refund — raises HTTPException(503) when SDK unavailable instead of returning stub success

**Infrastructure changes:** None.

**Testing required:**
- Test refund amount validation: request refund exceeding order total → 400
- Test generic gateway amount mismatch: callback with wrong amount → 400
- Test webhook idempotency: send same webhook twice → second is rejected
- Test encrypted credentials: verify decryption works after migration

**Deployment strategy:**
- Expand/contract for encrypted credentials:
  1. Expand: Add encrypted_secret_key column; backfill encrypted values from secret_key
  2. Dual-read: Application reads from both columns (prefer encrypted)
  3. Contract: Stop writing to secret_key; drop old column in later migration
- Feature flags:
  - REQUIRE_WEBHOOK_SIGNATURES=true (already enforced in Phase 4)
  - ENABLE_REFUND_VALIDATION=true — toggle refund amount checks
  - ENABLE_GENERIC_GATEWAY_AMOUNT_CHECK=true — toggle amount verification

**Rollback strategy:**
- Feature flags allow instant disable of new validation if it blocks legitimate transactions
- Database: revert unique constraint if it causes webhook replay issues
- Encrypted credential migration: keep old column until new column is verified

**Risk:** HIGH — payment changes directly affect revenue. Mitigated by feature flags, staging validation, and gradual rollout.

**Exit criteria:**
- [ ] Generic gateway callback validates amount against order total
- [ ] Refund endpoints validate against remaining refundable balance
- [ ] Stripe refund raises 503 when SDK unavailable
- [ ] ProcessedWebhookEvent has unique constraint on (event_id, processor)
- [ ] All payment gateway credentials stored encrypted
- [ ] All payment tests pass
- [ ] Payment reconciliation passes in staging

---

### PHASE 12: INCREMENTAL FEATURE MIGRATION
**Objective:** Use feature flags and strangler pattern to migrate remaining legacy code paths and introduce new features without big-bang deployments.

**Prerequisites:** Phase 11 (payment hardened) — financial safety must be established before feature migration.

**Files/components affected:**
- All domains with legacy code paths
- Feature flag configuration (new file or extend existing config)

**Database changes:** None directly — feature flags may trigger new data paths.

**API changes:** New endpoints deployed alongside old ones; old ones deprecated gradually.

**Infrastructure changes:** None.

**Techniques:**
- Feature flags for all new features (percentage rollout, user segment targeting)
- Strangler pattern for legacy endpoint replacement:
  1. New endpoint deployed at /api/v2/orders/{id}
  2. Gateway routes 1% → 5% → 25% → 100% traffic to new endpoint
  3. Old endpoint kept for rollback; removed after 30 days of stability
- Dual-read (only when justified): Read from both old and new data sources during migration; compare results before cutover

**Testing required:**
- Feature flag toggling tested in staging
- Strangler pattern traffic splitting tested
- Dual-read consistency verified

**Deployment strategy:**
- Deploy feature flags in configuration (database or environment variable)
- Use percentage-based rollout for high-risk features
- Monitor error rates and latency during traffic migration

**Rollback strategy:**
- Feature flags allow instant rollback
- Strangler pattern: route 100% traffic back to legacy endpoint
- Dual-read: stop reading from new source, continue with old

**Risk:** LOW-MEDIUM — feature flags provide safety net.

**Exit criteria:**
- [ ] All new features behind feature flags
- [ ] Legacy endpoints replaced via strangler pattern with documented timeline
- [ ] No dual-write patterns in production (dual-read only when justified)
- [ ] Feature flag cleanup scheduled for post-migration

---

### PHASE 13: DATA MIGRATION
**Objective:** Migrate existing production data to match the stabilized schema (hashed tokens, encrypted credentials, standardized columns, non-nullable foreign keys).

**Prerequisites:** Phase 5 (database stabilization), Phase 11 (payment hardening) — target schema must be finalized.

**Files/components affected:**
- Alembic migration scripts
- Backfill scripts (one-time execution)

**Database changes:**
- Migration 1: Hash existing plaintext password reset tokens
  - SQL: UPDATE accounts.password_reset_tokens SET token = crypt(token, gen_salt(bf, 12)) WHERE token IS NOT NULL AND token !~ ^\[aby]\$;
- Migration 2: Hash existing plaintext email verification tokens (same pattern)
- Migration 3: Backfill orders.customer_id where null — infer from user_id or set to guest user
- Migration 4: Consolidate duplicate amount columns — copy subtotal_amount → subtotal, total_amount → total if needed, or vice versa
- Migration 5: Encrypt existing plaintext payment credentials
- Migration 6: Normalize order status values if any invalid values exist

**API changes:** None.

**Infrastructure changes:** None.

**Testing required:**
- Run backfill scripts against staging database copy
- Verify no data loss during migration
- Verify all users can still log in after token hashing
- Verify orders remain accessible after column consolidation

**Deployment strategy:**
- Run data migrations during maintenance window
- Expand/contract: Add new columns/constraints; backfill data; switch application to use new schema; remove old columns
- Blue/green for database schema changes when possible:
  1. Apply migration to green database
  2. Verify green database integrity
  3. Switch application to green database
  4. Keep blue database for 24h rollback window

**Rollback strategy:**
- Database: restore from backup taken before migration
- Application: revert to previous git commit (if schema changes break application)

**Risk:** HIGH — data migrations affect all production data. Mitigated by staging rehearsal, blue/green database, and backup verification.

**Exit criteria:**
- [ ] All password reset tokens hashed in production database
- [ ] All email verification tokens hashed in production database
- [ ] orders.customer_id has no null values
- [ ] Payment credentials encrypted in production database
- [ ] All order amount columns are consistent
- [ ] No invalid order status values in production
- [ ] Migration scripts tested against staging copy with zero data loss

---

### PHASE 14: TRAFFIC MIGRATION
**Objective:** Migrate production traffic to the new hardened infrastructure with zero downtime and instant rollback capability.

**Prerequisites:** Phases 1–13 complete — all blockers, security fixes, database changes, and infrastructure changes must be finalized.

**Files/components affected:**
- Reverse proxy configuration (Nginx/Caddy)
- Load balancer configuration (if using external LB)
- Railway deployment configuration

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:**
- Configure blue/green deployment on Railway
- Configure canary deployment rules (1% → 5% → 25% → 100%)
- Configure health check-based automatic rollback
- Configure database connection failover

**Testing required:**
- Smoke tests pass on green environment
- Health checks pass
- Load test at 100% traffic on green
- Chaos test: kill green backend pod; verify blue takes over

**Deployment strategy:**
- Blue/Green deployment (primary strategy):
  1. Deploy current stable version to Blue
  2. Deploy new hardened version to Green
  3. Run smoke tests on Green
  4. Switch 1% traffic to Green via load balancer
  5. Monitor for 30 minutes
  6. Ramp to 5%, 25%, 50%, 100%
  7. If any metric degrades, instant switch back to Blue
- Canary deployment (for smaller changes):
  1. Deploy to 1 replica
  2. Monitor for 30 minutes
  3. Scale to full replicas if healthy

**Rollback strategy:**
- Blue/green: instant traffic switch (seconds)
- Railway: railway rollback to previous deployment
- Database: restore from backup if schema migration fails
- Feature flags: disable new features without redeployment

**Risk:** MEDIUM — traffic migration is high-visibility. Mitigated by canary rollout and instant rollback.

**Exit criteria:**
- [ ] 100% production traffic running on hardened stack
- [ ] Zero downtime during migration
- [ ] All health checks passing
- [ ] Error rate < 0.1%
- [ ] p95 latency within baseline
- [ ] Rollback tested and verified < 60 seconds

---

### PHASE 15: PRODUCTION VALIDATION
**Objective:** Validate the migrated production system against all quality gates defined in the target architecture.

**Prerequisites:** Phase 14 (traffic migrated) — system must be on hardened stack before validation.

**Files/components affected:**
- All production systems
- Validation scripts and reports

**Database changes:** None.

**API changes:** None.

**Infrastructure changes:** None.

**Testing required:**
- Full Playwright e2e test suite against production
- Load test: 10,000 concurrent users for 1 hour
- Security penetration test (OWASP Top 10)
- Database failover test
- Valkey cluster failover test
- Backup restore drill (RTO < 1 hour, RPO < 15 minutes)
- Disaster recovery runthrough
- Chaos engineering: kill random backend pod, kill database primary, kill Valkey node

**Deployment strategy:**
- Validation runs in production during low-traffic window
- Use shadow traffic for load testing (duplicate production traffic to test environment)
- No new deployments during validation phase

**Rollback strategy:**
- If validation reveals critical issues, use blue/green rollback to previous stable version
- If database issues, restore from backup

**Risk:** MEDIUM — validation reveals unknown issues. Mitigated by comprehensive pre-production testing.

**Exit criteria:**
- [ ] All e2e tests pass against production
- [ ] Load test passes: 10K concurrent users, p95 < 500ms
- [ ] Security penetration test: 0 critical, 0 high findings
- [ ] Database failover completes in < 30 seconds
- [ ] Backup restore completes in < 1 hour
- [ ] Valkey cluster tolerates single node failure
- [ ] All observability dashboards populated with production data
- [ ] On-call rotation tested with real alert

---

### PHASE 16: LEGACY REMOVAL
**Objective:** Remove deprecated code, columns, endpoints, and infrastructure components after the migration is validated.

**Prerequisites:** Phase 15 (production validated) — legacy removal must only happen after new system is proven stable.

**Files/components affected:**
- Deprecated API endpoints under /api/v1/ (after v2 is stable for 6 months)
- Deprecated database columns (subtotal, total, shipping_fee, status if hybrid property added)
- Deprecated infrastructure (old Redis scripts, old Docker Compose files)
- Unused dependencies removed in Phase 2 but still in lockfiles
- Empty directories confirmed empty and removed

**Database changes:**
- Drop deprecated columns after confirmed unused
- Drop old indexes that are superseded by new ones
- Vacuum and analyze tables after column removal

**API changes:**
- Remove deprecated v1 endpoints after deprecation window
- Remove legacy websocket routes

**Infrastructure changes:**
- Remove old Docker Compose files (keep as docker-compose.yml.bak for 30 days)
- Remove old monitoring configurations
- Clean up CI workflows for deprecated environments

**Testing required:**
- Verify no code references deprecated columns or endpoints
- Run full test suite after each removal
- Verify production logs show no access to deprecated endpoints

**Deployment strategy:**
- Gradual removal: Remove one endpoint/column per deployment
- Monitoring: Watch for 404 errors on removed endpoints; if significant traffic, extend deprecation
- Feature flags: Keep deprecated endpoints behind ENABLE_LEGACY_ENDPOINTS=false flag for 30 days before code removal

**Rollback strategy:**
- Deprecated endpoints/columns can be restored from git history
- Database columns can be re-added via migration if needed

**Risk:** LOW — legacy removal happens only after stable operation.

**Exit criteria:**
- [ ] No deprecated API endpoints serving production traffic
- [ ] No deprecated database columns in schema
- [ ] No redis references in production code or configuration
- [ ] No empty placeholder directories
- [ ] No unused dependencies in manifests
- [ ] All tests pass with legacy code removed

---

## 4. MIGRATION DEPENDENCY GRAPH

`
Phase 1: Repository Cleanup ──────────────────────┐
     │                                             │
     ▼                                             │
Phase 2: Dependency Stabilization ────────────────┤
     │                                             │
     ▼                                             │
Phase 3: Test Foundation ─────────────────────────┤
     │                                             │
     ▼                                             │
Phase 4: Security Remediation ────────────────────┤
     │                                             │
     ▼                                             │
Phase 5: Database Stabilization ──────────────────┤
     │                                             │
     ▼                                             │
Phase 6: Architecture Refactoring ────────────────┤
     │                                             │
     ▼                                             │
Phase 7: API Stabilization/Versioning ────────────┤
     │                                             │
     ▼                                             │
Phase 8: Infrastructure Modernization ────────────┤
     │                                             │
     ▼                                             │
Phase 9: Observability ───────────────────────────┘
     │
     ▼
Phase 10: Performance Optimization ───────────────┐
     │                                              │
     ▼                                              │
Phase 11: Payment Hardening ──────────────────────┤
     │                                              │
     ▼                                              │
Phase 12: Incremental Feature Migration ──────────┤
     │                                              │
     ▼                                              │
Phase 13: Data Migration ─────────────────────────┤
     │                                              │
     ▼                                              │
Phase 14: Traffic Migration ──────────────────────┤
     │                                              │
     ▼                                              │
Phase 15: Production Validation ──────────────────┘
     │
     ▼
Phase 16: Legacy Removal
`

### Dependency Rules

| Phase | Must Complete Before | Rationale |
|-------|---------------------|-----------|
| 1 | All others | Repository cleanliness reduces confusion during migration |
| 2 | 3, 4, 5, 6, 7 | Broken dependencies block tests, security fixes, and refactoring |
| 3 | 4, 5, 6, 7 | Test foundation required to verify critical fixes |
| 4 | 5, 6, 7 | Security fixes must precede production deployment |
| 5 | 6, 7, 10, 11, 13 | Database schema must stabilize before data migration and performance work |
| 6 | 7, 8 | Architecture alignment must precede infrastructure and API work |
| 7 | 9, 10, 11, 12, 13, 14 | Stable API required before traffic migration |
| 8 | 9 | Infrastructure must be modernized before observability can be deployed |
| 9 | 10, 11, 12, 13, 14 | Observability required to validate performance and payment changes |
| 10 | 12, 13, 14 | Performance baseline established before feature migration |
| 11 | 12, 13, 14 | Payment safety required before production traffic |
| 12 | 13, 14 | Features must be stable before traffic migration |
| 13 | 14 | Data must be migrated before traffic cutover |
| 14 | 15 | Traffic must be on hardened stack before validation |
| 15 | 16 | System must be validated before legacy removal |

---

## 5. CRITICAL PATH

The critical path determines the minimum time to complete the migration. Delays on the critical path delay the entire project.

### Critical Path Steps

`
Phase 2: Dependency Stabilization
    ↓
Phase 4: Security Remediation
    ↓
Phase 5: Database Stabilization
    ↓
Phase 8: Infrastructure Modernization
    ↓
Phase 13: Data Migration
    ↓
Phase 14: Traffic Migration
    ↓
Phase 15: Production Validation
`

**Estimated critical path duration:** 6–10 weeks

| Step | Estimated Duration | Key Deliverable |
|------|-------------------|-----------------|
| Phase 2 | 3–5 days | pip install succeeds; all tests pass |
| Phase 4 | 5–7 days | All CRITICAL/HIGH security fixes deployed |
| Phase 5 | 7–14 days | Order status attribute fixed; DB integrity restored |
| Phase 8 | 3–5 days | Valkey-only production; SSL; monitoring deployed |
| Phase 13 | 2–3 days | Data backfilled and validated |
| Phase 14 | 1–2 days | Traffic fully migrated |
| Phase 15 | 2–3 days | Validation complete |
| **Total** | **~6–10 weeks** | **Production-ready hardened system** |

### Non-Critical Path (Can Run in Parallel)

| Phase | Runs In Parallel With | Rationale |
|-------|----------------------|-----------|
| Phase 1 | Phase 2 | Repository cleanup is independent |
| Phase 3 | Phase 2 | Tests can be written while dependencies are being fixed |
| Phase 6 | Phase 5 | Architecture refactoring can begin on stable domains while database fixes are in progress |
| Phase 7 | Phase 6 | API work can begin on stable endpoints |
| Phase 9 | Phase 8 | Observability configuration can proceed in parallel with infrastructure deployment |
| Phase 10 | Phase 9 | Performance optimization uses observability data |
| Phase 11 | Phase 10 | Payment hardening can proceed alongside performance work |
| Phase 12 | Phase 11 | Feature migration can begin once core is stable |
| Phase 16 | Phase 15 | Legacy removal planning can begin during validation |

---

## 6. RISK MATRIX

| Risk | Likelihood | Impact | Mitigation | Phase |
|------|-----------|--------|-----------|-------|
| Dependency fix breaks imports | Medium | High | Test in isolated virtualenv; pin exact versions | Phase 2 |
| Security fix blocks legitimate users | Medium | High | Blue/green deployment; feature flags | Phase 4 |
| Order status refactor misses a file | High | Critical | Automated grep + architecture test; batch deployment | Phase 5 |
| Database migration fails on large table | Medium | High | Rehearse on staging copy; blue/green DB | Phase 13 |
| Valkey connection fails after Redis removal | Medium | High | Strangler pattern; dual-run period | Phase 6 |
| Payment validation blocks legitimate refunds | Medium | Critical | Feature flags; canary rollout; staging validation | Phase 11 |
| Traffic migration causes downtime | Low | Critical | Blue/green; canary; instant rollback | Phase 14 |
| Load test reveals performance bottleneck | Medium | High | Pre-production load testing; capacity planning | Phase 15 |
| Backup restore fails | Low | Critical | Regular restore drills; RTO/RPO testing | Phase 15 |

---

## 7. EVIDENCE CITATIONS

All major claims in this roadmap are backed by verified source code evidence from the audit phases:

| Claim | Evidence File | Line | Symbol |
|-------|--------------|------|--------|
| Registration accepts client role | auth_service.py | 2404 | register_user |
| Role default in schema | user_schemas.py | 20, 47 | UserCreate.role, RegisterRequest.role |
| Public router no auth | modules/customer/routers/accounts.py | 317-329 | router |
| OIDC dev bypass | auth_service.py | 3557-3569 | verify_social_identity |
| redis in requirements | requirements.txt | 20 | redis==8.0.1 |
| valkey imported | infrastructure/valkey/client.py | 81 | import valkey |
| Pillow non-existent | requirements.txt | 51 | Pillow==12.3.0 |
| Next.js RCE | frontend/web_app/package-lock.json | — | next@16.1.6 |
| Generic gateway missing status = success | payment_orchestrator.py | 877-885 | handle_generic_gateway_callback |
| Webhook signature skippable | gateway_tap.py | 981-1003, 1415-1423 | handle_tap_webhook, handle_thawani_webhook |
| /ws/user unauthenticated | main.py | 194-196 | websocket_user |
| order.status vs status_code | order_entities.py | 24 | status_code column |
| Infinite recursion create_address | checkout/service.py | 96 | create_address |
| Duplicate functions finance_service | finance_service.py | 372-487 | get_global_config, etc. |
| Production uses Redis | docker-compose.prod.yml | 96-104 | redis:7-alpine |
| ML worker path mismatch | docker-compose.prod.yml | 71 | python -m utils.ml_worker |
| orders.customer_id nullable | order_entities.py | 22 | customer_id |
| Plaintext reset tokens | auth_service.py | 3118-3143 | forgot_password |
| Plaintext email tokens | auth_service.py | 2516-2539 | verify_email |
| CORS wildcard fallback | main.py | 123-126 | CORS middleware |

---

## 8. SUMMARY

The ZOZI Marketplace migration from **CURRENT VERIFIED SYSTEM** to **TARGET ARCHITECTURE** is achievable through 16 incremental phases over 8–16 weeks. The critical path runs through Dependency Stabilization → Security Remediation → Database Stabilization → Infrastructure Modernization → Data Migration → Traffic Migration → Production Validation.

The system does **not** require a rewrite. The domain model, database schema, and overall architecture are sound. The blockers are discrete, fixable defects concentrated in auth, payments, dependencies, and database integrity. Each phase has clear exit criteria, rollback conditions, and evidence-based claims.

**Recommended immediate next action:** Begin Phase 2 (Dependency Stabilization) and Phase 3 (Test Foundation) in parallel, followed by Phase 4 (Security Remediation) as the highest-priority production blocker.

---

*End of PHASE_20_MIGRATION_ROADMAP.md. No files were modified during this audit.*
