# ZOZI SCOPE · 01 — DATABASE SYSTEM (CONSTITUTION)
**Document type:** Scope-binding specification — **single source of truth** for the entire data layer.
**Version:** 2.1 · **Status:** DRAFT → needs founder sign-off · **Owner:** Platform / DBA
**Last reviewed:** 2026-07-30
**Supersedes & deletes after sign-off:** `DATABASE_SCOPE.md`, `DATABASE_STRUCTURE.md`, `DATABASE_TABLE.md`, `DATABASE_ECOSYSTEM_HANDLING_PLAN.md`, `DATABASE_ALIGNMENT_AUDIT.md`, `GENERATED_DATA_DICTIONARY.md`, and any separate `DATABASE_RELATIONSHIP_MAP.md` / `DATABASE_INDEXING_STRATEGY.md` / `DATABASE_MIGRATION_GUIDELINES.md` / `DATABASE_PRODUCTION_STRUCTURE.md` / `DATABASE_DEVELOPMENT_STRUCTURE.md` (now embedded as §6–§10).
**How to read:** **Part I** (§1–§5 + Appendices) binds *decisions & rules*. **Part II** (§6–§10) binds *operations & infra*. **Appendix A** is the paste-in contract for every AI/engineering task.
**Rule:** Any AI or engineer MUST read this file in full before creating, altering, or dropping any table, migration, or model. No change lands without the Appendix D checklist.

> **Honesty notes (baked in, never papered over):**
> - Table count disagrees across sources (262 live / 263 catalogued / ~270–310 ORM models). This doc does **not** invent an inventory; regenerating the canonical count is **Phase 0** (§4). The discrepancy is itself a governance finding (App. F, finding *a*).
> - `DATABASE_ALIGNMENT_AUDIT.md` states "0 migration files" — **this is stale/wrong.** `backend/alembic/versions/` + `versions_archive/` already hold 100+ migrations incl. merge-heads (`a268796caed2`, `t2u3v4w5x6y7`, `b1c8f348e2c7`, `d5477adebb01`). The real defect is the broken head (`Union` import) + 3 ORM-only tables. Recorded as ADR-018.
> - Items marked **[CONFIRM]** require your real values; they are intentionally left blank rather than fabricated.

---

# PART I — THE CONSTITUTION

## 1. Overview

### 1.1 Feature title
ZOZI Database System — the multi-country marketplace data platform (Commerce · Supplier · Customer · Logistics · Finance · Treasury · HR · Country · Media · AI · Communication · Audit · Security · Analytics · Configuration).

### 1.2 Objective / purpose
Treat the database as an **Enterprise Data Platform**, not an app database. Provide a stable, governed, domain-driven foundation that the ORM surface (~270–310 models over ~263 live tables) can grow within for the next decade **without** redesign, drift, or hallucinated structure. This document is the contract that binds all future work to that scope.

### 1.3 Scope
**In scope:** schema governance, bounded-context separation, migration discipline, country isolation (RLS), partitioning, indexing/caching, the canonical data patterns (catalog, finance ledger, AI staging, analytics snapshots, events), machine documentation, and the AI-binding rules.
**Out of scope (own scope docs, must cite this file & never contradict App. A):** application feature logic, UI, the Search feature (`02_SEARCH.md`), Finance feature behavior (`03_FINANCE.md`), etc. This doc governs *how data is stored and governed*, not what features do with it.

### 1.4 Scope boundary (crisp ✔ / ✘)
```
IN THIS DOCUMENT (the data constitution)         NOT HERE (own scope docs)
✔ Data architecture, schemas, ownership           ✘ Business logic / workflows
✔ Table standards, naming, classification       ✘ UI / mobile
✔ Security, RLS, encryption posture               ✘ Search ranking algorithm   → 02_SEARCH
✔ Performance: indexing / partition / cache rules ✘ AI model logic             → 07_AI_MEDIA
✔ Backup / DR / retention / lifecycle             ✘ Finance posting workflow   → 03_FINANCE
✔ Migration & versioning governance               ✘ Feature requirements
✔ Decision log (ADR)
```

### 1.5 Business value / KPIs
- Zero "surprise" schema changes in production (100% of changes via reviewed migration + CI drift gate).
- Country data can never leak across borders (RLS coverage = 100% of country-scoped tables).
- Storefront/analytics queries stay fast at scale (hot-list p95 < 300ms; dashboards served from snapshots).
- Any engineer can onboard a domain in < 1 day via machine-generated docs + ownership map.

---

## 2. Architecture & Design

### 2.1 Ground rules — THE CONSTITUTION (non-negotiable)
1. **Single source of truth.** Never duplicate transactional data; reference it.
2. **Keep all tables.** Do not merge or drop tables to make the count look smaller. Hundreds of tables is correct for this scope. Optimize for *domain clarity*, not *fewer tables*.
3. **One ecosystem per table.** Every table belongs to exactly one bounded context (§2.2) with a named owner.
4. **Extend before you create.** A new feature extends an existing ecosystem before creating a new one.
5. **No ad-hoc `ALTER`.** Every schema change is a reviewed Alembic migration with a downgrade and a contract test. `Base.metadata.create_all()` is **forbidden in production** (dev-only).
6. **Country isolation is first-class.** Every country-scoped table carries `country_code` and is protected by PostgreSQL Row-Level Security; hot tables are physically partitioned.
7. **Cross-ecosystem = services/events, never raw FK chains.** Domains communicate through well-defined service calls or durable events (§2.13), not arbitrary foreign keys spanning ecosystems.
8. **Separate master data, configuration, transactions, snapshots, and events** (§2.4b). Never mix them in one table.
9. **Store accounting events, not calculations.** Financial movement flows through the ledger chain only; never `UPDATE` posted journal entries; no separate "financial truth."
10. **AI outputs are staged.** AI writes to `ai_*` / staging tables and is *committed* into business tables by an explicit step; never directly.
11. **Config is data.** Commission %, delivery fee, refund %, reward %, feature toggles live in config tables — never hardcoded.
12. **Files: metadata in DB, bytes in object storage.** The DB stores `media_assets` metadata; S3/CDN (Cloudflare R2) holds bytes.
13. **Machine-document the schema.** The data dictionary is generated (`backend/scripts/generate_data_dictionary.py`), never hand-maintained.
14. **Event-driven downstream.** Writes are synchronous & ACID; analytics, cache, AI, and notifications are async via events (§2.3b).
15. **AI-friendly & backward-compatible.** Schema evolves by *addition* (nullable/default) so old code keeps working; AI ingestion has first-class staging tables.
16. **No silent fallbacks** that mask a broken pipeline. If a path can't run, report it explicitly (e.g. `mode: "lexical"`).

