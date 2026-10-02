# DIMENSION: Database

## Summary
- Confirmation: ❌
- Files inspected: 12
- Files compliant: 4
- Files with findings: 8
- Laws implicated: [L-45, L-46, L-47, L-48, L-50, L-52, L-53, L-55, L-56, L-57, L-58]
- Findings: 8
- P0: 3  P1: 2  P2: 2  P3: 1
- Clusters: 3
- Average confidence: 4.5/5
- Average evidence strength: multiple
- Status: NEW: 8 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 4 yes · 0 partial · 4 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| DB-001 | db | COMPILED | CLUSTER-migration-divergent | backend/alembic/versions/* | 5 divergent migration heads (`20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`) | Exactly one head (`alembic heads` returns one revision) | Migration history has 5 heads instead of one linear chain | Merge all 5 heads into single linear chain via new merge migration | L (8h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/alembic/versions/2026_09_04_17_00-f88d0dc00ece_merge_divergent_heads.py:15 | `alembic heads` returns exactly one revision | tests/architecture/test_migration_linearity.py | Revert merge migration | F-001, F-002, CHAIN-001 | none | DB-002 | yes |
| DB-002 | db | RESOLVED | CLUSTER-migration-divergent | backend/alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py:31 | `from migration_helpers import safe_add_column, safe_drop_column` fails with `ModuleNotFoundError` when `alembic heads` loads revision files | `alembic heads` executes successfully and returns one head | `alembic heads` command crashes with `ModuleNotFoundError: No module named 'migration_helpers'` when loading revision files | Add `alembic/` to `sys.path` in `env.py` or fix import to use absolute import | S (1h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/alembic/env.py:8-10 | `alembic heads` returns one head without error | tests/architecture/test_migration_linearity.py | Revert path fix | F-001 | DB-001 | yes |
| DB-003 | db | COMPILED | CLUSTER-n1-relationships | backend/domains/*/models/*.py | 293 relationships across domain models omit `lazy=` parameter (default `lazy='select'` causes N+1 queries) | All relationships use `lazy='selectin'` or `lazy='joined'` | 293 relationships default to lazy-loaded SELECT-per-access pattern instead of eager loading | Add `lazy='selectin'` or `lazy='joined'` to all 293 relationship() calls | L (12h) | P1 | 5 | triangulated | L0 | VERIFIED | backend/domains/finance/models/general_ledger.py:133-135 | `pytest tests/performance/test_n_plus_one.py` passes | tests/performance/test_n_plus_one.py | Revert lazy additions | F-003, F-004, F-005 | DB-004 | yes |
| DB-004 | db | COMPILED | CLUSTER-n1-relationships | backend/domains/catalog/models/products.py:37 | `products = relationship("Product", back_populates="category_rel")` — no lazy loading | `lazy='selectin'` or `lazy='joined'` | Category relationship triggers separate SELECT per product row | Add `lazy='selectin'` to relationship | S (0.5h) | P1 | 5 | single | L0 | VERIFIED | backend/domains/finance/models/general_ledger.py:133 | `pytest tests/domains/catalog/test_products.py::test_category_lazy` | tests/domains/catalog/test_products.py | Revert lazy addition | F-003 | DB-003 | no |
| DB-005 | security | COMPILED | CLUSTER-rls-mismatch | backend/infrastructure/database/sql/pg_rls_policies.sql:23-26 | RLS policy uses `current_setting('app.current_country_code', true)` | Middleware sets `app.country_scope` via `SET LOCAL app.country_scope = :country_scope` | Policy variable `app.current_country_code` does not match session variable `app.country_scope` set by middleware | Align policy SQL to use `app.country_scope` or rename middleware SET LOCAL target | S (2h) | P0 | 5 | triangulated | L0 | VERIFIED | backend/middleware/country_context.py:272 | `pytest tests/security/test_rls_policy_alignment.py` | tests/security/test_rls_policy_alignment.py | Revert policy rename | F-006, F-007, CHAIN-004 | none | yes |
| DB-006 | db | COMPILED | CLUSTER-rls-mismatch | backend/infrastructure/database/rls_interceptor.py:223-270 | `generate_rls_policy_sql()` generates policies using `auth.country_access_check()` function, but `pg_rls_policies.sql` uses inline `current_setting()` expressions | Single canonical RLS policy generation strategy | Two divergent RLS policy implementations exist: SQLAlchemy interceptor approach vs raw SQL file approach | Deprecate `pg_rls_policies.sql` and standardize on `install_rls_policies()` OR remove interceptor and use raw SQL | M (4h) | P2 | 4 | multiple | L0 | VERIFIED | backend/infrastructure/database/rls_interceptor.py:279-296 | `pytest tests/infrastructure/test_rls_coverage.py` | tests/infrastructure/test_rls_coverage.py | Revert standardization | F-006 | DB-005 | no |
| DB-007 | db | COMPILED | CLUSTER-read-replica-unused | backend/infrastructure/database/database.py:360 | `get_read_db()` is defined but never called in application code (only in tests) | `get_read_db()` is used in read-heavy routers (catalog browse, search, analytics) | Read replica dependency exists but is not wired into any router or service | Wire `get_read_db()` into catalog/search/analytics routers | M (3h) | P2 | 5 | triangulated | L0 | VERIFIED | backend/modules/customer/routers/*.py | `pytest tests/infrastructure/test_database_integrity.py::test_get_read_db_is_callable` passes with actual usage | tests/infrastructure/test_database_integrity.py | Revert router wiring | F-008 | none | no |
| DB-008 | db | COMPILED |  | backend/infrastructure/database/database.py:200-217 | Async engine creation omits `statement_cache_size=0` in `connect_args` | `asyncpg` connection uses `statement_cache_size=0` to avoid server-side statement cache memory leak | asyncpg default statement cache may accumulate unbounded prepared statements under high churn | Add `"statement_cache_size": 0` to `async_connect_args` in `_get_async_engine()` | S (0.5h) | P3 | 4 | single | L0 | VERIFIED | backend/infrastructure/database/database.py:200-217 | `pytest tests/infrastructure/test_asyncpg_config.py` | tests/infrastructure/test_asyncpg_config.py | Remove statement_cache_size override | F-009 | none | no |

## Over all

### Problem(s)
1. Migration history has 5 divergent heads (`20260930_0002`, `20260930_0003`, `20260930_0006`, `20260930_0007`, `20261001_0001`) instead of one linear chain; `alembic heads` crashes with `ModuleNotFoundError`
2. 293 domain model relationships use default `lazy='select'`, causing N+1 query explosion on every collection endpoint
3. RLS policy SQL references `app.current_country_code` but middleware sets `app.country_scope`; two competing RLS implementations exist
4. Read replica engine is built but never wired into application routers

### Solution(s)
1. Merge all 5 heads into single linear chain; fix `migration_helpers` import path
2. Add `lazy='selectin'` to all 293 relationship() calls missing it
3. Align RLS policy variable names and standardize on one implementation
4. Wire `get_read_db()` into catalog/search/analytics routers

### Suggestion(s)
1. Add CI gate that fails if `alembic heads` returns != 1
2. Add CI gate that scans for `relationship(` without `lazy=` in domain models
3. Add integration test that verifies `SET LOCAL app.country_scope` matches policy `current_setting()`

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
| P0 | Merge 5 divergent migration heads into single linear chain | backend/alembic/versions/ | yes | L | 5 |
| P0 | Fix migration_helpers ModuleNotFoundError blocking `alembic heads` | backend/alembic/versions/2026_08_06_0001_add_analytics_audit_columns.py:31 | yes | S | 5 |
| P0 | Align RLS policy variable name with middleware SET LOCAL target | backend/infrastructure/database/sql/pg_rls_policies.sql | yes | S | 5 |
| P3 | Add `statement_cache_size=0` to asyncpg connect_args | backend/infrastructure/database/database.py:200-217 | no | S | 4 |
| P1 | Add `lazy='selectin'` to 293 relationships missing lazy parameter | backend/domains/*/models/*.py | partial | L | 5 |
| P1 | Wire `get_read_db()` into read-heavy routers | backend/modules/*/routers/*.py | no | M | 5 |
| P2 | Standardize RLS implementation (interceptor vs raw SQL) | backend/infrastructure/database/rls_interceptor.py | no | M | 4 |
| P2 | Verify `install_rls_policies()` is called during deployment | backend/infrastructure/database/init_db.py | no | M | 4 |
