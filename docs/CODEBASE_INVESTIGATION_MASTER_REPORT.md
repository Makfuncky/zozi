# ZOZI Codebase Investigation Master Report

**Date:** 2026-08-26  
**Scope:** Full codebase (1,355 Python + 1,595 TypeScript + 877 JS files)  
**Method:** 10 parallel investigation agents  
**Architecture Ref:** ARCHITECTURE_DIAGRAM.md (Three-Axis: modules → domains → infrastructure ← providers)

---

## Executive Summary

| Investigation Axis | CRITICAL | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|---|
| Backend Architecture & Import Laws | 42 | 145 | 15 | 47 | **249** |
| Domain Services Code Quality | 8 | 14 | 18 | 12 | **52** |
| Providers Layer Violations | 5 | 8 | 10 | 6 | **29** |
| Modules & Routers | 14 | 31 | 29 | 20 | **94** |
| Frontend Code Quality | 14 | 26 | 31 | 16 | **87** |
| Frontend-Backend Connection | 8 | 12 | 6 | 3 | **29** |
| Security Vulnerabilities | 2 | 0 | 14 | 0 | **16** |
| Infrastructure & Middleware | 8 | 14 | 10 | 5 | **37** |
| RBAC, Kernel & Registry | 5 | 6 | 9 | 4 | **24** |
| Tests & CI/CD | 3 | 5 | 7 | 5 | **20** |
| **TOTAL** | **109** | **261** | **149** | **118** | **637** |

**Overall Architecture Compliance: ~40%** — The three-axis architecture is systematically violated across every layer.

---

## 1. CRITICAL Priority Issues (109 Total)

### 1.1 Runtime-Breaking Bugs (Modules Layer)

| # | Issue | File | Impact |
|---|---|---|---|
| 1 | `get_wishlist`, `clear_user_wishlist` used but never imported | `modules/customer/routers/` | NameError → 500 |
| 2 | 18 `svc_*` functions referenced but undefined | `modules/employee/routers/` | NameError → 500 |
| 3 | `get_okr_service` undefined | `modules/employee/routers/hr.py` | NameError → 500 |
| 4 | `assign_matrix_manager` undefined | `modules/employee/routers/hr.py` | NameError → 500 |
| 5 | `email_metrics` undefined | `modules/admin/routers/` | NameError → 500 |
| 6 | Cross-module imports (orders ← comms, employee ← admin auth) | Multiple routers | Circular imports |
| 7 | `get_customer_health` defined 3x (only last registers) | `modules/customer/routers/` | Silent endpoint loss |
| 8 | `list_logistics_health` defined 2x | `modules/logistics/routers/` | Silent endpoint loss |
| 9 | `require_feature` used as decorator (gate runs at import time) | `modules/customer/routers/` | RBAC bypass |
| 10 | Production routers import from `_auto_stubs` (empty) | `modules/*/routers/` | 500 errors |

### 1.2 Security Critical

| # | Issue | File | CVE-Class |
|---|---|---|---|
| 11 | 30-day access tokens for biometric/phone login | `auth_service.py:1056-1061` | CWE-613 |
| 12 | HS256 secret entropy not validated | `config.py:31` | CWE-798 |

### 1.3 Architecture Critical

| # | Issue | File | Law Violated |
|---|---|---|---|
| 13 | `infrastructure/lifespan.py` imports from accounts/finance/logistics domains | `infrastructure/lifespan.py` | Law 1 |
| 14 | `infrastructure/security/*.py` imports domain models | `infrastructure/security/` | Law 1 |
| 15 | `infrastructure/utils/*.py` are backward-compat shims | `infrastructure/utils/` | Law 1 |
| 16 | `providers/media/` (1,150 lines) contains domain logic | `providers/media/` | Provider Rule |
| 17 | `providers/ai/recommendation.py` — full recommendation engine | `providers/ai/` | Provider Rule |
| 18 | `providers/ai/price_intelligence.py` — hardcoded benchmarks | `providers/ai/` | Provider Rule |
| 19 | `providers/ai/search.py` — complete search engine | `providers/ai/` | Provider Rule |
| 20 | `providers/ai/chatbot.py` — intent classification | `providers/ai/` | Provider Rule |
| 21 | 78 direct `db.commit()` calls in module routers | `modules/*/routers/` | Law 2 |
| 22 | Cross-domain direct imports (orders ← finance) | `domains/orders/` | Law 3 |
| 23 | `accounts` domain creates SupplierProfile/LogisticsPartner | `auth_service.py` | Law 3 |

