# ZOZI Database Alignment Plan

## Goal
Align the current database structure with `documents/01_DATABASE.md` (v2.1, DRAFT) - the single source of truth for the database constitution.

## Executive Summary

From the audit (63641 debt score, 262 violations), the database is significantly out of alignment with the constitution. The plan follows the phased approach documented in §4 of 01_DATABASE.md.

---

## Phase 0: Freeze & Inventory (Immediate)

### Actions
1. **Regenerate canonical inventory**
   - Run `backend/scripts/generate_data_dictionary.py` → `GENERATED_DATA_DICTIONARY.md`
   - Reconcile table count: 262 live vs ~310 ORM models
   - Create definitive table → ecosystem ownership map (Appendix C)

2. **Verify model file count**
   - Current: 27 model files in `backend/models/`
   - Expected: ~270-310 ORM models
   - Missing: `country_basics.py`, `country_economics.py`, `country_tax.py` (already created)

3. **Document discrepancies** in a findings report

---

## Phase 1: Migration Pipeline Hardening (High Priority)

### Issues Found
- **Multiple Alembic heads**: `20260730_0005` and `20260730_0008` (DB13, DB24)
- **3 ORM-only tables** not in migrations: `points_transactions`, `upload_jobs`, `user_points`
- **create_all ungated in 5 locations** (DB02 violations)
- **Migration contract tests missing**

### Actions
1. **Merge Alembic heads**
   - Create merge migration in `backend/alembic/versions/`
   - Verify single head: `alembic current`

2. **Create missing migrations** for ORM-only tables
   - `20260730_0001`: `user_points` table
   - `20260730_0002`: `points_transactions` table  
   - `20260730_0003`: `upload_jobs` table

3. **Gate create_all**
   - Verify `backend/db/database.py` raises in production (already done)
   - Audit all 5 locations: `test_search_endpoints.py`, `promotion_engine_service.py`, `test_create_all.py`, `init_db.py`, `baseline_canonical_orm_schema_clean.py`
   - Ensure APP_ENV=development gate is airtight

4. **Add migration contract test harness**
   - Create `backend/tests/test_database.py` with 33 tests as specified

---

## Phase 2: Bounded-Context Schemas (Medium Priority)

