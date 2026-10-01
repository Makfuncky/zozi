# ZOZI Database Constitution — Gap Analysis & Implementation Plan
**Based on:** `documents/01_DATABASE.md` v2.1  
**Date:** 2026-07-30  
**Status:** DRAFT — ready for execution

---

## 1. Executive Summary

The ZOZI database has completed **Phase 0** (inventory) and **Phase 1** (migration hardening) foundations. The Alembic chain is linear (head = `20260730_0003`), the dual-`Base` metadata bug is fixed, and 3 catch-up migrations are in place. However, significant gaps remain between the current state and the constitution's target architecture.

| Dimension | Current | Target | Gap |
|---|---|---|---|
| ORM tables | 282 | 282 | — |
| DB tables (SQLite) | 314 | ~282 + events + analytics | +32 orphan tables, missing event/analytics |
| Schema declarations (`__table_args__`) | 0 of 282 | 282 of 282 | **All models unclassified** |
| Standard column set (mixin adoption) | 0 of 282 | All business tables | **No mixin usage** |
| `country_code` width | `String(10)` on all 282 | `VARCHAR(3)` | Width mismatch everywhere |
| Event tables (outbox/inbox/DLQ) | 0 of 4 | 4 | **Missing entirely** |
| Analytics snapshots | 0 of 11 | 11 | **Missing entirely** |
| Native PostgreSQL RLS | 0 policies | ~154 tables | SQLAlchemy interceptor only |
| Bounded-context schemas | 0 | 16 | Phase 2 pending |
| Partitioning | 3 tables (migration only) | ~8 hot tables | Needs verification |
| `country_configs` columns | 85 | Split into 4 tables | Oversized monolith |

**Bottom line:** The foundation is solid (282 tables, linear migrations, unified metadata). The next work is **Phase 2** (schemas + event/analytics tables) and **Phase 3** (RLS + canonical patterns), followed by **Phase 5** (normalisation).

---

## 2. Detailed Gap Analysis

### 2.1 Schema Classification (Constitution §2.2, FR-1)
**Status: 🔴 Critical — 0% complete**

Every ORM model lacks `__table_args__ = {"schema": "<context>"}`. All 282 tables resolve in `public`. The constitution requires 16 bounded-context schemas:
- `core` (16), `commerce` (31), `supplier` (13), `customer` (9), `logistics` (28), `finance` (28), `treasury` (18), `hr` (35), `country` (21), `media` (8), `ai` (6), `communication` (53), `audit` (10), `security` (16), `analytics` (5), `configuration` (6)

**Impact:** No logical separation; every ecosystem shares one namespace; cross-schema queries impossible; RLS policies unorganised.

### 2.2 Standard Column Set / Mixins (Constitution §2.9)
**Status: 🔴 Critical — 0% mixin adoption**

`db/mixins.py` defines `AuditMixin`, `SoftDeleteMixin`, and `TimestampMixin`, but **no model inherits them**. Manual column usage is inconsistent:
- 98 tables have `created_at`/`updated_at` (but not via mixin)
- 17 tables have soft-delete columns
- 1 table has audit columns (`created_by`/`updated_by`)
- 0 tables have the full standard set

Constitution requires every business table to carry:
```
id, country_code, is_active, created_at, updated_at,
created_by, updated_by, is_deleted, deleted_at, deleted_by, version
```

**Impact:** Audit trail incomplete; soft-delete inconsistent; no optimistic locking; compliance risk.

### 2.3 Event-Driven Infrastructure (Constitution §2.13, ADR-014)
**Status: 🔴 Missing — 0 of 4 tables**

Required tables for transactional outbox pattern:
- `outbox_events` — service writes here in same transaction as business write
- `inbox_events` — consumer deduplication (`idempotency_key` UNIQUE)
- `event_retry_queue` — retry scheduling
- `event_dead_letter` — manual review queue

Current state: services publish events ad-hoc or not at all. No durable outbox means no reliable cross-ecosystem communication.

**Impact:** Cross-ecosystem decoupling impossible; event replay/recovery unavailable; audit gap.

### 2.4 Analytics Snapshots / Materialized Views (Constitution §2.15, ADR-008)
**Status: 🔴 Missing — 0 of 11 tables**

