# Zozi Production Scaling Plan — Implementation Ready

**Target load:** 500k+ products, 1M+ media, heavy sustained traffic.  
**Goal:** eliminate crash/downtime causes; keep performance flat as data grows.  
**Status:** P0-A storage abstraction is complete. Remaining work is task-queue offloading, Postgres validation/partitioning, and hardening.

---

## Current State (Verified)

| Component | Status |
|---|---|
| `services/storage.py` — `LocalStorage` + `S3Storage` with `save/read/url/delete/list/presign_put` | ✅ Done |
| `routers/upload.py` — `POST /presign` endpoint | ✅ Done |
| `main.py` — conditional `/uploads` StaticFiles mount only when `STORAGE_BACKEND=local` | ✅ Done |
| Media writes routed through storage in `auth_controller`, `banner_controller`, `products_controller`, `logistics_partner_controller`, `supplier_document_controller`, `supplier_controller`, `batch_upload`, `supplier_orders`, `chat_system`, `video_service` | ✅ Done |
| Postgres search indexes migration `c0f3f1817791` (pg_trgm GIN + tsvector GIN) | ✅ Done |
| Postgres-native FTS in `search_controller.py` (`_database_supports_postgres_fts`, `_build_postgres_search_document`, `_build_postgres_tsquery`) | ✅ Done |
| `background_jobs.py` — Redis-backed jobs, per-kind concurrency governors, backpressure, ML worker pools | ✅ Done |
| `pagination.py` — `safe_page`, `paginated_query`, `paginated_response` with `MAX_PAGE_SIZE=100` | ✅ Done |
| N+1 elimination with `selectinload`/`joinedload` across controllers | ✅ Partial |
| Cache utils — versioned cache + stampede protection | ✅ Done |
| Connection pooling — `QueuePool` + `pool_pre_ping=True` | ✅ Done |
| Gap tables (`onboarding_pipelines`, `onboarding_steps`, `offboarding_cases`, `employee_activity_logs`, `employee_bank_accounts`, `payout_batches`, `journal_entries`) have ORM models | ✅ Done |
| Schema drift check migration `9ff24a0683dd` | ✅ Done |

---

## Execution Plan

### Phase 1 — P0-A: Media Migration to Object Storage (remaining items)

**1.1 Clean up legacy path constants**
- Remove unused `UPLOAD_DIR = "uploads/supplier_documents"` from `controllers/supplier_document_controller.py:41`
- Remove unused `_LP_DOC_UPLOAD_DIR` / `_LP_COD_RECEIPT_UPLOAD_DIR` from `controllers/logistics_partner_controller.py:3498-3499`
- Audit all controllers for any remaining `/uploads/...` path construction in response serializers; replace with `storage.url(key)` or keep as-is if already returning storage URLs.

**1.2 One-off migration script for existing files**
- Create `scripts/migrate_media_to_s3.py`:
  - Walk `uploads/` directory recursively
  - For each file, compute storage key (preserve existing folder structure or use a deterministic mapping)
  - Upload to S3/R2 via `S3Storage.save()`
  - Batch-update DB columns that store paths: `products.image_url`, `product_variants.image_url`, `users.profile_image`, `supplier_profiles.logo_url`, `supplier_documents.file_url`, `logistics_partner_documents.file_url`, `chat_attachments.url`, `product_videos.video_url`, `banners.image_url`
  - Process in batches of 100–500 with progress logging; skip already-migrated URLs (detected by CDN base or `http(s)://` prefix)
  - Dry-run mode (`--dry-run`) to preview changes before writing

**1.3 Presigned upload rollout**
- Enable `PRESIGNED_UPLOADS_ENABLED=true` in production `.env`
- Frontend switches to: `POST /upload/presign` → get presigned URL → client PUTs directly to S3/R2 → `POST /upload/{folder}` with returned `key` to record metadata (or extend presign response to include a callback endpoint)

---

### Phase 2 — P0-B: Offload Heavy Work to Task Queue

**2.1 Migrate bg removal + AI analysis out of request handlers**
- In `routers/supplier.py`, `routers/supplier_bg_ab_test.py`, `controllers/supplier_controller.py`: wrap `remove_background`, `analyze_product_image_async`, `generate_angles` in `enqueue_ml_job()` (already exists in `utils/background_jobs.py`)
- Return `job_id` + `GET /jobs/{job_id}` polling endpoint (pattern already exists in `routers/supplier.py:559, 664`)
- Frontend polls or uses websocket for progress

**2.2 Migrate bulk import**
- `controllers/supplier_controller.py` bulk upload → `enqueue_bulk_import_job()`
- Return job ID; process CSV + image pipeline in background worker

**2.3 Tune worker pools**
- Set `BACKGROUND_JOB_WORKERS` (fast) and `ML_WORKERS` (heavy) via env
- Fast workers: email, notifications, cache clear
- ML workers: bg removal, AI analysis, video transcode
- Add queue depth metric + alert threshold

---

### Phase 3 — P1: Postgres Validation & Search

**3.1 Local Postgres validation**
- Stand up Postgres via Docker (`docker compose up -d postgres`)
- Point `DATABASE_URL` to it; run `alembic upgrade head`
- Run full test suite against Postgres
- Re-run `EXPLAIN ANALYZE` on hot queries (product listing, search, order lookup) and compare to SQLite plans

