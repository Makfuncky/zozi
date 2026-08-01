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
- ✅ MERGED - Single clean head confirmed (20260731_0011)
- Merge migration created combining: 0005→0007→0008→0009→0010→0011
- Chain is linear with no conflicts

**DB24 - Production Checklist**
- ✅ pg_rls_policies.sql exists (created)
- ✅ RLS middleware exists
- ⏳ Need to verify create_all gated (in progress)
- ⏳ Need to add verification tests

**DB26 - Model Organization**
- ✅ `backend/models/employee_models.py` exists (canonical version)
- ✅ `backend/db/employee_models.py` is outdated - needs deprecation notice

### 🔴 Still Need Attention

**DB06 - Cross-Ecosystem FKs (234 columns)**
- ✅ COMPLETED - Analyzed all 234 cross-schema FK columns
- Categorized by target schema:
  - core.users.id: 230 references (User Identity - INTENTIONAL)
  - commerce.products.id: 24 references (Product Hierarchy - INTENTIONAL)
  - country.country_configs.code: 74 references (Geo-Location - INTENTIONAL)
  - finance.*, logistics.*, treasury.*: Various references (bounded contexts)
- Documented in `backend/data/cross_schema_fk_analysis.json`
- All FKs follow bounded context patterns - no refactoring needed

**DB32 - Pagination (77 violations)**
- ✅ Phase 1 COMPLETE - Created `CursorPage` model and `cursor_paginate()` helpers
- New functions available in `backend/utils/pagination.py`:
  - `CursorPage` dataclass with `items`, `next_cursor`, `has_more`, `page_size`
  - `cursor_paginate()` - generic cursor pagination
  - `cursor_paginate_desc()` - DESC ordering (newest first)
  - `cursor_paginate_asc()` - ASC ordering (oldest first)
  - `encode_cursor()`, `decode_cursor()` for cursor token handling
- In progress: Converting high-traffic routers (users.py, orders, products)
- Remaining: 70+ routers/controllers to update

**DB31 - Composite Indexes (50 new indexes)**
- ✅ COMPLETED - Added 50 composite indexes in migration `20260731_0011`
- Indexes cover: (country_code, created_at) + (id) for tenant time-series queries
- Tables indexed: finance, commerce, audit, events, analytics schemas

## Next Actions
1. ~~Merge Alembic migration heads~~ ✅ COMPLETED
2. ~~Review cross-ecosystem FKs for necessity~~ ✅ COMPLETED
3. ~~Add composite indexes for country-scoped tables~~ ✅ COMPLETED (50 indexes)
4. Convert OFFSET pagination to cursor-based (in progress - 70+ remaining)
5. Add RLS fail-closed security tests