Required read-model tables:
- `mv_daily_sales`, `mv_monthly_sales`
- `kpi_customer`, `kpi_supplier`, `kpi_country`
- `kpi_revenue`, `kpi_orders`, `kpi_retention`, `kpi_conversion`
- `mv_cash_position`, `mv_facet_counts`

Current state: analytics queries hit transactional tables live (if they exist at all). No snapshot infrastructure.

**Impact:** Dashboard queries load the primary DB; p95 > 300ms likely at scale; no historical KPI tracking.

### 2.5 `country_code` Width (Constitution §2.9, App. F-c)
**Status: 🟡 Inconsistent — 282 tables use `String(10)`**

Constitution mandates `VARCHAR(3)`. Current reality:
- Most tables: `String(10)` (e.g., `users`, `products`, `orders`)
- Some tables already use `String(3)` (e.g., `account_balances`, `logistics_partner_documents`)
- The constitution itself notes this inconsistency

**Impact:** Storage waste; potential join/compare bugs; standardisation required before Phase 3 RLS.

### 2.6 `country_configs` Monolith (Constitution §2.6, §2.4b, Phase 5)
**Status: 🟡 85 columns in one table**

Current table mixes:
- Basics: `code`, `name`, `official_name`, `currency`, `currency_symbol`, `phone_code`, `language`, `timezone`, `date_format`, `flag_url`
- Economics: `exchange_rate_to_usd`, `population`, `internet_penetration_pct`, `gdp_per_capita_usd`, `urbanization_pct`, `mobile_subs_per_100`, `economic_tier`, `fraud_risk_tier`, `data_residency_tier`
- Tax: `tax_type`, `tax_rate`, `tax_name`, `tax_inclusive`, `tax_exempt_categories_json`, `tax_reduced_rates_json`
- Legal: `legal_rules_json`, `consumer_protection_days`, `data_privacy_framework`, `supplier_kyc_tier`, `legal_entity_required`

Constitution target: split into `country_basics`, `country_economics`, `country_tax`, `country_legal`.

**Impact:** Wide-row performance; unclear ownership; migration risk.

### 2.7 Variant / Product Pattern (Constitution §2.4, ADR-004/005)
**Status:** 🟡 Partial

**Categories:** Already use materialized path (`path`, `depth` columns). Constitution specifies `/1/15/42/` format. Current `path` values need audit.

**Variants:** `product_variants` has:
- ✅ `attributes_json` + `variant_key`
- ❌ Legacy flat columns still present: `size`, `color`, `material`, `pattern`, `gender`, `barcode`, `product_code`
- ❌ Missing GIN index on `attributes_json`

**Products:** Has legacy columns: `color`, `sizes`, `materials`, `filter_attributes`, `variant_axes`, `subcategory` (not in constitution standard set).

**Impact:** Schema drift; index inefficiency; migration debt.

### 2.8 Native PostgreSQL RLS (Constitution §2.6, §2.9, ADR-011)
**Status:** 🟡 Interceptor only — 154 mappings in `rls_interceptor.py`

Current: SQLAlchemy `before_execute` event injects `country_code IN (...)` filters.
Target: Native PostgreSQL `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` + `CREATE POLICY` per table, backed by `auth.country_access_check()` security-definer function.

**Impact:** Interceptor is dialect-specific, bypassable at raw-SQL level, adds query-plan overhead; native RLS is fail-closed.

### 2.9 Partitioning (Constitution §2.6, §7.2)
**Status:** 🟡 Migration exists, status unverified

Migration `20260729_2030` range-partitions `audit_logs`, `notifications`, `shipment_events`. Constitution targets monthly range partitions on hot append-only tables. Need to verify:
- Are partitions actually created in the live DB?
- Is the trigger/cron for partition creation in place?

### 2.10 Standard Naming & Conventions (Constitution §2.5, App. B)
**Status:** 🟡 Mostly compliant

- Snake_case, plural tables: ✅
- `is_*` booleans, `*_at` timestamps: ✅
- `country_code` present: ✅
- UUID for public refs: ❌ (no UUID columns found in ORM)
- `version` for optimistic locking: ❌ (not found)

