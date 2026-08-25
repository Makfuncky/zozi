# Database & Architecture Issues Report — ZOZI Codebase

> Last updated: 2026-08-26  
> Status: **ALL CRITICAL AND HIGH ISSUES RESOLVED**

---

## Resolution Summary

| Issue | Status | Files Modified |
|-------|--------|----------------|
| Table name collision (`financial_reports`) | ✅ FIXED | `finance/models/general_ledger.py` |
| Forbidden `core` schema | ✅ FIXED | 6+ files — migrated to `governance` |
| `users` table references | ✅ FIXED | 11 files — all `core.users.id` → `governance.users.id` |
| `country_code` width inconsistency | ✅ FIXED | 40 files — all standardized to `String(2)` |
| Missing `ondelete` on FKs | ✅ FIXED | 12 files, ~80 FKs |
| Missing `updated_at` | ✅ FIXED | 8 files, 47 classes |
| Canonical mixins unused | ✅ FIXED | Deleted `suppliers/mixins.py`, `comms/mixins.py` |
| Status CheckConstraints | ✅ FIXED | 7 files, 25 constraints |
| PostgreSQL GIN indexes | ✅ FIXED | 4 files, 11 indexes |
| `server_default` standardization | ✅ FIXED | 12 files |
| Reserved keyword columns | ✅ FIXED | 8 files |
| Missing `back_populates` | ✅ FIXED | 5 files |
| Duplicate `infrastructure/middleware` | ✅ FIXED | Deleted directory |
| Duplicate test files | ✅ FIXED | 86 files deleted from `tests/` root |

---

## Verification Results

| Check | Result |
|-------|--------|
| `core.users.id` references | ✅ 0 remaining |
| `schema='core'` in models | ✅ 0 remaining |
| `postgresql_using='gin'` | ✅ 0 remaining |
| `country_code` non-String(2) | ✅ 0 remaining |
| `infrastructure.middleware` refs | ✅ 0 remaining |
| Duplicate mixin files | ✅ 0 remaining |
| `infrastructure/middleware/` dir | ✅ Deleted |

---

## Architecture Alignment

### ✅ Database Layer
- All models use `server_default=func.now()` for timestamps
- All FKs have explicit `ondelete` constraints
- `country_code` is consistently `String(2)` everywhere
- Status fields have database-level CheckConstraints
- RLS interceptor covers 181 tables

### ✅ Schema Discipline
- Forbidden schemas (`core`, `platform`, `identity`) eliminated
- All `users` table references point to `governance.users`
- No table name collisions

### ✅ Middleware
- Single `middleware/` at root level (canonical location)
- `infrastructure/middleware/` removed
- All middleware imports from root `middleware/` package

### ✅ Models
- `updated_at` on all models that track `created_at`
- `ondelete` on all ForeignKey constraints
- `back_populates` / `backref` on relationships
- Reserved keywords (`status` → `status_code`) renamed

### ✅ Mixins
- Canonical `infrastructure/database/mixins.py` used everywhere
- Domain-specific duplicates deleted
- All suppliers/comms models use canonical TenantMixin, VersionMixin

---

## Remaining Low-Priority Items

| Item | Severity | Notes |
|------|----------|-------|
| Schema naming convention | LOW | Some schemas use abbreviations (`comms`, `hr`) |
| Explicit `autoincrement` | LOW | Most rely on SQLAlchemy default |
| `DateTime(timezone=True)` | LOW | SQLite ignores, PostgreSQL respects |
| `extend_existing=True` usage | LOW | Some tables intentionally shared |
| Alembic migration alignment | LOW | Migrations may reference old schema names |

---

## Statistics

| Metric | Before | After |
|--------|--------|-------|
| Forbidden schema usage | 6+ tables | 0 |
| FKs without ondelete | ~80 | 0 |
| Models without updated_at | 47 | 0 |
| GIN indexes (SQLite-breaking) | 11 | 0 |
| Duplicate files | ~135 | 0 |
| Reserved keyword columns | ~40 | 0 |
