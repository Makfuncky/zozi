# CODEBASE STANDARDIZATION PLAN
## ZOZI Marketplace — Neon 18 + Valkey 9.0 + R2 + Next.js 16.3.4

**Date:** 2026-09-11
**Goal:** Eliminate all Redis server/client references, standardize on Valkey, ensure all seed data lives in Neon (not local files), confirm R2 for object storage, lock Next.js 16.3.4, rename `redis_client.py` → `valkey_client.py`.
**Constraint:** Do NOT drift from mentioned tech versions. Every version pinned below is the target.

---

## 0. TARGET STACK (locked — never change these versions)

| Layer | Technology | Version | Evidence |
|-------|-----------|---------|----------|
| Database | Neon PostgreSQL | 18 | `ARCHITECTURE_DIAGRAM.md` Law section; `docker-compose.yml` postgres:18-alpine |
| Cache | Valkey | 9.0-alpine (dev), 9.0 (prod) | `docker-compose.yml:21` |
| Object Storage | Cloudflare R2 | S3-compatible | `backend/providers/storage/r2_client.py` |
| Frontend | Next.js | 16.3.4 | `frontend/web_app/package.json:30` |
| Backend | FastAPI | 0.115.2 | `backend/requirements.txt:8` |
| ORM | SQLAlchemy | 2.0.51 | `backend/requirements.txt:14` |
| Cache Client | valkey-py | 8.0.1 | TO BE ADDED (replaces redis-py) |
| Image Processing | Pillow | 12.2.0 | `backend/requirements.txt:51` (fixes non-existent 12.3.0) |
| Celery | celery | 5.4.0 | `backend/requirements.txt:31` |

---

## 1. FILE RENAMING: `redis_client.py` → `valkey_client.py`

### 1.1 Rename the file

| Action | Detail |
|--------|--------|
| Source | `backend/infrastructure/database/redis_client.py` |
| Target | `backend/infrastructure/database/valkey_client.py` |
| Reason | File manages Valkey client; name must reflect technology |

### 1.2 Fix the file content (current file is BROKEN — mixes redis-py and valkey-py)

The current `redis_client.py` has `import valkey` at line 70 but still references `redis.Redis` at lines 76, 79, 86, and uses `redis = None` at line 73. After renaming to `valkey_client.py`, the content must be corrected to use `valkey` consistently:

| Line | Current (broken) | Target |
|------|-----------------|--------|
| 71 | `_redis_available = True` | `_valkey_available = True` |
| 73 | `redis = None` | `valkey = None` |
| 76 | `_client: redis.Redis \| _NoOpValkey \| None = None` | `_client: valkey.Valkey \| _NoOpValkey \| None = None` |
| 79 | `def valkey_client() -> redis.Redis \| _NoOpValkey:` | `def valkey_client() -> valkey.Valkey \| _NoOpValkey:` |
| 86 | `client = redis.Redis.from_url(` | `client = valkey.Valkey.from_url(` |
| 113 | `"backend": "redis"` | `"backend": "valkey"` |
| 115 | `"backend": "redis"` | `"backend": "valkey"` |

### 1.3 Update all imports of the renamed file

Every file that imports from `infrastructure.database.redis_client` must be updated to `infrastructure.database.valkey_client`:

| File | Line(s) | Current Import | Target Import |
|------|---------|---------------|---------------|
| `backend/lifespan.py` | 367 | `from infrastructure.database.redis_client import redis_client` | `from infrastructure.database.valkey_client import redis_client` |
| `backend/tests/infrastructure/test_redis_integration.py` | 35, 40, 140, 150, 159, 168, 182, 193, 207, 219, 300, 306 | `from infrastructure.database.redis_client import redis_client` | `from infrastructure.database.valkey_client import redis_client` |
| `backend/tests/infrastructure/test_infrastructure_services.py` | 138 | `from infrastructure.database.redis_client import redis_client` | `from infrastructure.database.valkey_client import redis_client` |
| `backend/tests/infrastructure/test_infrastructure.py` | 69 | `from infrastructure.database.redis_client import redis_client` | `from infrastructure.database.valkey_client import redis_client` |

### 1.4 Update the architecture test