### 2.11 Missing Indexes & FKs (Constitution §7, App. F-e)
**Status:** 🟡 Backlog exists

From `DATABASE_REFERENCE.md` schema audit:
- 62 single-index tables
- 44 tables missing FK constraints
- 694 `index_columns_mismatch` issues
- Constitution says add in Phase 5, **PostgreSQL only**

---

## 3. Implementation Plan (Phased)

### Guiding Principle
Each phase is independently shippable, reversible, and gated by `APP_ENV`. No phase touches behaviour unless intended. Tests must stay green throughout.

---

### Phase 0 — Freeze & Inventory ✅ COMPLETE
**Goal:** Establish single source of truth for what exists.

**Completed:**
- [x] Unified `models.Base` with `db.base.Base` (`models/__init__.py`)
- [x] Created `documents/DATABASE_REFERENCE.md` as operational companion
- [x] Fixed `validate_migrations.py` regex for typed/untyped migration declarations
- [x] Added 3 catch-up migrations: `20260730_0001` (`user_points`), `20260730_0002` (`points_transactions`), `20260730_0003` (`upload_jobs`)
- [x] Verified Alembic: `stamp=head`, linear chain, no multiple heads
- [x] Generated `backend/docs/schema_mapping.json` (282 tables → 16 schemas)
- [x] Ran schema audit: 282 ORM / 314 DB tables, 853 issues catalogued

**Deliverables:**
- `documents/DATABASE_REFERENCE.md`
- `backend/docs/schema_mapping.json`
- `backend/utils/schema_audit.py`
- `backend/scripts/validate_migrations.py`

---

### Phase 1 — Migration Pipeline Hardening ✅ COMPLETE
**Goal:** Ensure no schema change reaches prod except via reviewed Alembic migration.

**Completed:**
- [x] `db/database.py` prod guard raises on SQLite + `APP_ENV=production`
- [x] Linear Alembic chain verified (16 migrations, single head)
- [x] 3 missing migrations created and applied
- [x] Schema drift auditor created and run

**Remaining:**
- [ ] Add CI schema-drift gate (`alembic check` in GitHub Actions / CI script)
- [ ] Add migration contract-test harness (one test per migration asserting before/after shape)

**Risk:** Low. Foundation is solid.

---

### Phase 2 — Bounded-Context Schemas + Event/Analytics Tables ⏳ NEXT
**Goal:** Logical separation of 282 tables into 16 PostgreSQL schemas; introduce event/analytics infrastructure.

#### 2.1 Event & Analytics Tables (NEW — no data migration risk)
Create ORM models + Alembic migrations for:

**Event tables (§2.13):**
```python
# backend/models/events.py
class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = {"schema": "communication"}  # or dedicated schema

class InboxEvent(Base):
    __tablename__ = "inbox_events"
    # idempotency_key UNIQUE

class EventRetryQueue(Base):
    __tablename__ = "event_retry_queue"

class EventDeadLetter(Base):
    __tablename__ = "event_dead_letter"
```

**Analytics snapshot tables (§2.15):**
```python
# backend/models/analytics.py (extend existing)
class DailySales(Base): ...
class MonthlySales(Base): ...
class KPICustomer(Base): ...
# etc.
```

**Action:**
1. Add models to `backend/models/events.py` and `backend/models/analytics.py` (or create new files).
2. Create Alembic migration `20260730_0004_create_event_and_analytics_tables.py`.
3. Migration is idempotent (`CREATE TABLE IF NOT EXISTS` for SQLite; standard for Postgres).
4. No data migration; these are brand-new tables.
5. Update `DATABASE_REFERENCE.md` with new tables.

**Risk:** Very low. New tables only.

#### 2.2 Schema Declaration on All Models (HIGH RISK — requires careful migration)
Add `__table_args__ = {"schema": "<context>"}` to all 282 models.

**Approach:**
1. **Step A — Code change (no DB change yet):** Update `backend/docs/schema_mapping.json` to drive automated `__table_args__` injection. Write a script (`backend/scripts/apply_schema_decorators.py`) that:
   - Reads `schema_mapping.json`
   - For each model file, adds/updates `__table_args__ = {"schema": "<context>"}` (preserving existing indexes/constraints)
   - Runs `pre-commit` / `ruff` to validate syntax
