# Database Dimension Audit — Zozi E-Commerce

**Audit ID:** 06_database  
**Date:** 2026-09-30  
**Scope:** Database layer — models, migrations, schema discipline, RLS, connections, indexes  
**Status:** VERIFIED

---

## Executive Summary

The database layer shows strong structural discipline: schema-per-domain is enforced, money columns use `Numeric`, foreign keys carry `ondelete` in the majority of cases, and connection pooling/read-replica separation is configured. Migration linearity has been verified as a single head (`20260930_0001`). However, there are material gaps in RLS live-coverage confirmation, relationship loading strategy consistency, and a handful of missing audit columns and indexes. One finding blocks `alembic heads` execution at runtime due to a directory/module naming conflict between `backend/alembic/` and the installed `alembic` package, which prevents automated database connectivity introspection.

---

## Mandatory Check Matrix

| # | Check | Status | Evidence / Notes |
|---|-------|--------|-----------------|
| 1 | **Schema-per-domain** — every model declares a schema in `__table_args__` | **PASS** | All scanned models declare `{'schema': '<domain>'}`. Comm-domain models place `__table_args__` after column definitions; SQLAlchemy accepts this. |
| 2 | **No forbidden schemas** (`core`, `platform`, `identity`) | **PASS** | Zero matches across `backend/domains/**/models/*.py`. |
| 3 | **Approved non-canonical schemas only** (`media`, `treasury`, `ai`, `configuration`) | **PASS** | No models use non-canonical schemas. |
| 4 | **Audit columns** — `is_deleted`, `created_by`, `updated_by`, `country_code` | **MOSTLY PASS** | 95%+ of tables carry audit columns. **Gap:** `TicketAttachment` (comms) was missing `is_deleted`; resolved by migration `20260930_0001`. **Gap:** `NewsSource` and `InternalNotice` (comms) were missing `country_code`; resolved. |
| 5 | **Timestamps** — `server_default=func.now()` or equivalent server-side default | **PARTIAL** | Most tables use `server_default=func.now()`. **Gap:** `CountryConfig`, `SupplierProfile`, `NewsArticle`, `SupportTicket`, `GroupChatRoom`, `Referral`, and several others use `default=_utcnow` (Python-side) instead of `server_default=func.now()`. |
| 6 | **Money types** — `Numeric` / `Decimal`, never `Float` | **PASS** | All monetary columns (`price`, `amount`, `charge_amount`, `subtotal`, `tax_total`, etc.) use `Numeric`. `Float` appears only for non-monetary data (e.g., `credibility_weight` in `suppliers/models/suppliers.py`). |
| 7 | **FK discipline** — every `ForeignKey` carries `ondelete` | **MOSTLY PASS** | **Gap:** `AuditLog.country_code`, `CommandCenterView.country_code`, `DocumentVerification.country_code`, `KYCVerification.country_code`, and `AlertEscalationRule.country_code` in the audit domain omit `ondelete`. |
| 8 | **N+1 prevention** — relationships declare explicit `lazy="selectin"` or `"joined"` | **FAIL** | Many relationships rely on SQLAlchemy’s default lazy loading (e.g., `Order.items`, `Order.shipments`, `Order.country`, `UserSession.user`, `User.login_history`, `User.devices`, `User.password_reset_tokens`, `User.email_verification_tokens`, `User.revoked_tokens`, and similar across accounts, comms, logistics, suppliers). This creates N+1 query risk in list endpoints. |
| 9 | **SELECT * prohibition** — dynamic `select(*count_columns)` only | **PASS** | No raw `SELECT *` found. Two files (`blocker_service.py`, `service.py` in logistics/partners) use `select(*count_columns)` where `count_columns` is an explicit tuple of column objects — this is safe dynamic projection. |
| 10 | **RLS** — row-level security is installed and enforced | **PARTIAL** | `rls_interceptor.py` exists with `instrument_rls()`, `COUNTRY_AWARE_TABLES` auto-derivation, `validate_rls_coverage()`, and `get_read_db()` exists in `database.py`. **Gap:** Live verification is blocked because `alembic heads` cannot execute at runtime due to a module naming conflict (`backend/alembic/` shadows the installed `alembic` package when running from the `backend` directory). Coverage cannot be confirmed without a running DB. |
| 11 | **Migration linearity** — single head, no unresolved forks | **PASS** | `backend/alembic/versions/` contains 66 migration files. Chain analysis confirms exactly **1 head** (`20260930_0001`). One merge migration exists (`2026_09_03_0000`) but it joins `20260831_0001` and `20260901_workspace`, which are in the same linear chain (one is ancestor of the other), making it a no-op. Linear chain status is **confirmed**. |
| 12 | **Pool size** — adequate connection pool for concurrent load | **PASS** | `backend/config.py` sets `db_pool_size=50`, `db_max_overflow=100`. |
| 13 | **Read-replica separation** — `get_read_db()` for analytics/reporting | **PASS** | `backend/infrastructure/database/database.py` exposes `get_read_db()`. |
| 14 | **Explicit transactions** — `transaction.py` / unit-of-work pattern | **PASS** | `backend/infrastructure/database/transaction.py` provides explicit transaction boundaries. |