| File | Line(s) | Current | Target |
|------|---------|---------|--------|
| `backend/tests/architecture/test_valkey_migration.py` | 73 | `infrastructure.database.redis_client is a backward-compat shim to valkey` | Update description to: `infrastructure.database.valkey_client is the canonical Valkey client` |
| `backend/tests/architecture/test_valkey_migration.py` | 93 | `test_infrastructure_redis_package_is_shim` | Rename to `test_infrastructure_valkey_client_works` |
| `backend/tests/architecture/test_valkey_migration.py` | 99 | `from infrastructure.redis import redis_client` | Keep as-is (this tests the shim at `infrastructure/redis/`, not the renamed file) |

### 1.5 Delete the old file

After renaming and updating all imports, delete `backend/infrastructure/database/redis_client.py`.

### 1.6 Note on `infrastructure.utils.redis_client` imports

Multiple files import from `infrastructure.utils.redis_client` (e.g., `performance_cache.py`, `realtime.py`, `ml_worker.py`, `auth_service.py`, `security/auth.py`, `siem_engine.py`, `behavioral_analytics.py`, `rate_limit_helpers.py`, `webhook_verification.py`, `rate_limit_middleware.py`, `impossible_travel_middleware.py`, `country_auto_populate.py`, `database_security.py`, `country_context.py`, `command_center/service.py`, `command_center/background.py`).

**INVESTIGATION REQUIRED:** `glob` found NO file at `backend/infrastructure/utils/redis_client*`. These imports may be:
- (a) Broken references to a file that was deleted
- (b) References to `backend/infrastructure/database/redis_client.py` via wrong path
- (c) References to a file that exists under a different name

**Action:** After renaming `redis_client.py` → `valkey_client.py`, verify these imports resolve correctly. If they were pointing to the renamed file, update them to `infrastructure.database.valkey_client`. If they were pointing to a different file, locate and rename that file too.

---

## 2. DEPENDENCY MANIFEST FIXES

### 2.1 `backend/requirements.txt`

| Line | Current | Target | Reason |
|------|---------|--------|--------|
| 19 | `# Redis & caching` | `# Valkey & caching` | Comment must reflect Valkey |
| 20 | `redis==8.0.1` | `valkey==8.0.1` | Code imports `valkey` package, not `redis` server client |
| 51 | `Pillow==12.2.0` | `Pillow==12.2.0` | ✅ Already correct (was 12.3.0, fixed) |

### 2.2 `backend/tests/architecture/test_manifest_drift.py:57`

| Line | Current | Target |
|------|---------|--------|
| 57 | `assert not line.strip().startswith("Pillow==12.3.0")` | Keep as-is (still validates Pillow is not 12.3.0) |

### 2.3 `frontend/web_app/package.json`

| Line | Current | Target | Status |
|------|---------|--------|--------|
| 30 | `"next": "16.3.4"` | `"next": "16.3.4"` | ✅ Already correct |
| 51 | `"eslint-config-next": "16.3.4"` | `"eslint-config-next": "16.3.4"` | ✅ Already correct |

### 2.4 `frontend/web_app/package-lock.json`

- Verify lockfile resolves `next@16.3.4` (not 16.1.6 or other)
- Run `npm install` in `frontend/web_app/` to regenerate if needed

---

## 3. DOCKER COMPOSE FIXES (redis → valkey)

### 3.1 `docker-compose.yml` — ALREADY CORRECT ✅

- Line 20-25: `valkey: image: valkey:9.0-alpine` ✅
- Line 34: `VALKEY_URL=valkey://valkey:6379` ✅
- Line 39-40: `CELERY_BROKER_URL=valkey://valkey:6379/1` ✅
- Line 173: `valkey_data` volume ✅

### 3.2 `docker-compose.prod.yml` — NEEDS FIX

| Line | Current | Target |
|------|---------|--------|
| 29 | `REDIS_URL=valkey://valkey:6379` | ✅ Already correct |
| 75 | `REDIS_URL=valkey://valkey:6379` | ✅ Already correct |
| 96 | `redis:` service name | `valkey:` service name |
| 97 | `image: redis:7-alpine` | `image: valkey:9.0-alpine` |
| 99 | `"127.0.0.1:6379:6379"` port | Keep (port number unchanged) |
| 101 | `valkey_data:/data` volume | ✅ Already correct |

### 3.3 `.github/workflows/schema-audit.yml`

