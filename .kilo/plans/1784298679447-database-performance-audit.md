# Database & Backend Performance/Reliability Audit — ZOZI Marketplace

**Date:** 2026-07-20
**Mode:** Plan (no source changes). Implementation-ready for an execution agent.
**Scope:** Complete audit of all ORM tables, SQL/queries, Alembic, and the DB
connection layer against the backend, plus code/folder-structure quality, for
production scale: ~294 tables, 500k+ products, 1M+ media, heavy order/user
traffic. Goal: stop the "system crashes / performance drops / goes down under
load" failure mode.

**Production DB (confirmed with user):** Managed PostgreSQL with a **read
replica** (RDS/CloudSQL-style). SQLite is dev-only. `db/database.py` already
has the Postgres `QueuePool` path (pool_size 50, max_overflow 100,
pool_recycle 3600, pool_pre_ping=True) and sslmode handling — wire to it.

---

## 1. Verified Findings (evidence from direct code inspection)

### P0 — will crash / not scale at all
1. **Running on SQLite.** `backend/.env` = `DATABASE_URL=sqlite:///.../zozi.db`.
   `db/database.py:22-28` only raises when `APP_ENV=production` + SQLite, so a
   deploy without that env flag boots on SQLite. SQLite serializes writers →
   `database is locked` under heavy concurrent order writes. This is the user's
   exact "system goes down" scenario.
2. **Synchronous `Session` inside 147 `async def` routes (27 routers mix async +
   `get_db`).** No `AsyncSession`/`create_async_engine`/`asyncpg` is wired
   (`db/database.py` has none). Every `db.query(...)` blocks the event loop →
   throughput ceiling under load regardless of DB power. `asyncpg` is only in
   `requirements.txt`.
3. **Dual ORM registry with 125 overlapping, divergent tables.**
   - `db/models.py` (130 tables) subclasses `db/base.py:Base` — a *separate*
     `DeclarativeBase` (confirmed by `db/base.py:3-8` docstring: *intentionally*
     separate). `models/*.py` (290 tables) subclasses `models/Base`.
   - **125 tables declared in BOTH** (`legacy&canon=125`, `only_legacy=5`,
     `only_canon=165`). Legacy-only: `commission_global_config`,
     `country_communication_templates`, `coupon_usages`, `ip_reputation`,
     `transaction_ledger`.
   - Proven divergence on the shared `products` table: legacy `Product` has
     nullable `name`, no `country_code`/`is_featured`/`barcode`/`is_verified`/
     `moderation_status`, `slug` len 180, `images` as `Text`; canonical `Product`
     has NOT NULL `name`, `country_code` (FK+idx), `is_featured`, `is_digital`,
     `is_verified`, `moderation_status`, `barcode` (unique), JSON columns.
4. **Alembic tracks only the canonical registry.** `alembic/env.py` sets
   `target_metadata = ModelsBase.metadata` (canonical `models/`). The 130 legacy
   tables — and their divergent columns — are invisible to
   `alembic revision --autogenerate`. Runtime reconciles both via
   `main.py:_real_metadata()` (lines 83-95), which masks the split but cannot
   prevent two mappers on one table.

### P1 — correctness / maintainability time-bombs
5. **Production routers query the LEGACY registry:** `routers/auth.py`,
   `supplier_analytics.py`, `supplier_documents.py`, `supplier_orders.py`,
   `supplier_payouts.py`, `supplier_products.py`, `command_center.py` all do
   `from db.models import ...`. Same rows read/written through two different
   mapper definitions → silent data-shape bugs.
6. **Boot-time schema self-heal is SQLite-only and unsafe.** `main.py:98-137`
   runs `inspect(engine)` + raw `ALTER TABLE {t} ADD COLUMN {col} {type}` at
   startup, gated to `app_env=development` AND SQLite. On Postgres this path is
   skipped → drift = boot crash, AND the raw SQL is Postgres-incompatible
   (`str(col.type)` dialect mismatches). Must be removed.
7. **Migration sprawl:** `alembic/versions/` = 161 + `versions_archive/` = 139
   = **300+ revision files**. Slow `alembic upgrade`, high drift risk, hard audit.
8. **No `Base.metadata.create_all`** anywhere (good — Alembic is the single
   source of truth). Preserve this invariant.

