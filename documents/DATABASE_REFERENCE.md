# ZOZI Database Reference

**Single source of truth for the live database state.**  
This file is the operational companion to `documents/scope/01_DATABASE.md`.  
Where the constitution defines target rules, this file records actuals.

---

## 1. Current Inventory

| Metric | Value | Source |
|--------|-------|--------|
| ORM-declared tables | **282** | `Base.metadata.tables` (unified `models.Base` == `db.base.Base`) |
| Live DB tables (SQLite dev) | **314** | `sqlite_master` |
| Extra DB-only tables | **32** | Tables without ORM models |
| Model files | **27** | `backend/models/*.py` |
| Alembic migrations | **16** | `backend/alembic/versions/` |
| Current head | `20260730_0003` | Linear chain |
| Current stamp | `20260730_0003` | `alembic_version` |
| RLS table registry | **~150** mappings | `utils/rls_interceptor.py` |

---

## 2. Schema Organization (Current)

All 313 ORM tables currently reside in the **`public`** PostgreSQL schema  
(target per constitution: 16 bounded-context schemas — see §2.2 of constitution).

Model files by domain (informal grouping; no `__table_args__["schema"]` yet):

| Domain | Model file | Table count |
|--------|-----------|-------------|
| Core / Users | `core.py`, `user.py` | ~30 |
| Products / Catalog | `products.py`, `media_models.py` | ~12 |
| Orders | `orders.py` | ~5 |
| Payments / Finance | `payments.py`, `finance.py` | ~50 |
| Logistics | `logistics.py` | ~20 |
| Suppliers | `suppliers.py`, `ai_upload.py`, `upload_job.py` | ~15 |
| Countries / Config | `countries.py`, `country_enhancements.py`, `country_control.py` | ~30 |
| Communication | `communication.py` | ~25 |
| HR / Employees | `employee_models.py`, `employee_risk_scores.py`, `employee_active_tasks.py`, `employee_audit_timeline.py` | ~50 |
| Admin / System | `admin.py` | ~40 |
| Fraud / Security | `fraud.py` | ~15 |
| Marketing | `marketing.py` | ~10 |
| Permissions | `permissions.py` | ~8 |
| Imports / Trading | `imports.py`, `trading.py` | ~15 |
| Misc | `commission.py`, `onboarding.py`, `incident.py`, `mixins.py` | ~15 |

---

## 3. Engine & Pool Configuration

| Setting | Dev (SQLite) | Prod (PostgreSQL) |
|---------|-------------|-------------------|
| Driver | `sqlite` | `postgresql` |
| Pool | `StaticPool` | `QueuePool` |
| `pool_size` | — | **5** |
| `max_overflow` | — | **10** |
| `pool_recycle` | — | 1800s |
| `pool_pre_ping` | — | `True` |
| `pool_timeout` | — | 10s |
| WAL / pragmas | `journal_mode=WAL`, `busy_timeout=5000`, 32MB cache, 64MB mmap | — |
| PgBouncer | Not configured | Supported via `DB_BEHIND_PGBOUNCER` |
| SSL | — | `sslmode=require` via env |
| Prod guard | `create_all` raises on Postgres + `APP_ENV=production` | ✅ |

File: `backend/db/database.py`

---

## 4. Migration Status

### 4.1 Chain (linear)

```
b81bfc888610 (baseline)
  └─ 20260726_20_27 → 20260726_21_30 → 20260726_22_00
       └─ 20260727_00_32 → 20260727_09_08
            └─ 20260728_0000 → 20260728_19_30 → 20260728_21_14
                 └─ 20260729_10_17 → 20260729_10_28
                      └─ 20260729_19_14 → 20260729_2030 → 20260730_0001 → 20260730_0002 → 20260730_0003 (head)
```

### 4.2 Recent migrations

| Revision | Purpose |
|----------|---------|
| `20260730_0003` | `upload_jobs` table migration |
| `20260730_0002` | `points_transactions` table migration |
| `20260730_0001` | `user_points` table migration |
| `20260729_2030` | Range-partition `audit_logs`, `notifications`, `shipment_events` |
| `20260729_1914` | `products.search_vector` tsvector + trigger + GIN |
| `9ff24a0683dd` | Schema drift check (unique constraints, missing indexes) |
| `e281faa0c087` | Orphaned employee HR tables |
| `87146598d2c3` | Missing FK constraints |
| `e8efae30fc29` | Missing indexes + constraints |
| `20260728_0000` | Employee HR/system tables |
| `20260727_0908` | Check constraints on status enums |
| `c0f3f1817791` | Production Postgres indexes + partitioning prep |
| `e70b2cb9a90f` | Fix internal channels FK |
| `c9e8f7d6a5b4` | Communication gap tables |
| `b81bfc888610` | Baseline canonical ORM schema clean |