| Line | Current | Target |
|------|---------|--------|
| 43-44 | `redis:` service (image: redis:7-alpine) | `valkey:` service (image: valkey:9.0-alpine) |
| 48 | `--health-cmd "redis-cli ping"` | `--health-cmd "valkey-cli ping"` |

### 3.4 `.github/workflows/e2e.yml`

| Line | Current | Target |
|------|---------|--------|
| 52-53 | `redis:` service (image: redis:8-alpine) | `valkey:` service (image: valkey:9.0-alpine) |
| 57 | `--health-cmd "redis-cli ping"` | `--health-cmd "valkey-cli ping"` |

### 3.5 `monitoring/docker-compose.monitoring.yml`

| Line | Current | Target |
|------|---------|--------|
| 102 | `REDIS_URL=redis://sentry-redis:6379/0` | `REDIS_URL=valkey://sentry-redis:6379/0` |
| 113 | `sentry-redis` volume name | `sentry-valkey` volume name |
| 131-132 | `sentry-redis:` service (image: redis:7-alpine) | `sentry-valkey:` service (image: valkey:9.0-alpine) |

### 3.6 `monitoring/prometheus/prometheus.yml`

| Line | Current | Target |
|------|---------|--------|
| 35 | `job_name: redis` | `job_name: valkey` |
| 39 | `redis-exporter:9121` | `valkey-exporter:9121` |
| 41 | `app: zozi-redis` | `app: zozi-valkey` |

---

## 4. BACKEND CONFIG FIXES

### 4.1 `backend/config.py` — ALREADY CORRECT ✅

- Line 74: `"valkey_url": "valkey://localhost:6379"` ✅
- Line 90: `"celery_broker_url": os.getenv("CELERY_BROKER_URL", "valkey://localhost:6379/1")` ✅
- Line 91: `"celery_result_backend": os.getenv("CELERY_RESULT_BACKEND", "valkey://localhost:6379/2")` ✅

**Note:** `settings.redis_url` does NOT exist in config.py. The canonical env var is `VALKEY_URL`. Any code referencing `settings.redis_url` must use `settings.valkey_url` instead.

### 4.2 `backend/.env.example` — ALREADY CORRECT ✅

- Line 7: `SEED_DATA_ON_STARTUP=true` ✅
- Line 20: `VALKEY_URL=valkey://localhost:6379` ✅
- Line 21: `REDIS_URL=valkey://localhost:6379` ✅ (backward-compat alias)
- Line 47: `STORAGE_BACKEND=r2` ✅
- Line 65: `CELERY_BROKER_URL=valkey://localhost:6379/1` ✅
- Line 66: `CELERY_RESULT_BACKEND=valkey://localhost:6379/2` ✅

---

## 5. BACKEND CODE IMPORT FIXES (redis-py → valkey-py)

### 5.1 `backend/infrastructure/database/valkey_client.py` (renamed from redis_client.py)

After renaming, the file content must be fully corrected (see Section 1.2). The canonical implementation already exists at `backend/infrastructure/valkey/client.py` and is correct.

### 5.2 `backend/domains/security/services/fraud/fraud_detection_service.py`

| Line | Current | Target |
|------|---------|--------|
| 16 | `from redis.exceptions import ConnectionError, ResponseError` | `from valkey.exceptions import ConnectionError, ResponseError` |

### 5.3 All Python files importing from `infrastructure.utils.redis_client`

**CRITICAL:** These imports reference a file that does NOT exist at `backend/infrastructure/utils/redis_client*`. After renaming `database/redis_client.py` → `database/valkey_client.py`, verify these imports resolve.

Files with `from infrastructure.utils.redis_client import redis_client`:
- `backend/infrastructure/messaging/realtime.py:46`
- `backend/jobs/ml_worker.py:67`
- `backend/domains/analytics/services/aggregation/command_center_service.py:29`
- `backend/infrastructure/utils/performance_cache.py:45`
- `backend/domains/accounts/services/auth/auth_service.py:86`
- `backend/infrastructure/security/auth.py:51`
- `backend/domains/security/services/threat/siem_engine.py:12`
- `backend/domains/security/services/threat/behavioral_analytics.py:15`
- `backend/infrastructure/security/rate_limit_helpers.py:45`
- `backend/middleware/webhook_verification.py:256`
- `backend/middleware/rate_limit_middleware.py:19, 88`
- `backend/middleware/impossible_travel_middleware.py:12`
- `backend/domains/country/services/research/country_auto_populate.py:81`
- `backend/middleware/database_security.py:16`
- `backend/middleware/country_context.py:30`
- `backend/domains/governance/services/command_center/service.py:25`
- `backend/domains/governance/services/command_center/background.py:39`

