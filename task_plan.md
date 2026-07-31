# ZOZI Database Governance Implementation Plan

## Goal
Resolve remaining database governance issues from DATABASE_AUDIT_REPORT.md

## Current Status
- ✅ **W1 violations**: 0 remaining (was 885) - COMPLETED
- ⏳ **W2 violations**: 3627 style issues - NOT PRIORITY
- ✅ **DB02 create_all**: Dev-gated via `_guard_dev_only()` and `test_create_all.py` fix
- ✅ **DB05 RLS**: Infrastructure exists in `rls_interceptor.py` and `country_context.py`
- ⏳ **DB06 Cross-Ecosystem FKs**: 225 FKs still present - NEEDS REVIEW
- ⏳ **DB13 Migration Heads**: 2 heads (20260730_0007, 20260730_0008) - NEEDS MERGE
- ⏳ **DB24 Production Checklist**: Partial - need verification tests
- ✅ **DB26 Models**: Already in correct location (`backend/models/`)
- ⏳ **DB31 Composite Indexes**: 110 tables missing indexes
- ⏳ **DB32 Pagination**: 77 OFFSET patterns need cursor conversion

## Phase 1: Merge Alembic Migration Heads
- [ ] Analyze head revisions 20260730_0007 and 20260730_0008
- [ ] Create merge migration to combine heads
- [ ] Verify single clean head

## Phase 2: Cross-Ecosystem FK Review (DB06)
- [ ] Review all 225 cross-schema FKs
- [ ] Categorize: intentional vs. needs refactoring
- [ ] Prioritize high-risk FKs (users.id, products.id, orders.id)
- [ ] Document remediation plan for each

## Phase 3: Composite Index Addition (DB31)
- [ ] Add indexes for country_code + created_at combinations
- [ ] Focus on high-traffic tables
- [ ] Schedule during low-traffic period

## Phase 4: Pagination Optimization (DB32)
- [ ] Identify 77 OFFSET patterns in routers/
- [ ] Convert to cursor-based pagination
- [ ] Update API documentation

## Phase 5: Production Verification
- [ ] Add tests for create_all dev-gating
- [ ] Add RLS fail-closed security tests
- [ ] Verify migration head is single

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
Analyze Alembic migration heads to understand what needs merging.