### Issues Found
- **Cross-ecosystem FKs**: 262 violations (DB06)
- **Models missing schema declaration**: ~150 models (DB01)
- **Tables outside models/**: 11 tables in `backend/db/` (DB26)

### Actions
1. **Create PostgreSQL schemas**
   ```sql
   CREATE SCHEMA core, commerce, supplier, customer, logistics, finance, 
                    treasury, hr, country, media, ai, communication, 
                    audit, security, analytics, configuration;
   ```

2. **Move tables to schemas** (metadata-only)
   - Use `ALTER TABLE ... SET SCHEMA ...` for each table
   - Update models with `__table_args__ = {"schema": "<context>"}`

3. **Move ORM models from db/ to models/**
   - Tables: `offices`, `physical_id_cards`, `dynamic_qr_sessions`, `employee_biometrics`, `geo_fence_logs`, `employee_roles`, `employees`, `employee_attendance`, `employee_work_logs`, `employee_leave_requests`, `employee_shift_rosters`, `employee_assets`, `employee_certifications`, `employee_documents`, `employee_dependents`, `employee_relations`, `employee_addresses`, `coi_reports`, `media_assets`, `media_upload_sessions`

4. **Replace cross-ecosystem FKs with services/events**
   - This is a major refactoring per ADR-014
   - Create event-driven communication patterns

---

## Phase 3: Country Isolation (High Priority)

### Issues Found
- **RLS not enabled**: No `pg_rls_policies.sql` (DB05)
- **No RLS context setter**: Missing middleware (DB05)
- **country_code width mismatch**: VARCHAR(3) vs VARCHAR(10) (DB04)
- **31 tables missing composite indexes** on (country_code, created_at) (DB31)

### Actions
1. **Create RLS policy file**
   - Create `backend/data/pg_rls_policies.sql`
   - Add policies for all country-scoped tables

2. **Add RLS middleware**
   - Update `backend/utils/rls_interceptor.py` or create new middleware
   - Set `app.current_country_code` per request
   - Fail closed on missing context

3. **Fix country_code width**
   - Standardize to VARCHAR(3) per document
   - Create unifying migration before any joins

4. **Add composite indexes**
   - 31 tables need `(country_code, created_at)` indexes

---

## Phase 4: Canonical Pattern Enforcement (Medium Priority)

### Issues Found
- **Missing analytics snapshots**: 10 tables (DB30)
- **Missing event tables**: outbox/inbox/DLQ (DB13)
- **Missing canonical tables**: commission_rules, feature_flags, worm_audit (DB29)
- **Live aggregates in request paths**: 28 locations (DB19)
- **AI staging incomplete**: missing ai_embeddings, ai_requests, ai_results (DB21)

### Actions
1. **Create analytics snapshot tables**
   - `mv_daily_sales`, `mv_monthly_sales`, `kpi_customer`, `kpi_supplier`, `kpi_country`
   - `kpi_revenue`, `kpi_orders`, `kpi_retention`, `kpi_conversion`, `mv_cash_position`, `mv_facet_counts`

2. **Create event infrastructure tables**
   - `outbox_events`, `inbox_events`, `event_retry_queue`, `event_dead_letter`

3. **Create canonical platform tables**
   - `commission_rules`, `feature_flags`, `worm_audit`

4. **Replace live aggregates with snapshots**
   - 28 request paths need refactoring
   - Move to materialized views refreshed by cron

5. **Complete AI staging**
   - Create `ai_embeddings`, `ai_requests`, `ai_results` tables
   - Ensure all AI outputs go through staging → commit pattern

---

## Phase 5: Normalization & Storage Fixes (Low Priority)

### Issues Found
- **Wide table**: `country_configs` has 85 columns (documented finding *a*)
- **62 tables with single index** (DB11)
- **44 tables missing FK constraints** (documented finding *e*)

### Actions
1. **Split country_configs**
   - Create `country_basics`, `country_economics`, `country_tax`, `country_legal`
   - Data-preserving migration
   - Resolve country_code width mismatch here

2. **Add missing FK constraints**
   - 44 tables need FK definitions (PostgreSQL only)

3. **Add composite indexes**
   - 62 tables need composite indexes

---

## Phase 6: Governance Automation (Ongoing)

### Actions
1. **Auto-regenerate data dictionary in CI**
   - Run on every merged migration
   - Update `CODEBASE_STATUS_MATRIX.md`

2. **Add orphan table detection**
   - CI warning for tables without ecosystem/owner

3. **Create ERD generator**
   - Extend `generate_data_dictionary.py` to emit Mermaid ERD

---

## Production Checklist (Gate)

Before any production deployment:
- [ ] Indexes verified (EXPLAIN, no seq-scan on hot paths)
- [ ] FKs + constraints verified
- [ ] Backup taken AND restore tested
- [ ] Migration upgrade + downgrade tested
- [ ] Performance tested (load test, p95 < 300ms)
- [ ] Security tested (RLS fail-closed)
- [ ] Monitoring + alerts enabled
- [ ] Runbook + rollback documented
- [ ] Data dictionary regenerated
- [ ] ADR added if a decision changed

---

## Priority Ranking

| Priority | Issue | Phase |
|----------|-------|-------|
| **Critical** | Multiple Alembic heads | 1 |
| **Critical** | create_all ungated in production | 1 |
| **Critical** | RLS not enabled | 3 |
| **High** | Cross-ecosystem FK spaghetti | 2 |
| **High** | Missing migration contract tests | 1 |
| **Medium** | Tables outside models/ | 2 |
| **Medium** | Missing analytics snapshots | 4 |
| **Medium** | Missing event infrastructure | 4 |
| **Low** | country_code width mismatch | 3 |
| **Low** | Wide country_configs table | 5 |

---

## Rollback Strategy

- Each phase is independently reversible
- Migrations have downgrades
- Pre-migration snapshots taken
- Feature flags can disable new behavior

---

## Files to Create/Modify

### Create
- `backend/alembic/versions/merge_heads_*.py`
- `backend/alembic/versions/20260730_0001_user_points.py`
- `backend/alembic/versions/20260730_0002_points_transactions.py`
- `backend/alembic/versions/20260730_0003_upload_jobs.py`
- `backend/data/pg_rls_policies.sql`
- `backend/tests/test_database.py`
- Analytics snapshot tables (via migrations)
- Event tables (via migrations)

### Modify
- `backend/db/database.py` - verify create_all gate
- `backend/models/*.py` - add schema declarations, move models
- `backend/utils/config.py` - verify pool settings (5/10)
- `backend/scripts/generate_data_dictionary.py` - add ERD generation

---

## Success Metrics

- 100% schema changes via reviewed migration
- CI drift gate green on all changes
- 100% RLS coverage on country-scoped tables
- 0 cross-country leak in tests
- Hot-list p95 < 300ms
- Data dictionary regenerated on 100% of merged migrations
- 0 orphan tables