2. **Step B — Alembic migration (DB change):** Create `20260730_0005_assign_bounded_context_schemas.py`:
   ```python
   # PostgreSQL: ALTER TABLE <table> SET SCHEMA <schema>
   # SQLite: no-op (SQLite ignores schema kwarg)
   if context.get_xbind().dialect.name == 'postgresql':
       for table_name, schema in mapping.items():
           op.execute(f'ALTER TABLE public.{table_name} SET SCHEMA {schema}')
   ```
3. **Step C — `search_path` update:** Update `db/database.py` to set `search_path = '<context>, public'` per session. For dev/SQLite, this is a no-op.
4. **Step D — Update `alembic/env.py`:** Ensure `target_metadata` reflects schema-qualified tables.

**Risk:** Medium-High. Must be tested on both SQLite (dev) and PostgreSQL (staging). Requires downtime-free deployment pattern:
- Deploy code with schema kwarg first (SQLite ignores it; Postgres tables still in `public`)
- Run migration to move tables to schemas
- Verify app behaviour unchanged

---

### Phase 3 — Country Isolation + Canonical Patterns ⏳ PENDING
**Goal:** Native PostgreSQL RLS; enforce materialized-path categories, JSONB variants, AI staging, finance ledger, config-as-data.

#### 3.1 Native PostgreSQL RLS (HIGH RISK)
Replace `rls_interceptor.py` SQLAlchemy-event-based filtering with native PostgreSQL RLS.

**Action:**
1. Create `backend/data/pg_rls_policies.sql` (or Alembic migration) that:
   - Creates `auth.country_access_check(p_country_code TEXT)` security-definer function
   - Enables `ENABLE ROW LEVEL SECURITY` + `FORCE ROW LEVEL SECURITY` on all ~154 country-aware tables
   - Creates `CREATE POLICY ... USING (country_code IS NULL OR auth.country_access_check(country_code))`
2. Update `backend/middleware/country_context.py` to set `app.current_country_code` via `SET LOCAL` instead of Python interceptor
3. Keep `rls_interceptor.py` as dev/SQLite fallback (SQLite has no native RLS)
4. Add security test: cross-country read returns empty set without correct session var

**Risk:** High. Must be fail-closed. Requires staging verification before prod.

#### 3.2 Canonical Patterns (Constitution §2.4)
**Categories → materialized path:**
- Verify `path` column format is `/1/15/42/` (not just `1/15/42`)
- Add `lft`/`rgt` columns if nested-set is needed for subtree queries
- Add GIN index on `path` for fast subtree lookups

**Variants → JSONB + GIN:**
- Migrate legacy flat columns (`size`, `color`, `material`, `pattern`, `gender`) into `attributes_json` JSONB
- Add GIN index on `attributes_json`
- Keep `variant_key` hash for equality lookups
- Make legacy columns nullable, then drop in later release (EXPAND → MIGRATE → CONTRACT)

**AI staging → explicit commit:**
- Verify `ai_upload_jobs` tracks all AI writes
- Ensure no AI service writes directly to `products`/`categories`

**Finance → ledger service:**
- Verify all money movements go through `journal_entries` + `journal_entry_lines`
- Add period-lock mechanism

**Risk:** Medium. Pattern migrations require data backfills.

---

### Phase 4 — Normalisation & Storage Fixes ⏳ PENDING
**Goal:** Resolve structural debt before it compounds.

#### 4.1 Split `country_configs` (85 cols → 4 tables)
**Action:**
1. Create `country_basics`, `country_economics`, `country_tax`, `country_legal`
2. Data-preserving migration: `INSERT INTO new SELECT cols FROM old`
3. Add 1:1 FKs back to `country_configs` (or replace entirely)
4. Resolve `country_code` width here: standardise all to `VARCHAR(3)`

#### 4.2 Standardise `country_code` Width
- Migration: `ALTER TABLE ... ALTER COLUMN country_code TYPE VARCHAR(3)` on all 282 tables
- **PostgreSQL only** (SQLite ignores column types)
- Do this **before** any joins or RLS policy creation