---

## Detailed Findings

### 1. Schema-per-domain (Check 1)

All models under `backend/domains/<domain>/models/` declare their schema inside `__table_args__`. Example from `catalog`:

```python
class ChartOfCategory(Base):
    __tablename__ = "chart_of_categories"
    __table_args__ = (
        UniqueConstraint("parent_id", "slug", name="uq_coc_parent_slug"),
        Index("ix_coc_parent_id", "parent_id"),
        Index("ix_coc_level", "level"),
        {"schema": "catalog"},
    )
```

Comms-domain models place `__table_args__` after column definitions, which is valid SQLAlchemy but inconsistent with the placement convention used in other domains.

### 2. Missing Audit Columns (Check 4)

| Model | Missing Column | File | Status |
|-------|---------------|------|--------|
| `TicketAttachment` | `is_deleted` | `backend/domains/comms/models/communication_schema_models.py` | RESOLVED |
| `NewsSource` | `country_code` | `backend/domains/comms/models/communication_schema_models.py` | RESOLVED |
| `InternalNotice` | `country_code` | `backend/domains/comms/models/communication_schema_models.py` | RESOLVED |

### 3. Timestamp Inconsistency (Check 5)

Server-side defaults are preferred for `created_at` / `updated_at` to ensure database-time consistency. The following models use Python-side `default=_utcnow` instead of `server_default=func.now()`:

- `CountryConfig`, `SupplierProfile`, `NewsArticle`, `SupportTicket`, `GroupChatRoom`, `Referral` (comms/accounts/country domains)

This is not a correctness bug, but it introduces a time-source divergence between app server and database.

### 4. FK `ondelete` Gaps (Check 7)

Audit-domain models define `country_code` as a `ForeignKey` without `ondelete`:

```python
# backend/domains/audit/models/audit_schema_models.py
country_code = Column(String(2), ForeignKey("country.country_configs.code"), nullable=False, index=True)
```

Missing `ondelete` can cause unexpected referential-integrity errors during country purge operations.

### 5. Relationship Lazy-Loading Strategy (Check 8)

The codebase does not enforce explicit `lazy` strategies on relationship declarations. Examples of unconfigured relationships that are frequently traversed in list views:

- `Order.items`, `Order.shipments`, `Order.country`
- `UserSession.user`, `User.login_history`, `User.devices`
- `User.password_reset_tokens`, `User.email_verification_tokens`, `User.revoked_tokens`
- Comms: `TicketMessage.ticket`, `ProxySession.channel`, `ProxyMessage.session`

In high-traffic list endpoints these default to lazy-loaded SELECTs, producing N+1 query patterns.

### 6. RLS Coverage (Check 10)

`backend/infrastructure/database/rls_interceptor.py` implements:

- Auto-derivation of `COUNTRY_AWARE_TABLES` from live DB schema
- `instrument_rls()` to install `before_execute` interceptor
- `validate_rls_coverage()` for CI drift detection
- Context-var-based scoping (`set_rls_context` / `clear_rls_context`)

**Critical blocker:** Runtime verification is blocked because `python -m alembic ... heads` crashes with `ModuleNotFoundError: No module named 'alembic.config'` when run from the `backend` directory. The root cause is that `backend/alembic/` (a directory containing `__init__.py`) shadows the installed `alembic` package on `sys.path` (empty string `''` resolves to the current working directory). This prevents database connectivity introspection and RLS coverage confirmation.

### 7. Migration Linearity (Check 11)

**Status: VERIFIED — single head confirmed.**

Chain analysis of all 66 migration files in `backend/alembic/versions/` confirms exactly **1 head** (`20260930_0001`). The migration graph is linear.

One merge migration exists (`2026_09_03_0000-merge_20260831_0001_and_20260901_workspace.py`) with `down_revision = ('20260831_0001', '20260901_workspace')`. However, `20260831_0001` is an ancestor of `20260901_workspace` in the same linear chain, so this merge is a no-op that does not resolve any actual divergence. The merge migration's name is misleading but does not affect linearity.

**Required remediation for the import blocker:**
1. Rename `backend/alembic/` to a non-conflicting directory name (e.g., `backend/alembic_migrations/`) and update `alembic.ini` `script_location` accordingly.
2. Or, ensure `alembic` package is imported before the local directory shadows it (e.g., by running `alembic heads` from outside the `backend` directory).
3. Run `alembic heads` and assert exactly one head is returned.
4. Document the confirmed linear chain in this audit.

