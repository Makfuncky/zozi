# DIMENSION: Architecture Tests (Backend)

## Summary
- Confirmation: ?
- Files inspected: 11 architecture test files (backend/tests/architecture/*.py, backend/tests/test_architecture_gates.py, backend/tests/system/test_import_direction_all_packages.py)
- Files compliant: 3
- Files with findings: 8
- Laws implicated: [L-1, L-4, L-6, L-7, L-20, L-23, L-51, L-53, L-71, L-97, L-99, L-100, L-104, L-105, L-106]
- Findings: 11
- P0: 5  P1: 3  P2: 2  P3: 1
- Clusters: 4
- Average confidence: 5/5
- Average evidence strength: multiple
- Status: NEW: 11 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 7 yes · 2 partial · 2 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| ARCHTEST-001 | testing | INVALID | CLUSTER-missing-test | backend/tests/architecture/test_schema_discipline.py:0 | File does not exist | __table_args__ schema discipline test exists per mandatory checks | Missing test file means no automated gate for Law 6 schema discipline | Create backend/tests/architecture/test_schema_discipline.py verifying __table_args__["schema"] on all ORM models | S (0.5h) | P0 | 5 | multiple | L0 | VERIFIED | backend/tests/architecture/test_db_schema_compliance.py:41 | ls backend/tests/architecture/test_schema_discipline.py | test_schema_discipline.py | N/A | Law 6 schema gate | ARCHTEST-002 | none | yes |
| ARCHTEST-002 | testing | INVALID | CLUSTER-missing-test | backend/tests/architecture/test_model_relocation.py:0 | File does not exist | Model relocation test exists per mandatory checks | Missing test file means no automated gate verifying models reside in correct domains | Create backend/tests/architecture/test_model_relocation.py asserting each model's module matches its domain package | S (0.5h) | P0 | 5 | multiple | L0 | VERIFIED | backend/tests/architecture/test_model_relocation.py:0 | ls backend/tests/architecture/test_model_relocation.py | test_model_relocation.py | N/A | Model placement gate | ARCHTEST-001 | none | yes |
| ARCHTEST-003 | testing | RESOLVED | CLUSTER-collection-blockage | backend/tests/architecture/test_feature_catalog.py:42-77; config.py:280 | 3 of 4 catalog tests fail with pydantic ValidationError: SECRET_KEY must be at least 64 characters when importing rbac.catalog | Feature catalog tests pass under CI with valid SECRET_KEY | Indirect config validation blocks Law 4 feature catalog aggregation tests | Inject 64+ char SECRET_KEY before config.py loads in test environment or mock settings in test | S (0.5h) | P0 | 5 | multiple | L0 | VERIFIED | backend/tests/architecture/test_feature_catalog.py:77 | cd backend && python -m pytest tests/architecture/test_feature_catalog.py -v 2>&1 | test_feature_catalog.py | Revert SECRET_KEY workaround | Law 4 feature gate | ARCHTEST-009 | none | yes |
| ARCHTEST-004 | testing | RESOLVED | CLUSTER-collection-blockage | backend/tests/architecture/test_feature_catalog.py:48-59 | test_every_domain_exposes_features_module fails: domains/media/features.py missing | Every domain package exposes domains/<domain>/features.py with FEATURES dict | media domain lacks features.py, blocking Law 4 single-sourcing gate | Add domains/media/features.py with FEATURES dict or exclude media from domain scan if intentional | S (0.5h) | P0 | 5 | single | L0 | VERIFIED | backend/tests/architecture/test_feature_catalog.py:59 | cd backend && python -m pytest tests/architecture/test_feature_catalog.py::TestFeaturesSingleSourced -v 2>&1 | test_feature_catalog.py | Revert features.py addition | Law 4 feature gate | ARCHTEST-003 | none | yes |
| ARCHTEST-005 | testing | RESOLVED | CLUSTER-collection-blockage | backend/tests/architecture/test_allowlist_shrinks.py:78-80 | DOMAIN_ALLOWLIST.yaml has 0 entries per _entry_count heuristic; test fails with AssertionError: 0 > 0 | DOMAIN_ALLOWLIST.yaml contains 23 allowlist entries in source/target/symbols YAML format | _entry_count() requires "->" in line but current YAML uses source:/target: format; heuristic is broken | Update _entry_count to detect YAML list entries under cross_domain_imports (count lines starting with "  - source:") | S (0.5h) | P0 | 5 | single | L0 | VERIFIED | backend/tests/architecture/test_allowlist_shrinks.py:36-42 | cd backend && python -m pytest tests/architecture/test_allowlist_shrinks.py -v 2>&1 | test_allowlist_shrinks.py | Revert _entry_count fix | Law 7 allowlist gate | none | none | yes |
| ARCHTEST-006 | testing | INVALID | CLUSTER-test-quality | backend/tests/test_architecture_gates.py:304-313; backend/tests/architecture/test_architecture_gates.py:336-352 | 1 of 7 architecture gate tests fails: TestAppBoot::test_app_loads_and_mounts_remediated_routes fails with SECRET_KEY validation error | All architecture gate tests pass | Indirect config validation blocks app boot gate (same root cause as ARCHTEST-003) | Fix SECRET_KEY injection in conftest.py to unblock app boot test | S (0.5h) | P1 | 5 | multiple | L0 | VERIFIED | backend/tests/test_architecture_gates.py:305 | cd backend && python -m pytest tests/test_architecture_gates.py -v 2>&1 | test_architecture_gates.py | Revert SECRET_KEY workaround | W1 router/controller/service gate | ARCHTEST-003 | none | partial |
| ARCHTEST-007 | testing | RESOLVED | CLUSTER-collection-blockage | backend/tests/architecture/test_country_staff_seed.py:28-55 | 3 of 4 seed tests fail with SECRET_KEY validation error when importing infrastructure.database.seed | Country staff seed tests pass under CI with valid SECRET_KEY | Indirect config validation blocks Law 5 seed data verification tests | Fix SECRET_KEY injection in conftest.py to unblock seed tests | S (0.5h) | P1 | 5 | multiple | L0 | VERIFIED | backend/tests/architecture/test_country_staff_seed.py:36 | cd backend && python -m pytest tests/architecture/test_country_staff_seed.py -v 2>&1 | test_country_staff_seed.py | Revert SECRET_KEY workaround | Law 5 country-isolation gate | ARCHTEST-003 | none | partial |
| ARCHTEST-008 | testing | COMPILED | CLUSTER-import-direction | backend/tests/system/test_import_direction_all_packages.py:621-676 | 3 of 6 import-direction tests fail: domains/infrastructure test files import rbac/providers; modules test files import __future__/sys/_ast_helpers | All lower-layer import-direction tests pass | tests/infrastructure/test_redis_integration.py and tests/infrastructure/test_storage_r2.py import forbidden layers rbac/providers; modules test files import stdlib not in allowed roots | Exclude tests/ subdirectories from import-direction scan or add test-file exclusion to layer scanners | S (1h) | P1 | 5 | single | L0 | VERIFIED | backend/tests/system/test_import_direction_all_packages.py:629 | cd backend && python -m pytest tests/system/test_import_direction_all_packages.py -v 2>&1 | test_import_direction_all_packages.py | Revert test exclusion | Law 1/97-106 import gate | none | none | no |
| ARCHTEST-009 | testing | INVALID | CLUSTER-collection-blockage | backend/tests:1 | 4251 tests collected / 9 collection errors: SECRET_KEY validation (2), HAS_BANK_API missing (1), CircuitBreakerRegistry missing (1), payments module missing (2), law-not-implemented assertion (1), domains/infrastructure import direction (2) | pytest --collect-only passes with zero errors (Law 71) | 9 test modules cannot be imported at collection time, blocking CI | Fix underlying import errors: SECRET_KEY, HAS_BANK_API, CircuitBreakerRegistry, payments module, law-not-implemented assertion, test import-direction exclusions | M (3h) | P1 | 5 | multiple | L0 | VERIFIED | backend/tests:1 | cd backend && python -m pytest --collect-only 2>&1 | tests/analytics/test_analytics_service.py; tests/architecture/test_rls_runtime.py; tests/domains/test_circuit_breaker.py; tests/finance/test_circuit_breaker.py; tests/finance/test_payment_idempotency.py; tests/architecture/test_law271_through_law295.py | Revert conftest.py and import fixes | CI pipeline, all downstream tests | ARCHTEST-003,ARCHTEST-005,ARCHTEST-008 | none | yes |
| ARCHTEST-010 | testing | INVALID | CLUSTER-ci-gap | .github/workflows/architecture-gate.yml:53; .github/workflows/deploy.yml:71-74 | CI runs tests/test_architecture_gates.py (architecture-gate.yml) and tests/architecture/test_import_laws.py + tests/architecture/test_architecture_gates.py + tests/architecture/test_laws_complete.py (deploy.yml) | CI runs ALL architecture law gates: test_import_laws, test_feature_catalog, test_schema_discipline, test_model_relocation, test_architecture_gates, test_db_schema_compliance, test_alembic_autogenerate_check, test_allowlist_shrinks, test_country_staff_seed, test_import_direction_all_packages | Missing from CI: test_feature_catalog.py, test_db_schema_compliance.py, test_alembic_autogenerate_check.py, test_allowlist_shrinks.py, test_country_staff_seed.py, test_import_direction_all_packages.py | Add all 11 architecture law gate test files to both CI workflows | M (1h) | P2 | 5 | multiple | L0 | VERIFIED | .github/workflows/deploy.yml:71 | grep -E "test_(import_laws | feature_catalog | schema_discipline | model_relocation | architecture_gates | db_schema_compliance | alembic_autogenerate_check | allowlist_shrinks | country_staff_seed | import_direction)" .github/workflows/*.yml | .github/workflows/architecture-gate.yml; .github/workflows/deploy.yml | N/A | CI architecture gate coverage | ARCHTEST-009 | none | partial |
| ARCHTEST-011 | testing | COMPILED | CLUSTER-test-duplication | backend/tests/test_architecture_gates.py:1-313; backend/tests/architecture/test_architecture_gates.py:1-354 | Identical architecture gate tests exist in both backend/tests/ and backend/tests/architecture/ | Single source of truth for architecture gate tests | Duplicate test files risk drift; CI references different paths in different workflows | Consolidate to backend/tests/architecture/test_architecture_gates.py and update CI references; remove duplicate | S (0.5h) | P2 | 5 | single | L0 | VERIFIED | backend/tests/test_architecture_gates.py:1; backend/tests/architecture/test_architecture_gates.py:1 | diff backend/tests/test_architecture_gates.py backend/tests/architecture/test_architecture_gates.py | backend/tests/test_architecture_gates.py | Revert consolidation | Test maintenance | none | none | no |

## Over all

### Problem(s)
1. `test_schema_discipline.py` does not exist ? no automated gate for Law 6 `__table_args__` schema discipline (though `test_db_schema_compliance.py` partially covers this).
2. `test_model_relocation.py` does not exist ? no automated gate verifying models reside in correct domain packages.
3. `test_feature_catalog.py` fails: `media/features.py` missing; SECRET_KEY validation blocks catalog aggregation tests.
4. `test_allowlist_shrinks.py` fails: `_entry_count()` heuristic is broken for current YAML `source:/target:` format.
5. `test_architecture_gates.py` fails: SECRET_KEY validation blocks `TestAppBoot::test_app_loads_and_mounts_remediated_routes`.
6. `test_country_staff_seed.py` fails: SECRET_KEY validation blocks 3 of 4 seed verification tests.
7. `test_import_direction_all_packages.py` partially fails: test files under `tests/infrastructure/` and `tests/modules/` import forbidden/stdlib roots.
8. `pytest --collect-only` reports 9 collection errors, blocking CI per Law 71.
9. CI workflows do not run all architecture law gate test files (missing 6 of 11 files).
10. Duplicate `test_architecture_gates.py` exists in both `backend/tests/` and `backend/tests/architecture/`.

### Solution(s)
1. Create `backend/tests/architecture/test_schema_discipline.py` with `__table_args__` schema assertions.
2. Create `backend/tests/architecture/test_model_relocation.py` with domain-package model placement assertions.
3. Add `domains/media/features.py` with `FEATURES` dict; fix SECRET_KEY injection in conftest.py to unblock catalog and app boot tests.
4. Update `_entry_count()` in `test_allowlist_shrinks.py` to count YAML list entries under `cross_domain_imports`.
5. Fix SECRET_KEY validation in conftest.py to pass a 64+ char key before importing config.py.
6. Exclude `tests/` subdirectories from import-direction layer scanners or add test-file exclusions.
7. Resolve collection errors: add `HAS_BANK_API` to `bank_api.py`, export `CircuitBreakerRegistry`, create missing `payments` module, remove or implement Law 280 assertion, fix test import paths.
8. Add all 11 architecture law gate test files to `.github/workflows/architecture-gate.yml` and `.github/workflows/deploy.yml`.
9. Consolidate duplicate `test_architecture_gates.py` to single location and update CI references.

### Suggestion(s)
1. Add a CI pre-collection gate (`pytest --collect-only`) that fails on any collection error before running tests.
2. Add architecture law gate tests to a dedicated CI workflow that runs on every push to `main`/`develop`.
3. Use `conftest.py` to inject a valid SECRET_KEY for all test environments to prevent config validation from blocking unrelated tests.
4. Add a test-coverage dashboard showing per-law gate pass/fail status.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Create missing test_schema_discipline.py | backend/tests/architecture/test_schema_discipline.py | yes | S | 5 |
| P0 | Create missing test_model_relocation.py | backend/tests/architecture/test_model_relocation.py | yes | S | 5 |
| P0 | Fix SECRET_KEY injection to unblock catalog, app boot, and seed tests | backend/tests/conftest.py | yes | S | 5 |
| P0 | Add domains/media/features.py | domains/media/features.py | yes | S | 5 |
| P0 | Fix _entry_count() heuristic for YAML allowlist format | backend/tests/architecture/test_allowlist_shrinks.py | yes | S | 5 |
| P0 | Resolve 9 collection errors (HAS_BANK_API, CircuitBreakerRegistry, payments module, Law 280, import paths) | multiple | yes | M | 5 |
| P1 | Exclude test files from import-direction layer scanners | backend/tests/system/test_import_direction_all_packages.py | partial | S | 5 |
| P1 | Add all 11 architecture law gate tests to CI workflows | .github/workflows/architecture-gate.yml; .github/workflows/deploy.yml | partial | S | 5 |
| P2 | Consolidate duplicate test_architecture_gates.py | backend/tests/test_architecture_gates.py | no | S | 5 |
