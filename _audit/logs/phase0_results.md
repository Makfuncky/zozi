# Phase 0 — Boot & Preflight Results

> **Generated:** 2026-10-01T19:xx:xxZ
> **Auditor:** Boot & Preflight Auditor (read-only)

## Summary

| Metric | Value |
|--------|-------|
| Total checks | 14 |
| PASS | 3 |
| FAIL | 9 |
| Completion blockers | 9 |

---

## Phase 0 — Boot Smoke Test

| # | Check | Command | Status | Evidence | Project completion blocker |
|---|-------|---------|--------|----------|---------------------------|
| 1 | Route count > 0 | `python -c "from backend.main import app; print(len(app.routes))"` | **FAIL** | `ModuleNotFoundError: No module named 'infrastructure'` — `backend/` lacks `__init__.py`; exact command cannot import. Adapted: `cd backend; python -c "from main import app; print(len(app.routes))"` → **82 routes** but emitted warnings: RLS policy install skipped (Neon unsupported `statement_timeout`), OpenTelemetry disabled (`No module named 'infrastructure.utils.tracing'`), Valkey connection timeouts (3 retries exhausted), `readiness_require_valkey` AttributeError, `Skipping router logistics: cannot import name 'bulk_archive_entities' from 'domains.governance.ports'`, `Skipping router orders: cannot import name 'bulk_archive_entities' from 'domains.governance.ports'`. | **yes** |
| 2 | Architecture test collection | `pytest test/architecture/ --collect-only` | **PASS** | 356 tests collected in 4.09s. Warnings: Unknown `pytest.mark.architecture` marks. | no |
| 3 | Frontend install | `cd frontend/web_app && pnpm install --frozen-lockfile` | **PASS** | Lockfile up to date, 1 package added. Done in 14.3s. | no |
| 4 | Frontend build | `cd frontend/web_app && pnpm build` | **PASS** | Next.js 16.3.4 compiled successfully in 13.9s. 151 static pages generated. | no |
| 5 | Docker compose config | `docker compose config` | **PASS** | Valid YAML. Services: backend, celery-beat, celery-worker-emails, celery-worker-ml, celery-worker-payouts, celery-worker-periodic, db, frontend, pgbouncer, valkey. | no |

---

## Phase 0.5 — Pre-flight Checks