### 4.3 Known migration issues

| Issue | Status |
|-------|--------|
| `validate_migrations.py` regex broken on typed annotations | ✅ Fixed |
| 3 ORM-only tables missing migrations (`points_transactions`, `upload_jobs`, `user_points`) | ✅ Created `20260730_0001`–`20260730_0003` |
| Downgrade incomplete on `9ff24a0683dd` (SQLite batch alter table limitation) | 🟡 Acceptable for SQLite dev |
| `20260729_1914` Revises `9ff24a0683dd`; `20260729_2030` Revises `20260729_1914`; `20260730_0001`–`0003` Revises `20260729_2030` — chain is linear | ✅ |

---

## 5. Mixins

Defined in `backend/db/mixins.py`:

| Mixin | Columns | Used by models |
|-------|---------|----------------|
| `AuditMixin` | `created_at`, `updated_at`, `created_by`, `updated_by` | ❌ **0 models** |
| `SoftDeleteMixin` | `is_deleted`, `deleted_at`, `deleted_by` | ❌ **0 models** |
| `TimestampMixin` | `created_at`, `updated_at` | ❌ **0 models** |

All models manually redeclare audit/timestamp columns.  
Constitution §2.9 mandates mixin adoption — target for Phase 5.

---

## 6. RLS & Multi-Tenancy

| Component | Status |
|-----------|--------|
| SQLAlchemy `before_execute` interceptor | ✅ Active (`utils/rls_interceptor.py`) |
| Country-aware table registry | ✅ ~150 tables mapped |
| Context propagation | ✅ `rls_country_scope_ctx` ContextVar |
| Native PostgreSQL `CREATE POLICY` | ❌ Not yet created |
| `FORCE ROW LEVEL SECURITY` | ❌ Not yet enabled |
| `search_path` per-schema isolation | ❌ Not yet implemented |

---

## 7. Full-Text Search

| Feature | Status |
|---------|--------|
| `products.search_vector` column | ✅ `_TsVector` TypeDecorator (tsvector on Postgres, Text on SQLite) |
| PL/pgSQL trigger | ✅ `products_search_vector_trigger` |
| GIN index | ✅ `ix_products_search_vector_gin` |
| `pg_trgm` extension | ✅ Created in migration |
| `LIKE '%kw%'` elimination | 🟡 Partial — needs full audit |

---

## 8. Partitioning

| Table | Status |
|-------|--------|
| `audit_logs` | ✅ Range-partitioned by `created_at` (monthly) |
| `notifications` | ✅ Range-partitioned by `created_at` (monthly) |
| `shipment_events` | ✅ Range-partitioned by `created_at` (monthly) |
| `journal_entries` | 🟡 Constitution target; not yet partitioned |
| `chat_messages` | 🟡 Constitution target; not yet partitioned |
| `product_variants` | 🟡 Constitution target (hash by `product_id` at >10M rows) |

---

## 9. AI / Media Pipeline

| Feature | Status |
|---------|--------|
| `ai_upload_jobs` | ✅ ORM model exists |
| `ai_staging_products` | ✅ ORM model exists |
| `ai_staging_variants` | ✅ ORM model exists |
| `ai_generation_logs` | ✅ ORM model exists |
| Staging → explicit commit flow | 🟡 Tables exist; service-layer enforcement unverified |
| Storage abstraction | ✅ `services/storage.py` (Local + S3) |
| Presigned upload | ✅ `routers/upload.py` |
| Media bytes in object storage | 🟡 Partial — some local paths remain |

---

## 10. Event-Driven Architecture

| Table | Status |
|-------|--------|
| `outbox_events` | ❌ Does not exist |
| `inbox_events` | ❌ Does not exist |
| `event_retry_queue` | ❌ Does not exist |
| `event_dead_letter` ❌ Does not exist |

Constitution §2.13 requires these for cross-ecosystem communication.  
Target: Phase 4.

---

## 11. Analytics Snapshots

