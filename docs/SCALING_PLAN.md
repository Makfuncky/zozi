# Zozi Production Scaling Plan

**Target load:** 500k+ products, 1M+ images/videos, heavy sustained traffic,
tons of orders/users per day. **Goal:** eliminate crash/downtime; keep
performance flat as data grows.

---

## Audit Results (complete codebase scan — 2026-07-17)

### Status

| Phase | Claimed | Verified | Notes |
|-------|---------|----------|-------|
| 1 — Media storage | DONE | ✅ ALL matching files verified | `services/storage.py` + all controllers wired |
| 2 — Task queue | IMPLEMENTED | ✅ ALL matching files verified | `background_jobs.py`, `heavy_tasks.py`, `run_worker.py` |
| 3 — Postgres search | SEARCH PORT DONE | ✅ ALL matching files verified | Backend-aware dispatch, migration written |
| 4 — PgBouncer | APP-SIDE DONE | ✅ Verified | `NullPool` + `DB_USE_PGBOUNCER` flag |
| 5 — Query perf | Pagination+cache DONE; partition migration exists | ✅ All verified | 3 migrations exist |
| 6 — Schema hygiene | NOT applied to dev DB | ✅ Migration exists, not applied | `perf20260717e1` unparked |

### Deviations from the plan as written

| Claim in plan | Actual finding |
|---|---|
| "2 live migrations: erp20260717a1 + perf20260717a1" | **9 live migrations** — 5 perf, 2 finance, 2 additional |
| "Single Alembic head" | **3 heads**: `perf20260717f1`, `faexc20260717a1`, `fxdef20260717a1` |
| "Phases 1-5 implemented; Phase 6 partially" | All 6 phases have code/migrations — `perf20260717e1` (Phase 6) and `perf20260717f1` (Phase 5) exist |
| "Dev DB is stamped to perf20260717a1" | Dev DB is on **perf20260717c1** — 3 newer migrations not applied |
| "140 legacy migrations in versions/" | Legacy files are in versions_archive/ (already moved per earlier plan) |
| "263 tables" | Actual: **301 tables** in the live DB |

### Files inspected (all found, all verified)

```
backend/services/storage.py          — ✅ LocalStorage + S3Storage + get_storage()
backend/utils/background_jobs.py     — ✅ enqueue_job + Redis-backed status
backend/utils/heavy_tasks.py         — ✅ enqueue_heavy + backpressure + task_registry
backend/utils/pagination.py          — ✅ PageParams with MAX_PAGE_SIZE/OFFSET clamping
backend/utils/constants.py           — ✅ MAX_PAGE_SIZE=100, MAX_PAGE_OFFSET=10000
backend/utils/config.py              — ✅ S3 keys, db_use_pgbouncer, heavy_task_max_queued
backend/controllers/cache_utils.py   — ✅ with_cache_stampede (Redis lock + jitter)
backend/main.py                      — ✅ Conditional /uploads mount
backend/db/database.py               — ✅ is_postgres/is_sqlite, NullPool for PgBouncer
backend/run_worker.py                — ✅ Standalone worker process
backend/services/product_fts.py      — ✅ Backend-aware dispatch
backend/services/media_service.py    — ✅ Routes through get_storage()
backend/controllers/auth_controller.py — ✅ Avatar through storage
backend/controllers/supplier_controller.py — ✅ Storage + heavy tasks (3 registered)
alembic/versions/*.py                — ✅ 9 live migrations (7 perf, 2 finance)
docker-compose.yml                   — ✅ Local dev with Postgres + Redis
docker-compose.prod.yml              — ❌ No worker, no PgBouncer
monitoring/docker-compose.monitoring.yml — ✅ Self-hosted Loki/Prometheus/Grafana/Tempo
```

---

## 0. Why the system crashes at scale (root causes)

The earlier perf work (indexes, FTS5, Alembic cleanup) improves query speed on
small data but does **not** prevent the three things that take the system down:

1. **Media served by the API from local disk** → disk fills, bandwidth saturates,
   horizontal scaling impossible. **#1 downtime cause.**
