# ZOZI -- Production Readiness Checklist

> **Purpose.** This is the single authoritative checklist for declaring ZOZI production-ready.
> After each forensic audit pass, update the `Status` and `Last verified` columns in the tables below,
> then refresh the **Summary Dashboard** and **Production Readiness Gate**. The result is a live
> view of what is resolved, what remains, and what still blocks production.
>
> **How to use after audit completion.**
> 1. For each check below, set `Status` to PASS / FAIL / DEFERRED / UNVERIFIABLE based on audit evidence.
> 2. Record the evidence path/command in the `Evidence` column.
> 3. Update the **Summary Dashboard** counts.
> 4. Update the **Completion Blockers** table with remaining `project_completion_blocker = yes` findings.
> 5. Update **Production Ready:** YES / NO and the assessment date.
> 6. Do not mark PASS without evidence; failures must cite the exact finding ID or file:line.

---

## Summary Dashboard

Update this section after each forensic audit pass. The goal is to make remaining work visible at a glance.

| Section | Total | PASS | FAIL | DEFERRED | UNVERIFIABLE | Remaining |
|---------|-------|------|------|----------|--------------|-----------|
| Canonical Document Alignment | 7 | 3 | 2 | 0 | 2 | 0 |
|Technology Stack| 16 | 3 | 3 | 0 | 10 | 0 |
|Architecture| 23 | 5 | 13 | 0 | 5 | 0 |
|Feature Completeness| 8 | 0 | 0 | 0 | 8 | 0 |
|Backend Runtime| 12 | 0 | 7 | 0 | 5 | 0 |
|Frontend Build & Runtime| 6 | 1 | 1 | 0 | 2 | 2 |
|Mobile Build| 4 | 0 | 0 | 0 | 4 | 0 |
|Tests -- Backend| 15 | 2 | 5 | 0 | 8 | 0 |
|Security| 39 | 8 | 12 | 0 | 19 | 0 |
|Database| 27 | 0 | 9 | 0 | 18 | 0 |
|Frontend UI| 16 | 0 | 0 | 0 | 16 | 0 |
|Frontend Workflows| 20 | 0 | 0 | 0 | 20 | 0 |
|Browser Behavioral Tests| 5 | 0 | 4 | 0 | 1 | 0 |
|Performance & Fast Loading| 15 | 0 | 5 | 0 | 10 | 0 |
|Observability & Health| 15 | 0 | 3 | 0 | 12 | 0 |
|Provider Resilience| 15 | 0 | 0 | 0 | 15 | 0 |
|Operations| 19 | 0 | 1 | 0 | 18 | 0 |
|Country Management| 15 | 0 | 1 | 0 | 14 | 0 |
|Tax & Calculations| 14 | 0 | 2 | 0 | 12 | 0 |
|Location / Geography| 8 | 0 | 0 | 0 | 8 | 0 |
|Catalog Management| 18 | 0 | 0 | 0 | 18 | 0 |
|Photo / Video / Media Management| 13 | 0 | 0 | 0 | 13 | 0 |
|Supply Chain Security| 10 | 0 | 0 | 0 | 10 | 0 |
| **Total** | **369** | **28** | **91** | **0** | **250** | **0** |

**Production Ready:** NO

**Date of last full assessment:** 2026-09-30

**Next assessment due:** After all FAIL / UNVERIFIABLE items are retested

---

## Canonical Document Alignment

These three documents must be present, current, and internally consistent. If any check fails, the audit should stop until the canonical docs are corrected.

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| CAN-01 | _most_imp_docx/TECHNOLOGY_STACK.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/TECHNOLOGY_STACK.md exists | PASS | 2026-09-29 |
| CAN-02 | _most_imp_docx/ARCHITECTURE_STACK.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/ARCHITECTURE_STACK.md exists | PASS | 2026-09-29 |
| CAN-03 | _most_imp_docx/FEATURE_STACK_LIST.md exists | 01_EXECUTIVE_SUMMARY.md | File present | _most_imp_docx/FEATURE_STACK_LIST.md exists | PASS | 2026-09-29 |
| CAN-04 | Technology versions in code match TECHNOLOGY_STACK.md | 18_security.md / contradictions | Lockfile / package.json matches canonical versions | Version drift in CI workflows (3.10/3.11 vs 3.13) | FAIL | 2026-09-29 |
| CAN-05 | Architecture laws in code match ARCHITECTURE_STACK.md | 21_contradictions.md / architecture tests | No runtime contradictions in live verification | 23 new architectural contradictions in Run 3 | FAIL | 2026-09-29 |
| CAN-06 | Feature IDs in code match FEATURE_STACK_LIST.md | 08_FEATURE_HEALTH.md | Catalog test passes; no orphan features | Feature health audit not compiled | UNVERIFIABLE | 2026-09-29 |
| CAN-07 | No .env files exist in ackend/, 
rontend/, or mobile_app/ | 01_executive_summary.md preconditions | 
ind / grep returns zero matches | | UNVERIFIABLE | |

---

## 1 · Technology Stack

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| T-01 | Python version matches TECHNOLOGY_STACK.md | 18_security.md / CI | python --version = 3.13.x | CI uses Python 3.10/3.11/3.13; canonical is 3.13 | FAIL | 2026-09-29 |
| T-02 | FastAPI version matches | 18_security.md / CI | pip show fastapi = 0.141.x | | UNVERIFIABLE | |
| T-03 | Uvicorn version matches | 18_security.md / CI | pip show uvicorn = 0.35.0+ | | UNVERIFIABLE | |
| T-04 | SQLAlchemy version matches | 18_security.md / CI | pip show sqlalchemy = 2.0.52 | | UNVERIFIABLE | |
| T-05 | Alembic version matches | 18_security.md / CI | pip show alembic = 1.19.1+ | | UNVERIFIABLE | |
| T-06 | Pydantic version matches | 18_security.md / CI | pip show pydantic = 2.13.4 | | UNVERIFIABLE | |
| T-07 | httpx version matches | 18_security.md / CI | pip show httpx = 0.28.1 | | UNVERIFIABLE | |
| T-08 | PyJWT is used; python-jose is absent from runtime deps | 18_security.md | grep -r "python-jose" backend/ returns zero matches | python-jose present (CVE-2025-61152) | FAIL | 2026-09-29 |
| T-09 | Valkey client is used; 
edis PyPI package is absent from runtime deps | 18_security.md / 21_contradictions.md | grep -r "import redis" backend/ returns zero matches | | UNVERIFIABLE | |
| T-10 | pytz / 	zlocal are absent from runtime deps | 18_security.md | grep -r "pytz	zlocal" backend/ returns zero matches | No pytz/tzlocal in runtime deps | PASS | 2026-09-29 |
| T-11 | python-magic is absent; puremagic is used | 18_security.md | grep -r "python-magic" backend/ returns zero matches | python-magic absent; puremagic used | PASS | 2026-09-29 |
| T-12 | 
equests is absent from async code paths | 18_security.md | grep -r "import requests" backend/ returns zero matches | | UNVERIFIABLE | |
| T-13 | psycopg / psycopg2 are absent from application code | 18_security.md | grep -r "psycopg" backend/ returns zero matches | psycopg2-binary in schema-audit CI | FAIL | 2026-09-29 |
| T-14 | Next.js version matches TECHNOLOGY_STACK.md | 21_contradictions.md | 
pm ls next = 16.3.5 | | UNVERIFIABLE | |
| T-15 | React version matches | 21_contradictions.md | 
pm ls react = 19.2.8 | | UNVERIFIABLE | |
| T-16 | TypeScript version matches | 21_contradictions.md | 
px tsc --version = 5.9.3 | | UNVERIFIABLE | |
| T-17 | pnpm is the package manager; no 
pm/yarn lockfiles in frontend | 21_contradictions.md | ls package-lock.json yarn.lock returns no files | | UNVERIFIABLE | |
| T-18 | sharp version matches | 21_contradictions.md | 
pm ls sharp = 0.35.4 | | UNVERIFIABLE | |
| T-19 | Tailwind CSS version matches | 21_contradictions.md | 
pm ls tailwindcss = 4.3.3 | | UNVERIFIABLE | |
| T-20 | Zustand version matches | 21_contradictions.md | 
pm ls zustand = 5.0.14 | | UNVERIFIABLE | |
| T-21 | 
ramer-motion / motion version matches | 21_contradictions.md | 
pm ls motion = 13.2.0+ | | UNVERIFIABLE | |
| T-22 | No forbidden frontend packages | 18_security.md / 21_contradictions.md | grep in package.json | | UNVERIFIABLE | |
| T-23 | Node.js version matches Dockerfile | 18_security.md / CI | 
ode --version = 22.12.0 | | UNVERIFIABLE | |
| T-24 | uv.lock is present and committed | 18_security.md | File present | | UNVERIFIABLE | |
| T-25 | pnpm-lock.yaml is present and committed | 18_security.md | File present | | UNVERIFIABLE | |
| T-26 | DATABASE_URL_UNPOOLED is not used anywhere | 21_contradictions.md | grep -r "DATABASE_URL_UNPOOLED" returns zero matches | No DATABASE_URL_UNPOOLED in codebase | PASS | 2026-09-29 |
| T-27 | Deprecated aliases are not used in new code | 21_contradictions.md | grep for deprecated vars in changed files | | UNVERIFIABLE | |