| View / Table | Status |
|--------------|--------|
| `mv_daily_sales` | ❌ Does not exist |
| `mv_monthly_sales` | ❌ Does not exist |
| `kpi_customer` | ❌ Does not exist |
| `kpi_supplier` | ❌ Does not exist |
| `kpi_country` | ❌ Does not exist |
| `kpi_revenue` | ❌ Does not exist |
| `kpi_orders` | ❌ Does not exist |
| `kpi_retention` | ❌ Does not exist |
| `kpi_conversion` | ❌ Does not exist |
| `mv_cash_position` | ❌ Does not exist |
| `mv_facet_counts` | ❌ Does not exist |

Constitution §2.15 requires materialized views / snapshot tables.  
Target: Phase 4/6.

---

## 12. Schema Audit Summary (Latest Run)

```
Tables: DB=314  ORM=282
Issues: 853 total
  table_extra_in_db: 32 (DB tables without ORM models)
  column_extra_in_db: 20
  column_default_mismatch: 9
  column_type_mismatch: 3
  fk_extra_in_db: 2
  index_columns_mismatch: 694
  index_extra_in_db: 93
```

**Note:** 694 of 853 issues are `index_columns_mismatch`. This reflects that
the live DB was largely created via `create_all` and incremental migrations,
while the ORM now declares many more indexes than have been migrated.

### 12.1 Extra DB Tables (no ORM model)

32 tables exist in the database but have no corresponding ORM model class:

| Table | Notes |
|-------|-------|
| `alembic_version` | Alembic stamping (expected) |
| `chat_attachments` | Chat feature |
| `chat_legal_holds` | Chat feature |
| `chat_reactions` | Chat feature |
| `chat_read_receipts` | Chat feature |
| `country_communication_templates` | Country config |
| `customs_entries` | Imports/trading |
| `email_folders` | Communication |
| `employee_active_tasks` | Orphaned table (has model in `db/employee_models.py`, registered under old `db.base.Base`) |
| `employee_activity_logs` | HR/employees |
| `employee_audit_timeline` | HR/employees |
| `employee_bank_accounts` | HR/employees |
| `employee_risk_scores` | HR/employees |
| `goods_receipt_lines` | Logistics/suppliers |
| `goods_receipt_notes` | Logistics/suppliers |
| `import_cost_templates` | Imports/trading |
| `import_shipment_lines` | Imports/trading |
| `import_shipments` | Imports/trading |
| `internal_emails` | Communication |
| `kpi_metrics` | Analytics |
| `landed_cost_allocations` | Finance/logistics |
| `okr_objectives` | HR/employees |
| `performance_reviews` | HR/employees |
| `points_transactions` | Loyalty (now has migration `20260730_0002`) |
| `purchase_order_lines` | Suppliers/procurement |
| `purchase_orders` | Suppliers/procurement |
| `sales_order_lines` | Orders/sales |
| `sales_orders` | Orders/sales |
| `stock_movements` | Logistics/inventory |
| `upload_jobs` | AI/media pipeline (now has migration `20260730_0003`) |
| `user_points` | Loyalty (now has migration `20260730_0001`) |
| `warehouses` | Logistics/inventory |

---

## 14. Phase 2 — Bounded-Context Schema Mapping

Per constitution §2.2, all 282 ORM tables are mapped to 16 PostgreSQL schemas.
Migration is metadata-only: `ALTER TABLE ... SET SCHEMA ...` does not rewrite data.

### 14.1 Schema inventory

| Schema | Tables | Owner | Examples |
|--------|--------|-------|---------|
| `core` | 16 | Identity | users, roles, sessions, devices, api_keys |
| `commerce` | 31 | Commerce | products, variants, categories, carts, orders, banners |
| `supplier` | 13 | Supplier Ops | supplier_profiles, supplier_documents, purchase_orders |
| `customer` | 9 | Customer | customers, addresses, wishlists, points, referrals |
| `logistics` | 28 | Logistics | partners, shipments, shipping, warehouses, stock_movements |
| `finance` | 28 | Finance (strictest) | accounts, journal, ledger, AR/AP, invoices, payments |
| `treasury` | 18 | Treasury | cash, payouts, bank_accounts, reconciliation |
| `hr` | 35 | People | employees, attendance, shifts, leave, performance, onboarding |
| `country` | 21 | Country Ops | country_configs, cities, tax_rates, commission_rates |
| `media` | 8 | Media/AI | media_assets, videos, video_rooms, ocr_results |
| `ai` | 6 | Media/AI | ai_upload_jobs, staging, generation_logs, chatbot |
| `communication` | 53 | Comms | chat, email, notifications, tickets, proxies, meetings |
| `audit` | 10 | Governance | audit_logs, admin_logs, system_events, retention |
| `security` | 16 | Risk | fraud, blacklist, risk_scores, ip_reputation, kyc |
| `analytics` | 5 | Data | kpi_metrics, financial_reports, webhook_events |
| `configuration` | 6 | Platform | system_settings, feature_flags, email_configs, legal_templates |

