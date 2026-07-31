# Database Changes Plan - Comparison of @documents/01_DATABASE.md with Current Structure

## Executive Summary

After comparing the "Database Constitution" document (`documents/01_DATABASE.md`) with the current codebase, I've identified several critical issues that need to be addressed. The document represents a mature, enterprise-grade database architecture that the current codebase is partially implementing.

---

## Key Findings

### 1. Migration Chain is Broken (CRITICAL)

**Issue**: Migration `20260730_0008_split_country_configs_into_domain_tables.py` references a missing migration `20260730_0007_fix_country_code_width`.

**Evidence**:
- File: `backend/alembic/versions/20260730_0008_split_country_configs_into_domain_tables.py`
- Line 15: `down_revision: Union[str, None] = "20260730_0007_fix_country_code_width"`
- Error when running: `KeyError: '20260730_0007_fix_country_code_width'`

**Impact**: Cannot run migrations; broken Alembic head; schema drift is masked.

### 2. Missing Model Files (CRITICAL)

**Issue**: `backend/models/__init__.py` imports models from files that don't exist.

**Missing Files**:
- `country_basics.py` - Expected to define `CountryBasics`
- `country_economics.py` - Expected to define `CountryEconomics`
- `country_tax.py` - Expected to define `CountryTax`
- `country_legal.py` - Expected to define `CountryLegal`

**Evidence**:
- File listing shows only: `admin.py, ai_upload.py, commission.py, communication.py, core.py, countries.py, country_control.py, country_enhancements.py, country_legal.py` (exists!), `employee_models.py, finance.py, fraud.py, incident.py, logistics.py, marketing.py, media_models.py, mixins.py, onboarding.py, orders.py, payments.py, permissions.py, products.py, suppliers.py, user.py, __init__.py`

**Wait - country_legal.py EXISTS** but the other three don't.

**Impact**: Import errors when loading models; migration failures.

### 3. Country Code Width Inconsistency (HIGH)

**Issue**: The document specifies `country_code VARCHAR(3)` but current models use `VARCHAR(10)`.

**Document Reference** (Section 2.9):
> "Resolve `country_code` `VARCHAR(3)` vs `(10)` here, **before** any joins."

**Current State**:
- `countries.py`: `CountryConfig.code = Column(String(10), ...)`
- `database.py`: `search_path = "public,analytics,audit,commerce,communication,configuration,core,country,customer,finance,hr,logistics,media,security,supplier,treasury"`
- Migration `20260730_0008`: Uses `String(3)` for new tables

**Impact**: Potential join failures; data integrity issues.

### 4. Pool Settings Mismatch (MEDIUM)

**Document Reference** (Section 2.12):
> "Pool: app `QueuePool` `pool_size=5`, `max_overflow=10`"

**Current State** (`utils/config.py`):
- Default: `db_pool_size = 20`, `db_max_overflow = 30`

**Impact**: Different resource usage; potential connection exhaustion.

### 5. Missing Data Dictionary Generation Script (MEDIUM)

**Document Reference** (Section 2.13):
> "The data dictionary is generated (`backend/scripts/generate_data_dictionary.py`), never hand-maintained."

**Current State**: Script does not exist in `backend/scripts/`.

**Impact**: No automated documentation; manual maintenance is error-prone.

### 6. Table Count Discrepancy (LOW)

**Document Reference** (Section 1, Finding a):
> "Table count disagrees across sources (262 live / 263 catalogued / ~270–310 ORM models)."

**Current State**: `GENERATED_DATA_DICTIONARY.md` shows 264 tables.

**Impact**: Need to verify actual table count vs ORM model count.

---

## Phase-by-Phase Action Plan

### Phase 0: Freeze & Inventory (No Code Changes)

**Actions**:
1. Create `backend/scripts/generate_data_dictionary.py` to auto-generate table inventory
2. Run inventory to determine actual table count vs model count
3. Document the reconciliation in findings

**Deliverable**: `backend/scripts/generate_data_dictionary.py` + inventory report

---

### Phase 1: Migration Pipeline Hardening (CRITICAL)

**Actions**:
1. Create the missing migration `20260730_0007_fix_country_code_width.py`
   - Purpose: Fix country_code width inconsistencies
   - Contains downgrade path