### 2.2 Bounded contexts (PostgreSQL schemas) + ownership
Map the models into PostgreSQL **schemas** (namespaces). Metadata-only — tables keep their names; the app keeps working. Each schema has an owner.
```
ZOZI Platform (PostgreSQL schemas)
├── core           users, roles, sessions, devices, auth          → Identity
├── commerce       products, variants, categories, carts, orders  → Commerce
├── supplier       supplier_profiles, supplier_documents          → Supplier Ops
├── customer       customers, addresses, wishlists, points        → Customer
├── logistics      partners, fleet, shipments, routes, POD        → Logistics
├── finance        accounts, journal, ledger, AR/AP, invoices     → Finance (strictest)
├── treasury       cash positions, bank, reconciliation, payouts  → Treasury
├── hr             employees, attendance, shifts, leave, COI      → People
├── country        country_configs(+split), cities, rules         → Country Ops
├── media          media_assets, video, image processing          → Media/AI
├── ai             ai_requests/results/embeddings/jobs, staging   → Media/AI
├── communication  chat, email, sms, push, tickets, notifications → Comms
├── audit          audit_logs, worm_audit, permission_audit       → Governance
├── security       api_keys, fraud, risk, blacklist, mfa, otp     → Risk
├── analytics      daily/monthly snapshots, KPIs (read models)    → Data
└── configuration  system/country/business rules, toggles         → Platform
```
> Vocabulary reconciliation: an earlier review proposed 16 *folders* (Core/Users/Products/Finance/Notification/AI/Chat/Analytics/Security/Audit/System…). Those map 1:1 onto the schemas above; **the schema names in this table are authoritative** (they are a superset — they also include `hr`, `country`, `media`, `treasury`, which that list omitted). Do not maintain a second naming system.

### 2.3 System diagram (layered request → data flow)
```
                  ┌──────────────────────────────┐
 HTTP / WS ───────►│  routers/   (entry, validate) │
                  └──────────────┬───────────────┘
                                 ▼
                  ┌──────────────────────────────┐
                  │ controllers/ (orchestrate)    │
                  └──────────────┬───────────────┘
                                 ▼
    ┌──────────────────────────────────────────────────────┐
    │ services/ (business logic — the ONLY writers)         │
    │   • finance ledger service  • ai staging/commit       │
    │   • advanced_filter/search  • country/RLS context     │
    └───────┬───────────────────────────────┬──────────────┘
            ▼                               ▼
┌────────────────────────┐      ┌────────────────────────────┐
│ providers/ (AI/external)│      │ models/ (SQLAlchemy, 27 files)│
└────────────────────────┘      └──────────────┬─────────────┘
                                                    ▼
                ┌──────────────────────────────────────────────────────┐
                │ PostgreSQL  (schemas §2.2 · RLS · partitioning · GIN) │
                └───────────────┬──────────────────────────┬───────────┘
                                ▼                          ▼
                  ┌───────────────────┐      ┌──────────────────────┐
                  │ Redis (cache/queue)│      │ Object storage (bytes)│
                  └───────────────────┘      └──────────────────────┘
   Events: services publish durable events (§2.13) → other ecosystems subscribe (no cross-FK).
```
Direction is always **router → controller → service → (providers + models) → DB**. Routers never touch the DB directly; services are the only writers. (Note: this stack uses `controllers/`+`services/`, not a "repository" layer.)

### 2.3b Data lifecycle
```
User → API → Validation → Business Rules → Service (only writer)
   → Database (transactional write) → Event published (§2.13 outbox)
      → Queue → (Analytics snapshots · Cache invalidation · AI jobs · Notifications)
   → Read models / Materialized views (§2.15) → Dashboard
```
Rule: the transactional write is synchronous & ACID; everything downstream (analytics, cache, AI, notify) is **event-driven & async**.

### 2.4 Canonical data patterns (apply everywhere)
| Concern | Forbidden (old) | Required (this scope) |
|---|---|---|
| Categories | recursive `parent_id` | **materialized path** `/1/15/42/` + `lft/rgt` |
| Variants | flat `color`/`size` columns | **JSONB `attributes` + GIN index** + `variant_key` hash |
| AI uploads | direct write to `products` | **staging tables → explicit commit**; audit in `ai_upload_jobs` |
| Search | `LIKE '%kw%'` | **tsvector + GIN** (+ pgvector semantic in `02_SEARCH.md`) |
| Finance | calc in app logic | **ledger chain**: CoA → Journal → Ledger → Balance → Trial Balance → P&L → Balance Sheet → Cash Flow |
| Analytics | live aggregation | **snapshots** (daily/monthly KPIs) + materialized views |
| Config | hardcoded constants | **config tables** (system/country/business/toggle) |
| Files | bytes in DB | **metadata in DB, bytes in object storage** |

### 2.4b Data classification (every table = exactly one class)
| Class | Meaning | Examples | Mutability |
|---|---|---|---|
| Master | slow-changing entities | users, suppliers, products, categories | versioned |
| Transactional | business events | orders, payments, shipments | append + status |
| Configuration | rules/toggles | commission_rules, country_configs, feature_flags | Maker-Checker |
| Financial ledger | accounting truth | journal_entries, ap/ar_ledger | **immutable** |
| Historical/Archive | aged-out rows | partitioned audit/chat/shipment events | read-only |
| Snapshot/Analytics | read models | daily/monthly KPIs, mat views | rebuilt |
| AI | model I/O + staging | ai_requests, ai_embeddings, ai_staging_products | staged→commit |
| Media | file metadata (bytes in object store) | media_assets | metadata only |
| Audit | who-did-what | audit_logs, worm_audit, permission_audit | append-only |
| Temporary/Cache | ephemeral | sessions, OTP, Redis keys | short TTL |

### 2.5 Files & folder wiring (authoritative)
```
backend/
├── models/            # 27 files · ~270–310 ORM models · each declares __table_args__={"schema":"<context>"}
│   ├── core.py  user.py  products.py  orders.py  payments.py
│   ├── logistics.py  finance.py  communication.py  countries.py  employee_models.py  ...
├── routers/           # HTTP/WS entrypoints (validation, rate-limit) — NO direct DB writes
├── controllers/       # request orchestration
├── services/          # business logic — the ONLY writers (advanced_filter_service.py, ai_search_service.py,
│                      #   ai_variant_config.py, bg_removal_service.py, finance ledger service, ...)
├── providers/         # AI/external adapters (embedding, CLIP, Whisper, OCR) — graceful degradation
├── alembic/           # env.py · versions/ (live) · versions_archive/ (retired/merged heads)
├── scripts/           # generate_data_dictionary.py · analyze_tables.py · seed · maintenance
├── db/                # base.py · database.py · mixins.py · schemas.py · seed.py · treasury_seeder.py
├── tests/             # unit / integration / contract / migration  (test_database.py = 33 tests)
├── monitoring/        # prometheus · grafana · promtail · fraud_monitoring · ghost_order_detector
├── docs/              # erd/ (generated) · data-dictionary · performance-reports
├── data/              # pg_rls_policies.sql (RLS as code)
├── utils/config.py    # Settings (env-driven)
└── zozi.db            # ⚠ DEV/SEED ONLY — never production
```

