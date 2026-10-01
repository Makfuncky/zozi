# ZOZI Platform — Work Plan

## Objective
Execute pending technology-stack upgrade tasks identified during alignment of `documents/TECHNOLOGY_USED.md` with the canonical `_most_imp_docx/TECHNOLOGY_STACK.md`.

## Scope
- Remove deprecated/forbidden Python packages from `backend/requirements.txt` and code
- Migrate JWT library from `python-jose` to `PyJWT`
- Update deprecated environment variable references to canonical names
- Update code that imports/uses removed packages

## Excluded
- Frontend/mobile dependency updates
- Database schema changes
- New feature development

## Work State

### Completed
- [x] Phase 0 reconnaissance: extracted routers, features, RBAC roles, pages, schemas into `_feature_extraction/`
- [x] Aligned `documents/TECHNOLOGY_USED.md` with canonical `_most_imp_docx/TECHNOLOGY_STACK.md`
- [x] Updated `_most_imp_docx/TECHNOLOGY_STACK.md` with deprecated aliases, security notes, and migration timelines

### Active
- [ ] Migrate `python-jose` → `PyJWT` across backend codebase
- [ ] Remove deprecated packages from `backend/requirements.txt`
- [ ] Update deprecated env var references in code/config

### Blocked
- (none)

## Next Steps
1. Migrate all `from jose import jwt` usages to `import jwt as pyjwt` / `from pyjwt import ...`
2. Remove `python-jose[cryptography]==3.5.0` from `backend/requirements.txt`
3. Remove `python-magic==0.4.27`, `pytz`, `tzlocal`, `duckdb-engine`, `prometheus-client`, `requests`, `psycopg2-binary` from requirements
4. Update config.py to map deprecated S3_* env vars to R2_* canonical names
5. Update config.py to map REDIS_URL → VALKEY_URL
6. Update config.py to map ENCRYPTION_KEY → FIELD_ENCRYPTION_KEY
7. Update alembic/env.py to use DATABASE_URL_DIRECT
8. Run tests to verify changes