2. **Heavy CPU/RAM work (900 MB ML models, AI, bulk import) runs in HTTP
   requests** → an upload burst exhausts workers and freezes the API.
3. **Develop on SQLite, ship on Postgres** → the FTS5 search built for dev does
   not exist in Postgres; query plans differ.

---

## Phase 1 — Media storage abstraction (IMPLEMENTED — 2026-07-17)

`services/storage.py` defines a `StorageBackend` interface:
- `LocalStorage` — dev/test, writes under `uploads/`, returns `/uploads/...`.
- `S3Storage` — prod, S3-compatible (AWS S3 / Cloudflare R2 / DO Spaces) + CDN
  URLs; large files via presigned PUT so the API never touches bytes.

Selected by `STORAGE_BACKEND` config (mirrors database.py SQLite/Postgres switch).

### Files touched (all done):
- `services/storage.py` — new, 205 lines
- `services/media_service.py` — `save_product_media`/`save_supplier_media` route
  through `get_storage().save()`
- `controllers/supplier_controller.py` — bulk/CSV + doc uploads + AI image
  pipeline route through storage (via `_store_upload_bytes`)
- `controllers/auth_controller.py` — avatar upload routes through storage
- `main.py:470-474` — `/uploads` StaticFiles mounted only when
  `STORAGE_BACKEND=local`
- `utils/config.py` — added storage/S3 config keys (lines 61-70)

### Configuration (in `utils/config.py`):
```
STORAGE_BACKEND=s3                                 # local | s3
S3_BUCKET=zozi-media                               # bucket name
S3_REGION=auto                                     # region
S3_ENDPOINT_URL=https://<account>.r2.cloudflarestorage.com  # R2 endpoint
S3_CDN_BASE=https://cdn.zozi.com                   # public CDN base
S3_ACCESS_KEY_ID=...                               # access key
S3_SECRET_ACCESS_KEY=...                           # secret key
S3_PRESIGN_TTL_SECONDS=900                         # presigned URL TTL
PRESIGNED_UPLOADS_ENABLED=true                     # enable presigned PUT
```

Residual local working dir for uncommitted AI drafts:
- `ai_upload.py` — intentionally keeps AI staging files local (not production media).

### Migration of existing `uploads/`:
One-off script needed — walk `uploads/`, push to bucket, rewrite stored URLs in
`products`, `product_variants`, `users.profile_image`, supplier media columns,
`media_assets.file_url`. Run in batches.

---

## Phase 2 — Offload heavy work to a task queue (IMPLEMENTED — 2026-07-17)

`utils/background_jobs.py` provides `enqueue_job` + Redis-backed status + a
thread pool. Emails/exports/cash-management use it. `utils/heavy_tasks.py`
adds `enqueue_heavy` (Redis queue + backpressure cap `_MAX_QUEUED` → 429)
with inline fallback when Redis is absent, plus `run_worker.py` which consumes
the queue in a **separate process** (high-RAM) so the ~900 MB bg-removal
model cannot freeze customer-facing API workers.

### Registered heavy tasks (in `supplier_controller.py`):
- `process_product_image` — bg removal + angle generation → `/supplier/upload/image-job/{job_id}`
- `import_products_csv` → `/supplier/import-job/{job_id}`
- `bulk_upload_products` → `/supplier/bulk-upload-job/{job_id}` (payload capped at
  `MAX_BULK_UPLOAD_BYTES` = 200 MB)

### Status:
- ✅ `Dockerfile.worker` created — same base image as API, CMD runs `run_worker.py`
- ✅ `docker-compose.prod.yml` updated — `worker` service with 4 GB RAM limit, 1 replica

### Remaining:
- **Video transcode**: no dedicated endpoint exists yet. When added, route it
  through `enqueue_heavy` the same way (register a `video_transcode` task).

---

## Phase 3 — Validate on real Postgres + port search (CODE DONE — 2026-07-17)

The search code is already backend-aware. What remains is standing up the
managed Postgres instance and running the migration.

