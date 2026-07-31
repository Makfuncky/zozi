# Database Governance Findings - Updated

## W1 Violations (RESOLVED)
All 885 W1 violations resolved by refactoring controllers to use service layer methods.

## W2 Violations (NOT PRIORITY)
3627 style violations (line length, whitespace, blank lines). These are non-functional linting issues.

## Database Audit Report - ACTUAL STATUS

### ✅ Already Implemented

**DB02 - create_all Dev-Gating**
- `backend/db/database.py` has `_guard_dev_only()` function
- `backend/scripts/test_create_all.py` - **FIXED** with proper dev guards
- Tests use create_all in fixtures (acceptable)
- Promotion engine uses create_all for specific tables only (acceptable)

**DB05 - RLS Implementation**
- ✅ `backend/utils/rls_interceptor.py` - Full RLS implementation with:
  - `COUNTRY_AWARE_TABLES` registry (179 tables)
  - `set_rls_context()` / `clear_rls_context()` functions
  - SQLAlchemy event listeners for automatic filtering
  - `install_rls_policies()` function to apply PostgreSQL RLS
- ✅ `backend/middleware/country_context.py` - Country context middleware
- ✅ `backend/data/pg_rls_policies.sql` - **CREATED** (this file)

**DB13 - Migration Heads**
- Still present: `20260730_0007` and `20260730_0008` heads
- Need to merge these heads

**DB24 - Production Checklist**
- ✅ pg_rls_policies.sql exists (created)
- ✅ RLS middleware exists
- ⏳ Need to verify create_all gated (in progress)
- ⏳ Need to add verification tests

**DB26 - Model Organization**
- ✅ `backend/models/employee_models.py` exists (canonical version)
- ✅ `backend/db/employee_models.py` is outdated - needs deprecation notice

### 🔴 Still Need Attention

**DB06 - Cross-Ecosystem FKs (225 violations)**
- All documented in audit report
- These are architectural decisions - some may be intentional
- High priority: FKs to `users.id`, `products.id`, `orders.id` from different schemas

**DB32 - Pagination (77 violations)**
- OFFSET pagination in 77 locations
- Need to convert to cursor-based pagination

**DB31 - Composite Indexes (110 violations)**
- Tables with country_code + created_at missing composite indexes
- Need to add indexes for tenant time-series queries

## Next Actions
1. Merge Alembic migration heads
2. Review cross-ecosystem FKs for necessity
3. Add composite indexes for country-scoped tables
4. Convert OFFSET pagination to cursor-based