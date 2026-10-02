# Forensic Audit: Alembic Migrations

**Status:** VERIFIED — state changed since 2026-09-30  
**Date:** 2026-10-01  
**Scope:** backend/alembic/versions/*.py, backend/alembic/env.py, backend/alembic/alembic.ini

## Summary

| Metric | Value |
|--------|-------|
| Total migration files | 75 |
| Baseline migrations | 1 (`b81bfc888610`) |
| Current head | `20261001_0001` |
| Divergent heads | 5 (`20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`) |
| Missing down revisions | 0 |
| Naming convention violations | 64/66 (97%) |
| Merge migration anomalies | 1 (`2026_09_03_0000`) |
| Missing model indexes | 6 models with no explicit Index declarations |

**project_completion_blocker:** yes — 64 of 66 migration filenames violate `check_migration_naming.py`, and one merge migration (`2026_09_03_0000`) claims to join two revisions that are in the same linear chain (not actually divergent). Additionally, `alembic heads` cannot execute at runtime because `backend/alembic/` shadows the installed `alembic` package when running from the `backend` directory.

> **State change note:** The 2026-09-30 audit reported 0 divergent heads with head `20260930_0001`. Between 2026-09-30 and 2026-10-01, 4 new migration files were added (`20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`) plus `20261001_0001` on 2026-10-01. These were not wired into the existing linear chain, creating 5 new divergent heads.

---

## Migration Chain Audit

| # | Revision | Filename | Down Revision | Head Status | Op Type | Destructive | Expand-Contract | Backward Compatible | Long-running | Index Concurrent | Staging Tested | DATABASE_URL_DIRECT | Naming OK | Notes |
|---|----------|----------|---------------|-------------|---------|-------------|-----------------|---------------------|--------------|------------------|----------------|---------------------|-----------|-------|
| 1 | b81bfc888610 | 2026_07_26_16_09-b81bfc888610_baseline_canonical_orm_schema_clean.py | None | Baseline | add col, add idx | No | N/A | Yes | No | No | Unknown | Yes | No | Baseline; down_revision=None is correct |
| 2 | c9e8f7d6a5b4 | 2026_07_26_21_30_c9e8f7d6a5b4_add_communication_gap_tables.py | b81bfc888610 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | Creates 12 communication tables |
| 3 | 837e1e29bd49 | 2026_07_26_20_27-837e1e29bd49_add_banner_layout_json.py | c9e8f7d6a5b4 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | Adds layout_json to banners |
| 4 | e70b2cb9a90f | 2026_07_26_22_00-e70b2cb9a90f_fix_internal_channels_fk.py | 837e1e29bd49 | Intermediate | add fk | No | N/A | Yes | No | No | Unknown | Yes | No | Batch mode FK add |
| 5 | c0f3f1817791 | 2026_07_27_00_32-c0f3f1817791_add_production_postgres_indexes.py | e70b2cb9a90f | Intermediate | create idx | No | N/A | Yes | No | No | Unknown | Yes | No | pg_trgm + GIN indexes |
| 6 | 20260727_0908 | 2026_07_27_09_08-20260727_0908_add_check_constraints_to_status_enum_columns.py | c0f3f1817791 | Intermediate | add constraint | No | N/A | Yes | No | No | Unknown | Yes | No | Check constraints on enums |
| 7 | 20260728_0000 | 2026_07_28_0000_employee_hr_tables.py | 20260727_0908 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | 10 HR tables; downgrade drops all |
| 8 | e8efae30fc29 | 2026_07_28_19_30-e8efae30fc29_add_missing_indexes_and_constraints.py | 20260728_0000 | Intermediate | create idx | No | N/A | Yes | No | No | Unknown | Yes | No | ~80 indexes; IF NOT EXISTS |
| 9 | 87146598d2c3 | 2026_07_28_21_14-87146598d2c3_add_missing_fk_constraints_for_.py | e8efae30fc29 | Intermediate | add fk | No | N/A | Yes | No | No | Unknown | Yes | No | Batch mode FK add |
| 10 | e281faa0c087 | 2026_07_29_10_17-e281faa0c087_add_orm_models_for_orphaned_employee_.py | 87146598d2c3 | Intermediate | add idx, add fk | No | N/A | Yes | No | No | Unknown | Yes | No | Idempotent SQLite-aware |
| 11 | 9ff24a0683dd | 2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py | e281faa0c087 | Intermediate | alter idx | No | N/A | Partial | No | No | Unknown | Yes | No | Downgrade incomplete (SQLite) |
| 12 | 20260729_1914 | 2026_07_29_19_14-20260729_1914_add_products_search_vector_trigger.py | 9ff24a0683dd | Intermediate | add col, trigger | No | N/A | Yes | No | No | Unknown | Yes | No | tsvector + GIN on products |
| 13 | 20260729_2030 | 2026_07_29_20_30-20260729_2030_add_postgres_range_partitioning_audit_notif.py | 20260729_1914 | Intermediate | partition | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | INSERT...SELECT on large tables; row-locks only |
| 14 | 20260730_0001 | 2026_07_30_0001-20260730_0001_create_user_points_table.py | 20260729_2030 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | loyalty.user_points |
| 15 | 20260730_0002 | 2026_07_30_0002-20260730_0002_create_points_transactions_table.py | 20260730_0001 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | loyalty.points_transactions |
| 16 | 20260730_0003 | 2026_07_30_0003-20260730_0003_create_upload_jobs_table.py | 20260730_0002 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | ai.upload_jobs |
| 17 | 20260730_0004 | 2026_07_30_0004-20260730_0004_create_event_tables.py | 20260730_0003 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | 4 event-bus tables in analytics |
| 18 | 20260730_0005 | 2026_07_30_0005-20260730_0005_bounded_context_schema_migration.py | 20260730_0004 | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | ALTER TABLE SET SCHEMA x 300+ tables |
| 19 | 20260801_0018 | 2026_08_01_0018-20260801_0018_move_lms_tables_to_hr_schema.py | 20260730_0005 | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Moves training_modules, employee_trainings |
| 20 | 20260805_0001 | 2026_08_05_0001-rename_return_deadline_to_return_deadline_at.py | 20260801_0018 | Intermediate | rename col | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | ALTER TABLE RENAME COLUMN |
| 21 | 20260806_0001 | 2026_08_06_0001_add_analytics_audit_columns.py | 20260805_0001 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | safe_add_column idempotent |
| 22 | 20260806_0002 | 2026_08_06_0001_media_add_audit_softdelete_mixins_and_rename_ai_result.py | 20260806_0001 | Intermediate | add col, rename col | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | DBA11 rename ai_result->ai_result_json |
| 23 | 20260806_0003 | 2026_08_06_0003-20260806_0003_baseline_sync_orm_tables.py | 20260806_0002 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | Guards per table; idempotent |
| 24 | 20260806_0004 | 2026_08_06_0004-catalog_categories_dba03_audit_softdelete.py | 20260806_0003 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | commerce.categories mixins |
| 25 | 20260806_0005 | 2026_08_06_0005-dba03_version_column_backfill.py | 20260806_0004 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | version on ~90 tables |
| 26 | 20260806_0006 | 2026_08_06_0006-upload_jobs_table.py | 20260806_0005 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | ai.upload_jobs (new table) |
| 27 | 20260806_0007 | 2026_08_06_0007_supplier_badge_and_risk_tables.py | 20260806_0006 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | 3 supplier/hr tables |
| 28 | 20260806_0008 | 2026_08_06_0008_role_permission_setting_maker_checker.py | 20260806_0007 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | Batch mode column add |
| 29 | 20260806_0009 | 2026_08_06_0009_promotion_ledger_order_id.py | 20260806_0008 | Intermediate | add col, add idx | No | N/A | Yes | No | No | Unknown | Yes | No | Batch mode column add |
| 30 | 20260808_0001 | 2026_08_08_0001_supplier_document_profile_columns.py | 20260806_0009 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | safe_add_column idempotent |
| 31 | ccw_unify_20260809 | 2026_08_09_0000-ccw_unify_20260809_unify_country_code_width.py | 20260808_0001 | Intermediate | alter col | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | ALTER COLUMN TYPE String(3); idempotent |
| 32 | 20260810_emp_act_log | 2026_08_10_1930-20260810_emp_act_log_create_employee_activity_logs.py | ccw_unify_20260809 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | logistics schema |
| 33 | 20260811_otp_codes | 2026_08_11_0000-20260811_otp_codes.py | 20260810_emp_act_log | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | core schema |
| 34 | 20260821_split_commerce | 2026_08_21_0001-20260821_split_commerce_schema.py | 20260811_otp_codes | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | 29 tables moved to bounded contexts |
| 35 | 20260821_core_to_accounts | 2026_08_21_0002-20260821_core_to_accounts_schema.py | 20260821_split_commerce | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Renames core->accounts schema |
| 36 | 20260821_hr_shift_handover_task | 2026_08_21_0003-20260821_hr_shift_handover_task.py | 20260821_core_to_accounts | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Code move only; no DDL |
| 37 | 20260821_hr_onboarding | 2026_08_21_0004-20260821_hr_onboarding.py | 20260821_hr_shift_handover_task | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Code move only; no DDL |
| 38 | 20260821_crosscutting_domains | 2026_08_21_0005-20260821_crosscutting_domains.py | 20260821_hr_onboarding | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Code move only; no DDL |
| 39 | 20260821_customer_comm_logistics_media | 2026_08_21_0006-20260821_customer_comm_logistics_media.py | 20260821_crosscutting_domains | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Code move only; no DDL |
| 40 | 20260821_user_referral_to_customer | 2026_08_21_0007-20260821_user_referral_to_customer.py | 20260821_customer_comm_logistics_media | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Code move only; no DDL |
| 41 | 20260822_country_to_country_schema | 2026_08_22_0001-20260822_country_to_country_schema.py | 20260821_user_referral_to_customer | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | 16 tables moved to country |
| 42 | 20260822_communication_to_comms_schema | 2026_08_22_0002-20260822_communication_to_comms_schema.py | 20260822_country_to_country_schema | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Renames communication->comms |
| 43 | 20260822_governance_schema_consolidation | 2026_08_22_0003-20260822_governance_schema_consolidation.py | 20260822_communication_to_comms_schema | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | 30 tables moved to governance |
| 44 | 20260822_supplier_to_suppliers_schema | 2026_08_22_0004-20260822_supplier_to_suppliers_schema.py | 20260822_governance_schema_consolidation | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Renames supplier->suppliers |
| 45 | 20260822_pluralize_supplier_table_names | 2026_08_22_0005-20260822_pluralize_supplier_table_names.py | 20260822_supplier_to_suppliers_schema | Intermediate | rename table | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | 3 tables pluralized |
| 46 | 20260822_governance_out_of_audit_schema | 2026_08_23_0001-20260823_governance_out_of_audit_schema.py | 20260822_pluralize_supplier_table_names | Intermediate | alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | 5 tables audit->governance |
| 47 | 20260827_audit_logs_worm_hash | 2026_08_27_0001-20260827_audit_logs_worm_hash.py | 20260822_governance_out_of_audit_schema | Intermediate | add col, add idx | No | N/A | Yes | No | No | Unknown | Yes | No | WORM hash columns |
| 48 | 20260831_0001 | 2026_08_31_0001_add_governance_schema.py | 20260827_audit_logs_worm_hash | Intermediate | create schema, alter schema | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Creates governance schema |
| 49 | 20260831_0002 | 2026_08_31_0002_add_uuid_columns.py | 20260831_0001 | Intermediate | add col | No | N/A | Yes | **Yes** | No | No | Unknown | Yes | No | UUID backfill on ~80 tables; UPDATE long-running |
| 50 | 20260831_0003 | 2026_08_31_0003_add_version_columns.py | 20260831_0002 | Intermediate | add col | No | N/A | Yes | **Yes** | No | No | Unknown | Yes | No | Version columns on ~30 tables |
| 51 | 20260831_0004 | 2026_08_31_0004_add_composite_indexes.py | 20260831_0003 | Intermediate | create idx | No | N/A | Yes | No | No | No | Unknown | Yes | No | Composite + partial indexes |
| 52 | 20260831_0005 | 2026_08_31_0005_add_materialized_views.py | 20260831_0004 | Intermediate | create mv | No | N/A | Yes | No | No | Unknown | Yes | No | 7 materialized views |
| 53 | 20260831_0006 | 2026_08_31_0006_add_partitioning.py | 20260831_0005 | Intermediate | partition | No | N/A | Yes | **Yes** | No | Unknown | Yes | No | Range partitioning on 4 tables |
| 54 | 20260901_workspace | 2026_09_01_workspace.py | 20260831_0006 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | 5 hr/comms tables + seed data |
| 55 | 2026_09_03_0000 | 2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py | (20260831_0001, 20260901_workspace) | Merged | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | **ANOMALY: merges non-divergent heads** |
| 56 | 2026_09_03_0001 | 2026_09_03_0001_add_audit_logs_missing_columns.py | 2026_09_03_0000 | Intermediate | add col, add idx | No | N/A | Yes | Partial | No | No | Unknown | Yes | No | WORM downgrade no-op |
| 57 | 2026_09_03_0002 | 2026_09_03_0002_add_audit_logs_composite_indexes.py | 2026_09_03_0001 | Intermediate | create idx | No | N/A | Yes | No | No | No | Unknown | Yes | No | 5 composite indexes |
| 58 | 2026_09_03_0003 | 2026_09_03_0003_create_audit_command_center_views.py | 2026_09_03_0002 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | audit.command_center_views |
| 59 | 2026_09_03_0004 | 2026_09_03_0004_audit_logs_fulltext_search_vector.py | 2026_09_03_0003 | Intermediate | add col, trigger | No | N/A | Yes | No | No | Unknown | Yes | No | tsvector + GIN + trigger |
| 60 | 2026_09_03_0005 | 2026_09_03_0005_add_country_code_to_law5_models.py | 2026_09_03_0004 | Intermediate | add col, add idx | No | N/A | Yes | No | No | Unknown | Yes | No | country_code on 54 tables |
| 61 | 2026_09_03_0006 | 2026_09_03_0006_add_performance_indexes.py | 2026_09_03_0005 | Intermediate | create idx | No | N/A | Yes | No | No | Unknown | Yes | No | ~40 performance indexes |
| 62 | 2026_09_03_0007 | 2026_09_03_0007_add_payments_schema_models.py | 2026_09_03_0006 | Intermediate | create table | No | N/A | Yes | No | No | Unknown | Yes | No | payments schema; 3 tables |
| 63 | 2026_09_04_0001 | 2026_09_04_0001_phase5b_adopt_mixins_in_5_domains.py | 2026_09_03_0007 | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | Mixin columns on 5 domains |
| 64 | f88d0dc00ece | 2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py | 2026_09_04_0001 | Intermediate | no-op | No | N/A | Yes | No | No | Unknown | Yes | No | Misleading name; not a merge |
| 65 | 20260929_0745 | 2026_09_29_07_45-20260929_0745_add_rollout_percentage_to_country_feature_flags.py | f88d0dc00ece | Intermediate | add col | No | N/A | Yes | No | No | Unknown | Yes | No | Additive; schema-probe safe |
| 66 | 20260930_0001 | 2026_09_30_0001_add_ticket_attachment_audit_columns.py | 20260929_0745 | **CURRENT HEAD** | add col, alter col | No | N/A | Yes | No | No | Unknown | Yes | No | comms.ticket_attachments audit cols |

---

## Critical Findings

### 1. Naming Convention Violations (97% failure rate)
`check_migration_naming.py` reports errors on 64 of 66 migration files. The expected pattern is `YYYY_MM_DD_HH_MM[-<rev>]_description.py`, but:
- 57 files use `YYYY_MM_DD_NNNN` (4-digit minute) instead of `YYYY_MM_DD_HH_MM` (2-digit hour + 2-digit minute)
- 2 files use `YYYY_MM_DD_HH_MM-rev_description` but the embedded rev doesn't match the filename-derived rev
- 5 files use bare `YYYY_MM_DD_NNNN_description` without a `-rev` separator

**Impact:** CI pre-commit hooks that enforce `check_migration_naming.py` will fail on every migration.

### 2. Misleading Merge Migration
`2026_09_03_0000` claims to merge divergent heads `20260831_0001` and `20260901_workspace`, but these two revisions are in the **same linear chain** (`20260831_0001` is an ancestor of `20260901_workspace` via `20260831_0002` → ... → `20260831_0006`). The merge is therefore a no-op that adds confusion without resolving any actual divergence.

### 3. Incomplete Downgrade
`2026_07_29_10_28-9ff24a0683dd_schema_drift_check.py` explicitly documents that downgrade is incomplete for SQLite (constraint→index reversals not implemented). On PostgreSQL, full downgrade is possible but not implemented in this migration.

### 4. Long-Running Backfills
- `20260831_0002` (UUID columns): `UPDATE ... SET uuid = gen_random_uuid() WHERE uuid IS NULL` on ~80 tables could lock large tables.
- `20260729_2030` (partitioning): `INSERT INTO ... SELECT * FROM` migrates data between shadow and partitioned tables; documented as requiring off-peak for tables > 10M rows.

### 5. No CONCURRENTLY Index Creation
No migration uses `CREATE INDEX CONCURRENTLY`. All index creation uses standard `CREATE INDEX` which briefly locks the table.

### 6. Runtime `alembic heads` Blocker
`python -m alembic ... heads` crashes with `ModuleNotFoundError: No module named 'alembic.config'` when run from the `backend` directory. The root cause is that `backend/alembic/` (a directory containing `__init__.py`) shadows the installed `alembic` package on `sys.path`. This prevents automated verification of migration head count and database connectivity introspection.

---

## Recommendations

1. **Renaming:** Adopt the convention `YYYY_MM_DD_HH_MM-rev_description.py` consistently, or update `check_migration_naming.py` to match the actual convention used.
2. **Merge cleanup:** Remove or correct `2026_09_03_0000` since it merges non-divergent revisions.
3. **Downgrade:** Complete the downgrade for `9ff24a0683dd` or document it as irreversible.
4. **Large-table safety:** Add `CONCURRENTLY` for indexes on tables > 1M rows, or schedule backfills during maintenance windows.
5. **Staging evidence:** Add a `tested_on_staging` field to each migration docstring or maintain a separate staging-test manifest.
6. **alembic directory rename:** Rename `backend/alembic/` to `backend/alembic_migrations/` (or similar) and update `alembic.ini` `script_location` to restore `alembic heads` functionality.

---

## env.py / alembic.ini Check

| Check | Status | Notes |
|-------|--------|-------|
| Uses DATABASE_URL_DIRECT | PASS | `env.py:20` reads `DATABASE_URL_DIRECT` first |
| Uses NullPool (non-pooled) | PASS | `env.py:42` uses `pool.NullPool` |
| alembic.ini sqlalchemy.url | PASS | Empty in .ini, overridden by env.py |
| Runtime `alembic heads` | **FAIL** | Crashes with `ModuleNotFoundError` due to `backend/alembic/` shadowing installed package |

---

## New Finding: Missing Model Indexes

Several models lack explicit `Index` declarations in `__table_args__`, which may cause full-table scans on common query filters:

| Model | Domain | Impact |
|-------|--------|--------|
| `AlertEscalationRule` | audit | No index on filter columns |
| `AuditLog` | audit | Relies on migration-created indexes only |
| `BOGOPromotion` | promotions | No index declared |
| `Banner` | catalog | No index declared |
| `CityDistanceMatrix` | logistics | No index declared |
| `CommandCenterView` | audit | No index declared |

---

*Audit completed. No source files were modified.*