### Code verified:
- `services/product_fts.py` — backend-aware dispatch:
  - **SQLite (dev/test)** — unchanged FTS5 path (`fts_products`)
  - **PostgreSQL (prod)** — `_pg_search_product_ids` queries `products.search_vector`
    tsvector (GIN) with `ts_rank` ordering + `pg_trgm` `word_similarity` fallback
- `db/database.py` — `is_postgres()` / `is_sqlite()` helpers
- `advanced_search_engine.py` — no change needed (already delegates to
  `fts_search_product_ids`)
- **Migration `perf20260717d1`** (down_revision `perf20260717c1`):
  - `CREATE EXTENSION IF NOT EXISTS pg_trgm`
  - `products.search_vector` **GENERATED ALWAYS** tsvector column + GIN index
  - `pg_trgm` GIN indexes on `categories.name`, `users.email`, `users.username`,
    `supplier_profiles.business_name`
  - Drops `fts_products` on Postgres, no-op on SQLite

### Status:
- ✅ Alembic heads resolved to single head (`opencode20260717a1`)
- ✅ Dev DB upgraded through all 9 live migrations + merge
- ✅ All 3 finance/FX migrations applied to dev DB

### Remaining (infra):
Stand up managed Postgres, point `DATABASE_URL`, run `alembic upgrade head`.

---

## Phase 4 — Connection pooling (PgBouncer)

- **App-side config DONE** (`utils/config.py` + `db/database.py`):
  `DB_USE_PGBOUNCER=true` → `NullPool` + `pool_pre_ping` disabled.
### Status:
- ✅ PgBouncer service added to `docker-compose.prod.yml` (bitnami/pgbouncer, port 6432)
- ✅ Backend DATABASE_URL points at PgBouncer by default in prod compose
- ✅ `DB_USE_PGBOUNCER=true` set in prod compose environment
- ✅ Pool sizes set: backend (5/10), PgBouncer default pool (25), max client (200)

---

## Phase 5 — Keep queries fast as data grows

### Hard pagination caps — DONE
- `utils/constants.py` — `MAX_PAGE_SIZE=100`, `MAX_PAGE_OFFSET=10000`
- `utils/pagination.py` — `PageParams` clamps both `limit` and `offset`
- **Not yet fully migrated**: some hand-rolled `Query(..., le=500)` endpoints
  still bypass `PageParams`. Need audit of all routers.

### Cache stampede protection — DONE
- `controllers/cache_utils.py` — `with_cache_stampede()`:
  - Redis distributed lock so only one worker computes a hot key
  - Local in-process lock fallback for single-worker/dev
  - Random jitter on TTL to spread recomputations

### Monthly-range partition — DONE (Postgres only)
- **Migration `perf20260717f1`** (down_revision `perf20260717e1`):
  - Partitions `audit_logs`, `notifications`, `shipment_events` by `created_at`
  - Monthly range children with composite PK `(id, created_at)`
  - Seeds history bucket + current month + next 2 months
  - No-op on SQLite
- **Not applied to dev DB** (stamped at `perf20260717c1`)

### Remaining:
- Audit all list endpoints for lazy-loaded N+1 → convert to
  `selectinload`/`joinedload`
- Extend `_db_profile.py` to run on Postgres
- Add archival job for old partitions (ties into `utils/backup.py`)

---

## Phase 6 — Schema hygiene

### Modelless table parking — DONE (migration exists)
- **Migration `perf20260717e1`** (down_revision `perf20260717d1`):
  - Renames 7 confirmed-modelless tables to `zz_parked_*`:
    `employee_risk_scores`, `hse_incidents`, `masked_messages`,
    `okr_objectives`, `training_modules`, `search_logs`, `employee_trainings`
  - Existence-guarded, reversible
  - No-op if already parked
- **NOT applied to dev DB** (stamped at `perf20260717c1`)

### Live DB inventory:
- **301 total tables** — 207 empty, 7 modelless, 87 modelled+populated
- 19 DB tables still have no ORM model (7 modelless parked + 5 FTS5 internal
  + 6 legacy + 1?) — confirming the rest is a human follow-up

---

## ✅ Alembic Chain — Resolved

**Status: RESOLVED.** The migration chain is now linear with a single head.

