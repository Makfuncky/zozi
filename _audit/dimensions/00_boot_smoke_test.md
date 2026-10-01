# DIMENSION: Boot Smoke Test

## Summary
- Confirmation: ❌
- Files inspected: 10
- Files compliant: 2
- Files with findings: 8
- Laws implicated: [L-83, L-83, L-83, L-83, L-83, L-83, L-83, L-83]
- Findings: 8
- P0: 8  P1: 0  P2: 0  P3: 0
- Clusters: 1
- Average confidence: 5/5
- Average evidence strength: triangulated
- Status: NEW: 6 · COMPILED: 0 · RESOLVED: 2 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 8 yes · 0 partial · 0 no

## Findings

| BOOT-001 | boot | RESOLVED | CLUSTER-boot-failure | backend/config.py:340 | AttributeError: Settings has no attribute 'DATABASE_URL' | DATABASE_URL is set and reachable | Required env var missing from settings | Define DATABASE_URL in pydantic-settings config | S | P0 | 5 | triangulated | L0 | VERIFIED | backend/config.py:340 | python -c "from backend.config import settings; print(settings.DATABASE_URL)" | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-002 | yes |
| BOOT-002 | boot | RESOLVED | CLUSTER-boot-failure | backend/config.py:340 | AttributeError: Settings has no attribute 'VALKEY_URL' | Valkey reachable | Required env var missing from settings | Define VALKEY_URL in pydantic-settings config | S | P0 | 5 | triangulated | L0 | VERIFIED | backend/config.py:340 | python -c "from backend.config import settings; import redis; r = redis.Redis.from_url(settings.VALKEY_URL); print(r.ping())" | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-001 | yes |
| BOOT-003 | boot | NEW | CLUSTER-boot-failure | frontend/web_app/src/app/admin/analytics/page.tsx:12 | Module not found: Can't resolve '@/stores/currencyStore' | Builds without error | 24 build errors including missing stores, leaflet, icons | Create missing store files and fix missing dependencies | M | P0 | 5 | triangulated | L0 | VERIFIED | frontend/web_app/src/app/admin/analytics/page.tsx:12 | cd frontend/web_app && pnpm build | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-004 | yes |
| BOOT-004 | boot | NEW | CLUSTER-boot-failure | docker-compose.yml:1 | service "pgbouncer" depends on undefined service "db": invalid compose project | Valid config | Docker compose references undefined service | Fix docker-compose service definitions | S | P0 | 5 | triangulated | L0 | VERIFIED | docker-compose.yml:1 | docker compose config | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-005 | yes |
| BOOT-005 | boot | NEW | CLUSTER-boot-failure | backend/alembic.ini:1 | FAILED: No 'script_location' key found in configuration | Exactly one revision head | Alembic configuration missing script_location | Add script_location to alembic.ini | S | P0 | 5 | triangulated | L0 | VERIFIED | backend/alembic.ini:1 | cd backend && alembic heads | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-006 | yes |
| BOOT-006 | boot | NEW | CLUSTER-boot-failure | tests/providers/test_functional_providers.py:679 | ruff reports 8393 errors | Passes | Massive lint failures across test suite | Fix ruff violations in 8393 locations | L | P0 | 5 | triangulated | L0 | VERIFIED | tests/providers/test_functional_providers.py:679 | cd backend && ruff check . | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-007 | yes |
| BOOT-007 | boot | NEW | CLUSTER-boot-failure | frontend/web_app/src/app/admin/analytics/page.tsx:12 | Multiple TS2551, TS2307, TS7006 errors | No type errors | TypeScript compilation fails with missing modules and implicit any types | Fix missing type declarations and implicit any types | M | P0 | 5 | triangulated | L0 | VERIFIED | frontend/web_app/src/app/admin/analytics/page.tsx:12 | cd frontend/web_app && pnpm tsc --noEmit | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-008 | yes |
| BOOT-008 | boot | NEW | CLUSTER-boot-failure | test/ | ERROR: file or directory not found: test/ | Collects without error | Test directory missing or misnamed | Create test directory or fix pytest collection path | S | P0 | 5 | triangulated | L0 | VERIFIED | test/ | pytest test/ --collect-only | test_ | irreversible | F-003, F-012, CHAIN-002, CHAIN-005 | none | BOOT-001 | yes |
