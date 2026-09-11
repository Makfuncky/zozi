# TECH STANDARDIZATION IMPLEMENTATION PLAN
## ZOZI Marketplace — Neon 18 + Valkey + R2 + Next.js 16.3.4

**Date:** 2026-09-11
**Goal:** Eliminate all Redis references, standardize on Valkey, ensure all seed data lives in Neon (not local files), confirm R2 for object storage, lock Next.js 16.3.4.
**Constraint:** Do NOT drift from mentioned tech versions.

---

## TARGET STACK (locked)

| Layer | Technology | Version | Evidence |
|-------|-----------|---------|----------|
| Database | Neon PostgreSQL | 18 | `docker-compose.yml:4` (postgres:18-alpine) |
| Cache | Valkey | 9.0-alpine (dev), 9.0 (prod) | `docker-compose.yml:21` |
| Object Storage | Cloudflare R2 | S3-compatible | `providers/storage/r2_client.py` |
| Frontend | Next.js | 16.3.4 | `frontend/web_app/package.json:30` |
| Backend | FastAPI | 0.115.2 | `backend/requirements.txt:8` |
| ORM | SQLAlchemy | 2.0.51 | `backend/requirements.txt:14` |
| Cache Client | valkey-py | 8.0.1 | TO BE ADDED (replaces redis-py) |

---

## PHASE A: Dependency Manifest Fixes

### A.1 `backend/requirements.txt`

| Line | Current | Target | Reason |
|------|---------|--------|--------|
| 20 | `redis==8.0.1` | `valkey==8.0.1` | Code imports `valkey`, not `redis` server client |
| 51 | `Pillow==12.3.0` | `Pillow==12.2.0` | 12.3.0 does not exist on PyPI |

### A.2 `backend/tests/architecture/test_manifest_drift.py:57`

| Line | Current | Target |
|------|---------|--------|
| 57 | `assert not line.strip().startswith("Pillow==12.3.0")` | `assert not line.strip().startswith("Pillow==12.3.0")` (keep — still validates) |

### A.3 `frontend/web_app/package.json`

| Line | Current | Target | Status |
|------|---------|--------|--------|
| 30 | `"next": "16.3.4"` | `"next": "16.3.4"` | ✅ Already correct |
| 51 | `"eslint-config-next": "16.3.4"` | `"eslint-config-next": "16.3.4"` | ✅ Already correct |

### A.4 `frontend/web_app/package-lock.json`

- Verify lockfile resolves next@16.3.4 (not 16.1.6)
- Run `npm install` in `frontend/web_app/` to regenerate if needed

---

## PHASE B: Docker Compose Fixes (redis → valkey)

### B.1 `docker-compose.yml` — ALREADY CORRECT ✅

- Line 20-25: `valkey: image: valkey:9.0-alpine` ✅
- Line 34: `VALKEY_URL=valkey://valkey:6379` ✅
- Line 39-40: `CELERY_BROKER_URL=valkey://valkey:6379/1` ✅
- Line 173: `valkey_data` volume ✅

### B.2 `docker-compose.prod.yml` — NEEDS FIX

| Line | Current | Target |
|------|---------|--------|
| 29 | `REDIS_URL=redis://redis:6379` | `REDIS_URL=valkey://valkey:6379` |
| 75 | `REDIS_URL=redis://redis:6379` | `REDIS_URL=valkey://valkey:6379` |
| 96-104 | `redis:` service (image: redis:7-alpine) | `valkey:` service (image: valkey:9.0-alpine) |
| 112 | `redis_data` volume | `valkey_data` volume |

### B.3 `.github/workflows/schema-audit.yml`

| Line | Current | Target |
|------|---------|--------|
| 43-44 | `redis:` service (image: redis:7-alpine) | `valkey:` service (image: valkey:9.0-alpine) |
| 48 | `--health-cmd "redis-cli ping"` | `--health-cmd "valkey-cli ping"` |

### B.4 `.github/workflows/e2e.yml`

| Line | Current | Target |
|------|---------|--------|
| 52-53 | `redis:` service (image: redis:8-alpine) | `valkey:` service (image: valkey:9.0-alpine) |
| 57 | `--health-cmd "redis-cli ping"` | `--health-cmd "valkey-cli ping"` |

### B.5 `monitoring/docker-compose.monitoring.yml`