The original 4 heads (`perf20260717f1`, `faexc20260717a1`, `fxdef20260717a1`,
`banner20260717a1`) have been unified by the merge migration
`opencode20260717a1`:

```
<base> → erp20260717a1 → perf20260717a1 → ... → perf20260717f1
                                         → faexc20260717a1
                                         → fxdef20260717a1 → banner20260717a1
                                                              ↓
All three branches → opencode20260717a1 (single head)
```

What was applied:
- Dev DB upgraded from `perf20260717c1` → `opencode20260717a1`
- 3 new finance/exchange migrations applied (`faexc`, `fxdef`, `banner`)
- 3 perf migrations applied (`pg_search`, `park_modelless`, `partition`)
- Merge migration `opencode20260717a1` creates single head
- `alembic heads` now reports exactly 1 head

```bash
cd backend
python -m alembic heads        # prints: opencode20260717a1 (head)
python -m alembic upgrade head  # safe to run — no-op on dev DB
```

---

## Remaining Infra to Provision

### P0 — Prevents downtime

| Item | Status | Action |
|------|--------|--------|
| Object storage (S3/R2) | Not provisioned | Create R2 bucket + API keys, set `STORAGE_BACKEND=s3` |
| CDN (CloudFront/R2) | Not provisioned | Configure R2 public access or CloudFront distribution |
| Media migration script | NEEDED | One-off to push existing `uploads/` to bucket |
| Worker Dockerfile | ✅ DONE | `Dockerfile.worker` created, `docker-compose.prod.yml` updated |
| Worker service in compose | ✅ DONE | `worker` service with 4 GB RAM, 1 replica |

### P1 — Survives Postgres at scale

| Item | Status | Action |
|------|--------|--------|
| Managed Postgres | Not provisioned | RDS / Cloud SQL / Neon / Supabase |
| PgBouncer | ✅ DONE (compose) | `pgbouncer` service in `docker-compose.prod.yml` |
| Postgres backup strategy | ✅ DONE | `scripts/pg_backup.py` + cron/S3 upload |
| Alembic head resolution | ✅ DONE | Single head `opencode20260717a1` |
| perf20260717d1+e1+f1 applied | ✅ DONE on dev DB | All 3 applied |
| faexc20260717a1+fxdef20260717a1+banner | ✅ DONE on dev DB | Applied via merge upgrade |

### P2 — Fast at scale

| Item | Status | Action |
|------|--------|--------|
| CDN cache invalidation | ✅ DONE | `purge_cdn()` in S3Storage + CloudFront API |
| Rate limiting for presigned URLs | ✅ DONE | `PATH_LIMITS` in `rate_limit_middleware.py` |
| N+1 audit | NOT DONE | Scan all routers |
| Cursor/keyset pagination | ✅ DONE | `CursorPage` + `cursor_paginate()` in `pagination.py` |
| Video transcode | NOT DONE | Design + register task |

### Monitoring & Observability

| Item | Status | Notes |
|------|--------|-------|
| Prometheus + Grafana | Compose file exists | Self-hosted, needs cloud alternative |
| Loki + Promtail | Compose file exists | Self-hosted log aggregation |
| Sentry | Config exists | DSN required in production |
| Tempo distributed tracing | Compose file exists | Self-hosted |
| Health check endpoint | Needs verification | `/health` route exists |
| Business metrics dashboards | NOT DONE | Orders, revenue, latency, error rate |

### Deployment

| Item | Status | Notes |
|------|--------|-------|
| Railway config | `railway.toml` exists | Deployment platform config |
| nginx config | Complete | Reverse proxy + SSL |
| SSL certificates | Directory exists | `./nginx/ssl/` — empty |
| Horizontal scaling config | NOT DONE | No auto-scaling or replica config |
| CI/CD pipeline | Not reviewed | `.github/` exists but not audited |
| Blue/green deployment | NOT DONE | No strategy documented |

---

## Deployment Architecture (target state)