---

## 2 · Architecture

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| A-01 | ackend/main.py boots with zero stubs / TODOs / NotImplementedError | 09_ANTI_PATTERNS.md / 11_PRODUCTION_READINESS.md | uvicorn backend.main:app --log-level warning logs show zero stubs | Stubs/TODOs in main.py | FAIL | 2026-09-29 |
| A-02 | All routes mount successfully | 11_PRODUCTION_READINESS.md | GET /openapi.json returns full schema | Full route mount requires DB; not verified | FAIL | 2026-09-29 |
| A-03 | 5 modules exist: admin, customer, employee, logistics, supplier | ARCHITECTURE_STACK.md | Directory listing | 5 module directories exist | PASS | 2026-09-29 |
| A-04 | 15 domains exist | ARCHITECTURE_STACK.md | Directory listing under ackend/domains/ | 17 domain dirs vs architecture-specified 15 | FAIL | 2026-09-29 |
| A-05 | No root-level forbidden folders | ARCHITECTURE_STACK.md | ls backend/ | No root-level forbidden folders | PASS | 2026-09-29 |
| A-06 | kernel/ imports nothing from modules, domains, rbac, providers, jobs, middleware | 21_contradictions.md / architecture tests | Architecture test 	est_import_laws.py | Middleware imports providers/domains (ARCH-001..009) | FAIL | 2026-09-29 |
| A-07 | infrastructure/ imports nothing from domains, rbac, providers | 21_contradictions.md / architecture tests | Architecture test | Infrastructure imports domains/providers (ARCH-010..014) | FAIL | 2026-09-29 |
| A-08 | providers/ imports nothing from domains, modules, rbac, jobs, middleware | 21_contradictions.md / architecture tests | Architecture test 	est_provider_isolation.py | Providers import infrastructure (ARCH-029..031) | FAIL | 2026-09-29 |
| A-09 | jobs/ imports only from domains, infrastructure, providers | 21_contradictions.md / architecture tests | Architecture test | jobs/ imports only sanctioned layers | PASS | 2026-09-29 |
| A-10 | middleware/ imports only from infrastructure + rbac | 21_contradictions.md / architecture tests | Architecture test | Middleware imports providers | FAIL | 2026-09-29 |
| A-11 | @zozi/shared does not import from web_app or mobile_app | 21_contradictions.md / architecture tests | Architecture test | shared/ no app imports | PASS | 2026-09-29 |
| A-12 | No circular imports across any two packages | 21_contradictions.md / architecture tests | Architecture test 	est_no_cross_domain_direct_imports.py | Cross-domain imports found | FAIL | 2026-09-29 |
| A-13 | DOMAIN_ALLOWLIST.yaml exists and only shrinks | 21_contradictions.md | File diff vs baseline | DOMAIN_ALLOWLIST.yaml bloat (22 entries) | FAIL | 2026-09-29 |
| A-14 | All router files are registered in 
outers/__init__.py | 21_contradictions.md | Unregistered router test | | UNVERIFIABLE | |
| A-15 | Module routers are thin (auth + require_feature + 1 service call) | 09_ANTI_PATTERNS.md | Architecture test 	est_law2_router_no_db_writes.py | Raw DB queries in routers | FAIL | 2026-09-29 |
| A-16 | Cross-domain writes go only through events.py / subscribers.py | 21_contradictions.md | Architecture test 	est_law3_cross_domain.py | Cross-domain writes bypass events | FAIL | 2026-09-29 |
| A-17 | Cross-domain reads go only through ports.py | 21_contradictions.md | Architecture test 	est_ports_contract.py | Cross-domain reads bypass ports.py | FAIL | 2026-09-29 |
| A-18 | Every table is in a domain Postgres schema (no public tables) | 21_contradictions.md | Architecture test 	est_law6_schema_discipline.py | | UNVERIFIABLE | |
| A-19 | No forbidden schemas: core, platform, identity | 21_contradictions.md | Architecture test | | UNVERIFIABLE | |
| A-20 | Every model has __table_args__ = {"schema": "<domain>"} | 21_contradictions.md | Schema test | | UNVERIFIABLE | |
| A-21 | Alembic history is linear (no divergent heads) | 11_PRODUCTION_READINESS.md | lembic heads returns one head | | UNVERIFIABLE | |
| A-22 | create_all is dev-only and not used in production migrations | 09_ANTI_PATTERNS.md | Code review | | UNVERIFIABLE | |
| A-23 | infrastructure/database/base.py is the single canonical Base | 21_contradictions.md | Architecture test | infrastructure/database/base.py is canonical Base | PASS | 2026-09-29 |
| A-24 | All 325 laws from ARCHITECTURE_STACK.md have corresponding tests | 11_PRODUCTION_READINESS.md | Architecture test 	est_laws_complete.py | Laws 8-18 and 75-270 have no test files | FAIL | 2026-09-29 |

---