| Line | Current | Target |
|------|---------|--------|
| 102 | `REDIS_URL=redis://sentry-redis:6379/0` | `REDIS_URL=valkey://sentry-redis:6379/0` |
| 113 | `sentry-redis` volume name | `sentry-valkey` |
| 131-132 | `sentry-redis:` service (image: redis:7-alpine) | `sentry-valkey:` service (image: valkey:9.0-alpine) |

### B.6 `monitoring/prometheus/prometheus.yml`

| Line | Current | Target |
|------|---------|--------|
| 35 | `job_name: redis` | `job_name: valkey` |
| 39 | `redis-exporter:9121` | `valkey-exporter:9121` |
| 41 | `app: zozi-redis` | `app: zozi-valkey` |

---

## PHASE C: Backend Config Fixes

### C.1 `backend/config.py`

| Line | Current | Target |
|------|---------|--------|
| 74 | `"redis_url": "redis://localhost:6379"` | `"valkey_url": "valkey://localhost:6379"` |
| 90 | `"celery_broker_url": os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1")` | `"celery_broker_url": os.getenv("CELERY_BROKER_URL", "valkey://localhost:6379/1")` |
| 91 | `"celery_result_backend": os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2")` | `"celery_result_backend": os.getenv("CELERY_RESULT_BACKEND", "valkey://localhost:6379/2")` |

**Note:** Any code referencing `settings.redis_url` must be updated to `settings.valkey_url`.

---

## PHASE D: Backend Code Import Fixes (redis-py → valkey-py)

### D.1 Primary Client: `backend/infrastructure/database/redis_client.py`

This file is imported by 30+ modules. Currently uses `import redis` (redis-py package).

**Change:** Replace `import redis` with `import valkey` throughout this file.
- All class names, method calls remain the same (valkey-py is API-compatible with redis-py)
- The `_NoOpRedis` class → rename to `_NoOpValkey`
- File path stays the same (for backward compat with imports)

### D.2 Secondary Client: `backend/infrastructure/valkey/client.py`

Already uses `import valkey`. ✅ No change needed.

### D.3 All Python files that import redis directly

Search pattern: `import redis` or `from redis` in `.py` files under `backend/`

Files to update (replace `import redis` → `import valkey`, `from redis` → `from valkey`):
- `backend/infrastructure/database/redis_client.py`
- Any other file with direct redis import

### D.4 Variable/parameter naming