### P2 — scale performance (Postgres, millions of rows)
9. **Full-text search via ILIKE:** `controllers/products_controller.py:486-534`
   filters `name/description/category/brand/subcategory/color` with
   `.ilike(f"%{term}%")` and `User.username.ilike`, `SupplierProfile.business_name.ilike`.
   At 500k products each call is a full sequential scan. No `tsvector`/GIN index.
10. **`visibility_regions` is a JSON-in-Text column** filtered via
    `func.lower(Product.visibility_regions).like(region_pattern)`
    (`products_controller.py:505`). Unindexable; scans every product per request.
11. **Indexes uneven:** 175 `Index()` declarations across 290 canonical tables,
    but high-volume tables (`audit_logs`, `admin_change_audit_logs`, chat/message
    tables, `order_logistics_allocations`) have few/no composite covering indexes
    for their real filter shapes. `orders` has `ix_orders_user_id`,
    `ix_orders_customer_id`, `ix_orders_status`, `order_number` unique — needs
    `(status, created_at)` and `(user_id, created_at)`.
12. **No read/write split:** 0 references to replica/RO_DSN/bind_key. All reads
    (catalog browse, admin dashboards) hit the primary, competing with order
    writes. Confirmed managed replica is available → wire read routing.
13. **`X-Total-Count` via `func.count()` on every list page** + flash-sale set
    rescanned on every catalog call (`_get_active_flash_sales` full scan) — should
    be cached/guarded.

### P3 — code quality / structure
14. **Giant files:** `controllers/supplier_controller.py` (4710),
    `payments_controller.py` (4512), `admin_controller.py` (4341),
    `logistics_partner_controller.py` (3841), `routers/admin.py` (1987).
15. **Triplicated layering:** `routers/` + `controllers/` + `services/` overlap;
    change-amplification cost is high (every schema edit touches several layers).
16. `payload: dict` write bodies on some endpoints bypass Pydantic validation.

---

## 2. Optimization Plan (ordered, each independently shippable)

### A. Stop the bleeding (P0)
- [ ] **A1. PostgreSQL in all deployed envs.** Set `DATABASE_URL=postgresql://…`
      and `APP_ENV=production`; remove the SQLite branch dependence. Verify the
      `db/database.py` `QueuePool` path is active (it is).
- [ ] **A2. Remove the boot self-heal** (`main.py:98-137` `_sqlite_*`) and the
      `combined` metadata reconciliation. Enforce: schema = Alembic only.
- [ ] **A3. Single ORM registry.** Make `models/` canonical. Diff the 125
      overlapping tables; canonical `Product` wins. Delete `db/models.py`, repoint
      the 7 legacy-importing routers (`auth.py`, `supplier_*.py`, `command_center.py`)
      to `models`. Remove `db/base.py` if nothing else needs it. Add a test
      asserting no duplicate `__tablename__` and one registry.

### B. Async DB access (P0/P1)
- [ ] **B1. Async engine + sessions.** Add `create_async_engine`,
      `async_sessionmaker`, `AsyncSession`. Provide `async def get_db()` yielding
      `AsyncSession`. Keep a sync `SessionLocal` for scripts/seed.
- [ ] **B2. Migrate hot paths first** (products list/detail, order create, search,
      auth, cart, chat) to `await db.execute(...)`. FastAPI tolerates mixed
      sync/async; prioritize by QPS. This removes the event-loop block.

### C. Alembic hygiene (P1)
- [ ] **C1. Squash to a baseline revision** emitting the full canonical schema;
      move the 300 files to `versions_archive/` as pre-baseline (read-only
      `version_locations`). Add CI gate: `alembic revision --autogenerate` diff
      must be empty after squash.
- [ ] **C2. Migration regression test:** ephemeral Postgres in CI, `alembic
      upgrade head`, assert every `models.Base` table + columns exist.

### D. Query & indexing for scale (P2)
- [ ] **D1. Full-text search:** add `tsvector` column(s) on products
      (`name`, `description`, `category`) + GIN index; replace ILIKE chains in
      `get_products`/`autocomplete_products` with `@@ to_tsquery`. Keep
      `autocomplete` on a `pg_trgm` trigram index for prefix speed.