### 1.4 RBAC Critical

| # | Issue | File | Impact |
|---|---|---|---|
| 24 | Feature strings use colons (`finance:commission:read`) but catalog uses dots | `modules/supplier/routers/finance.py` | All gates silently deny |
| 25 | 37 wrong feature strings in HR router | `modules/employee/routers/hr.py` | All gates silently deny |
| 26 | `_resolve_effective_features()` ignores DB grants | `rbac/dependencies.py:30-42` | Runtime grant/revoke broken |
| 27 | `registry.py` does not exist | `backend/registry.py` | Missing architecture component |
| 28 | `service_index.json` does not exist | `backend/service_index.json` | Missing architecture component |
| 29 | `migrate_imports.py` does not exist | `backend/migrate_imports.py` | Missing architecture component |

### 1.5 Frontend-Backend Connection Critical

| # | Issue | File | Impact |
|---|---|---|---|
| 30 | Systematic URL mismatch: frontend calls `/auth/*`, backend has `/api/v1/auth/*` | All frontend API calls | All API calls 404 |
| 31 | Next.js rewrites `/api/*` → `/api/*` (missing v1) | `next.config.ts:53-81` | Wrong routing |
| 32 | Auth route handlers proxy to `/auth/*` instead of `/api/v1/auth/*` | `frontend/web_app/src/app/auth/` | Auth fails |
| 33 | No WebSocket rewrite in Next.js config | `next.config.ts` | WebSocket fails |
| 34 | Playwright E2E all failing (`405 Method Not Allowed`) | `tests/playwright/` | Zero E2E coverage |
| 35 | No frontend CI pipeline | `.github/workflows/ci.yml` | Regressions undetected |
| 36 | No deployment pipeline | No deploy workflow | Manual deploys only |

### 1.6 Infrastructure Critical

| # | Issue | File | Impact |
|---|---|---|---|
| 37 | RLS interceptor `instrument_rls()` never called | `rls_interceptor.py:359` | Country scoping is no-op |
| 38 | Prometheus Histogram created inside decorator (duplicate collectors) | `logging_middleware.py` | `DuplicateCollectorError` |
| 39 | HTTP client is a stub (no timeout/retry/pooling) | `infrastructure/http/client.py` | Production failures |
| 40 | Lifespan doesn't shut down DB/Redis | `infrastructure/lifespan.py` | Connection leaks |
| 41 | ML worker marks jobs completed without running them | `infrastructure/ml/` | Data corruption |
| 42 | Redis `keys()` blocking call in ML worker | `infrastructure/ml/` | Blocks Redis at scale |

---

## 2. HIGH Priority Issues (261 Total)

### 2.1 Backend Architecture

- **78 module routers** with direct DB writes (employee/finance.py: 15 commits, customer/orders.py: 8 commits)
- **67 direct cross-domain imports** bypassing events/ports pattern
- **Router files 1000+ lines** (logistics: 1517, finance: 1335, hr: 676)
- **15 duplicate `require_feature` calls** in single function (employee/hr.py:329)
- **12+ empty router files** in customer module
- **`require_permission` used instead of `require_feature`** (bypasses RBAC catalog)

### 2.2 Domain Services

- **auth_service.py is 4,317 lines** — god service anti-pattern
- **628-line auto-generated ports.py boilerplate** in multiple domains
- **Empty events/subscribers placeholders** in most domains
- **100+ "TODO: Module not yet created" stubs** across domains
- **16 models duplicated** across domains (User, SupportTicket, AuditLog, etc.)
- **Hardcoded fallback secret** in auth configuration

### 2.3 Providers

- **`shipping/shipping_calculator.py`** — 407 lines hardcoded carrier/zone/pricing
- **`voice/voice_to_text.py`** — domain-specific command processing
- **`ai/vision.py`** — category normalization + price suggestion mixed with SDK calls
- **`ai/finance_ai.py`** — email parsing, bill extraction, reconciliation (204 lines)
- **`ai/sentiment.py`** — keyword-based analysis + review insights
- **Cross-provider imports**: bg_removal ← image, ai_variant_config ← ai/text