| # | Check | Command | Status | Evidence | Project completion blocker |
|---|-------|---------|--------|----------|---------------------------|
| 6 | DATABASE_URL set | `python -c "from backend.config import settings; print(settings.DATABASE_URL)"` | **FAIL** | Exact command raises `AttributeError: Settings has no attribute 'DATABASE_URL'`. Adapted: `settings.database_url` → `postgresql://neondb_owner:***@ep-sparkling-dream-za50z6c0-pooler.c-2.eu-west-2.aws.neon.tech/neondb`. Setting name is lowercase `database_url`, not uppercase `DATABASE_URL`. | **yes** |
| 7 | Valkey connectivity | `python -c "from backend.config import settings; import redis; r = redis.Redis.from_url(settings.VALKEY_URL); print(r.ping())"` | **FAIL** | Exact command raises `ValueError: Redis URL must specify one of the following schemes (redis://, rediss://, unix://)` because settings uses `valkey://` scheme. Adapted: `import valkey; valkey.Redis.from_url(settings.valkey_url)` → `ConnectionRefusedError: Error 10061 connecting to localhost:6379`. No local Valkey server running. | **yes** |
| 8 | Full test collection | `pytest test/ --collect-only` | **FAIL** | 4657 tests collected but **6 collection errors**: `tests/domains/catalog/test_category_deletion.py` (ImportError: `_CATEGORY_DELETED_MESSAGE`), `tests/domains/catalog/test_file_54_resolution.py` (ImportError: `MODERATION_APPROVE_MESSAGE`), `tests/domains/customers/test_cross_country_session.py` (ModuleNotFoundError: `backend`), `tests/domains/customers/test_customer_router_service.py` (ImportError: `_delete_response`), `tests/domains/orders/test_core_admin.py` (ImportError: `bulk_archive_entities`), `tests/domains/test_circuit_breaker.py` (ImportError: `CircuitBreakerRegistry`). | **yes** |
| 9 | Frontend type check | `cd frontend/web_app && pnpm tsc --noEmit` | **FAIL** | 60+ TypeScript errors including: `setConfig` not found, `ExportButtonProps` missing `data`, `PaginationProps` missing `current`, `StatCardProps` missing `subtitle`, JSX namespace issues, React Native type mismatches in `.native.tsx` files, `discount_percent` vs `discount_percentage`, resolver type mismatches. | **yes** |
| 10 | Lint check | `cd backend && ruff check .` | **FAIL** | 8335 errors (2954 fixable). Dominated by F401 unused imports in test files, F821 undefined names, E402 module-level import not at top of file, E712 boolean comparisons, E741 ambiguous variable names. | **yes** |
| 11 | Migration status — current | `cd backend && alembic current` | **PARTIAL** | Multiple revisions shown: `20260930_0006 (head)`, `20260930_0007 (head)`, `20260930_0008`, `20260930_0002 (head)`, `20260930_0003 (head)`. Database has multiple applied revisions but heads are divergent. | **yes** |
| 12 | Migration status — heads | `cd backend && alembic heads` | **FAIL** | 5 divergent heads: `20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`. Violates Law 49 (linear Alembic history). Requires `alembic heads` to return exactly one revision. | **yes** |
| 13 | Lockfile sync — Python | Compare `uv.lock` / `requirements.txt` vs `TECHNOLOGY_STACK.md` | **FAIL** | `uv.lock` contains only 1 package entry (`zozi-backend==0.1.0`) — not a functional lockfile. `requirements.txt` has multiple mismatches: `fastapi==0.115.2` (target `0.141.x`), `sqlalchemy==2.0.51` (target `2.0.52`), `alembic==1.18.5` (target `1.19.1+`), `pydantic-settings==2.7.1` (target `2.9.1+`), `sentry-sdk==2.66.1` (target `2.68.1`), `prometheus-fastapi-instrumentator==7.1.0` (target `8.1.0+`), `celery==5.4.0` (target `5.5+`). Forbidden packages present: `psycopg2-binary==2.9.12` (asyncpg required), `python-magic==0.4.27` (puremagic required), `pytz==2026.3.post1` (zoneinfo required), `tzlocal==5.4.4` (forbidden), `requests==2.34.2` (httpx required). Unapproved packages: `babel`, `slowapi`, `cachetools`, `schedule`, `text-unidecode`, `duckdb`, `duckdb-engine`. | **yes** |
| 14 | Lockfile sync — Frontend | Compare `pnpm-lock.yaml` vs `TECHNOLOGY_STACK.md` | **FAIL** | Mismatches found: `next: 16.3.4` (target `16.3.5`), `framer-motion: 12.43.0` (target `13.2.0+`), `@stripe/react-stripe-js: 5.6.1` (target `6.9.0`), `@hookform/resolvers: 5.9.1` (target `5.2.2`), `react-hook-form: 7.89.0` (target `7.84.0`), `zod: 3.25.76` (target `4.3.6` — major version drift), `tailwind-merge: 3.7.0` (target `3.5.0`), `dompurify: 3.4.16` (target `3.4.0`), `jose: 6.2.12` (target `6.2.10`). | **yes** |

---

## Findings