**Total: 282 tables across 16 schemas**

### 14.2 Full table-to-schema mapping

Stored in `backend/docs/schema_mapping.json` (generated from live ORM metadata).
Use this file to drive:
1. Model `__table_args__={"schema": "<context>"}` updates
2. Alembic migration `ALTER TABLE ... SET SCHEMA ...` statements
3. `search_path` configuration per ecosystem

### 14.3 Migration approach

- **Step 1:** Add `schema="<context>"` to each model's `__table_args__` (or class-level `__table_args__`).
- **Step 2:** Create a single Alembic migration that issues `ALTER TABLE <table> SET SCHEMA <schema>` for all 282 tables.
  - On PostgreSQL: native `ALTER TABLE ... SET SCHEMA` (metadata-only, instant).
  - On SQLite: no-op (SQLite doesn't support schemas); the `schema` kwarg is ignored by SQLAlchemy's SQLite dialect.
- **Step 3:** Update `db/database.py` to set `search_path = '<context>, public'` per request or per session.
- **Step 4:** Verify ` alembic upgrade head` works on both SQLite (dev) and PostgreSQL (staging/prod).
- **Done when:** every model resolves under its schema; app behavior unchanged; tests green.

### 14.4 SQLite compatibility

SQLite does not support PostgreSQL schemas. The migration must be conditional:
```python
if context.get_xbind().dialect.name == 'postgresql':
    # ALTER TABLE ... SET SCHEMA ...
else:
    # no-op on SQLite
```

---

## 13. Open Governance Findings (from constitution App. F)

| ID | Finding | Target Phase |
|----|---------|--------------|
| (a) | Table count discrepancy (262 / 263 / ~270 / ~310) | ✅ Resolved — 282 ORM / 314 DB tables reconciled |
| (b) | Confirm prod has no seeded credentials | Phase 0 |
| (c) | `country_code` width mismatch `VARCHAR(3)` vs `(10)` | Phase 5 |
| (d) | Stale "0 migration files" audit claim | ✅ Resolved (ADR-018) |
| (e) | 62 single-index tables, 44 missing FKs | Phase 5 |
| (f) | **Dual `Base` classes** (`db.base.Base` vs `models.Base`) caused schema audit to report 0 ORM tables | ✅ Resolved — `models/__init__.py` now imports `Base` from `db.base`, unifying metadata |

---

## 14. Quick Reference — Key Files

| Purpose | Path |
|---------|------|
| Engine + pool | `backend/db/database.py` |
| Declarative base | `backend/db/base.py` |
| Mixins | `backend/db/mixins.py` |
| All ORM models | `backend/models/` (27 files) |
| Alembic config | `backend/alembic.ini` |
| Alembic env | `backend/alembic/env.py` |
| Migrations | `backend/alembic/versions/` |
| Schema audit | `backend/utils/schema_audit.py` |
| Migration validator | `backend/scripts/validate_migrations.py` |
| RLS interceptor | `backend/utils/rls_interceptor.py` |
| Storage abstraction | `backend/services/storage.py` |
| Background jobs | `backend/utils/background_jobs.py` |
| Cache helpers | `backend/utils/cache.py` |
| Constitution | `documents/scope/01_DATABASE.md` |

---

## 15. Execution Progress

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 0 — Freeze & inventory | ✅ Complete | 282 ORM / 314 DB tables reconciled |
| Phase 1 — Migration hardening | ✅ Complete | Validator fixed, 3 missing migrations added, linear chain to `20260730_0003` |
| Phase 1.5 — Schema audit fix | ✅ Complete | Unified `models.Base` with `db.base.Base` by changing `models/__init__.py` to import `Base` from `db.base`; schema audit now correctly reports 282 ORM tables |
| Phase 2 — Bounded-context schemas | ⏳ Pending | Metadata-only `ALTER TABLE SET SCHEMA` |
| Phase 3 — Country isolation | ⏳ Pending | Native RLS policies + partitioning |
| Phase 4 — Canonical patterns | ⏳ Pending | FTS, AI staging, events, analytics |
| Phase 5 — Normalization + storage | ⏳ Pending | `country_configs` split, indexes, FKs |
| Phase 6 — Governance automation | ⏳ Pending | CI gates, auto-generated docs |