**Action:** Determine where `infrastructure.utils.redis_client` actually resolves. If it was a symlink or alias to `database/redis_client.py`, update it to point to `database/valkey_client.py`. If the file was deleted, create `backend/infrastructure/utils/redis_client.py` as a re-export shim from `database/valkey_client.py` for backward compatibility, OR update all 17 import sites to use `database/valkey_client`.

### 5.4 `backend/lifespan.py`

| Line | Current | Target |
|------|---------|--------|
| 367 | `from infrastructure.database.redis_client import redis_client` | `from infrastructure.database.valkey_client import redis_client` |
| 372 | `logger.exception("Failed to close Redis client")` | `logger.exception("Failed to close Valkey client")` |

### 5.5 `backend/middleware/lifespan.py` — ALREADY CORRECT ✅

- Line 362: `from infrastructure.valkey.client import valkey_client` ✅
- Line 367: `logger.exception("Failed to close Valkey client")` ✅

---

## 6. SEED DATA MIGRATION (Local Files → Neon)

### 6.1 Current State — Already Mostly Correct ✅

**Canonical seed path (PRODUCTION):**
- `backend/infrastructure/database/seed/_seed_constants.py` — all seed data as Python literals (single source of truth)
- `backend/infrastructure/database/seed/_common.py` — `seed_data()` function (inserts via SQLAlchemy into Neon PostgreSQL)
- `backend/infrastructure/database/seed/seed_part{1,2,3}.py` — domain-specific seed helpers
- `backend/infrastructure/database/seed/__init__.py` — public re-exports

**Legacy dev loader (deprecated):**
- `backend/infrastructure/database/seed_data/_README.md` — documents the deprecated path
- `backend/infrastructure/database/seed_data/` directory contains ONLY `_README.md` — no JSON files remain

### 6.2 Actions

| # | Action | Priority | Status |
|---|--------|----------|--------|
| 6.2.1 | Verify `backend/infrastructure/database/seed_data/` contains only `_README.md` (no JSON/data files) | HIGH | ✅ Already correct |
| 6.2.2 | Confirm `backend/infrastructure/database/seed/_common.py` inserts into Neon PostgreSQL (not SQLite/local) | HIGH | ✅ Already correct — uses `engine` from `infrastructure.database.database` |
| 6.2.3 | Confirm `backend/infrastructure/database/seed/_seed_constants.py` docstring is accurate (says "legacy JSON files in seed_data/ are kept for backward compatibility" but JSON files are gone) | MEDIUM | ⚠️ Update docstring to remove reference to JSON files |
| 6.2.4 | Verify `scripts/seed_loader.py` is marked as dev-only/deprecated | MEDIUM | Check and document |
| 6.2.5 | Ensure `SEED_DATA_ON_STARTUP=true` is only used in development, NOT in production | HIGH | ⚠️ Currently `true` in `.env.example` — acceptable for dev template, but production must set `false` |
| 6.2.6 | Verify all test fixtures seed into Neon, not local SQLite | HIGH | Check `backend/tests/conftest.py` and related |

### 6.3 Seed Data Flow Confirmation

```
Production flow:
  Application startup → lifespan.py → seed_data(SessionLocal)
    → infrastructure/database/seed/_common.py:seed_data()
      → Reads from _seed_constants.py (Python literals)
      → Inserts via SQLAlchemy ORM into Neon PostgreSQL 18

Development flow:
  pytest fixtures → conftest.py → seed_data() if DB empty
    → Same canonical path as production

Deprecated (DO NOT USE):
  scripts/seed_loader.py → Was SQLite utility reading JSON from seed_data/
    → JSON files removed; now reads from _seed_constants.py
```

---

## 7. OBJECT STORAGE (R2 Confirmation)

### 7.1 Current State — Already Correct ✅