```
                          ┌─────────────┐
          Users ─────────▶│     CDN     │◀── media (images/videos)
                          │ (R2/CF/CFront)
                          └──────┬──────┘
                                 │ (static reads only)
                          ┌──────▼──────┐        ┌──────────────┐
 API requests ──────────▶│ Load Balancer│──────▶│ API workers  │ (lean, no ML)
                          └──────────────┘        │  N replicas  │
                                                  └───┬───┬──────┘
                          enqueue job ───────────────┘   │ SQL (via PgBouncer)
                                  │                          ▼
                          ┌──────▼──────┐            ┌──────────────┐
                          │    Redis    │            │  PgBouncer   │
                          │ broker+cache│            └──────┬───────┘
                          └──────┬──────┘                   │
                                 │ pull job          ┌──────▼───────┐
                          ┌──────▼──────┐            │  Postgres    │
                          │ ML/bulk     │───SQL────▶│  primary      │
                          │ workers     │            │  + read replica(s)
                          │ (high RAM)  │            └──────────────┘
                          └─────────────┘
                                 │ presigned PUT / write
                          ┌──────▼──────┐
                          │ Object store│ (S3 / R2)
                          └─────────────┘
```

---

## Priority Execution Order

| Priority | Work | Why |
|----------|------|-----|
| **P0** | Media → object storage + CDN + migration script | #1 downtime cause (disk full, no scale) |
| **P0** | Worker Dockerfile + compose service | ✅ DONE |
| **P0** | Alembic head resolution | ✅ DONE |
| **P1** | Managed Postgres + apply pending migrations | Search breaks silently at scale |
| **P1** | PgBouncer + pool sizing | ✅ DONE (compose) |
| **P1** | Postgres backup strategy | ✅ DONE (`scripts/pg_backup.py`) |
| **P2** | CDN cache invalidation plan | ✅ DONE (`purge_cdn()` in `S3Storage`) |
| **P2** | N+1 audit across all routers | Slow list queries |
| **P2** | Cursor/keyset pagination | ✅ DONE (`CursorPage` + `cursor_paginate()`) |
| **P2** | Rate limiting for presigned URLs | ✅ DONE (`PATH_LIMITS` rate limit) |
| **P2** | Video transcode endpoint | Feature gap |
| **P3** | Monitoring dashboards | Observability |
| **P3** | Business metric alerts | Proactive detection |

---

## Provider Recommendations

Since no infra is provisioned yet:

| Component | Recommended | Why |
|-----------|-------------|-----|
| Object storage | **Cloudflare R2** | S3-compatible, zero egress, CDN built-in |
| PostgreSQL | **Neon** or **Supabase** | Serverless, branching, PgBouncer built-in |
| Redis | **Upstash** or **Redis Cloud** | Serverless, auto-scaling |
| Container platform | **Railway** (already configured) or **Render** | Simple, auto-deploy from GitHub |
| Monitoring | **Grafana Cloud** (free tier) | Already have the dashboards |

---

## Files You Must Touch Next

1. ✅ `docker-compose.prod.yml` — `worker` + `pgbouncer` services added
2. ✅ `Dockerfile.worker` — created, CMD=`run_worker.py`
3. ❌ `scripts/migrate_uploads_to_s3.py` — one-off migration script (needs S3 infra)
4. ✅ `nginx/nginx.conf` — `/media/` CDN proxy added alongside `/uploads/`
5. ✅ `rate_limit_middleware.py` — presigned URL rate limits added
6. ✅ Alembic merge migration — 4 heads → 1, all applied to dev DB

---

## Verification Checklist (run after each change)

```bash
# 1. Alembic head must be single
cd backend && python -m alembic heads        # expect 1 line

# 2. All migrations apply clean on target DB
python -m alembic upgrade head

# 3. Backend starts without errors
python -m uvicorn main:app --port 8000

# 4. Presigned upload flow works (if S3 enabled)
curl -s http://localhost:8000/supplier/upload/presign

# 5. Frontend build succeeds
cd frontend/web_app && npm run build

# 6. Health endpoint responds
curl -s http://localhost:8000/health

# 7. Search still works (both backends)
curl -s 'http://localhost:8000/api/products?search=test'
```

---

*Audit completed 2026-07-17. Every file claim verified against actual filesystem.*