### 2.6 Handling & normalization (summary; deep rules in §7)
- **RLS:** `SET app.current_country_code` per session (`rls_interceptor.py`, ~154 mappings); policies on every country-scoped table; verified by test.
- **Partitioning:** range by `created_at` (monthly) for `journal_entries`, `audit_logs`, chat/messages, shipment events; hash `product_variants` by `product_id` past ~10M rows.
- **Indexes:** composite `(country_code, created_at)`, `(status, due_date)`, `(entity_type, entity_id)`, `(supplier_id, is_active)`.
- **Caching:** Redis for hot reads + facet counts; invalidate on write; materialized views refreshed by cron.
- **Naming:** `snake_case`, plural tables, `<context>_<entity>` when clarifying; `*_json` for JSONB; `is_*` booleans; `*_at` timestamps; `country_code` on all tenant rows; `id` INTEGER PK + `uuid` for public refs; soft-delete via `is_deleted`/`deleted_at`/`deleted_by`/`delete_reason`; `version` for optimistic locking; `created_by`/`updated_by` → `users.id`.
- **Normalization fix (planned):** split the 85-column `country_configs` into `country_basics`, `country_economics`, `country_tax`, `country_legal`.

### 2.7 Technologies
- **Target prod:** PostgreSQL 15 (+ `pgvector` for search/AI), Alembic, SQLAlchemy, Redis, S3/CDN (Cloudflare R2).
- **Dev/seed:** SQLite `zozi.db` with `create_all` + auto-seed + `StaticPool` + `echo=True` (dev ONLY — see §10).
- **Docs:** `generate_data_dictionary.py` → `GENERATED_DATA_DICTIONARY.md` (regenerated, never edited by hand).

### 2.8 Data retention policy (*confirm* legal values)
| Data | Retention | Notes |
|---|---|---|
| OTP / sessions | 7 days | hard delete |
| Notifications | 90 days | archive then purge |
| Application logs | 180 days | cold storage after 30 |
| AI processing artifacts | 30 days | keep `ai_upload_jobs` audit forever |
| Deleted images/media | 30 days | object-storage lifecycle rule |
| Chat / Email | duration + legal-hold | append-only |
| Orders / Invoices | **forever** (statutory) | archive partitions |
| Audit / Ledger | **forever** | WORM / immutable |
| *GDPR/PDPL erasure* | on lawful request | tombstone + key crypto-shred |

### 2.9 Standard column set (mandatory mixins)
Implement in `db/mixins.py` as `AuditMixin` + `SoftDeleteMixin` + `TenantMixin`; every business table inherits them.
```
id            INTEGER PK (performance)        uuid          UUID (external/public refs)
country_code  VARCHAR(3)  → RLS               is_active     BOOLEAN
created_at    DATETIME    updated_at DATETIME created_by    INT → users.id
updated_by    INT → users.id                  is_deleted    BOOLEAN
deleted_at    DATETIME    deleted_by INT      delete_reason TEXT (nullable)
version       INTEGER (optimistic locking)
```
Rules: integer PK for speed + UUID for public APIs (matches ecosystem plan §6/§7). **No hard delete** on business tables — use status `Cancelled / Voided / Archived / Superseded` instead.