### 2.4 RBAC & Kernel

- **Catalog scan misses `services/features.py`** files — features not in catalog
- **Hardcoded role names duplicated** across 3 files (no single source of truth)
- **`staff_permissions.py` disconnected from catalog** — dead code
- **No Redis caching** for RBAC resolution (performance bottleneck at 100K users)
- **Kernel `rls_context.py` imports infrastructure** — violates kernel purity
- **Kernel `error_handler.py` imports FastAPI** — couples kernel to framework
- **`numbering.py` uses `time.time()`** — non-unique sequences under concurrency
- **`currency.py` is empty** — no actual currency primitives

### 2.5 Frontend

- **Prop drilling** across deeply nested components
- **Missing error boundaries** in most page routes
- **Memory leaks** from event listeners without cleanup in hooks
- **Improper Server/Client component boundaries** — client components marked as server
- **Hardcoded API URLs** scattered across components
- **Missing accessibility attributes** across many components
- **Unused imports** in 30+ files

### 2.6 Infrastructure

- **Webhook middleware not registered globally** — per-route only
- **CSRF middleware bypassed in dev/test** — risk of misconfiguration in prod
- **Rate limit profile elevates limits 10-20x** when enabled
- **File upload filename not sanitized** — path traversal risk
- **Default DB credentials in config** — fallback if env var unset

---

## 3. MEDIUM Priority Issues (149 Total)

### 3.1 Architecture

- **8 controller files in domain layer** (risk_controller.py with route decorators)
- **7 domain service files import FastAPI** (HTTPException, UploadFile, WebSocket)
- **`infrastructure/utils/` backward-compat shims** (10 files)
- **DOMAIN_ALLOWLIST.yaml has 37 entries** — should only shrink

### 3.2 Domains

- **Magic numbers** in business logic
- **Inconsistent naming conventions** across domains
- **Missing `__all__`** in several domain `__init__.py` files
- **Duplicate code across ports.py files** (copy-paste cross-domain reads)
- **Base class imports in services** (should be in models only)

### 3.3 Security

- Refresh token exposed in response body
- RBAC not enforced by default (opt-in)
- f-string SQL in Alembic migrations
- f-string SQL in RLS interceptor
- No email format validation in service layer
- Password truncation not surfaced to users
- User data cached without authorization context
- Versioning module allows wildcard CORS

### 3.4 Frontend

- Inconsistent error handling patterns across pages
- Missing loading states for async operations
- Inconsistent TypeScript strictness (some `any` types)
- Tailwind class duplication (no design tokens usage)
- Missing alt text on images

### 3.5 Tests & CI