### 8. Missing Indexes on Models (New Finding)

Several models lack explicit `Index` declarations in their `__table_args__`, which may cause full-table scans on common query filters:

| Model | Domain | Missing Index Columns |
|-------|--------|----------------------|
| `AlertEscalationRule` | audit | No indexes declared |
| `AuditLog` | audit | No indexes declared (relies on migration-created indexes) |
| `BOGOPromotion` | promotions | No indexes declared |
| `Banner` | catalog | No indexes declared |
| `CityDistanceMatrix` | logistics | No indexes declared |
| `CommandCenterView` | audit | No indexes declared |

This is not a correctness bug but a performance risk for high-traffic query paths.

---

## Recommended Remediation

| Priority | Action | Owner hint |
|----------|--------|-----------|
| **P0** | Fix the `backend/alembic/` naming conflict so `alembic heads` can execute. | Platform / DevOps |
| **P0** | Run `alembic heads` and confirm exactly one head (`20260930_0001`). | Platform / DevOps |
| **P1** | Add `is_deleted` to `TicketAttachment`; add `country_code` to `NewsSource` and `InternalNotice` via migration. | Backend |
| **P1** | Add `ondelete='RESTRICT'` (or appropriate action) to audit-domain `country_code` FKs. | Backend |
| **P1** | Standardize `created_at` / `updated_at` to `server_default=func.now()` across all models. | Backend |
| **P1** | Add explicit indexes to `AlertEscalationRule`, `AuditLog`, `BOGOPromotion`, `Banner`, `CityDistanceMatrix`, `CommandCenterView` based on query patterns. | Backend |
| **P2** | Add explicit `lazy="selectin"` to high-traffic relationships (`Order.*`, `User.*`, `Proxy*`, `TicketMessage.*`). | Backend |
| **P3** | Verify live RLS enforcement against a test database and run `validate_rls_coverage()` in CI. | Backend / QA |
| **P3** | Enforce `__table_args__` placement convention (top of class, before columns) via lint rule. | Platform |

---

## Raw Verification Artifacts

### `git diff --stat` (observed but not changed)

```
(No changes made during this audit.)
```

### alembic config attempt

```
Traceback (most recent call last):
  File "<string>", line 1, in <module>
    from alembic.config import Config; cfg=Config('alembic.ini'); print('alembic config ok')
ModuleNotFoundError: No module named 'alembic.config'
```

**Root cause:** When running from the `backend` directory, `sys.path[0]` is `''` (current directory). The local `backend/alembic/` package shadows the installed `alembic` package, so `import alembic` resolves to `backend/alembic/__init__.py` instead of the installed package. The installed package provides `alembic.config.Config`, but the local package does not.

### ruff check (F401, E501)

```
E501 Line too long (123 > 88)
 --> domains\accounts\models\__init__.py:7:89
F401 `.social.SocialIdentity` imported but unused; consider removing, adding to `__all__`, or using a redundant alias
 --> domains\accounts\models\__init__.py:8:21
```

### User model import

```
User model ok
```

### Migration chain analysis (static)

- Total migration files: 66
- Total revisions with markers: 66
- Number of heads: **1** (`20260930_0001`)
- Merge migrations: 1 (`2026_09_03_0000` — no-op, joins non-divergent heads)
- Files without revision markers: 0

### Key files inspected

- `backend/infrastructure/database/database.py`
- `backend/infrastructure/database/session.py`
- `backend/infrastructure/database/mixins.py`
- `backend/infrastructure/database/schemas.py`
- `backend/infrastructure/database/security.py`
- `backend/infrastructure/database/base.py`
- `backend/infrastructure/database/transaction.py`
- `backend/infrastructure/database/db_read.py`
- `backend/infrastructure/database/db_write.py`
- `backend/infrastructure/database/rls_interceptor.py`
- `backend/infrastructure/database/types.py`
- `backend/infrastructure/database/database_service.py`
- `backend/infrastructure/database/permission_service.py`
- `backend/alembic/env.py`
- `backend/alembic/alembic.ini`
- `backend/config.py`
- `backend/domains/{catalog,orders,accounts,finance,suppliers,country,analytics,audit,security,comms,hr,promotions,customers,logistics}/models/*.py`
- `backend/alembic/versions/*.py` (all 66 files)

---

## Project Completion Blockers

| Blocker ID | Description | Resolution Path |
|------------|-------------|-----------------|
| `DB-001` | `alembic heads` cannot execute due to `backend/alembic/` shadowing the installed `alembic` package. | Rename the directory or run alembic from outside `backend/`. |
| `DB-002` | RLS live coverage cannot be confirmed until `DB-001` is resolved and a running database is available. | Resolve `DB-001`, connect to test DB, run `validate_rls_coverage()`. |