### 2.10 Relationship & cascade rules
- **1:1** → FK + `UNIQUE`; **1:N** → FK on child; **M:N** → explicit bridge table (never implicit).
- **Bridge tables** carry their own PK + audit columns (e.g., `group_chat_members`).
- **ON DELETE:** default `RESTRICT`; `CASCADE` only for true composition (e.g., `order_items`→`order`); **never** cascade into `finance`/`audit`.
- **ON UPDATE:** `RESTRICT` on natural keys; surrogate PKs make this rare.
- **No cross-ecosystem FK** (rule #7 / ADR-014) — use events/services.
- **Reference, don't copy:** store `supplier_id`, not the supplier name; snapshot only immutable legal data (e.g. invoice recipient).

### 2.11 Approved PostgreSQL features & extensions
| Feature | Use for |
|---|---|
| `JSONB` + GIN | variant `attributes`, config payloads |
| `ENUM` / lookup tables | stable status sets (prefer lookup tables when values evolve) |
| `ARRAY` | tags, multi-value filters |
| Generated columns | `search_vector` (tsvector), slug |
| Materialized views | dashboards / facet counts (ADR-008) |
| Triggers / Functions | RLS context, `updated_at`, ledger immutability guard |
| **Extensions** | `pgvector` (search/AI), `pgcrypto` (`gen_random_uuid`, hashing), `citext` (case-insensitive email), `btree_gin` (composite GIN), `pg_trgm` (fuzzy/trigram), `uuid-ossp` |
> Ban: stored procedures for business logic (keep logic in services); `LIKE '%…%'` on large tables.

### 2.12 Transaction & query rules
- **Isolation:** `READ COMMITTED` default; `SERIALIZABLE` only for ledger posting (ADR-006).
- **Idempotency:** every external/write action carries an idempotency key recorded in `inbox_events` / `processed_webhook_events`.
- **Query budget:** p95 < 300ms (hot lists); soft cap ≤ 3 JOINs (more → review/materialize); `EXPLAIN ANALYZE` CI gate on products/orders/journal.
- **Pagination:** cursor-based everywhere; no `OFFSET` on large tables.
- **Bulk:** batch inserts/updates; never row-by-row in a loop.
- **N+1:** mandatory `selectinload`/`joinedload`.
- **Pool:** app `QueuePool` `pool_size=5`, `max_overflow=10` (utils/config; **grounded** in `DATABASE_SCOPE.md`) behind PgBouncer in prod; raise app pool only after PgBouncer is in place (see §9.3).
- **Retry:** transient failures retry with exponential backoff + jitter; idempotency makes retries safe.

### 2.13 Event-driven tables (transactional outbox — ADR-014)
```
outbox_events      id, uuid, event_type, aggregate_type, aggregate_id, payload_json,
                   status(pending/published/failed), country_code, created_at, published_at
inbox_events       id, idempotency_key (UNIQUE), event_type, status, processed_at   ← dedupe
event_retry_queue  id, event_id, attempt, next_attempt_at, last_error
event_dead_letter  id, event_id, payload_json, failed_at, reason, resolved_by        ← manual review
```
Pattern: a service writes to `outbox_events` in the **same transaction** as the business write (transactional outbox); a relay publishes to the broker; consumers record `inbox_events` for idempotency; failures → retry → DLQ. This is how commerce/logistics/finance/analytics talk without cross-FK chains.

### 2.14 Log & archive taxonomy (disciplined — do NOT create 7 log tables)
- **One** append-only `audit_logs`, **range-partitioned monthly**, with a `log_type` enum (`activity | security | finance | api | error | system`) + `actor`, `entity`, `old/new_value_json`, `country_code`. Add `worm_audit` only for immutable financial/legal records.
- **Archive schema** (`archive`): detached partitions older than retention (§2.8) move here (or to cold object storage) — old orders/chats/notifications/logs/analytics. Read-only; excluded from hot queries.
- Monitoring additions: slow-query log, index-usage, deadlock, connection count, **vacuum/autovacuum**, replication lag (extends §9.6).

### 2.15 Analytics snapshot tables (enumerated — ADR-008)
Materialized views / snapshot tables, refreshed by cron, never live aggregates:
```
mv_daily_sales · mv_monthly_sales · kpi_customer · kpi_supplier · kpi_country
kpi_revenue · kpi_orders · kpi_retention · kpi_conversion · mv_cash_position · mv_facet_counts
```

---

## 3. Requirements

### 3.1 Use cases
- **UC-1 Developer adds a feature:** reads this doc → extends an existing schema via reviewed migration → adds contract test → regenerates dictionary → updates status matrix.
- **UC-2 Country Ops:** data is physically/RLS-isolated per country; a country head sees only their country.
- **UC-3 Finance posts:** every money movement creates balanced journal lines via the ledger service; periods lock.
- **UC-4 AI ingestion:** supplier upload → AI writes staging → human/auto commit → business table; cost/audit in `ai_upload_jobs`.
- **UC-5 Analytics:** dashboards read snapshots/materialized views, never live heavy aggregates.

### 3.2 Functional requirements
- **FR-1** All models declare a bounded-context schema (§2.2).
- **FR-2** Alembic is the only schema-change path; `create_all` disabled outside `APP_ENV=development`.
- **FR-3** Every country-scoped table has `country_code` + an RLS policy.
- **FR-4** Catalog uses materialized-path categories + JSONB variants + GIN.
- **FR-5** AI writes only to staging/`ai_*`; commit is explicit and audited.
- **FR-6** Finance writes only through the ledger service; posted entries immutable; period-close locking.
- **FR-7** Config values live in config tables; no hardcoded business constants.
- **FR-8** File bytes in object storage; DB holds metadata only.

### 3.3 UI/UX requirements
Largely N/A (data layer). Surfaces affected: admin **schema/data-dictionary viewer**, migration status panel; any feature reading facets/snapshots must show loading + empty states (no silent zeros).

### 3.4 Technical requirements
- **TR-1** CI **schema-drift gate**: `alembic check` fails the build if models ≠ migrations.
- **TR-2** Every migration has a downgrade + a contract test asserting the intended shape.
- **TR-3** RLS bypass attempts fail closed; covered by a dedicated security test.
- **TR-4** Nightly reconciliation cron (sub-ledgers ↔ ledger; snapshot freshness) with alerting on variance.
- **TR-5** Hot-list query p95 < 300ms with warm cache; load-tested.

### 3.5 Dependencies
PostgreSQL provisioned for staging/prod (dev stays SQLite). Redis. Object storage (R2). CI runner. The `02_SEARCH.md` (pgvector) and `03_FINANCE.md` (ledger) feature docs depend on this foundation.

---

## 4. Execution Plan

> Phased; each phase independently shippable & reversible. **Read §2 fully before Phase 0.**

### Phase 0 — Freeze & inventory (no code changes)
- Regenerate the canonical inventory: run `backend/scripts/generate_data_dictionary.py` → `GENERATED_DATA_DICTIONARY.md`. Reconcile the count discrepancy (262 live vs ~310 ORM) and record the truth.
- Produce the **table → ecosystem map** (App. C) from the live schema.
- **Done when:** one authoritative inventory + ownership map exists and the count is reconciled in writing.

### Phase 1 — Migration pipeline hardening
- Gate `Base.metadata.create_all()` behind `APP_ENV=development`; prod uses `alembic upgrade head` only (already raises in prod per `db/database.py` — verify the gate is airtight).
- Repair the broken Alembic head (`Union` import) so the existing `versions/` + `versions_archive/` chain runs; create the **3 missing migrations** for ORM-only tables: `points_transactions`, `upload_jobs`, `user_points`.
- Add CI **schema-drift gate** (`alembic check`) + a migration contract-test harness.
- **Done when:** no path to change prod schema except Alembic; drift gate red on any un-migrated model change.
- **Rollback:** revert the startup guard; migrations are individually downgrade-able.

### Phase 2 — Bounded-context schemas
- `CREATE SCHEMA core, commerce, finance, ...`; move tables via `ALTER TABLE … SET SCHEMA …` (metadata-only).
- Set `__table_args__={"schema":"<context>"}` on models; update `search_path`.
- **Done when:** every model resolves under its schema; app behavior unchanged; tests green.

### Phase 3 — Country isolation
- Enable RLS on country-scoped tables (`data/pg_rls_policies.sql`); set `app.current_country_code` in middleware per request.
- Add monthly range partitioning to the hot append-only tables (§2.6 / §7.2).
- **Done when:** a cross-country read returns nothing without the correct session var (security test passes).

### Phase 4 — Canonical pattern enforcement
- Categories → materialized path (+ backfill). Variants → JSONB `attributes` + GIN + `variant_key`.
- AI → staging + commit + `ai_upload_jobs` audit. Finance → ledger-chain service + immutable posted entries + period lock. Analytics → snapshots + materialized views. Events → outbox/inbox/DLQ (§2.13).
- **Done when:** each pattern has a passing contract test and the old anti-pattern is gone from new code.

### Phase 5 — Normalization & storage fixes
- Split `country_configs` (85 cols) → `country_basics/economics/tax/legal` with a data-preserving migration; resolve `country_code` `VARCHAR(3)` vs `(10)` here, **before** any joins.
- Enforce metadata-in-DB / bytes-in-object-storage for all file-bearing tables. Add the high-priority composite indexes + missing FKs (**PostgreSQL only** — SQLite default B-tree; 62 single-index tables would slow writes).
- **Done when:** no table > ~40 columns without justification; no file bytes stored in the DB.

### Phase 6 — Governance automation
- Auto-regenerate the data dictionary in CI on every merged migration; publish ownership map; alert on any table lacking an ecosystem/owner.
- **Done when:** docs are always current; orphan tables trigger a CI warning.

### Deployment plan
- Roll out phase-by-phase behind `APP_ENV` gates; each phase behind a feature flag where it touches behavior.
- Migrations run in a maintenance window with a pre-taken snapshot; **rollback = `alembic downgrade` + restore**.

### Testing & validation
- **Unit:** model constraints, ledger balance (`Σdebit==Σcredit`), variant-key hashing, config resolution.
- **Integration:** RLS isolation, staging→commit, snapshot refresh, reconciliation cron, outbox relay.
- **Contract:** one per migration asserting the exact before/after shape.
- **Performance:** k6/Locust on hot lists; assert p95 < 300ms warm; snapshot-backed dashboards < 500ms.
- **Schema / RLS / Failover / Backup / Chaos** tests per §8 / §9.
- Locations: backend tests in `backend/tests` (incl. `test_database.py`); Playwright e2e where `playwright.config.ts` `testDir` points (existing specs in `frontend/web_app/e2e/`); Jest/component in `frontend/web_app/__tests__`.

---

## 5. Risk & Governance

### 5.1 Risks & constraints
| Risk | Mitigation |
|---|---|
| AI/agent drift & hallucinated structure | This doc + App. A binding contract + read-before-edit rule |
| Silent table merges/drops | Constitution rules #1/#2; CI orphan-table warning |
| `create_all` in prod | Phase 1 env gate + drift gate |
| Cross-country data leak | RLS fail-closed + security test (Phase 3) |
| Cross-ecosystem FK spaghetti | Rule #7; services/events only |
| Wide/unwieldy tables (85-col) | Phase 5 split + <40-col guideline |
| Undocumented schema | Machine-generated dictionary in CI (Phase 6) |
| Trusting a stale audit doc | App. A rule #13 + ADR-018 (verify against code, not prose) |

### 5.2 Maintenance & support
- **Ownership:** each schema has a team owner (§2.2); the owner approves migrations touching it.
- **Monitoring:** migration status, drift-gate result, RLS coverage, reconciliation variance, snapshot freshness, hot-query p95 (see §9.6).
- **Escalation:** any change to `finance`/`security`/`audit` schemas requires Platform/DBA + domain-owner sign-off.

### 5.3 Success metrics
- 100% schema changes via reviewed migration; CI drift gate green.
- 100% RLS coverage on country-scoped tables; 0 cross-country leak in tests.
- Hot-list p95 < 300ms; dashboards served from snapshots.
- Data dictionary regenerated on 100% of merged migrations; 0 orphan tables.

---

## Appendices (Part I)

### Appendix A — AI BINDING CONTRACT (paste into every AI task that touches the DB)
> You are working on the ZOZI database. Before any change you MUST have read `documents/scope/01_DATABASE.md` in full. You MUST obey, without exception:
> 1. Never run `Base.metadata.create_all()` in production; Alembic migrations only.
> 2. Never drop or merge tables to reduce count; extend an existing ecosystem (§2.2).
> 3. Every new table declares its schema/ecosystem and an owner.
> 4. Every migration is reviewed, has a downgrade, and has a contract test.
> 5. Never add a foreign key that spans ecosystems; use a service call or a durable event (§2.13).
> 6. Every country-scoped table carries `country_code` and an RLS policy.
> 7. Financial writes go only through the ledger service; never `UPDATE` a posted journal entry.
> 8. AI outputs go to staging/`ai_*` tables and are committed explicitly — never written straight into business tables.
> 9. Store business constants in config tables; never hardcode them.
> 10. Store file metadata in the DB and bytes in object storage.
> 11. After any schema change: regenerate the data dictionary and update `CODEBASE_STATUS_MATRIX.md`.
> 12. No silent fallbacks. If a pipeline can't run, report it explicitly.
> 13. **This file is the single source of truth.** Do not maintain parallel companion docs; verify claims against the codebase, not against other prose (audits rot — see ADR-018).
> 14. If a requested change conflicts with this contract, **STOP and ask** before proceeding.

### Appendix B — Naming conventions
`snake_case`; plural tables; `<context>_<entity>` when clarifying; `*_json` for JSONB; `is_*` booleans; `*_at` timestamps; `country_code` on all tenant rows; `id` INTEGER PK + `uuid` for public refs; soft-delete via `is_deleted`/`deleted_at`/`deleted_by`/`delete_reason`; `version` for optimistic locking; `created_by`/`updated_by` → `users.id`.

### Appendix C — Table → ecosystem map
*Regenerate from live schema in Phase 0 (do not hand-maintain).* Until then, treat the §2.2 tree as the target and `GENERATED_DATA_DICTIONARY.md` (grouped by schema, e.g. `hr (21)`, finance `ap_ledger_entries`/`ar_ledger_entries`/`payouts`) as the working reference.

### Appendix D — Change-control checklist (the PR gate)
- [ ] Read `01_DATABASE.md`; change fits an existing ecosystem.
- [ ] Alembic migration created with downgrade.
- [ ] Contract test added; drift gate green.
- [ ] `country_code` + RLS if tenant-scoped.
- [ ] No cross-ecosystem FK; events/services used.
- [ ] Finance/AI/config/file rules respected (§2.4).
- [ ] Data dictionary regenerated; `CODEBASE_STATUS_MATRIX.md` updated.
- [ ] Domain owner + (for finance/security/audit) Platform/DBA sign-off.

### Appendix E — How this scope series works (single-file rule)
This is doc **01** and — for the database domain — it is **the only file**. The operational specs (relationship map, indexing, migrations, production, development) are embedded as **§6–§10** (with ADR-016 forbidding parallel copies). Each *future feature* domain gets its own file using the same template + rigor: `02_SEARCH.md`, `03_FINANCE.md`, `04_LOGISTICS.md`, `05_HR.md`, `06_COMMUNICATION.md`, `07_AI_MEDIA.md`, `08_COUNTRY.md`, `09_SECURITY_AUDIT.md`, `10_ANALYTICS.md`. Each MUST cite this doc for any data-layer rule and MAY NOT contradict Appendix A.

### Appendix F — DATABASE DECISION LOG (ADR) · *the anti-drift memory*
> Every major data decision is recorded here. **Future AI/dev sessions MUST NOT reverse an ADR without a new, approved ADR.** This is what stops flip-flopping.

| ID | Decision | Rationale | Grounded in | Date | Status |
|---|---|---|---|---|---|
| ADR-001 | PostgreSQL in prod; SQLite **dev-only** | ACID, JSONB, RLS, pgvector; `db/database.py` raises on SQLite in prod | codebase / DATABASE_SCOPE | 2026 | Accepted |
| ADR-002 | Keep all tables; govern, don't consolidate | each domain is an in-use subsystem; *rejects the earlier "merge ~20%" idea* | ecosystem plan | 2026 | Accepted |
| ADR-003 | Bounded-context PostgreSQL schemas (16 ecosystems) | clarity without rewrite; metadata-only move | §2.2 | 2026 | Accepted |
| ADR-004 | JSONB `attributes` + GIN for variants (not flat cols) | flexible, fast faceting at 1M+ variants | ecosystem plan | 2026 | Accepted |
| ADR-005 | Materialized-path categories (`/1/15/42/`) | instant subtree queries vs recursive CTE | ecosystem plan | 2026 | Accepted |
| ADR-006 | Immutable double-entry ledger; writes via ledger service only | accounting correctness; no second financial truth | treasury_seeder, journal/ap/ar | 2026 | Accepted |
| ADR-007 | AI writes to **staging**, explicit commit; audit in `ai_upload_jobs` | safety + cost tracking | ai_search_service, bg_removal_service | 2026 | Accepted |
| ADR-008 | Analytics via snapshots/materialized views, never live aggregation | protect transactional DB | §2.4 | 2026 | Accepted |
| ADR-009 | Config-as-data (no hardcoded business constants) | runtime-tunable per country | rule #11 | 2026 | Accepted |
| ADR-010 | Media **metadata in DB, bytes in object storage/CDN** (Cloudflare R2) | disk/bandwidth/horizontal-scaling | DATABASE_STRUCTURE P0-A | 2026 | Accepted |
| ADR-011 | Country isolation via RLS (`rls_interceptor.py`, ~154 mappings) + `country_code` | fail-closed multi-tenancy | codebase | 2026 | Accepted |
| ADR-012 | Alembic-only schema changes; **ban `create_all` in prod** | drift gate | DATABASE_SCOPE | 2026 | Accepted |
| ADR-013 | **Hybrid** search (FTS + pgvector + CLIP), not vector-only | precision on brand/price + semantic recall | 02_SEARCH | 2026 | Accepted |
| ADR-014 | Cross-ecosystem comms via **events/services** (transactional outbox), never cross-FK chains | decoupling | ecosystem plan | 2026 | Accepted |
| ADR-015 | Local Ollama models (`phi3:mini`, `qwen2.5`, `moondream`); vision OFF by default on VPS | cost control at 1000s of suppliers | codebase | 2026 | Accepted |
| ADR-016 | **Single-file constitution**; operational specs embedded (§6–§10), no parallel companion files | one source of truth; kills drift | this doc v2.1 | 2026 | Accepted |
| ADR-017 | Dev seed password = `DevSeed123!`; **prod never seeded** | standardize the two-convention confusion | DATABASE_SCOPE | 2026 | Accepted |
| ADR-018 | Migrations **exist** (`versions/` + `versions_archive/`, merge-heads present); the "0 files" audit claim is **stale**. Real defect = broken head (`Union` import) + 3 ORM-only tables | verify against code, not prose | codebase.md, DATABASE_SCOPE | 2026 | Accepted |

> **Open governance findings (resolve, don't hide):**
> - *(a)* Table count disagrees (262 / 263 / ~270 / ~310) → regenerate canonical count in Phase 0.
> - *(b)* Seed password now standardized to `DevSeed123!` (ADR-017); confirm prod has **no** seeded credentials.
> - *(c)* `country_code` width mismatch `VARCHAR(3)` vs `(10)` (evidenced: `account_balances`/`logistics_partner_documents` = 3, `employee_addresses` = 10) → fix in the Phase-5 unifying migration **before** joins.
> - *(d)* Stale "0 migration files" audit claim vs actual `versions_archive/` (ADR-018).
> - *(e)* 62 tables have a single index; 44 tables lack FK constraints (DATABASE_SCOPE) → add in Phase 5, **PostgreSQL only**.

### Appendix G — Production deployment checklist (gate)
```
[ ] Indexes verified (EXPLAIN, no seq-scan on hot paths)   [ ] FKs + constraints verified
[ ] Backup taken AND restore tested                        [ ] Migration upgrade + downgrade tested
[ ] Performance tested (load test, p95 < 300ms)            [ ] Security tested (RLS fail-closed)
[ ] Monitoring + alerts enabled                            [ ] Runbook + rollback documented
[ ] Data dictionary regenerated · CODEBASE_STATUS_MATRIX updated · ADR added if a decision changed
```

---

# PART II — OPERATIONAL SPECIFICATIONS (embedded; do not duplicate elsewhere)

## 6. DATABASE RELATIONSHIP MAP
**Type:** reference · **Owner:** Platform/DBA · **Rule:** the FULL per-table ERD is **generated**, never hand-drawn (§6.4). This section holds the domain graph + the canonical pattern ERDs every feature must conform to.

### 6.1 Domain (ecosystem) relationship graph
Allowed interactions are via services/events only (ADR-014). No cross-ecosystem FK chains.
```
                  ┌──────────────┐
                  │     core     │  users · roles · sessions · devices · auth
                  └──────┬───────┘
        ┌───────────────┬──┴───────────┬────────────────┐
        ▼               ▼              ▼                ▼
  ┌──────────   ┌──────────┐   ┌──────────┐    ┌────────────┐
  │ commerce │   │ supplier │   │ customer │    │    hr      │
  │ products │   │ profiles │   │ addresses│    │ employees  │
  │ orders   │   │ docs/KYC │   │          │    │ attendance │
  └────┬─────┘   └────┬─────   └────┬─────┘    └────────────┘
       │  events       │              │
       ▼               ▼              ▼
  ┌──────────┐   ┌──────────   ┌──────────────
  │logistics │   │ finance  │◄──┤   treasury   │
  │ shipments│   │ ledger   │   │ cash/payouts │
  └────┬─────┘   └────┬─────   └──────────────
       │              │
       ▼              ▼
  ┌──────────────────────────┐  ┌──────────────┐  ┌────────────┐
  │        audit             │  │  analytics   │  │  media/ai  │
  │  (append-only, WORM)     │  │  snapshots   │  │  staging   │
  └──────────────────────────┘  └──────────────┘  └────────────┘
   Cross-cutting (read by all, written by owners): country · configuration · communication · security
```

### 6.2 Pattern ERDs (canonical — conform to these)
**Catalog**
```
categories (materialized path /1/15/42/)
   │ 1:N
products ── N:1 ── supplier_profiles
   │ 1:N
product_variants (attributes JSONB + GIN, variant_key hash)
products ── M:N ── media_assets (metadata; bytes in object store)
```
**Order → Finance (event-driven, ADR-006/014)**
```
orders ──1:N── order_items
   │ publish OrderDelivered / RefundRequested (NO direct FK to finance)
   ▼
finance.ledger_service ──► journal_entries ──1:N── journal_entry_lines ──N:1── accounts
                               ▲                        │
             ap_ledger / ar_ledger (sub-ledgers reconcile to control accounts)
payout_batches ──► treasury payout ──► journal (balanced) ──► bank
```
**AI staging → commit (ADR-007)**
```
upload_jobs/ai_upload_jobs ──1:N── ai_staging_products ──(explicit commit)──► products
ai_requests ── ai_results ── ai_embeddings (pgvector) ── ai_recommendations
```
**Communication**
```
chat_threads ──1:N── chat_messages (partitioned monthly)
channels ── channel_members ; notifications (queue-backed) ; email_messages ; video_rooms
```
**Country (RLS context)**
```
country_configs (→ split: basics/economics/tax/legal) ──1:N── country_cities
   every tenant row carries country_code → RLS policy
```

### 6.3 Forbidden patterns
- ✘ `orders` with 20 FKs to customer/supplier/driver/warehouse/… → use events.
- ✘ copying supplier name into orders → store `supplier_id`; snapshot only immutable legal data.
- ✘ FK from `commerce` directly into `finance` tables → go through the ledger service/event.

### 6.4 Generating the FULL ERD (honest: hundreds of tables can't be hand-drawn)
Extend `backend/scripts/generate_data_dictionary.py` to also emit FK edges → Mermaid `erDiagram`: introspect `Base.metadata` for tables/columns/PK/FK; group by schema (§2.2); output `docs/erd/<schema>.mmd` + a domain index; run in CI; commit output. The hand-maintained ERD is **banned** (same rule as the data dictionary).

---

## 7. DATABASE INDEXING STRATEGY
**Type:** standard · **Owner:** Platform/DBA · **Goal:** predictable performance from 10K → 100M products and 1 → 50 countries.

### 7.1 Index rules
- PK/FK indexed automatically; every FK has an explicit index (closes finding *e*).
- Composite (leftmost-prefix aware): `(country_code, created_at)`, `(status, due_date)`, `(entity_type, entity_id)`, `(supplier_id, is_active)`.
- Partial indexes for hot subsets: `WHERE is_deleted = false AND is_active = true`.
- JSONB: GIN on `product_variants.attributes`; GIN trigram (`pg_trgm`) for fuzzy name search.
- Full-text: tsvector column + GIN (replaces `LIKE '%…%'`).
- Vector: pgvector HNSW (or IVFFlat) on `products.embedding` / `ai_embeddings`.
- Covering indexes (`INCLUDE`) for hot-list columns to enable index-only scans.
- Anti-rule: never index every column; every index must justify its write cost.

### 7.2 Partitioning (only where it earns its keep)
- RANGE by `created_at` (monthly): `journal_entries`, `audit_logs`, `chat_messages`, `shipment_events`.
- HASH by `product_id`: `product_variants` once > ~10M rows.
- Detach + archive old partitions; never partition small lookup tables.

### 7.3 Materialized views / read models (ADR-008)
- Dashboards & facet counts read from mat views, refreshed by cron (~15 min) + on-write invalidation.
- Examples: `mv_daily_revenue`, `mv_ap_aging`, `mv_facet_counts`, `mv_cash_position`.
- Never run heavy aggregates on transactional tables in a request path.

### 7.4 Query discipline
- `EXPLAIN ANALYZE` gate in CI for any query touching products/orders/journal.
- Eliminate N+1 via `selectinload`/`joinedload`; cursor pagination everywhere; cap candidate sets.
- Read replicas serve analytics/reporting; primary serves writes.

### 7.5 Caching & pooling
- Redis: hot reads, facet counts, rate-limit, queue broker; invalidate on write; guard stampedes.
- PgBouncer (transaction mode) in front of Postgres; app pool `pool_size=5`, `max_overflow=10` (grounded).

### 7.6 Concrete backlog (grounded in DATABASE_SCOPE)
- Add the 10 high-priority composite indexes, then the remaining ~52 (**PostgreSQL only** — SQLite default B-tree; 62+ indexes there would slow writes).
- Add FK constraints to the ~44 tables missing them.
- Benchmark before/after.

### 7.7 Scale ladder
| Stage | Products | Actions |
|---|---|---|
| MVP | 10K | indexes + FTS + Redis cache |
| Growth | 100K | + mat views, read replica, PgBouncer |
| Scale | 1M | + JSONB GIN, pgvector, partition audit/chat |
| Large | 10M | + partition variants (hash), query gating |
| Massive | 100M | + shard by country, dedicated search cluster |

---

## 8. DATABASE MIGRATION GUIDELINES
**Type:** governance · **Owner:** Platform/DBA · **Rule:** Alembic is the ONLY path to a schema change; `create_all` is dev-only.

### 8.1 Versioning
- One reviewed migration per logical change; Alembic revision = source of truth.
- Version labels: migration rev · database version · rollback rev · feature flag · release tag.
- Naming: `YYYYMMDD_HHMM-<rev>_<slug>.py`; keep `versions_archive/` for retired/merged lines (already in use — e.g. merge-heads `a268796caed2`, `t2u3v4w5x6y7`, `b1c8f348e2c7`).

### 8.2 Authoring rules
- Every migration has `upgrade()` AND `downgrade()`.
- Every migration ships a contract test asserting the exact before/after shape.
- Data migrations separated from schema migrations; idempotent; batched for big tables.
- Resolve `country_code` `VARCHAR(3)` vs `(10)` in the unifying migration **before** joins.
- Create the 3 missing migrations for ORM-only tables: `points_transactions`, `upload_jobs`, `user_points`.
- Repair the broken Alembic line (the `Union` import) so the existing chain runs (ADR-018).

### 8.3 Deployment sequencing (zero-downtime pattern) — EXPAND → MIGRATE → CONTRACT
1. **Expand:** add new column/table (nullable/with default) — backward compatible.
2. **Migrate:** backfill data; dual-write; flip readers via feature flag.
3. **Contract:** drop old column/table in a **later** release.
- Never add + drop in the same release. Keep one release of deprecated tables (T5) for rollback.
- Never drop in a patch release. Grep for references; run `test_database.py` (33 tests) after each change.
- Do not drop empty tables blindly — many are wired (e.g., `entity_chat_threads`, `journal_entries`).

### 8.4 CI gates
- `alembic check` schema-drift gate: fail build if models ≠ applied migrations.
- naming-lint (domain prefix), RLS-registry lint (`country_code` tables ∈ `COUNTRY_AWARE_TABLES`), contract tests.

### 8.5 Rollback & safety
- Pre-take a snapshot before any prod migration; run in a maintenance window.
- Rollback = `alembic downgrade -1` + restore-from-snapshot if a data-migration was involved.
- Finance/security/audit schema changes require Platform/DBA + domain-owner sign-off.

---

## 9. DATABASE PRODUCTION STRUCTURE
**Type:** infrastructure · **Owner:** Platform/DevOps · **Note:** `[CONFIRM]` items need your real values — not invented.

### 9.1 Topology
```
                 WAF (ModSecurity + OWASP CRS) · fail2ban · Let's Encrypt TLS
                                   │
                          Nginx reverse proxy
                                   │
         ┌─────────────────────────┼──────────────────────────┐
         ▼                         ▼                          ▼
    FastAPI (API)          Task workers (Celery/ARQ)     WS servers
         │                  AI/ML · bulk · email · AI jobs
         ▼                         │
    PgBouncer ──► PostgreSQL 15 (primary) ──► read replica(s)
         │                         │
         ▼                         ▼
    Redis (cache/queue/rate-limit)   Object storage + CDN (Cloudflare R2)  ← media bytes
```
- Postgres: managed (RDS/Cloud SQL/Neon/Supabase), primary + ≥1 read replica **[CONFIRM provider]**.
- Object storage + CDN: Cloudflare R2 (S3-compatible, zero egress; works with existing `boto3` + `endpoint_url`).
- Redis: managed instance for broker + cache + rate-limit.

### 9.2 Media architecture (millions of images — ADR-010)
```
Upload → Original (object store) → Optimized → Thumbnail → WebP → CDN → Archive → Delete(lifecycle)
DB stores media_assets metadata ONLY (url, mime, hash, w/h, ai_status). Never store bytes in the DB.
```
This removes the #1 crash cause: local-disk media served by the API (DATABASE_STRUCTURE P0-A).

### 9.3 Concurrency — handling 1000s of concurrent users
- Pool: PgBouncer (transaction mode) in front; app pool 5 + overflow 10 (raise only after PgBouncer is in place).
- Offload: AI/ML/bulk/email → task queue workers (never in the request path).
- Read scale: dashboards/reports → read replicas + materialized views.
- Cache: Redis for hot reads/facets; invalidate on write; stampede guards.
- Query: cursor pagination, N+1 elimination, capped candidate sets, EXPLAIN gate.
- Protect: rate limiting (re-enabled in prod), CDN for static/media, gzip.
- Load-test target: hot-list p95 < 300ms warm; sustained **[CONFIRM]** rps.

### 9.4 Backup strategy **[CONFIRM cadence/tooling]**
- Daily incremental + weekly full + monthly archive; PITR via WAL.
- Offsite + cold storage; periodic **restore drills** (a backup you can't restore isn't a backup).
- Object-storage lifecycle for media; partition detach+archive for aged transactional data.

### 9.5 Disaster recovery **[CONFIRM RPO/RTO]**
```
Primary → Replica (streaming) → Automatic failover → Restore → Verification → Go-live
```
- Documented runbook; failover + backup-restore tested quarterly (chaos test).

### 9.6 Monitoring (grounded in `monitoring/`)
- Prometheus (backend `/metrics`, postgres-exporter) + Grafana dashboards + Promtail logs.
- Alert on: slow queries, deadlocks, replication lag, CPU/RAM/storage, connection count, index usage, cache hit ratio, **vacuum/autovacuum**, reconciliation variance, snapshot freshness.

### 9.7 Security posture (grounded in `SECURITY_CONFIG.ini`)
- Encryption at rest + TLS in transit (`sslmode=require`); secrets in Vault (or Azure Key Vault free tier); key rotation.
- DB firewall / IP allowlist; least-privilege roles per schema owner; MFA for privileged access.
- WAF + fail2ban + rate limiting; full access/audit logging (append-only). PII masking at the app layer for sensitive columns.

### 9.8 Scalability ladder
- Products: 10K → 100K → 1M → 10M → 100M (see §7.7).
- Countries: 1 → 5 → 10 → 25 → 50 — enabled by RLS + `country_code` + config-as-data (no schema change to add a country).

---

## 10. DATABASE DEVELOPMENT STRUCTURE
**Type:** environment · **Owner:** Platform · **Rule:** this convenience stack is DEV/SEED ONLY. None of it runs in production.

### 10.1 Dev mode (`APP_ENV=development`) — grounded in `DATABASE_SCOPE.md`
| Aspect | Config |
|---|---|
| Database | SQLite `zozi.db` (project root) |
| Schema creation | `Base.metadata.create_all()` on startup (dev only) |
| Seed | auto-seed on startup (`SEED_DATA_ON_STARTUP=true`) |
| Migrations | `alembic upgrade head` via `_bootstrap_runtime()` |
| Pool | `StaticPool` (single connection) |
| Debug | SQL logged (`echo=True`) |
| CORS | permissive (localhost) · CSRF bypassed · rate-limit disabled |
| Local AI | Ollama: `phi3:mini` (EN), `qwen2.5` (AR), `moondream` (vision, OFF by default) |
| Test account | `admin@zozi.com` / `DevSeed123!` (ADR-017) |

Startup flow: `_ensure_tables_exist()` → `_bootstrap_runtime()` (Alembic) → `_seed_demo_data()` → port 8000.

### 10.2 Prod mode (contrast — grounded)
| Aspect | Config |
|---|---|
| Database | PostgreSQL (QueuePool `pool_size=5`, `max_overflow=10`) |
| Schema creation | **BLOCKED** — `create_all()` raises |
| Seed | **DISABLED** (`SEED_DATA_ON_STARTUP=false`) |
| Migrations | manual `alembic upgrade head` before deploy |
| SSL | `sslmode=require` · secrets env-only (no `.env` in repo) |

### 10.3 Folder structure (full ecosystem, extends §2.5)
```
backend/
├── db/            base.py · database.py · mixins.py · schemas.py · seed.py · treasury_seeder.py
├── models/        27 files · ~270–310 ORM models (each declares its schema)
├── routers/  controllers/  services/  providers/
├── alembic/       env.py · versions/ · versions_archive/
├── scripts/       generate_data_dictionary.py · analyze_tables.py · seed · maintenance
├── tests/         unit · integration · contract · migration (test_database.py = 33 tests)
├── monitoring/    prometheus · grafana · promtail · fraud_monitoring · ghost_order_detector
├── docs/          erd/ · data-dictionary · performance-reports
└── zozi.db        ⚠ DEV/SEED ONLY
```

### 10.4 Dev → Prod parity rules
- Anything that changes schema must work via Alembic in **both** (so dev `create_all` never masks a missing migration).
- CI runs the migration path on a clean Postgres, **not** SQLite, to catch prod-only failures.

---

## Grounding summary (what is real vs. what you must confirm)
- **Grounded in your code/files:** all 18 ADRs; the 16 schemas; RLS (`rls_interceptor.py`, ~154 mappings); JSONB/FTS/pgvector patterns; AI staging (`ai_search_service`, `bg_removal_service`, `ai_variant_config`); Ollama models; dev/prod modes + pool 5/10 + `DevSeed123!` (`DATABASE_SCOPE`); existing migrations + merge-heads (`versions_archive/`); media→R2 + PgBouncer + replicas (`DATABASE_STRUCTURE`); monitoring stack (`monitoring/`); security tools (`SECURITY_CONFIG.ini`); the 62 single-index / 44 missing-FK / 85-col `country_configs` / 3 ORM-only tables / `country_code` width mismatch backlogs.
- **Left as `[CONFIRM]` (will not invent):** backup cadence/tooling, RPO/RTO, cloud provider, sustained-rps target, exact retention periods (legal).
- **Cannot be hand-authored:** the full ERD — it must be generated (§6.4).

## Suggested next step
Sign off **Appendix F (the ADRs)** first — they are the leash. Then this database domain is fully bound in one file, and we move to the next feature scope (`03_FINANCE.md` or `06_COMMUNICATION.md`) in the same binding format — citing §01, never contradicting Appendix A. If you want, the next concrete artifact is the `generate_data_dictionary.py` **ERD-extension script** so §6.4 (and therefore the Relationship Map) becomes self-maintaining.

<!-- FILE END: documents/scope/01_DATABASE.md -->