- [ ] **D2. Normalize `visibility_regions`** into
      `product_visibility_regions(product_id, country_code)` (or JSONB + GIN + `@>`);
      backfill from existing JSON; flip the query path off `lower(...).like(...)`.
- [ ] **D3. Composite covering indexes** for real filter shapes:
      `products(country_code, is_active, created_at)`,
      `products(is_active, sales_count DESC)`,
      `orders(status, created_at)`, `orders(user_id, created_at)`,
      plus audit/chat tables by `(entity_id, created_at)`. Validate with
      `EXPLAIN (ANALYZE, BUFFERS)` — require index scans, no seq scans.
- [ ] **D4. Read/write split:** route catalog/admin-read paths to the managed
      **replica**; keep writes on primary. Add replica DSN config + per-route
      `AsyncSession` binding (primary for writes, replica for reads).
- [ ] **D5. Cache flash-sale set** (short TTL) and guard when no sale requested;
      keep `X-Total-Count` but cache it per filter signature.

### E. Partitioning & media offload (P2/P3)
- [ ] **E1. Range-partition** `orders`, `order_items`, `audit_logs`,
      `admin_change_audit_logs`, chat/message tables by `created_at` (monthly);
      archive >12-month rows to cold storage.
- [ ] **E2. Media offload:** store `images`/`additional_images`/`videos` as
      object-storage URLs (S3/R2) + CDN; keep metadata only in DB (already mostly
      URLs — finish migration; use `JSONB` for image lists).

### F. Structure cleanup (P3)
- [ ] **F1. Split giant controllers** by domain (≤ ~600 lines/file); enforce a
      size lint.
- [ ] **F2. Collapse `routers`/`controllers`/`services` triplication** into a
      clear `routers` → `services` split.
- [ ] **F3. Replace `payload: dict` write bodies** with Pydantic models.

---

## 3. Rollout / Migration Path
1. **Phase A (stop crash):** switch to Postgres + remove self-heal. Validate on a
   staging clone with a restored SQLite→Postgres data load. Zero-downtime if DNS
   cutover; otherwise a short maintenance window.
2. **Phase A3/B (registry + async):** do registry consolidation and async migration
   **per-router behind the existing sync path** (no big-bang). Ship behind feature
   flags; load-test after each batch.
3. **Phase C (Alembic squash):** run `alembic upgrade head` on a fresh DB = exactly
   canonical schema; keep old files archived for forensics.
4. **Phase D/E (perf):** add FTS/indexes/partitioning as online operations
   (`CREATE INDEX CONCURRENTLY`, native partitioning requires table rewrite → do
   in maintenance window or via logical replication).

## 4. Risks
- **A3 + C1 interact:** squash migrations and delete legacy registry together to
  avoid orphaned tables. Validate `alembic upgrade head` on empty DB == `models.Base`.
- **B (async) is large:** incremental per-router; mixed sync/async is fine in
  FastAPI. Don't block on a full rewrite.
- **D2 (visibility normalization)** needs a data backfill before flipping queries.
- **E1 partitioning** rewrites big tables → schedule window or use
  logical-replication cutover.

## 5. Validation (acceptance)
- `DATABASE_URL` is Postgres in all deployed envs; SQLite self-heal removed.
- `grep -rn "from db.models import" backend` → 0 results; single registry test passes.
- `alembic revision --autogenerate` → empty diff vs fresh DB.
- Hot paths use `AsyncSession`; load test shows event loop not blocked.
- Product search uses `tsvector`; `EXPLAIN` shows index scans (no seq scan) on
  `products`/`orders` under representative filters at 500k rows + heavy traffic.
- Read replica serves catalog/admin reads; primary load drops materially.
- `orders`/`audit_logs` partitioned; archive job runs without downtime.
- Soak test: seeded 500k products + simulated heavy order/user traffic → p95
  latency within SLO; no `database is locked`; pool metrics stable (no unbounded
  overflow); system stays up.

## 6. Open Questions (for execution agent to confirm)
- Exact Postgres version (affects partitioning syntax / `pg_trgm` availability).
- Pool sizing vs worker count (uvicorn workers × threads); may need PgBouncer.
- Acceptable maintenance window for the Alembic squash + partition rewrite.
- Whether media S3/R2 bucket + CDN already exist.