Files that use `redis_client`, `_get_redis`, `redis_url` in function/variable names:
- These are internal names — can keep as-is for API compatibility, but all server references must be valkey
- `redis_client` function name → keep (it's a client function, name is fine)
- `_get_redis` function name → keep (internal helper)
- `REDIS_URL` env var → change to `VALKEY_URL`
- `redis_data` volume → change to `valkey_data`

---

## PHASE E: Seed Data Migration (Local Files → Neon)

### E.1 Current State

- `backend/infrastructure/database/seed_data/` — local seed files (if exists)
- `ARCHITECTURE_DIAGRAM.md` already states: "Seed data is directly inserted into Neon PostgreSQL 18 instead of being stored in local file fixtures"
- The old local seed-file system should already be removed per ARCHITECTURE_DIAGRAM.md

### E.2 Actions

1. Verify `backend/infrastructure/database/seed_data/` is removed or empty
2. If seed data files exist, they should be converted to SQL migration scripts
3. All seed/reference data must be inserted via Neon PostgreSQL migrations
4. Update any code that reads from local seed files to instead query Neon tables

### E.3 Files to check

- `backend/infrastructure/database/seed_data/` — verify removal
- Any Python file that reads seed data from local files
- `backend/tests/` — any test that depends on local seed data

---

## PHASE F: Object Storage (R2 Confirmation)

### F.1 Current State — Already Correct ✅

- `backend/providers/storage/r2_client.py` — R2 client implementation
- `backend/providers/storage/s3_client.py` — S3 client (alias to R2)
- `backend/infrastructure/storage/storage.py` — R2Storage class
- `backend/tests/infrastructure/test_storage_r2.py` — R2 tests
- All object storage references already use R2/S3-compatible

### F.2 Actions

- No changes needed for R2 — already the standard
- Verify no local storage references remain in production paths
- Confirm `STORAGE_BACKEND=s3` in docker-compose.prod.yml uses R2 endpoint

---

## PHASE G: Documentation Updates

### G.1 Files to update

| File | Changes |
|------|---------|
| `documents/BACKUP_STRATEGY.md` | redis:7-alpine → valkey:9.0-alpine, redis_data → valkey_data |
| `documents/ARCHITECTURE_DIAGRAM.md` | Ensure all references are valkey (not redis) |
| `documents/CODEBASE_STATUS_MATRIX.md` | Update redis references |
| `documents/CODEBASE_STATUS_MATRIX_AUTO.md` | Update redis references |
| `documents/02_DATABASE_IMPLEMENTATION_PLAN.md` | Ensure seed data references Neon |
| `.gitleaks.toml` | redis-url pattern → valkey-url pattern (optional, security scan) |
| `documents/Fraud_Detection_System.txt` | REDIS_URL → VALKEY_URL |
| `update_diagram.py` | Already has valkey replacement logic ✅ |

### G.2 Audit scripts

| File | Changes |
|------|---------|
| `scripts/audit/full_system_audit.py` | redis references → valkey (lines 107, 411, 1467, 1542, 1662, 1888-1894, 2358-2363, 2408-2409) |
| `documents/action/generate_law_matrix.py` | redis references → valkey (lines 630, 957) |
| `documents/action/AUDIT_RESULTS.json` | redis references → valkey (multiple lines) |

---

## PHASE H: Verification

### H.1 Grep Verification

After all changes, run:
```bash
# Should return ZERO results (no redis server references)
grep -r "redis:" --include="*.{yml,yaml,json,txt}" .
grep -r "redis://" --include="*.{py,yml,yaml,json,txt}" backend/ frontend/
grep -r "image: redis" --include="*.{yml,yaml}" .
grep -r "redis-cli" --include="*.{yml,yaml}" .

# Should return results only for valkey
grep -r "valkey" --include="*.{py,yml,yaml,json,txt}" . | head -50
```

### H.2 Requirements Verification

```bash
# Verify no redis package in requirements
grep "redis==" backend/requirements.txt  # Should return nothing
grep "valkey" backend/requirements.txt     # Should return valkey==8.0.1

# Verify Pillow version
grep "Pillow==" backend/requirements.txt   # Should return Pillow==12.2.0
```

### H.3 Docker Compose Verification

```bash
# Verify all compose files use valkey
grep "image: redis" docker-compose*.yml monitoring/docker-compose*.yml .github/workflows/*.yml  # Should return nothing
grep "image: valkey" docker-compose*.yml monitoring/docker-compose*.yml .github/workflows/*.yml  # Should return valkey:9.0-alpine
```

### H.4 Frontend Verification

```bash
# Verify Next.js version
grep '"next"' frontend/web_app/package.json  # Should return "16.3.4"
grep '"eslint-config-next"' frontend/web_app/package.json  # Should return "16.3.4"
```

---

## CHANGE SUMMARY TABLE

| Phase | File | Change Type | Priority |
|-------|------|-------------|----------|
| A | `backend/requirements.txt` | redis→valkey, Pillow fix | CRITICAL |
| B | `docker-compose.prod.yml` | redis→valkey (service, env vars, volumes) | CRITICAL |
| B | `.github/workflows/schema-audit.yml` | redis→valkey | HIGH |
| B | `.github/workflows/e2e.yml` | redis→valkey | HIGH |
| B | `monitoring/docker-compose.monitoring.yml` | redis→valkey | HIGH |
| B | `monitoring/prometheus/prometheus.yml` | redis→valkey | MEDIUM |
| C | `backend/config.py` | redis_url→valkey_url, URLs | CRITICAL |
| D | `backend/infrastructure/database/redis_client.py` | import redis→import valkey | CRITICAL |
| D | All Python files with `import redis` | import redis→import valkey | CRITICAL |
| E | `backend/infrastructure/database/seed_data/` | Remove if exists | HIGH |
| G | Documentation files | redis→valkey references | MEDIUM |
| H | Verification | Grep checks | HIGH |

---

## EXECUTION ORDER

1. **Immediate (Day 1):** Phase A (requirements.txt) — unblocks installation
2. **Immediate (Day 1):** Phase C (config.py) — unblocks startup
3. **Day 2:** Phase B (docker-compose files) — unblocks deployment
4. **Day 3:** Phase D (code imports) — unblocks runtime
5. **Day 4:** Phase E (seed data) — ensures data consistency
6. **Day 5:** Phase F (R2 verification) — confirm no changes needed
7. **Day 5:** Phase G (docs) — align documentation
8. **Day 6:** Phase H (verification) — full grep validation

---

## TECH VERSION LOCK

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