- `backend/providers/storage/r2_client.py` — R2 client implementation
- `backend/providers/storage/s3_client.py` — S3 client (alias to R2)
- `backend/infrastructure/storage/storage.py` — R2Storage class
- `backend/tests/infrastructure/test_storage_r2.py` — R2 tests
- `backend/infrastructure/utils/media_storage.py` — uses R2
- `.env.example` line 47: `STORAGE_BACKEND=r2` ✅
- `docker-compose.prod.yml` line 32: `STORAGE_BACKEND=s3` (S3-compatible endpoint for R2) ✅

### 7.2 Actions

| # | Action | Priority | Status |
|---|--------|----------|--------|
| 7.2.1 | No code changes needed for R2 | LOW | ✅ Already standard |
| 7.2.2 | Verify `docker-compose.prod.yml` `STORAGE_BACKEND=s3` uses R2 endpoint URL | MEDIUM | Check env vars |
| 7.2.3 | Confirm no local storage paths in production code | MEDIUM | Grep for `local` storage in providers/ |

---

## 8. DOCUMENTATION UPDATES

### 8.1 Files to update

| File | Changes | Priority |
|------|---------|----------|
| `documents/BACKUP_STRATEGY.md` | redis:7-alpine → valkey:9.0-alpine, redis_data → valkey_data, REDIS_URL → VALKEY_URL | MEDIUM |
| `documents/ARCHITECTURE_DIAGRAM.md` | Ensure all references are valkey (not redis); already mostly correct per Line 74, 81 | MEDIUM |
| `documents/CODEBASE_STATUS_MATRIX.md` | Update redis references | MEDIUM |
| `documents/CODEBASE_STATUS_MATRIX_AUTO.md` | Update redis references | MEDIUM |
| `documents/02_DATABASE_IMPLEMENTATION_PLAN.md` | Ensure seed data references Neon | MEDIUM |
| `documents/Fraud_Detection_System.txt` | REDIS_URL → VALKEY_URL | MEDIUM |
| `.gitleaks.toml` | redis-url pattern → valkey-url pattern | LOW |
| `scripts/audit/full_system_audit.py` | redis references → valkey (lines 107, 411, 1467, 1542, 1662, 1888-1894, 2358-2363, 2408-2409) | HIGH |
| `documents/action/generate_law_matrix.py` | redis references → valkey (lines 630, 957) | MEDIUM |
| `documents/action/AUDIT_RESULTS.json` | redis references → valkey (multiple lines) | MEDIUM |
| `scripts/system_trackers/feature_definitions.yaml` | `backend/db/seeds/` references → `backend/infrastructure/database/seed/` (lines 822, 1786, 2442, 2826, 3270, 3783) | LOW |

### 8.2 `backend/infrastructure/database/seed/_seed_constants.py` docstring fix

| Line | Current | Target |
|------|---------|--------|
| 7-9 | "The legacy JSON files in `seed_data/` are kept for backward compatibility with `scripts/seed_loader.py`" | "The legacy JSON files in `seed_data/` have been removed. Production seed data lives in Neon via the canonical module." |

---

## 9. CI/CD AND MONITORING FIXES

### 9.1 `.github/workflows/schema-audit.yml`

See Section 3.3.

### 9.2 `.github/workflows/e2e.yml`

See Section 3.4.

### 9.3 `monitoring/docker-compose.monitoring.yml`

See Section 3.5.

### 9.4 `monitoring/prometheus/prometheus.yml`

See Section 3.6.

---

## 10. VERIFICATION (post-implementation)

### 10.1 Grep Verification — Zero redis server references

```bash
# Should return ZERO results (no redis server references)
grep -r "redis:" --include="*.{yml,yaml,json,txt}" .
grep -r "redis://" --include="*.{py,yml,yaml,json,txt}" backend/ frontend/
grep -r "image: redis" --include="*.{yml,yaml}" .
grep -r "redis-cli" --include="*.{yml,yaml}" .
grep -r "redis:" --include="*.{yml,yaml}" .
```

### 10.2 Grep Verification — valkey references present

```bash
# Should return results for valkey
grep -r "valkey" --include="*.{py,yml,yaml,json,txt}" . | head -50
```

### 10.3 Requirements Verification

```bash
# Should return nothing (no redis package)
grep "redis==" backend/requirements.txt

# Should return valkey==8.0.1
grep "valkey" backend/requirements.txt

# Should return Pillow==12.2.0
grep "Pillow==" backend/requirements.txt
```