2. Create missing model files:
   - `backend/models/country_basics.py`
   - `backend/models/country_economics.py`
   - `backend/models/country_tax.py`
3. Update `backend/models/country_legal.py` to match migration expectations
4. Add CI schema-drift gate (`alembic check`)
5. Add migration contract test harness

**Deliverable**: Working migration chain; all models importable; CI gate in place

---

### Phase 2: Bounded-context Schemas

**Actions**:
1. Verify all tables have correct schema assignments
2. Update `database.py` search_path if needed
3. Ensure `CountryConfig.code` is `VARCHAR(3)` for consistency
4. Run tests to verify behavior unchanged

**Deliverable**: All models resolve under correct schemas

---

### Phase 3: Country Isolation

**Actions**:
1. Verify RLS policies are applied to all country-scoped tables
2. Test cross-country read isolation
3. Verify `rls_interceptor.py` covers all tables

**Deliverable**: Security test passes; no cross-country data leak

---

### Phase 4: Canonical Pattern Enforcement

**Actions**:
1. Categories → materialized path (already partially implemented)
2. Variants → JSONB `attributes` + GIN (already partially implemented)
3. AI → staging + commit + `ai_upload_jobs` audit (already implemented in `ai_upload.py`)
4. Finance → ledger-chain service + immutable posted entries

**Deliverable**: Pattern tests pass

---

### Phase 5: Normalization & Storage Fixes

**Actions**:
1. Split `country_configs` (85 columns) into:
   - `country_basics`
   - `country_economics`
   - `country_tax`
   - `country_legal`
2. Add missing indexes (~62 single-index tables)
3. Add missing FK constraints (~44 tables)
4. Verify no file bytes stored in database

**Deliverable**: Normalized tables; improved query performance

---

### Phase 6: Governance Automation

**Actions**:
1. Auto-regenerate data dictionary in CI
2. Publish ownership map
3. Alert on orphan tables

**Deliverable**: Automated documentation pipeline

---

## Detailed Task Breakdown

### Immediate Actions (Next Session)

1. **Create generate_data_dictionary.py**
   - Introspect `Base.metadata`
   - Output markdown table dictionary
   - Generate schema index
   - Output to `documents/GENERATED_DATA_DICTIONARY.md`

2. **Create missing model files**

   `country_basics.py`:
   ```python
   class CountryBasics(Base):
       __tablename__ = "country_basics"
       __table_args__ = {"schema": "country"}
       id = Column(Integer, primary_key=True)
       code = Column(String(3), unique=True, nullable=False, index=True)
       name = Column(String, nullable=False)
       # ... other columns from countries.py that belong in basics
   ```

   `country_economics.py`:
   ```python
   class CountryEconomics(Base):
       __tablename__ = "country_economics"
       __table_args__ = {"schema": "country"}
       country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
       # ... economic columns
   ```

   `country_tax.py`:
   ```python
   class CountryTax(Base):
       __tablename__ = "country_tax"
       __table_args__ = {"schema": "country"}
       country_code = Column(String(3), ForeignKey("country.country_configs.code"), nullable=False, unique=True)
       # ... tax columns
   ```

3. **Create missing migration**

   `20260730_0007_fix_country_code_width.py`:
   - Rename `code` column from VARCHAR(10) to VARCHAR(3)
   - Update all FK references
   - Create country_basics, country_economics, country_tax, country_legal tables

4. **Update pool settings**
   - Change defaults in `utils/config.py` to 5/10
   - Or update `DATABASE_SCOPE.md` if 20/30 is intentional

---

## Verification Checklist

After each phase:

- [ ] All models import without error
- [ ] `alembic check` passes (no schema drift)
- [ ] Migration chain runs without error
- [ ] Tests pass (unit + integration)
- [ ] Data dictionary regenerated
- [ ] ADR updated if decisions changed

---

## References

- Document: `documents/01_DATABASE.md` (v2.1)
- Current migrations: `backend/alembic/versions/`
- Current models: `backend/models/`
- Configuration: `backend/utils/config.py`
- Database setup: `backend/db/database.py`
- RLS: `backend/utils/rls_interceptor.py`