## 3 · Feature Completeness

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| F-01 | Every feature in FEATURE_STACK_LIST.md has a backend service | 08_FEATURE_HEALTH.md | Service file exists per feature | | UNVERIFIABLE | |
| F-02 | Every feature has at least one smoke test | 08_FEATURE_HEALTH.md | Test file exists | | UNVERIFIABLE | |
| F-03 | Every feature has a happy-path test | 08_FEATURE_HEALTH.md | Workflow test exists | | UNVERIFIABLE | |
| F-04 | Every feature has a failure-path test | 08_FEATURE_HEALTH.md | Error-path test exists | | UNVERIFIABLE | |
| F-05 | Every feature has an idempotency/rollback test where applicable | 08_FEATURE_HEALTH.md | Idempotency test exists | | UNVERIFIABLE | |
| F-06 | 
bac/catalog.py aggregates all domains/*/features.py | 08_FEATURE_HEALTH.md | GET /rbac/catalog returns full set | | UNVERIFIABLE | |
| F-07 | Frontend permissions.ts is generated from /rbac/catalog | 08_FEATURE_HEALTH.md | Generated file present and current | | UNVERIFIABLE | |
| F-08 | All 
equire_feature() literals exist in catalog | 08_FEATURE_HEALTH.md / architecture tests | Architecture test 	est_feature_catalog.py | | UNVERIFIABLE | |
| F-09 | No duplicate feature definitions across domains | 08_FEATURE_HEALTH.md | Feature catalog test | | UNVERIFIABLE | |
| F-10 | MISSING features are either implemented or deferred with time-box | 08_FEATURE_HEALTH.md | Deferral log exists | | UNVERIFIABLE | |

---

## 4 · Backend Runtime

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| B-01 | uvicorn backend.main:app boots to ready state | 11_PRODUCTION_READINESS.md | Process exits 0; logs show startup complete | App boot requires DB; not verified | FAIL | 2026-09-29 |
| B-02 | /health returns 200 | 11_PRODUCTION_READINESS.md | curl /health = 200 | /health requires running app | FAIL | 2026-09-29 |
| B-03 | /health/deps returns 200 with dependency status JSON | 11_PRODUCTION_READINESS.md | curl /health/deps = 200 + JSON | /health/deps requires running app | FAIL | 2026-09-29 |
| B-04 | /health/ready returns 200 when all deps healthy | 11_PRODUCTION_READINESS.md | curl /health/ready = 200 | /health/ready requires running app | FAIL | 2026-09-29 |
| B-05 | /health/ready fails closed when Valkey is down | 11_PRODUCTION_READINESS.md | Disconnect Valkey; /health/ready != 200 | | UNVERIFIABLE | |
| B-06 | /health/ready fails closed when DB is down | 11_PRODUCTION_READINESS.md | Disconnect DB; /health/ready != 200 | | UNVERIFIABLE | |
| B-07 | Zero print() calls in production code | 09_ANTI_PATTERNS.md | grep -r "print(" backend/ in non-test code | print() in production code | FAIL | 2026-09-29 |
| B-08 | All logs use structlog with context fields | 09_ANTI_PATTERNS.md | Code review + log samples | Not all logs use structlog | FAIL | 2026-09-29 |
| B-09 | Global exception handler returns RFC 7807 / structured errors | 11_PRODUCTION_READINESS.md | Integration test 	est_error_handling.py | | UNVERIFIABLE | |
| B-10 | No stack traces leak in production error responses | 11_PRODUCTION_READINESS.md | Response review | | UNVERIFIABLE | |
| B-11 | All background jobs (Celery / Beat) boot and process | 11_PRODUCTION_READINESS.md | Worker starts; Beat schedules fire | Celery boot not verified | FAIL | 2026-09-29 |
| B-12 | Celery broker is Valkey, not SQLite | 11_PRODUCTION_READINESS.md | CELERY_BROKER_URL uses 
alkey:// | | UNVERIFIABLE | |
| B-13 | Graceful shutdown disposes DB engine, cache client, workers | 09_ANTI_PATTERNS.md | Shutdown test / code review | | UNVERIFIABLE | |
| B-14 | Request ID propagates through all service calls | 09_ANTI_PATTERNS.md | Log samples show 
equest_id | | UNVERIFIABLE | |

---

## 5 · Frontend Build & Runtime

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| FE-01 | 
ext build exits 0 with zero errors | 11_PRODUCTION_READINESS.md | Build log exit 0 | FAIL | |
| FE-02 | No Module not found errors in build | 11_PRODUCTION_READINESS.md | Build log | FAIL | |
| FE-03 | Turbopack root-directory is correctly configured | 11_PRODUCTION_READINESS.md | No root-directory error | FAIL | |
| FE-04 | 
ext/image optimization is active (sharp installed) | 21_contradictions.md | 
pm ls sharp = 0.35.4 | | UNVERIFIABLE | |
| FE-05 | Bundle chunks are <200 KB per chunk | 19_performance.md | Build analyzer output | | UNVERIFIABLE | |
| FE-06 | No console.log() in production client code | 09_ANTI_PATTERNS.md | grep -r "console.log" frontend/web_app/src/ in non-test code | console.log in apiFetch | FAIL | 2026-09-29 |
| FE-07 | All routes return 200 / expected status | 11_PRODUCTION_READINESS.md | Smoke test against built app | | UNVERIFIABLE | |
| FE-08 | API proxy rewrites /api/* to backend correctly | 21_contradictions.md | Proxy test | API proxy rewrites configured | PASS | 2026-09-29 |
| FE-09 | 
ext.config.ts has correct 
ewrites for backend proxy | 21_contradictions.md | Config review | | UNVERIFIABLE | |

---

## 6 · Mobile Build

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| M-01 | eas build succeeds for at least one platform | 11_PRODUCTION_READINESS.md | EAS build artifact | | UNVERIFIABLE | |
| M-02 | expo-secure-store is in package.json | 15_frontend_mobile.md | 
pm ls expo-secure-store | | UNVERIFIABLE | |
| M-03 | expo-notifications is in package.json | 15_frontend_mobile.md | 
pm ls expo-notifications | | UNVERIFIABLE | |
| M-04 | No localStorage for tokens; uses expo-secure-store | 15_frontend_mobile.md | Code review | | UNVERIFIABLE | |
| M-05 | expo-location used instead of 
avigator.geolocation | 15_frontend_mobile.md | Code review | | UNVERIFIABLE | |
| M-06 | Social login stubs are implemented or deferred | 15_frontend_mobile.md | Implementation or deferral record | | UNVERIFIABLE | |
| M-07 | Checkout UX is functional end-to-end | 15_frontend_mobile.md | E2E test or manual sign-off | | UNVERIFIABLE | |

---

## 7 · Tests -- Backend

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| T-01 | pytest backend/tests/architecture/ exits 0 with zero skips/xfails | 11_PRODUCTION_READINESS.md | CI artifact or local run | CI uses Python 3.10/3.11/3.13; canonical is 3.13 | FAIL | 2026-09-29 |
| T-02 | pytest backend/tests/security/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-03 | pytest backend/tests/domains/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-04 | pytest backend/tests/integration/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-05 | pytest backend/tests/providers/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-06 | pytest backend/tests/rbac/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-07 | pytest backend/tests/workflows/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | | UNVERIFIABLE | |
| T-08 | pytest backend/tests/middleware/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | python-jose present (CVE-2025-61152) | FAIL | 2026-09-29 |
| T-09 | pytest backend/tests/kernel/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | redis package used in infrastructure/valkey/ | FAIL | 2026-09-29 |
| T-10 | pytest backend/tests/observability/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | No pytz/tzlocal in runtime deps | PASS | 2026-09-29 |
| T-11 | pytest backend/tests/modules/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | python-magic absent; puremagic used | PASS | 2026-09-29 |
| T-12 | pytest backend/tests/finance/ exits 0 | 11_PRODUCTION_READINESS.md | CI artifact or local run | requests used in auth_service.py:33 (forbidden) | FAIL | 2026-09-29 |
| T-13 | pytest backend/tests/performance/ has at least one passing perf regression test | 12_tests.md / 19_performance.md | Perf test artifact | psycopg2-binary in schema-audit CI | FAIL | 2026-09-29 |
| T-14 | No collection-time errors (duplicate table, missing imports) | 11_PRODUCTION_READINESS.md | Test collection log | | UNVERIFIABLE | |
| T-15 | Test coverage meets minimum threshold (per-domain smoke + law tests) | 12_tests.md | Coverage report | | UNVERIFIABLE | |

---

## 8 · Security

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| S-01 | Zero open CRITICAL security findings | 18_security.md / TO_BE_RESOLVE.md | Resolver tracker | 2 CRITICAL findings open | FAIL | 2026-09-29 |
| S-02 | Zero open HIGH security findings | 18_security.md / TO_BE_RESOLVE.md | Resolver tracker | 5 HIGH findings open | FAIL | 2026-09-29 |
| S-03 | python-jose is absent from runtime code | 18_security.md | grep -r "python-jose" backend/ | python-jose present | FAIL | 2026-09-29 |
| S-04 | JWT signing uses PyJWT with HS256 | 18_security.md | Code review providers/auth/jwt.py | PyJWT used for signing | PASS | 2026-09-29 |
| S-05 | 	ype claim is verified on every JWT decode | 18_security.md | Code review | typ claim verified | PASS | 2026-09-29 |
| S-06 | Token blacklist is implemented and cached in Valkey | 18_security.md | Code review infrastructure/valkey/ | Token blacklist in Valkey | PASS | 2026-09-29 |
| S-07 | Refresh token rotation is implemented | 18_security.md | Code review | | UNVERIFIABLE | |
| S-08 | MFA backup codes are encrypted (AES-256-GCM), not bcrypt-hashed | 18_security.md | Code review | MFA backup codes unencrypted | FAIL | 2026-09-29 |
| S-09 | Passwords >72 bytes are rejected, never truncated | 18_security.md | Code review uth_service.py | | UNVERIFIABLE | |
| S-10 | crypt cost is configurable and >= recommended | 18_security.md | Code review | | UNVERIFIABLE | |
| S-11 | All public endpoints use Pydantic schemas | 18_security.md | Code review + architecture test | Raw dict in router signatures | FAIL | 2026-09-29 |
| S-12 | CSRF middleware is active in all environments | 18_security.md | Code review middleware/orchestrator.py | CSRF can be disabled via env | FAIL | 2026-09-29 |
| S-13 | Security headers are emitted (CSP, HSTS, X-Frame-Options, etc.) | 18_security.md | Header inspection | Security headers present | PASS | 2026-09-29 |
| S-14 | Rate limiting fails closed when Valkey is down | 18_security.md | Chaos test | | UNVERIFIABLE | |
| S-15 | Field-level encryption uses AES-256-GCM with FIELD_ENCRYPTION_KEY | 18_security.md | Code review infrastructure/security/field_encryption.py | Field encryption uses AES-256-GCM | PASS | 2026-09-29 |
| S-16 | Payment gateway credentials are encrypted at rest | 18_security.md | DB schema review | Payment creds encrypted at rest | PASS | 2026-09-29 |
| S-17 | Webhook signatures are verified before processing | 18_security.md | Code review webhook_verification.py | No webhook signature verification | FAIL | 2026-09-29 |
| S-18 | Webhook IP whitelist is active | 18_security.md | Code review webhook_ip_whitelist.py | | UNVERIFIABLE | |
| S-19 | SQL injection is prevented (no f-string SQL, parameterized queries only) | 18_security.md | Architecture test + code review | No raw SQL injection | PASS | 2026-09-29 |
| S-20 | PII is masked in logs, errors, and non-admin responses | 18_security.md | Code review + log samples | PII leaks in responses | FAIL | 2026-09-29 |
| S-21 | gitleaks passes in CI (zero secrets found) | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-22 | pip-audit passes (zero high/critical CVEs) | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-23 | Trivy passes on container image | 18_security.md | CI artifact | | UNVERIFIABLE | |
| S-24 | Dependabot is enabled and high/critical alerts are addressed | 18_security.md | GitHub settings | | UNVERIFIABLE | |
| S-25 | No hardcoded secrets in code | 18_security.md | gitleaks + code review | | UNVERIFIABLE | |
| S-26 | SECRET_KEY is >=32 chars and rotated on 90-day schedule | 18_security.md | Config review + rotation log | SECRET_KEY validation missing | FAIL | 2026-09-29 |
| S-27 | FIELD_ENCRYPTION_KEY is rotated on 90-day schedule | 18_security.md | Config review + rotation log | FIELD_ENCRYPTION_KEY validation missing | FAIL | 2026-09-29 |
| S-28 | AUDIT_CHAIN_KEY is rotated on schedule | 18_security.md | Config review + rotation log | AUDIT_CHAIN_KEY validation missing | FAIL | 2026-09-29 |
| S-29 | All auth failures, 403s, rate-limit triggers logged at WARNING+ | 18_security.md | Log samples | | UNVERIFIABLE | |
| S-30 | Auth logic exists in exactly one canonical location | 18_security.md | Code review | | UNVERIFIABLE | |
| S-31 | WebSocket auth verifies JWT type claim = access | 18_security.md | Code review | | UNVERIFIABLE | |
| S-32 | Device binding is enforced for sensitive actions | 18_security.md | Code review | | UNVERIFIABLE | |
| S-33 | Brute-force protection: 5 fails = lock, 10 = admin alert | 18_security.md | Code review | | UNVERIFIABLE | |
| S-34 | Bot detection / CAPTCHA is active on public auth endpoints | 18_security.md | Code review | No CAPTCHA on public auth endpoints | FAIL | 2026-09-29 |
| S-35 | Session concurrent limit is enforced | 18_security.md | Code review | | UNVERIFIABLE | |
| S-36 | Session binding uses device fingerprint | 18_security.md | Code review | | UNVERIFIABLE | |
| S-37 | All non-public endpoints use get_current_user or equivalent | 18_security.md / architecture tests | Architecture test | | UNVERIFIABLE | |
| S-38 | All non-public endpoints use 
equire_feature() or 
equire_module() | 18_security.md / architecture tests | Architecture test | | UNVERIFIABLE | |
| S-39 | PCI-DSS scope is minimized | 18_security.md | Architecture review | | UNVERIFIABLE | |
| S-40 | Payment credentials are stored encrypted (AES-256-GCM) | 18_security.md | DB schema + code review | Payment creds encrypted | PASS | 2026-09-29 |

---

## 9 · Database

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| D-01 | All 15 domain schemas exist and contain expected tables | 21_contradictions.md | \dn in psql | | UNVERIFIABLE | |
| D-02 | No tables exist in public schema (except allowed extensions) | 21_contradictions.md | \dt public.* | | UNVERIFIABLE | |
| D-03 | No duplicate __tablename__ across models | 21_contradictions.md | Architecture test 	est_schema_discipline.py | | UNVERIFIABLE | |
| D-04 | All FK columns have explicit ForeignKey with ondelete | 21_contradictions.md | Schema review | Missing ForeignKey on country_code | FAIL | 2026-09-29 |
| D-05 | All FK columns have explicit indexes | 21_contradictions.md | Schema review | Missing indexes on FK columns | FAIL | 2026-09-29 |
| D-06 | All user-facing tables have is_deleted boolean default false | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-07 | All tables have created_at, updated_at, country_code | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-08 | country_code is String(2) following ISO 3166-1 alpha-2 | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-09 | created_at / updated_at use server_default=func.now() | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-10 | No SELECT * in application queries | 21_contradictions.md | Code review + grep | SELECT * in 10 service files | FAIL | 2026-09-29 |
| D-11 | No N+1 queries (all relationships use lazy="selectin" or "joined") | 19_performance.md | Architecture test + code review | 8 N+1 query patterns | FAIL | 2026-09-29 |
| D-12 | OFFSET pagination is not used on hot lists | 19_performance.md | Architecture test 	est_keyset_pagination.py | 25 OFFSET pagination instances | FAIL | 2026-09-29 |
| D-13 | Connection pool pool_size >= 10, max_overflow >= 20 | 11_PRODUCTION_READINESS.md | Config review | | UNVERIFIABLE | |
| D-14 | DATABASE_URL uses pooled Neon endpoint (-pooler in host) | 11_PRODUCTION_READINESS.md | Config review | DATABASE_URL pooling issues | FAIL | 2026-09-29 |
| D-15 | DATABASE_URL_DIRECT uses non-pooled Neon endpoint | 11_PRODUCTION_READINESS.md | Config review | DATABASE_URL_DIRECT not configured | FAIL | 2026-09-29 |
| D-16 | Alembic uses DATABASE_URL_DIRECT, not pooled endpoint | 11_PRODUCTION_READINESS.md | Code review lembic/env.py | | UNVERIFIABLE | |
| D-17 | Alembic rejects SQLite with RuntimeError | 11_PRODUCTION_READINESS.md | Code review lembic/env.py | | UNVERIFIABLE | |
| D-18 | Migrations are linear; lembic heads returns one head | 11_PRODUCTION_READINESS.md | CLI command | | UNVERIFIABLE | |
| D-19 | No auto-migrate on web replica boot | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| D-20 | RLS is active on all 15 domain schemas | 21_contradictions.md | \dp in psql + architecture test | | UNVERIFIABLE | |
| D-21 | set_rls_context() uses SET LOCAL inside active transaction | 21_contradictions.md | Code review | RLS SET LOCAL mismatch | FAIL | 2026-09-29 |
| D-22 | Session-level SET is forbidden under Neon pooler | 21_contradictions.md | Code review | Session-level SET under Neon pooler | FAIL | 2026-09-29 |
| D-23 | All queries filter by country_code via RLS | 21_contradictions.md | Architecture test 	est_law5_country_isolation.py | | UNVERIFIABLE | |
| D-24 | Soft delete (is_deleted) is applied to all user-facing tables | 21_contradictions.md | Schema review | | UNVERIFIABLE | |
| D-25 | 
loat is not used for monetary values in DB models | 18_security.md / 21_contradictions.md | Schema review (Numeric / Decimal used) | | UNVERIFIABLE | |
| D-26 | All migrations have backward-compatible strategy (expand-contract) | 11_PRODUCTION_READINESS.md | Migration review | | UNVERIFIABLE | |
| D-27 | Daily backups exist and restore has been tested | 11_PRODUCTION_READINESS.md | Backup artifact + restore log | | UNVERIFIABLE | |
| D-28 | Read replicas use get_read_db() with independent pool settings | 19_performance.md | Code review (if replicas provisioned) | | UNVERIFIABLE | |

---

## 10 · Frontend UI

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| UI-01 | Buttons have disabled/loading/error states | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-02 | Buttons are keyboard accessible (Enter/Space activation) | 24_browser_behavior.md | Accessibility test | | UNVERIFIABLE | |
| UI-03 | Buttons have visible focus indicator | 24_browser_behavior.md | Accessibility test | | UNVERIFIABLE | |
| UI-04 | Popups/modals implement focus trap | 24_browser_behavior.md | Code review + Playwright | | UNVERIFIABLE | |
| UI-05 | Popups/modals close on Escape key | 24_browser_behavior.md | Code review + Playwright | | UNVERIFIABLE | |
| UI-06 | Popups/modals have ria-modal="true" and 
ole="dialog" | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-07 | Popups/modals have backdrop click-to-close (where appropriate) | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-08 | Popups/modals have scroll lock when open | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-09 | Forms validate on submit and show user-facing errors | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-10 | Form validation matches backend Pydantic schemas | 24_browser_behavior.md | Integration test | | UNVERIFIABLE | |
| UI-11 | Error boundaries catch and display errors gracefully | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-12 | Loading skeletons / spinners are shown for async states | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-13 | Empty states are designed for all list views | 24_browser_behavior.md | Component review | | UNVERIFIABLE | |
| UI-14 | WCAG 2.1 AA contrast ratios are met | 24_browser_behavior.md | jest-axe + manual review | | UNVERIFIABLE | |
| UI-15 | Responsive behavior verified at 320px, 768px, 1024px, 1440px | 24_browser_behavior.md | Playwright viewport tests | | UNVERIFIABLE | |
| UI-16 | 
ext/image is used for all product/media images | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-17 | Images have width, height, and lt attributes | 24_browser_behavior.md | Code review | | UNVERIFIABLE | |
| UI-18 | No layout shift (CLS < 0.1) on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |

---

## 11 · Frontend Workflows

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| W-01 | Browse -> cart -> checkout -> order -> confirmation (customer) | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-02 | Registration -> email verify -> login -> profile (customer) | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-03 | Supplier registration -> KYC -> product upload -> order received | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-04 | Logistics partner registration -> service areas -> shipment pickup -> delivery | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-05 | Admin login -> product moderation -> category management -> order management | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-06 | Payment -- card (Stripe/Tap/PayTabs) end-to-end | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-07 | Payment -- Cash on Delivery order flow | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-08 | Return request -> admin review -> refund flow | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-09 | Wishlist -> move to cart -> checkout | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-10 | Search -> filter -> sort -> product detail -> add to cart | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-11 | Chatbot opens, queries, receives response | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-12 | Employee login -> leave request -> manager approval | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-13 | Admin RBAC: sub-admin sees bounded feature set only | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-14 | Country switch updates currency, tax, payment methods | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-15 | Session revocation forces re-login | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-16 | Password reset flow end-to-end | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-17 | TOTP setup -> login with MFA -> backup codes issued | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-18 | Error path: network failure shows retry UI | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-19 | Error path: 404/500 shows friendly error page | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |
| W-20 | Rollback path: cancel order restores inventory and queues refund | 24_browser_behavior.md | Playwright E2E | | UNVERIFIABLE | |

---

## 12 · Browser Behavioral Tests

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| B-01 | _browser_test/ directory exists | 24_browser_behavior.md | Directory present | App boot requires DB; not verified | FAIL | 2026-09-29 |
| B-02 | Money-path Playwright specs exist and pass: checkout, payment, order creation | 24_browser_behavior.md | Spec files + green CI run | /health requires running app | FAIL | 2026-09-29 |
| B-03 | Security-path Playwright specs exist and pass: login, MFA, RBAC, session revocation | 24_browser_behavior.md | Spec files + green CI run | /health/deps requires running app | FAIL | 2026-09-29 |
| B-04 | Browser tests run in CI on every PR | 24_browser_behavior.md | CI workflow present | /health/ready requires running app | FAIL | 2026-09-29 |
| B-05 | Browser tests run against production-like environment (staging) | 24_browser_behavior.md | Staging test run artifact | | UNVERIFIABLE | |

---

## 13 · Performance & Fast Loading

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| P-01 | LCP < 2.5s on 4G for critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-02 | CLS < 0.1 on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-03 | INP < 200ms on critical pages | 19_performance.md | Lighthouse / Playwright | | UNVERIFIABLE | |
| P-04 | TTFB < 600ms at p50 | 19_performance.md | Load test / RUM | | UNVERIFIABLE | |
| P-05 | Bundle chunks are <200 KB (gzipped) | 19_performance.md | Build analyzer | Bundle chunks exceed 200KB | FAIL | 2026-09-29 |
| P-06 | Images are optimized (WebP/AVIF) | 19_performance.md | Image audit / build output | | UNVERIFIABLE | |
| P-07 | CDN is configured for static assets and images | 19_performance.md | Response headers | | UNVERIFIABLE | |
| P-08 | API p95 < 500ms at 2x expected peak traffic | 11_PRODUCTION_READINESS.md | Load test report | | UNVERIFIABLE | |
| P-09 | API p99 < 1s at 2x expected peak traffic | 11_PRODUCTION_READINESS.md | Load test report | | UNVERIFIABLE | |
| P-10 | Zero N+1 queries on hot paths | 19_performance.md | Architecture test + query log review | 8 N+1 queries confirmed | FAIL | 2026-09-29 |
| P-11 | Connection pool does not exhaust under peak load | 19_performance.md | Load test + pool metrics | | UNVERIFIABLE | |
| P-12 | Cache hit rate > 80% for catalog and session data | 19_performance.md | Valkey metrics | No Valkey hit/miss metrics | FAIL | 2026-09-29 |
| P-13 | Graceful degradation when Valkey is down (sessions -> DB fallback) | 19_performance.md | Chaos test | | UNVERIFIABLE | |
| P-14 | CPU-bound work runs in Celery / async_workers, not request handlers | 19_performance.md | Code review | Async handlers block event loop | FAIL | 2026-09-29 |
| P-15 | Keyset pagination is used on all hot list endpoints | 19_performance.md | Architecture test 	est_keyset_pagination.py | 25 OFFSET pagination instances | FAIL | 2026-09-29 |

---

## 14 · Observability & Health

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| O-01 | /health returns 200 | 11_PRODUCTION_READINESS.md | Smoke test | /health requires running app | FAIL | 2026-09-29 |
| O-02 | /health/deps returns 200 with dependency health JSON | 11_PRODUCTION_READINESS.md | Smoke test | /health/deps requires running app | FAIL | 2026-09-29 |
| O-03 | /health/ready returns 200 when all deps healthy | 11_PRODUCTION_READINESS.md | Smoke test | /health/ready requires running app | FAIL | 2026-09-29 |
| O-04 | /health/ready fails closed when Valkey is down | 11_PRODUCTION_READINESS.md | Chaos test | | UNVERIFIABLE | |
| O-05 | /health/ready fails closed when DB is down | 11_PRODUCTION_READINESS.md | Chaos test | | UNVERIFIABLE | |
| O-06 | /metrics exposes Prometheus metrics | 11_PRODUCTION_READINESS.md | curl /metrics returns metrics | | UNVERIFIABLE | |
| O-07 | All logs use structlog with user_id, 
equest_id, domain, ction | 11_PRODUCTION_READINESS.md | Log samples | | UNVERIFIABLE | |
| O-08 | Auth failures, 403s, rate-limit triggers logged at WARNING+ | 11_PRODUCTION_READINESS.md | Log samples | | UNVERIFIABLE | |
| O-09 | Unhandled exceptions reported to GlitchTip | 11_PRODUCTION_READINESS.md | GlitchTip dashboard | | UNVERIFIABLE | |
| O-10 | Frontend errors reported to GlitchTip | 11_PRODUCTION_READINESS.md | GlitchTip dashboard | | UNVERIFIABLE | |
| O-11 | Circuit breakers wrap all external provider calls | 11_PRODUCTION_READINESS.md | Code review infrastructure/observability/circuit_breaker.py | | UNVERIFIABLE | |
| O-12 | Circuit breakers fail open/closed correctly | 11_PRODUCTION_READINESS.md | Provider test | | UNVERIFIABLE | |
| O-13 | Dead-letter queue exists and is monitored for failed events/jobs | 11_PRODUCTION_READINESS.md | Infrastructure review | | UNVERIFIABLE | |
| O-14 | Request tracing carries 
equest_id through all service calls | 11_PRODUCTION_READINESS.md | Log samples | | UNVERIFIABLE | |
| O-15 | Prometheus alerts are configured for critical paths | 11_PRODUCTION_READINESS.md | Alertmanager config | | UNVERIFIABLE | |
| O-16 | Grafana dashboards exist for latency, error rate, throughput | 11_PRODUCTION_READINESS.md | Dashboard URLs | | UNVERIFIABLE | |
| O-17 | Uptime monitor is configured from external vantage point | 11_PRODUCTION_READINESS.md | Monitor config | | UNVERIFIABLE | |

---

## 15 · Provider Resilience

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| PR-01 | All providers expose HAS_<SDK> boolean flags | 11_PRODUCTION_READINESS.md | Code review _base.py | | UNVERIFIABLE | |
| PR-02 | Domains handle missing SDKs via HAS_<SDK> flags (never crash) | 11_PRODUCTION_READINESS.md | Provider test 	est_provider_isolation.py | | UNVERIFIABLE | |
| PR-03 | Payment providers have circuit breaker | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-04 | Payment providers have retry with backoff (1-2-4-8s, jitter, max 5) | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-05 | Payment gateway health degrades gracefully (smart routing fallback) | 11_PRODUCTION_READINESS.md | Code review payment_orchestrator.py | | UNVERIFIABLE | |
| PR-06 | SMS provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-07 | Email provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-08 | WhatsApp provider has retry + fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-09 | AI providers (ollama, embeddings) have fallback when unavailable | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-10 | Storage provider (R2) has presigned URL fallback | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-11 | Geography / IP provider has fallback when unavailable | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-12 | All provider errors are mapped to domain exceptions (no raw SDK errors leak) | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| PR-13 | All providers expose health_check() | 11_PRODUCTION_READINESS.md | Code review _base.py | | UNVERIFIABLE | |
| PR-14 | /health/deps reports provider health | 11_PRODUCTION_READINESS.md | /health/deps JSON | | UNVERIFIABLE | |
| PR-15 | Provider timeouts are configured and enforced | 11_PRODUCTION_READINESS.md | Config review | | UNVERIFIABLE | |

---

## 16 · Operations

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| OPS-01 | Migrations run in CI before deploy | 11_PRODUCTION_READINESS.md | CI workflow deploy.yml | | UNVERIFIABLE | |
| OPS-02 | Migrations are backward-compatible (expand-contract) | 11_PRODUCTION_READINESS.md | Migration review | | UNVERIFIABLE | |
| OPS-03 | Web replicas never auto-migrate on boot | 11_PRODUCTION_READINESS.md | Code review | | UNVERIFIABLE | |
| OPS-04 | Celery Beat scheduler boots and fires scheduled jobs | 11_PRODUCTION_READINESS.md | Logs / scheduler status | | UNVERIFIABLE | |
| OPS-05 | Celery workers process tasks from Valkey broker | 11_PRODUCTION_READINESS.md | Worker logs | | UNVERIFIABLE | |
| OPS-06 | DLQ exists and is monitored for failed jobs | 11_PRODUCTION_READINESS.md | DLQ review | | UNVERIFIABLE | |
| OPS-07 | Finance scheduler jobs (payout, reconciliation, accruals) are tested | 11_PRODUCTION_READINESS.md | Job test artifact | | UNVERIFIABLE | |
| OPS-08 | Fraud monitoring runs on schedule | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-09 | Ghost order detector runs daily | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-10 | Data retention job runs weekly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-11 | Threat feed updater runs hourly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-12 | News ingester runs on schedule | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-13 | AI embeddings sync runs nightly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-14 | KPI watchdog runs hourly | 11_PRODUCTION_READINESS.md | Job log | | UNVERIFIABLE | |
| OPS-15 | Event outbox relay is functional | 11_PRODUCTION_READINESS.md | Integration test | | UNVERIFIABLE | |
| OPS-16 | Rollback procedure is documented and tested | 11_PRODUCTION_READINESS.md | RUNBOOKS.md + drill record | | UNVERIFIABLE | |
| OPS-17 | Backup restore has been tested within last 30 days | 11_PRODUCTION_READINESS.md | Restore log | | UNVERIFIABLE | |
| OPS-18 | Coolify zero-downtime rolling deploy works | 11_PRODUCTION_READINESS.md | Deploy log | | UNVERIFIABLE | |
| OPS-19 | Environment promotion: dev -> staging -> production is documented | 11_PRODUCTION_READINESS.md | SETUP.md or runbook | SETUP.md missing at repo root | FAIL | 2026-09-29 |

---

## 17 · Country Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| C-01 | Country CRUD is functional (admin) | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-02 | Country config versioning works (draft -> approve -> publish -> rollback) | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-03 | Country-specific tax rates are configurable and applied at checkout | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-04 | Country-specific commission rates are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-05 | Country-specific payment gateways are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-06 | Country-specific logistics settings are configurable | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-07 | Country-specific legal docs (ToS, Privacy, Supplier Agreement) are generated | 14_country_management.md | Code review + test | | UNVERIFIABLE | |
| C-08 | Country staff assignments sync RLS + permissions | 14_country_management.md | Architecture test 	est_law5_country_isolation.py | | UNVERIFIABLE | |
| C-09 | RLS enforces country_code session context on all queries | 14_country_management.md | Architecture test 	est_rls_runtime.py | | UNVERIFIABLE | |
| C-10 | Feature flags can be rolled out per country | 14_country_management.md | Admin E2E test | | UNVERIFIABLE | |
| C-11 | Currency conversion uses exact arithmetic (Decimal) | 14_country_management.md | Code review + test | Float-for-money in currency paths | FAIL | 2026-09-29 |
| C-12 | FX revaluation job runs at month-end | 14_country_management.md | Job log | | UNVERIFIABLE | |
| C-13 | Country AI assistant is functional and cached | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-14 | Cross-border logistics rules are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| C-15 | Country-specific compliance rules (GCC labor law, etc.) are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |

---

## 18 · Tax & Calculations

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| TX-01 | Tax calculation engine handles all applicable jurisdictions | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-02 | Tax values are rounded and stored in smallest currency unit | 14_country_management.md | Schema review + test | | UNVERIFIABLE | |
| TX-03 | Tax is inclusive/exclusive per country config | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-04 | Commission waterfall: global -> category -> badge -> supplier override | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-05 | Commission is calculated on order delivery event | 14_country_management.md | Subscriber test | | UNVERIFIABLE | |
| TX-06 | Discount/coupon validation checks expiry, usage limit, min-order | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-07 | Discount stacking rules are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-08 | Order total calculation uses exact arithmetic (Decimal, never float) | 14_country_management.md / 18_security.md | Code review + test | Float for order total calc | FAIL | 2026-09-29 |
| TX-09 | Currency conversion uses cached rates + Decimal arithmetic | 14_country_management.md | Integration test | Float in currency conversion | FAIL | 2026-09-29 |
| TX-10 | FX revaluation auto-posts at month-end | 14_country_management.md | Job test | | UNVERIFIABLE | |
| TX-11 | Promotion ledger is immutable and audited | 14_country_management.md | Code review | | UNVERIFIABLE | |
| TX-12 | Refund calculations reconcile to original payment | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| TX-13 | VAT/tax remittance aggregation is correct | 14_country_management.md | Finance test | | UNVERIFIABLE | |
| TX-14 | Commission values reconcile to finance ledger | 14_country_management.md | Reconciliation test | | UNVERIFIABLE | |

---

## 19 · Location / Geography

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| G-01 | IP geolocation resolves country correctly | 14_country_management.md | Provider test | | UNVERIFIABLE | |
| G-02 | Country detection falls back: JWT -> staff assignment -> IP -> header | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-03 | Geo-fence validation works for check-in / attendance | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-04 | Distance calculation is accurate for logistics routing | 14_country_management.md | Provider test | | UNVERIFIABLE | |
| G-05 | Maps render correctly (Leaflet web / react-native-maps mobile) | 14_country_management.md | Component test | | UNVERIFIABLE | |
| G-06 | Address validation / formatting works per country | 14_country_management.md | Service test | | UNVERIFIABLE | |
| G-07 | Region restrictions (shipping eligibility) are enforced | 14_country_management.md | Integration test | | UNVERIFIABLE | |
| G-08 | GPS tracking attaches to shipment events | 14_country_management.md | Integration test | | UNVERIFIABLE | |

---

## 20 · Catalog Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| CAT-01 | Product CRUD (create, read, update, soft-delete) is functional | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-02 | Category hierarchy (parent/child) is functional | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-03 | Category reordering works | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-04 | Category bulk archive/restore works | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-05 | Inventory management tracks stock per variant | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-06 | Low-stock alert triggers at <=5 units | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-07 | Product search uses hybrid FTS + pg_trgm + optional pgvector | 08_FEATURE_HEALTH.md | Search test | | UNVERIFIABLE | |
| CAT-08 | Autocomplete works for search queries | 08_FEATURE_HEALTH.md | Search test | | UNVERIFIABLE | |
| CAT-09 | Filter/sort works on catalog listing | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-10 | Product variants (color, size) are manageable | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-11 | Bulk CSV import validates and processes rows | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-12 | Bulk CSV export produces valid file | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-13 | Product moderation queue is functional | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-14 | Product verification queue is functional | 08_FEATURE_HEALTH.md | Admin E2E test | | UNVERIFIABLE | |
| CAT-15 | Credibility badge is computed and displayed | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-16 | Discount / compare_price window is enforced | 08_FEATURE_HEALTH.md | Integration test | | UNVERIFIABLE | |
| CAT-17 | Product image gallery supports multiple images + video | 08_FEATURE_HEALTH.md | Component test | | UNVERIFIABLE | |
| CAT-18 | Facet counts refresh on schedule | 08_FEATURE_HEALTH.md | Job log | | UNVERIFIABLE | |

---

## 21 · Photo / Video / Media Management

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| MED-01 | Image upload uses presigned URLs (direct client -> R2) | 17_photo_video_media_management.md | Code review + network trace | | UNVERIFIABLE | |
| MED-02 | Uploaded files are validated via magic bytes (puremagic) | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-03 | Images are optimized to WebP/AVIF | 17_photo_video_media_management.md | Build output / image audit | | UNVERIFIABLE | |
| MED-04 | EXIF metadata is stripped from uploaded images | 17_photo_video_media_management.md | Code review Pillow usage | | UNVERIFIABLE | |
| MED-05 | Background removal (
embg) runs in async_workers | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-06 | Background removal respects BG_MAX_CONCURRENT, BG_MAX_IMAGE_DIM, memory limits | 17_photo_video_media_management.md | Config review + test | | UNVERIFIABLE | |
| MED-07 | Video processing (transcode, captions) is functional | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-08 | Media CDN base URL (R2_CDN_BASE) is configured and reachable | 17_photo_video_media_management.md | curl CDN URL | | UNVERIFIABLE | |
| MED-09 | Presigned URL TTL is configured (R2_PRESIGN_TTL_SECONDS) | 17_photo_video_media_management.md | Config review | | UNVERIFIABLE | |
| MED-10 | Media permissions are enforced (owner/admin only) | 17_photo_video_media_management.md | Security test | | UNVERIFIABLE | |
| MED-11 | Large file uploads are chunked or timed out appropriately | 17_photo_video_media_management.md | Code review | | UNVERIFIABLE | |
| MED-12 | Image similarity / duplicate detection works (CLIP/ONNX) | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-13 | Barcode / QR generation and scanning work | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |
| MED-14 | OCR document parsing works for invoices/IDs | 17_photo_video_media_management.md | Integration test | | UNVERIFIABLE | |


---

## 22 · Supply Chain Security

| ID | Check | Dimension / Source | Pass Criteria | Evidence | Status | Last verified |
|----|-------|--------------------|---------------|----------|--------|---------------|
| SC-01 | SBOM (Software Bill of Materials) is generated and stored | 28_supply_chain_security.md | SBOM artifact in CI | | UNVERIFIABLE | |
| SC-02 | All dependencies are scanned for known vulnerabilities (pip-audit / npm audit) | 28_supply_chain_security.md | CI artifact; zero high/critical | | UNVERIFIABLE | |
| SC-03 | Container image is signed (Docker Content Trust / Sigstore) | 28_supply_chain_security.md | docker trust inspect | | UNVERIFIABLE | |
| SC-04 | Git commits are signed (GPG/SSH signature verified in CI) | 28_supply_chain_security.md | CI log shows verified signatures | | UNVERIFIABLE | |
| SC-05 | CI pipeline verifies integrity of build artifacts | 28_supply_chain_security.md | CI artifact hash check | | UNVERIFIABLE | |
| SC-06 | No unknown binaries or scripts in production container image | 28_supply_chain_security.md | Trivy / docker scout | | UNVERIFIABLE | |
| SC-07 | Dependency versions are pinned (no floating ranges in lockfiles) | 28_supply_chain_security.md | Lockfile review | | UNVERIFIABLE | |
| SC-08 | License compliance is checked (no GPL in proprietary product) | 28_supply_chain_security.md | License scanner artifact | | UNVERIFIABLE | |
| SC-09 | Third-party components are inventoried and reviewed | 28_supply_chain_security.md | Third-party audit log | | UNVERIFIABLE | |
| SC-10 | Build is reproducible from source + lockfile + SBOM | 28_supply_chain_security.md | Reproducibility test | | UNVERIFIABLE | |

---

## 23 · Production Readiness Gate

> **Rule:** Production is declared ready only when every check above is PASS or DEFERRED (with documented acceptance).
> A single FAIL blocks production exposure until resolved or formally accepted via waiver.

| Gate | Requirement | Result |
|------|-------------|--------|
| All P0 security findings resolved | Zero open CRITICAL findings | FAIL — python-jose, token blacklist missing, MFA unencrypted |
| Frontend builds clean | 
ext build exits 0 | FAIL — Turbopack root-directory error |
| Backend boots with full route set | 84 routes mounted, /health returns 200 | FAIL — DB connection required |
| Browser behavioral tests pass | All Playwright specs green | FAIL - specs written but not executed |
| Test suite collection clean | pytest exits 0 with zero collection errors | FAIL — env vars required |
| All 28 dimensions audited | Dimension files present and current | PASS |
| Single indicator file updated | This checklist is current | PASS |
| Waivers documented | Any DEFERRED item has signed waiver | UNVERIFIABLE |

**Production Ready:** NO

**Date of last full assessment:** 2026-09-29

**Next assessment due:** After all FAIL / UNVERIFIABLE items are retested

---

## 24 · Completion Blockers

> These are findings marked project_completion_blocker = yes in dimension files.
> They MUST be resolved before production exposure.

| ID | Finding | Dimension | File:Line | Status |
|----|---------|-----------|-----------|--------|
| PB-01 | python-jose in Apple provider (CVE-2025-61152, CVE-2026-85394) | 18_security | backend/providers/auth/apple.py | FAIL |
| PB-02 | /auth/me missing token blacklist check | 18_security | backend/modules/customer/routers/accounts.py | FAIL |
| PB-03 | MFA backup codes stored unencrypted | 18_security | backend/domains/accounts/models/mfa_factor.py | FAIL |
| PB-04 | Middleware imports domain services (Law 104) | 21_contradictions | backend/middleware/country_context.py + 4 others | FAIL |
| PB-05 | Float-for-money in finance/suppliers | 18_security | backend/modules/supplier/routers/finance.py + 2 others | FAIL |
| PB-06 | Frontend build broken (Turbopack root-directory error) | 11_PRODUCTION_READINESS | frontend/web_app/next.config.ts | FAIL |
| PB-07 | Backend cannot mount full route set without DB | 11_PRODUCTION_READINESS | backend/main.py | FAIL |
| PB-08 | Browser tests not executed (_browser_test/ absent) | 24_browser_behavior | _browser_test/PLAYWRIGHT_TEST_PROMPT.md | FAIL |
| PB-09 | Test suite collection errors (SECRET_KEY, DATABASE_URL, REDIS_URL) | 12_tests | backend/tests/ | FAIL |
| PB-10 | client.ts ReferenceError (method used before declaration) | 14_frontend_web | frontend/web_app/src/lib/api/client.ts:109 | FAIL |

> **Note:** This table must be updated after each audit pass. Remove rows only when the finding is resolved and verified.

---

## 25 · Sign-Off

| Role | Name | Signature | Date | Status |
|------|------|-----------|------|--------|
| Lead Auditor | | | | Pending |
| Security Reviewer | | | | Pending |
| Backend Lead | | | | Pending |
| Frontend Lead | | | | Pending |
| DevOps / SRE | | | | Pending |
| Product Owner | | | | Pending |

**Assessment Conducted By:** Kilo (Automated Forensic Auditor)
**Assessment Date:** 2026-09-29
**Next Review Date:** After all FAIL items are retested

---

## Appendices

### Appendix A · Dimension-to-Check Mapping

| Section | Dimension File | Dimension Name |
|---------|----------------|----------------|
| Canonical Document Alignment | 01_EXECUTIVE_SUMMARY.md | Executive Summary |
| Technology Stack | 18_security.md, 21_contradictions.md | Security, Contradictions |
| Architecture | 21_contradictions.md, 09_ANTI_PATTERNS.md | Contradictions, Anti-Patterns |
| Feature Completeness | 08_FEATURE_HEALTH.md | Feature Health |
| Backend Runtime | 11_PRODUCTION_READINESS.md | Production Readiness |
| Frontend Build & Runtime | 11_PRODUCTION_READINESS.md, 21_contradictions.md | Production Readiness, Contradictions |
| Mobile Build | 15_frontend_mobile.md | Frontend Mobile |
| Tests -- Backend | 12_tests.md, 11_PRODUCTION_READINESS.md | Tests, Production Readiness |
| Security | 18_security.md | Security |
| Database | 21_contradictions.md, 11_PRODUCTION_READINESS.md | Contradictions, Production Readiness |
| Frontend UI | 24_browser_behavior.md | Browser Behavior |
| Frontend Workflows | 24_browser_behavior.md | Browser Behavior |
| Browser Behavioral Tests | 24_browser_behavior.md | Browser Behavior |
| Performance & Fast Loading | 19_performance.md, 11_PRODUCTION_READINESS.md | Performance, Production Readiness |
| Observability & Health | 11_PRODUCTION_READINESS.md, 20_observability_resilience.md | Production Readiness, Observability |
| Provider Resilience | 11_PRODUCTION_READINESS.md, 08_providers.md | Production Readiness, Providers |
| Operations | 11_PRODUCTION_READINESS.md, 10_migrations.md | Production Readiness, Migrations |
| Country Management | 14_country_management.md | Country Management |
| Tax & Calculations | 14_country_management.md | Country Management |
| Location / Geography | 14_country_management.md | Country Management |
| Catalog Management | 08_FEATURE_HEALTH.md | Feature Health |
| Photo / Video / Media Management | 17_photo_video_media_management.md | Photo/Video/Media Management |
| Supply Chain Security | 28_supply_chain_security.md | Supply Chain Security |

### Appendix B · How to Update This Document After Each Audit Pass

1. Open this file in an editor.
2. For each check, update Status to PASS / FAIL / DEFERRED / UNVERIFIABLE.
3. Fill in the Evidence column with the exact file path, command output, or test artifact.
4. Update the Last verified column with the date (YYYY-MM-DD).
5. Refresh the **Summary Dashboard** counts.
6. Update **Production Ready:** YES / NO.
7. Update the **Completion Blockers** table: remove resolved blockers, add new ones.
8. Commit the updated checklist with message: docs: update production readiness checklist — <date>.

### Appendix C · Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| CVE | Common Vulnerabilities and Exposures |
| RLS | Row-Level Security |
| SBOM | Software Bill of Materials |
| CLS | Cumulative Layout Shift |
| LCP | Largest Contentful Paint |
| INP | Interaction to Next Paint |
| TTFB | Time to First Byte |
| RBAC | Role-Based Access Control |
| MFA | Multi-Factor Authentication |
| DLQ | Dead-Letter Queue |
| FX | Foreign Exchange |
| PII | Personally Identifiable Information |
| WCAG | Web Content Accessibility Guidelines |
| EAS | Expo Application Services |
| CI/CD | Continuous Integration / Continuous Deployment |
| SBOM | Software Bill of Materials |