### 10.4 Docker Compose Verification

```bash
# Should return nothing
grep "image: redis" docker-compose*.yml monitoring/docker-compose*.yml .github/workflows/*.yml

# Should return valkey:9.0-alpine
grep "image: valkey" docker-compose*.yml monitoring/docker-compose*.yml .github/workflows/*.yml
```

### 10.5 Frontend Verification

```bash
# Should return "16.3.4"
grep '"next"' frontend/web_app/package.json
grep '"eslint-config-next"' frontend/web_app/package.json
```

### 10.6 Python Import Verification

```bash
# Should return ZERO results (no direct redis-py imports in domain code)
grep -r "import redis\|from redis" --include="*.py" backend/domains/

# Should return results for valkey imports
grep -r "import valkey\|from valkey" --include="*.py" backend/

# Should return ZERO results (no redis_client.py file)
find backend/ -name "redis_client.py"

# Should return valkey_client.py
find backend/ -name "valkey_client.py"
```

### 10.7 Seed Data Verification

```bash
# Should return only _README.md (no data files)
ls -la backend/infrastructure/database/seed_data/

# Should return seed files
ls -la backend/infrastructure/database/seed/

# Verify seed_data function exists and uses Neon
grep "def seed_data" backend/infrastructure/database/seed/_common.py
```

### 10.8 Architecture Test Verification

```bash
# Run architecture tests
cd backend && python -m pytest tests/architecture/test_valkey_migration.py -v
```

---

## 11. CHANGE SUMMARY TABLE

| Phase | File | Change Type | Priority | Status |
|-------|------|-------------|----------|--------|
| 1 | `backend/infrastructure/database/redis_client.py` | RENAME → valkey_client.py + fix content | CRITICAL | 🔴 Pending |
| 1 | All imports of `database.redis_client` | UPDATE import path | CRITICAL | 🔴 Pending |
| 1 | `backend/tests/architecture/test_valkey_migration.py` | Update test descriptions | MEDIUM | 🔴 Pending |
| 2 | `backend/requirements.txt` line 20 | `redis==8.0.1` → `valkey==8.0.1` | CRITICAL | 🔴 Pending |
| 2 | `backend/requirements.txt` line 19 | Comment: Redis → Valkey | LOW | 🔴 Pending |
| 3 | `docker-compose.prod.yml` lines 96-97 | Service name + image: redis → valkey | CRITICAL | 🔴 Pending |
| 3 | `.github/workflows/schema-audit.yml` | redis → valkey | HIGH | 🔴 Pending |
| 3 | `.github/workflows/e2e.yml` | redis → valkey | HIGH | 🔴 Pending |
| 3 | `monitoring/docker-compose.monitoring.yml` | redis → valkey | HIGH | 🔴 Pending |
| 3 | `monitoring/prometheus/prometheus.yml` | redis → valkey | MEDIUM | 🔴 Pending |
| 4 | `backend/config.py` | ✅ Already correct | — | ✅ Done |
| 5 | `backend/domains/security/services/fraud/fraud_detection_service.py:16` | `redis.exceptions` → `valkey.exceptions` | CRITICAL | 🔴 Pending |
| 5 | `backend/lifespan.py:367,372` | Import path + log message | HIGH | 🔴 Pending |
| 5 | 17 files importing `infrastructure.utils.redis_client` | INVESTIGATE + FIX | CRITICAL | 🔴 Pending |
| 6 | `backend/infrastructure/database/seed/_seed_constants.py` docstring | Remove JSON file reference | MEDIUM | 🔴 Pending |
| 6 | `backend/infrastructure/database/seed_data/` | ✅ Only _README.md | — | ✅ Done |
| 7 | R2 storage | ✅ Already correct | — | ✅ Done |
| 8 | Documentation files (11 files) | redis → valkey references | MEDIUM | 🔴 Pending |
| 9 | CI/CD + monitoring configs | redis → valkey | HIGH | 🔴 Pending |
| 10 | Verification | Run all grep + test checks | HIGH | 🔴 Pending |

---

## 12. EXECUTION ORDER

### Day 1 — Critical Path (unblocks build and startup)