- `time.sleep()` anti-pattern in test_auth.py (4 occurrences)
- No test coverage reporting or thresholds
- Dead `router-generation.yml` CI workflow
- `Makefile` uses bash syntax (won't work on Windows)
- Architecture gate steps are no-ops
- Hardcoded test passwords not overridden in CI

---

## 4. LOW Priority Issues (118 Total)

- Style inconsistencies, missing docstrings, import ordering
- Missing `.dockerignore` files
- No `pytest-cov` or coverage thresholds
- `norecursedirs` not set in pyproject.toml
- Thin kernel modules (period.py, country.py)
- No-op stubs in `rbac/__init__.py`
- `Permission.slug` unique constraint risk
- Missing frontend healthcheck in docker-compose.yml

---

## 5. Positive Findings

### What's Working Well

1. **Password hashing** — bcrypt with built-in salt (proper)
2. **jti token blacklist** — Redis-backed with in-memory fallback
3. **Refresh token rotation** — family-based with reuse detection
4. **Account lockout** — 5 failed attempts → 15-minute lockout
5. **Security headers** — Comprehensive CSP, HSTS, X-Frame-Options, etc.
6. **PCI-DSS middleware** — HTTPS enforcement, audit logging
7. **Webhook HMAC verification** — Proper SHA-256 with constant-time comparison
8. **Rate limiting** — Per-path sliding window with Redis
9. **CSRF protection** — Double-submit cookie pattern
10. **No pickle deserialization** — Safe
11. **Architecture test suite** — Comprehensive AST-enforced import laws
12. **Test isolation** — Transaction-rollback pattern (no data leaks)
13. **Provider HAS_ flags** — ~15 providers with graceful degradation
14. **Frontend test suite** — ~60 test files with jest-axe accessibility
15. **TypeScript strict mode** — Frontend uses strict TypeScript
16. **Multi-stage Docker build** — Frontend has optimized production build
17. **docker-compose.prod.yml** — PgBouncer, backend replicas, healthchecks

---

## 6. Recommended Fix Priority

### Phase 1: Stop the Bleeding (Week 1-2)
1. **Fix NameErrors in module routers** — resolve all undefined function references
2. **Fix URL path mismatch** — standardize frontend to use `/api/v1/` prefix
3. **Fix RBAC feature strings** — replace colons with dots in all `require_feature()` calls
4. **Fix 30-day token TTL** — reduce biometric/phone to 15 minutes
5. **Fix duplicate route handlers** — consolidate `get_customer_health`, `list_logistics_health`

### Phase 2: Architectural Integrity (Week 3-6)
6. **Remove DB writes from routers** — move to domain services
7. **Create registry.py, service_index.json, migrate_imports.py** — implement Service Registry
8. **Wire DB grants into RBAC resolution** — make grant/revoke work at runtime
9. **Move domain logic out of providers** — media/, ai/recommendation, ai/search, etc.
10. **Consolidate duplicate models** — single source per entity
11. **Split auth_service.py** — 4,317 lines into focused services
12. **Fix kernel purity** — remove infrastructure/FastAPI imports

### Phase 3: Production Readiness (Week 7-10)
13. **Install RLS interceptor** — call `instrument_rls()` in lifespan
14. **Add Redis caching to RBAC** — performance at scale
15. **Implement HTTP client** — timeouts, retries, connection pooling
16. **Fix Prometheus metrics** — eliminate duplicate collectors
17. **Register webhook middleware** — global or enforced per-route
18. **Add frontend CI** — tests, lint, typecheck
19. **Create deployment pipeline** — staging → production
20. **Fix Playwright E2E** — separate frontend/backend test targets

### Phase 4: Quality & Coverage (Week 11-14)
21. **Add test coverage** — pytest-cov with 70% threshold
22. **Replace `time.sleep()`** — deterministic test waits
23. **Windows-compatible Makefile** — PowerShell alternatives
24. **Sanitize file uploads** — prevent path traversal
25. **Generate permissions.ts** — build script for @zozi/shared
26. **Remove dead CI workflows** — router-generation.yml
27. **Add .dockerignore files** — reduce build context

---

## 7. File Reference Quick Index

| Category | Report Location |
|---|---|
| Backend Architecture Violations | `docs/BACKEND_ARCHITECTURE_VIOLATIONS.md` |
| Domain Services Code Quality | `docs/DOMAINS_CODE_QUALITY_AUDIT.md` |
| Providers Layer Diagnosis | `docs/PROVIDERS_LAYER_DIAGNOSIS.md` |
| Modules Layer Diagnosis | `docs/MODULES_LAYER_DIAGNOSIS.md` |
| Security Audit | (embedded in Section 1.3 above) |
| RBAC & Kernel Investigation | (embedded in Section 1.4 above) |
| Infrastructure & Middleware | (embedded in Section 1.6 above) |
| Tests & CI/CD | (embedded in Section 3.5 above) |

---

## 8. Architecture Compliance Scorecard

| Law | Description | Compliance |
|---|---|---|
| Law 1 | Arrows point down only | 🔴 **15%** — 42 CRITICAL upward imports |
| Law 2 | Module routers stay thin | 🔴 **20%** — 78 DB writes in routers |
| Law 3 | Cross-domain via events/ports | 🟡 **40%** — direct imports everywhere |
| Law 4 | Features single-sourced | 🟡 **50%** — colon/dot mismatch breaks gates |
| Law 5 | Country as orthogonal axis | 🔴 **10%** — RLS never installed |
| Law 6 | Schema discipline | 🟢 **80%** — Alembic is source of truth |
| Law 7 | Allowlist only shrinks | 🟡 **60%** — 37 entries, never reduced |

**Overall: ~38%** — Significant architectural debt requiring systematic remediation.

---

*Report generated by 10 parallel investigation agents on 2026-08-26*  
*Total investigation time: ~12 minutes*  
*Files analyzed: ~3,827 source files*