#### 4.3 Add Missing Indexes + FKs
- Add 10 high-priority composite indexes: `(country_code, created_at)`, `(status, due_date)`, `(entity_type, entity_id)`, `(supplier_id, is_active)`
- Add FK constraints to ~44 tables missing them
- **PostgreSQL only** (SQLite default B-tree; many indexes slow writes)

#### 4.4 Enforce Metadata-in-DB / Bytes-in-Object-Storage
- Audit `media_assets` and any table with `url`/`path` columns for inline byte storage
- Remove any `BLOB`/`LargeBinary` columns holding file bytes

**Risk:** Medium-High. Requires careful data migration and staging verification.

---

### Phase 5 — Governance Automation ⏳ PENDING
**Goal:** Make the constitution self-enforcing.

1. **Auto-regenerate data dictionary in CI:** Run `generate_data_dictionary.py` on every merged migration; fail build if diff is uncommitted.
2. **Ownership map enforcement:** CI warning on any table lacking schema/owner in `schema_mapping.json`.
3. **Drift gate:** `alembic check` + schema audit in CI on every PR.
4. **RLS coverage lint:** CI check that every `country_code` table is in `COUNTRY_AWARE_TABLES`.

---

## 4. Execution Order & Dependencies

```
Phase 0 ✅ ──► Phase 1 ✅ ──► Phase 2.1 (events/analytics tables) ──► Phase 2.2 (schema declarations)
                                                                    │
                                                                    ▼
                                                              Phase 3 (RLS + patterns)
                                                                    │
                                                                    ▼
                                                              Phase 4 (normalisation)
                                                                    │
                                                                    ▼
                                                              Phase 5 (governance)
```

**Critical path:**
1. Phase 2.1 (new tables) → zero risk, unblock analytics/events work
2. Phase 2.2 (schemas) → enables logical organisation for all subsequent phases
3. Phase 3.1 (RLS) → requires Phase 2.2 schemas for organised policy management
4. Phase 4.1 (`country_configs` split) → requires Phase 2.2 schemas for clean FK structure
5. Phase 4.2 (`country_code` width) → must happen before Phase 3.1 RLS policies

---

## 5. Risk Register & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Schema migration breaks queries | Medium | High | Deploy in EXPAND → MIGRATE → CONTRACT phases; test on staging Postgres first |
| RLS misconfiguration leaks data | Low | Critical | Fail-closed policies; dedicated security test; staged rollout |
| `country_code` migration locks tables | Medium | Medium | Batch ALTER in maintenance window; use `CONCURRENTLY` where possible |
| Analytics tables not populated | Medium | Medium | Backfill cron + on-write triggers; dashboards show loading state |
| Event tables unused by services | Medium | Medium | Instrument 3 critical paths first (order, payment, notification) |
| Mixin adoption causes regressions | Low | Medium | Add mixins to new tables first; migrate existing tables incrementally |

---

## 6. Success Criteria (Per Phase)

| Phase | Success Criteria |
|---|---|
| 0 | Single inventory doc; 282 ORM / 314 DB tables reconciled; linear Alembic |
| 1 | CI drift gate red on un-migrated change; all migrations have downgrade |
| 2.1 | 15 new tables present; Alembic clean; tests green |
| 2.2 | All 282 models declare schema; `search_path` set; app behaviour unchanged |
| 3.1 | Native RLS policies active; cross-country read returns empty without session var |
| 3.2 | Categories use materialized path; variants use JSONB+GIN; AI writes staged |
| 4.1 | `country_configs` split; `country_code` = `VARCHAR(3)` everywhere |
| 4.2 | 10 composite indexes added; 44 FKs added; no seq-scan on hot paths |
| 5 | Data dictionary auto-regenerated; orphan-table CI warning active |

---

## 7. Recommended Next Steps

1. **Immediate (this session):** Approve this plan and begin **Phase 2.1** — create event + analytics ORM models and migration. Zero risk, unblocks downstream work.
2. **Next session:** Begin **Phase 2.2** — script-assisted schema declaration injection + `ALTER TABLE SET SCHEMA` migration. Requires staging Postgres verification.
3. **Parallel track:** Start **Phase 4.2** (`country_code` width standardisation) early, as it must complete before Phase 3.1 RLS.