**3.2 tsvector maintenance via trigger**
- Current search builds `to_tsvector(...)` on-the-fly in queries. Add a Postgres trigger to maintain a `search_vector` column on `products` so the GIN index is used persistently:
  ```sql
  ALTER TABLE products ADD COLUMN search_vector tsvector;
  UPDATE products SET search_vector = to_tsvector('english', coalesce(name,'') || ' ' || coalesce(description,''));
  CREATE INDEX ix_products_search_vector_gin ON products USING GIN (search_vector);
  CREATE OR REPLACE FUNCTION products_search_vector_update() RETURNS trigger AS $$
  BEGIN
    NEW.search_vector := to_tsvector('english', coalesce(NEW.name,'') || ' ' || coalesce(NEW.description,''));
    RETURN NEW;
  END;
  $$ LANGUAGE plpgsql;
  CREATE TRIGGER products_search_vector_trigger BEFORE INSERT OR UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION products_search_vector_update();
  ```
- Update `search_controller.py` to use `search_vector` column when on Postgres; keep `to_tsvector` fallback for SQLite dev.

**3.3 Native RLS policies for Postgres**
- Run `generate_rls_policy_sql()` from `utils/rls_interceptor.py` after each migration in production
- Store policy SQL in `alembic/versions/` as a repeatable migration or post-deploy script

---

### Phase 4 — P1-C: PgBouncer & Connection Sizing

**4.1 Deploy PgBouncer**
- Sidecar or managed service between app and Postgres
- Mode: `transaction` pooling
- App `DB_POOL_SIZE` → 5–10 per worker; PgBouncer `max_db_connections` sized to Postgres limit
- Document the math: `workers × pool_size ≤ Postgres max_connections` (via PgBouncer)

**4.2 Pool tuning**
- Keep `pool_pre_ping=True`
- Set `pool_recycle=1800` (already configured)
- Add connection pool metrics to `/health/deps`

---

### Phase 5 — P2: Query Performance at Scale

**5.1 Audit remaining unbounded list endpoints**
- Search codebase for `.all()` on list queries without preceding `.limit()`
- Apply `paginated_query()` or explicit `.limit(MAX_PAGE_SIZE)` to every public list endpoint
- Priority: products, orders, notifications, audit_logs, shipment_events

**5.2 Partition time-series tables (Postgres native declarative partitioning)**
- `audit_logs`, `notifications`, `shipment_events` — partition by `created_at` monthly
- Add Alembic migration that:
  - Creates child tables `audit_logs_2026_07`, etc.
  - Adjusts indexes to be local per partition
  - Adds a partition manager function or cron job to create future partitions
- Retention: detach + drop partitions older than N months (or archive to S3)

**5.3 Cache hardening**
- Extend versioned cache pattern to product listing/search result pages
- Add cache stampede lock (`SETNX` with short TTL) around cache miss computation
- Key pattern: `search:{country_code}:{hash(query)}:v{cache_version}`

---

### Phase 6 — P2-D: Schema Hygiene & Hardening

**6.1 Regenerate schema audit report**
- Run `python -m utils.schema_audit --json` and commit updated `schema-audit-report.json`

**6.2 Deprecate `get_db_session()`**
- Replace remaining `get_db_session()` calls with `get_db_context()` or `get_service_session()`
- Add deprecation warning to `get_db_session()` that fires on first call per process

**6.3 Seed password fail-closed**
- In `db/seed.py`, raise `RuntimeError` if `SEED_*_PASSWORD` is missing outside `development` environment

**6.4 Auto-migration gate**
- Remove auto-migration from `lifespan.py` in all environments; require explicit `alembic upgrade head`
- Enforce `schema_audit_ci.py` in deployment pipeline

---

## Infra to Provision

| Infra | Purpose | Notes |
|---|---|---|
| **PostgreSQL** (RDS / Cloud SQL / Neon / Supabase) | Primary + read replica(s) | Managed preferred for backups/HA |
| **Object storage + CDN** (Cloudflare R2 or AWS S3 + CloudFront) | Media hosting | R2 recommended: S3-compatible, zero egress |
| **Redis** (managed) | Broker + cache + rate limiting | Already in code; production instance needed |
| **Container platform** (ECS/Fargate, K8s, or Railway/Render) | Separate API vs ML worker pools | ML workers need more RAM |
| **PgBouncer** | Connection pooling | Sidecar or managed; transaction mode |

---

## Rollout Order

| Step | Phase | Downtime risk removed |
|---|---|---|
| 1 | P0-A cleanup + migration script | Path leaks, legacy local-disk assumptions |
| 2 | P0-B queue offload | Worker exhaustion / API freeze |
| 3 | P1 Postgres validation + tsvector trigger | Search collapse, wrong query plans |
| 4 | P1-C PgBouncer | Connection storms |
| 5 | P2-A pagination audit + partitioning | Slow queries / OOM as data grows |
| 6 | P2-C/D cache hardening + schema hygiene | Cache stampede, schema drift |

---

## Validation

- **Storage:** `tests/test_scaling_implementations.py` covers LocalStorage + S3Storage path-traversal safety
- **Background jobs:** Same test file covers enqueue, retry, backpressure, inline mode
- **Search:** `tests/test_search_endpoints.py` + `tests/_test_provider/test_search.py`
- **Pagination:** `tests/test_scaling_implementations.py` covers `safe_page`, `paginated_query`
- **Postgres validation:** Run full test suite against Postgres; `EXPLAIN ANALYZE` hot queries
- **Media migration:** `--dry-run` mode verifies key mapping before DB rewrite
