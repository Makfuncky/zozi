# ZOZI Platform — Progress Log

## 2026-09-27

### Completed
- **Phase 0 Reconnaissance**: Created `_feature_extraction/00_manifest.md` and `_feature_extraction/01_raw/*.md` documenting all routers, features, RBAC roles, web pages, mobile screens, and database schemas.
- **Technology Stack Alignment**: Corrected `documents/TECHNOLOGY_USED.md` to align with canonical `_most_imp_docx/TECHNOLOGY_STACK.md`. Updated both documents with:
  - Single-engine Neon PostgreSQL at every level (no local Postgres container)
  - Valkey as canonical cache/session/broker (replacing Redis naming)
  - Cloudflare R2 as canonical object storage (replacing S3 naming)
  - PyJWT as canonical JWT library (replacing python-jose)
  - Deprecated aliases section with migration timelines
  - Security note on AUTH_SECRET duplication risk
- **python-jose → PyJWT Migration**:
  - Removed `python-jose[cryptography]==3.5.0` from `backend/requirements.txt`
  - Updated `backend/providers/auth/jwt.py` to use PyJWT with backward-compat exports
  - Updated `backend/infrastructure/security/auth.py` to use `pyjwt`/`PyJWTError`
  - Updated `backend/domains/comms/services/system_comms_status_service.py` to remove unused jose import
  - Updated test files: `test_authentication.py`, `test_functional_providers.py`, `test_provider_isolation.py`, `test_security_regression.py`, `test_import_direction_all_packages.py`
- **Deprecated Package Removals from requirements.txt**:
  - Removed `python-magic==0.4.27` (unused in codebase; `puremagic` is preferred per stack doc)
  - Removed `pytz==2026.3.post1` and `tzlocal==5.4.4` (no imports found; `zoneinfo`+`tzdata` are canonical)
  - Removed `duckdb==1.5.5` and `duckdb-engine==0.17.0` (no imports found; DuckDB not deployed)
  - Removed `psycopg2-binary==2.9.12` (no imports found; `asyncpg` is canonical)
- **Env Var Canonicalization**:
  - Updated `backend/infrastructure/storage/storage.py` to prefer `R2_*` env vars with fallback to deprecated `S3_*` aliases

### Active
- (none)

### Blocked
- (none)
