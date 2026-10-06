# K-08 Migration Runbook

## Overview
K-08 reconciles ORM schema drift in the migration chain for three areas:
1. `catalog.products.currency` missing column
2. `accounts.mfa_factors` table missing from chain + `secret` type mismatch
3. `catalog.products` missing FK constraints and incorrect column defaults/types

Migrations: `20261004_0019`, `20261004_0020`, `20261004_0021`

## Pre-Flight Checks
1. `alembic heads` must return exactly `20261004_0021_fix_products_fk_and_defaults`
2. Database must be at `20261004_0013` or later
3. Ensure no active transactions on `catalog.products` or `accounts.mfa_factors`
4. Confirm `accounts.users` and `country.country_configs` have data matching FK references

## Operation Risk Notes

### Migration 0019: add_products_currency
| Operation | Risk | Mitigation |
|-----------|------|------------|
| `ADD COLUMN currency VARCHAR(3) NOT NULL DEFAULT 'USD'` | Low | Additive; existing rows get 'USD'. Requires `ACCESS EXCLUSIVE` lock briefly on `catalog.products`. |
| `CREATE INDEX ix_products_currency` | Low | Non-unique index; concurrent-safe in PostgreSQL 12+. |

**Rollback**: Drops column and index. Safe because column is additive.

### Migration 0020: create_mfa_factors_and_align_secret
| Operation | Risk | Mitigation |
|-----------|------|------------|
| `CREATE TABLE accounts.mfa_factors` (IF NOT EXISTS) | Low | Guarded; no-op if table exists from `create_all`. |
| `ALTER COLUMN secret TYPE TEXT` | Medium | Rewrites entire column; lock on `accounts.mfa_factors`. Schedule during low-traffic window. Existing `VARCHAR(1024)` data is compatible with `Text`. |
| Add `version`, `is_deleted`, `updated_at`, `country_code`, `backup_codes`, `last_used_at` | Low | Additive columns with defaults. |

**Rollback**: Drops added columns, restores `VARCHAR(1024)` type, drops table if it was created here. Note: if production has data in `mfa_factors`, `drop_table` in downgrade will fail — override downgrade manually if needed.

### Migration 0021: fix_products_fk_and_defaults
| Operation | Risk | Mitigation |
|-----------|------|------------|
| `ALTER country_code VARCHAR(3) -> VARCHAR(2)` | Medium | Type shrink; PostgreSQL requires rewrite if data exceeds new size. Verify all `country_code` values are 2-char ISO codes before running. Uses `batch_alter_table` for SQLite compatibility. |
| `ADD CONSTRAINT fk_products_category` | Medium | FK validation scans `catalog.categories`; lock on `catalog.products`. Ensure no orphaned `category_id` values exist. |
| `ADD CONSTRAINT fk_products_supplier` | Medium | References `accounts.users`; validates all `supplier_id` values. `ON DELETE SET NULL` — ensure application handles NULL suppliers. |
| `ADD CONSTRAINT fk_products_country` | Medium | References `country.country_configs`; validates all `country_code` values match existing codes. |
| `ALTER is_deleted SET DEFAULT false, NOT NULL` | Low | Adds index `ix_products_is_deleted`. Existing NULLs become `false`. |
| `ALTER created_at SET DEFAULT now(), NOT NULL` | Low | Existing NULLs get `now()`. |
| `ALTER updated_at SET DEFAULT now(), NULLABLE` | Low | Existing NULLs get `now()`. |

**Rollback**: Drops FKs, drops index, reverses type and defaults. Safe but verify data integrity before downgrading.

## Execution Order
```sql
BEGIN;
-- 0019: add currency
-- 0020: create mfa_factors + align secret
-- 0021: fix products FKs and defaults
COMMIT;
```

## Post-Migration Verification
1. `alembic current` → `20261004_0021`
2. `alembic heads` → exactly 1 head
3. `SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_schema='catalog' AND table_name='products' AND column_name IN ('currency','country_code','is_deleted','created_at','updated_at');`
4. `SELECT conname, contype FROM pg_constraint WHERE conrelid='catalog.products'::regclass AND contype='f';`
5. `SELECT * FROM accounts.mfa_factors LIMIT 0;` — confirm table exists
6. `SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='accounts' AND table_name='mfa_factors' AND column_name='secret';` — confirm `text`

## Known Blockers
- Full `alembic downgrade --sql` from head to base fails on pre-existing migration `2026_08_31_0005` (`op.execute` with params in offline mode). Not related to K-08.
- K-08 migrations (0019–0021) downgrade cleanly to 0018 in `--sql` mode.

## Emergency Rollback
If any migration fails mid-execution:
```sql
ROLLBACK;
-- Fix underlying issue, then re-run migration chain from 0019.
```
