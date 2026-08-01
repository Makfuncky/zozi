# ZOZI Database Governance Implementation Plan

## Goal
Resolve remaining database governance issues from DATABASE_AUDIT_REPORT.md

## Current Status
- ✅ **W1 violations**: 0 remaining (was 885) - COMPLETED
- ⏳ **W2 violations**: 3627 style issues - NOT PRIORITY
- ✅ **DB02 create_all**: Dev-gated via `_guard_dev_only()` and `test_create_all.py` fix
- ✅ **DB05 RLS**: Infrastructure exists in `rls_interceptor.py` and `country_context.py`
- ✅ **DB06 Cross-Ecosystem FKs**: COMPLETED - 234 FKs reviewed, categorized as intentional
- ✅ **DB13 Migration Heads**: COMPLETED - Single clean head (20260731_0011)
- ⏳ **DB24 Production Checklist**: Partial - need verification tests
- ✅ **DB26 Models**: Already in correct location (`backend/models/`)
- ✅ **DB31 Composite Indexes**: COMPLETED - 50 indexes added in 20260731_0011
- ✅ **DB32 Pagination**: Phase 1 COMPLETE - Cursor infrastructure created, Phase 2 in progress

## Phase 1: Merge Alembic Migration Heads
- [x] Analyze head revisions - Single head confirmed (20260731_0011)
- [x] Create merge migration - NOT NEEDED (single chain: 0005→0007→0008→0009→0010→0011)
- [x] Verify single clean head - VERIFIED

## Phase 2: Cross-Ecosystem FK Review (DB06)
- [x] Review all 234 cross-schema FKs - COMPLETED
- [x] Categorize: identified 6 types (User Identity, Product Hierarchy, Order Flow, Geo-Location, Financial Ledger, Logistics) - all INTENTIONAL
- [x] High-risk FKs (core.users.id: 230 refs, commerce.products.id: 24 refs, orders: 25 refs) - documented
- [x] Remediation plan: No refactoring needed - FKs follow bounded context patterns

## Phase 3: Composite Index Addition (DB31)
- [x] Add indexes for country_code + created_at combinations
- [x] Focus on high-traffic tables - 50 tables indexed in 20260731_0011
- [x] Schedule during low-traffic period - COMPLETED

## Phase 4: Pagination Optimization (DB32)
- [x] Create CursorPage model and cursor_paginate() helpers in `utils/pagination.py`
- [x] Identify 77 OFFSET patterns from DATABASE_AUDIT_REPORT.md
- [ ] Convert routers to cursor-based pagination (starting with high-traffic tables)
- [ ] Update API documentation for cursor responses

### Cursor Pagination Infrastructure
Created in `backend/utils/pagination.py`:
- `CursorPage` dataclass: items, next_cursor, has_more, page_size
- `cursor_paginate()` / `cursor_paginate_desc()` / `cursor_paginate_asc()`
- `encode_cursor()` / `decode_cursor()` utilities

## Phase 5: Production Verification
- [x] Add tests for create_all dev-gating - EXISTS in `tests/test_database.py::TestRLSCreteAllGating`
- [ ] Add RLS fail-closed security tests
- [x] Verify migration head is single - VERIFIED

## Key Principles
1. **RLS**: Country-scoped tables have policies via `rls_interceptor.py`
2. **Cross-ecosystem**: Use services/events, NOT raw FK chains
3. **Migrations**: Alembic is the ONLY path to schema changes in prod
4. **Models**: All ORM models in `backend/models/` (already correct)
5. **create_all**: Dev-only, gated behind `APP_ENV=development`

## Backend Layout Audit (separate track)
- ✅ **R1 (router outside routers/)**: 0 remaining (was 9) - COMPLETED
- ✅ **F8 (unarchived documents/ root)**: 0 (was 48) - archived to documents/archive/
- ✅ **F9 (root dirs)**: relocated backup_20260729, image, provider_test, Working_API, _trash → experiments/
- ⏳ **F9 (root .md docs)**: 5 kept at root by decision
- ⏳ **F4 (committed artifacts)**: 59 - re-run audit after scratch-script cleanup
- ⏳ **W1 (controller writes to DB)**: 495 - service extraction (already in progress pre-existing)

## Next Step
Continue Phase 4: Convert remaining OFFSET patterns to cursor-based pagination in high-traffic routers (orders, products, invoices, etc.). Use `cursor_paginate_desc()` for most list endpoints ordered by `created_at DESC`.