1. **Phase 1:** Rename `redis_client.py` → `valkey_client.py` + fix content (Section 1)
2. **Phase 1:** Update all 4 import sites of `database.redis_client` (Section 1.3)
3. **Phase 2:** Fix `backend/requirements.txt` (Section 2.1)
4. **Phase 5:** Fix `fraud_detection_service.py` import (Section 5.2)
5. **Phase 5:** Fix `backend/lifespan.py` import (Section 5.4)

### Day 2 — Docker & CI (unblocks deployment)

6. **Phase 3:** Fix `docker-compose.prod.yml` (Section 3.2)
7. **Phase 3:** Fix `.github/workflows/schema-audit.yml` (Section 3.3)
8. **Phase 3:** Fix `.github/workflows/e2e.yml` (Section 3.4)
9. **Phase 3:** Fix `monitoring/docker-compose.monitoring.yml` (Section 3.5)
10. **Phase 3:** Fix `monitoring/prometheus/prometheus.yml` (Section 3.6)

### Day 3 — Code Imports & Investigation

11. **Phase 5:** Investigate `infrastructure.utils.redis_client` imports (Section 5.3)
12. **Phase 5:** Fix all 17 files importing from `infrastructure.utils.redis_client`
13. **Phase 5:** Update `backend/tests/architecture/test_valkey_migration.py` (Section 1.4)

### Day 4 — Seed Data & Documentation

14. **Phase 6:** Fix `_seed_constants.py` docstring (Section 6.3)
15. **Phase 8:** Update all documentation files (Section 8.1)
16. **Phase 6:** Verify seed data flow (Section 6.2)

### Day 5 — Final Verification

17. **Phase 10:** Run all verification checks (Section 10.1–10.8)
18. **Phase 10:** Run architecture tests
19. **Phase 10:** Run full test suite to confirm no regressions

---

## 13. TECH VERSION LOCK (final — do not drift)

| Component | Version | Status |
|-----------|---------|--------|
| PostgreSQL (Neon) | 18 | ✅ Locked |
| Valkey | 9.0-alpine (dev), 9.0 (prod) | ✅ Locked |
| R2 (S3-compatible) | Current | ✅ Locked |
| Next.js | 16.3.4 | ✅ Locked |
| FastAPI | 0.115.2 | ✅ Locked |
| SQLAlchemy | 2.0.51 | ✅ Locked |
| valkey-py | 8.0.1 | ✅ Locked (replaces redis-py) |
| Pillow | 12.2.0 | ✅ Locked (fixes non-existent 12.3.0) |
| Celery | 5.4.0 | ✅ Locked |
| Python | 3.11 | ✅ Locked (Dockerfile.prod base image) |

---

## 14. RISK ASSESSMENT

| Risk | Impact | Mitigation |
|------|--------|------------|
| `infrastructure.utils.redis_client` imports break after rename | HIGH — 17 files affected | Investigate before renaming; create shim if needed |
| `fraud_detection_service.py` imports `redis.exceptions` | HIGH — runtime failure | Change to `valkey.exceptions` (API-compatible) |
| `backend/infrastructure/database/valkey_client.py` content is currently broken | HIGH — mixed redis/valkey references | Fix all lines per Section 1.2 before renaming |
| Tests reference old import paths | MEDIUM — test failures | Update test imports per Section 1.3 |
| Documentation drift | LOW — cosmetic | Update per Section 8.1 |
| `SEED_DATA_ON_STARTUP=true` in production | HIGH — security risk | Document that production must set `false` |

---

## 15. BACKWARD COMPATIBILITY STRATEGY

To avoid breaking existing code during migration, maintain these shims:

1. **`backend/infrastructure/valkey/client.py`** already has:
   - `redis_client = valkey_client` (line 115)
   - `get_redis = valkey_client` (line 117)
   - `_NoOpRedis = _NoOpValkey` (line 119)

2. **`backend/infrastructure/database/valkey_client.py`** (renamed) should maintain:
   - `get_redis = valkey_client` (line 102)
   - `redis_client` function name stays (it's a client function, name is fine)

3. **`backend/infrastructure/redis/`** package — if it exists as a shim, keep it working during transition period.

4. **Environment variables:**
   - `VALKEY_URL` is canonical
   - `REDIS_URL` is backward-compat alias (already in `.env.example` line 21)

5. **Volume names:**
   - `valkey_data` is canonical
   - `redis_data` should be removed after migration

---

*End of Plan*