### F-001: Backend package import path broken (Phase 0, Check 1)
- **File:** `backend/` (no `__init__.py`)
- **Current:** `python -c "from backend.main import app"` raises `ModuleNotFoundError: No module named 'infrastructure'`
- **Target:** Backend directory must be importable as a package per `_most_imp_docx/ARCHITECTURE_STACK.md` §3
- **Delta:** Missing `__init__.py` prevents direct package import from project root
- **Fix:** Add `backend/__init__.py` or update audit commands to run from inside `backend/`
- **Effort:** S
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-002: DATABASE_URL config attribute mismatch (Phase 0.5, Check 6)
- **File:** `backend/config.py:472`
- **Current:** `settings.DATABASE_URL` raises `AttributeError`; actual attribute is `settings.database_url` (lowercase)
- **Target:** Config attributes should match canonical names from `TECHNOLOGY_STACK.md` §20 (`DATABASE_URL`)
- **Delta:** Case mismatch between documented env var name and actual Pydantic settings attribute
- **Fix:** Align config attribute names with documented env var names or update `TECHNOLOGY_STACK.md`
- **Effort:** S
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-003: Valkey not running locally (Phase 0.5, Check 7)
- **File:** `backend/config.py` (valkey_url setting)
- **Current:** `valkey_url = valkey://localhost:6379`; connection refused — no local Valkey server
- **Target:** Valkey 9.0.6+ should be reachable for cache, sessions, rate-limiting, event bus
- **Delta:** Local Valkey service not running; all Valkey-dependent features (rate limiting, token blacklist, cache) will fail
- **Fix:** Start local Valkey via Docker Compose (`docker compose up valkey`) or install Valkey locally
- **Effort:** S
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-004: Test collection failures (Phase 0.5, Check 8)
- **Files:** 6 test files with ImportError/ModuleNotFoundError
- **Current:** 4657 tests collected, 6 errors
- **Target:** All tests must collect without error per `PROMPT_FORENSIC_AUDIT.md` §0.1
- **Delta:** Broken imports prevent full test suite execution
- **Fix:** Fix missing imports in: `test_category_deletion.py`, `test_file_54_resolution.py`, `test_cross_country_session.py`, `test_customer_router_service.py`, `test_core_admin.py`, `test_circuit_breaker.py`
- **Effort:** M
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-005: TypeScript compilation errors (Phase 0.5, Check 9)
- **Files:** Multiple `src/` files in `frontend/web_app/`
- **Current:** 60+ TypeScript errors in `tsc --noEmit`
- **Target:** TypeScript must compile cleanly per `PROMPT_FORENSIC_AUDIT.md` §0.1
- **Delta:** Type mismatches, missing properties, implicit `any` types
- **Fix:** Fix TypeScript errors in checkout, employee/attendance, supplier/bulk, supplier/dashboard, suppliers/[id], AuthForms, ProductCard, Heading, serverCountry, shared components
- **Effort:** L
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-006: Ruff lint failures (Phase 0.5, Check 10)
- **Files:** Multiple test files in `backend/tests/`
- **Current:** 8335 errors (2954 fixable)
- **Target:** Ruff must pass per `TECHNOLOGY_STACK.md` §11 (ruff 0.16.6+)
- **Delta:** Massive unused import and undefined name issues across test files
- **Fix:** Fix or suppress ruff errors across test files
- **Effort:** L
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-007: Alembic divergent heads (Phase 0.5, Checks 11-12)
- **Files:** `backend/alembic/versions/*.py`
- **Current:** 5 divergent heads: `20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`
- **Target:** Single linear head per Law 49
- **Delta:** Multiple unmerged branches in migration history
- **Fix:** Merge or squash divergent migration heads into single linear history
- **Effort:** L
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-008: Backend version mismatches and forbidden packages (Phase 0.5, Check 13)
- **Files:** `backend/requirements.txt`, `backend/uv.lock`
- **Current:** Multiple version mismatches and forbidden packages (see Check 13 evidence)
- **Target:** Versions must match `TECHNOLOGY_STACK.md`; forbidden packages must be removed
- **Delta:** FastAPI 0.115.2 vs 0.141.x, SQLAlchemy 2.0.51 vs 2.0.52, Alembic 1.18.5 vs 1.19.1+, psycopg2-binary present (forbidden), python-magic present (forbidden), pytz/tzlocal present (forbidden), requests present (forbidden)
- **Fix:** Update versions in requirements.txt to match TECHNOLOGY_STACK.md, remove forbidden packages
- **Effort:** M
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

### F-009: Frontend version mismatches (Phase 0.5, Check 14)
- **Files:** `frontend/web_app/package.json`, `frontend/web_app/pnpm-lock.yaml`
- **Current:** Multiple version mismatches (see Check 14 evidence)
- **Target:** Versions must match `TECHNOLOGY_STACK.md`
- **Delta:** Next.js 16.3.4 vs 16.3.5, framer-motion 12.43.0 vs 13.2.0+, @stripe/react-stripe-js 5.6.1 vs 6.9.0, zod 3.25.76 vs 4.3.6
- **Fix:** Update package.json and pnpm-lock.yaml to match TECHNOLOGY_STACK.md versions
- **Effort:** M
- **Priority:** P0
- **Confidence:** 5
- **Completion blocker:** yes

---

## Observed but not changed

- App boots with 82 routes despite missing `__init__.py` when run from inside `backend/`
- OpenTelemetry tracing disabled due to missing `infrastructure.utils.tracing` module
- Two routers skipped during boot: `logistics` and `orders` (missing `bulk_archive_entities` in `domains.governance.ports`)
- `uv.lock` contains only 1 package entry — not a functional dependency lockfile
- 6 pytest collection errors prevent full test suite execution
- 5 divergent Alembic migration heads violate Law 49 (linear history)
