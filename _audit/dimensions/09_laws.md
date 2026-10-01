# DIMENSION: Laws — RBAC Sections

## Summary
- Confirmation: ✔️
- Files inspected: 36
- Files compliant: ~19
- Files with findings: 17
- Laws implicated: [L-4, L-12, L-18, L-42, L-70, L-84, L-102, L-104, L-167, L-197]
- Findings: 15
- P0: 0  P1: 0  P2: 0  P3: 15
- Clusters: 6
- Average confidence: 4/5
- Average evidence strength: multiple
- Status: NEW: 15 · COMPILED: 0 · RESOLVED: 1 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 3 yes · 0 partial · 12 no

## Findings

| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/admin/routers/disputes.py:35 | `require_feature("moderation.suppliers")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `moderation.suppliers` used in 3 endpoints but not defined in any `domains/*/features.py` (Law 4) | Add `moderation.suppliers` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/suppliers/features.py:1 | `grep -rn "moderation.suppliers" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Admin disputes, supplier moderation | none | yes |
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/admin/routers/tickets.py:43 | `require_feature("support.read")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `support.read` used in 3 endpoints but not defined in any `domains/*/features.py` (Law 4) | Add `support.read` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/comms/features.py:1 | `grep -rn "support.read" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Admin support tickets | none | yes |
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/admin/routers/tickets.py:82 | `require_feature("support.reply")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `support.reply` used in 1 endpoint but not defined in any `domains/*/features.py` (Law 4) | Add `support.reply` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/comms/features.py:1 | `grep -rn "support.reply" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Admin support tickets | none | yes |
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/admin/routers/tickets.py:109 | `require_feature("support.update")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `support.update` used in 1 endpoint but not defined in any `domains/*/features.py` (Law 4) | Add `support.update` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/comms/features.py:1 | `grep -rn "support.update" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Admin support tickets | none | yes |
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/customer/routers/reviews.py:63 | `require_feature("catalog.review.create")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `catalog.review.create` used in 1 endpoint but not defined in any `domains/*/features.py` (Law 4) | Add `catalog.review.create` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/catalog/features.py:1 | `grep -rn "catalog.review.create" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Customer review photo uploads | none | yes |
| LAW-12 | rbac | NEW | CLUSTER-missing-domain-features | backend/domains/media:1 | `domains/media/` exists with `services/` but no `features.py` | Every domain exposes a `features.py` (Law 4, Law 12) | `media` domain has no `features.py`, causing `test_feature_catalog.py` to fail and breaking catalog aggregation for media features (Law 12) | Add `features.py` to `domains/media/` or remove the domain if non-canonical | S (0.5h) | P3 | 5 | single | L0 | VERIFIED | backend/domains/media:1 | `ls backend/domains/media` | tests/architecture/test_feature_catalog.py | Revert media/features.py addition | Media asset management | none | no |
| LAW-167 | rbac | NEW | CLUSTER-permissions-drift | frontend/shared/src/permissions.ts:7 | Hardcoded static seed with 185 feature atoms | Dynamically generated from backend `/rbac/catalog` at build time (Law 167, Law 197) | `permissions.ts` is a hardcoded static seed with 185 atoms while backend catalog has 367 atoms; the file header claims AUTO-GENERATED but the generation script is not wired into build (Law 167) | Wire `scripts/generate-permissions.mjs` into frontend build pipeline and regenerate `permissions.ts` | M (2h) | P3 | 4 | multiple | L1 | VERIFIED | frontend/shared/src/permissions.ts:1 | `wc -l frontend/shared/src/permissions.ts` | tests/frontend/test_permissions_sync.py | Revert manual edits to permissions.ts | UI gating, all frontend feature checks | none | no |
| LAW-167 | rbac | NEW | CLUSTER-permissions-drift | backend/rbac/dependencies.py:49 | `_resolve_effective_features` does not accept or use `country` | Feature resolution incorporates country scope from ORM (Law 167, orthogonal country check) | `_resolve_effective_features` ignores country entirely; `db_grants` is always `[]` and `RolePermissionAssignment`/`UserPermissionOverride` tables with `country_code` are never queried (Law 167) | Query `RolePermissionAssignment` and `UserPermissionOverride` filtered by user country; merge country-scoped grants into `effective_features` | L (4h) | P3 | 3 | multiple | L1 | VERIFIED | backend/rbac/models/permission_entities.py:54 | `grep -n "country_code" backend/rbac/models/permission_entities.py` | tests/rbac/test_country_resolution.py | Revert resolution.py changes | All country-scoped permission enforcement | none | yes |
| LAW-167 | rbac | NEW | CLUSTER-country-not-orthogonal | backend/rbac/resolution.py:20 | `effective_features(role_features, db_grants, overrides, catalog)` — no `country` parameter | Country is orthogonal to feature check (Law 167) | `effective_features` signature has no `country` parameter; docstring claims country scope but implementation ignores it (Law 167) | Add `country: Optional[str] = None` parameter; filter `db_grants` by country before merging | M (2h) | P3 | 3 | multiple | L1 | VERIFIED | backend/rbac/dependencies.py:39 | `grep -n "def effective_features" backend/rbac/resolution.py` | tests/rbac/test_country_resolution.py | Revert resolution.py signature change | All country-scoped permission enforcement | none | yes |
| LAW-12 | rbac | NEW | CLUSTER-domain-rbac-model-mismatch | backend/domains/security/models:112 | RBAC ORM models live in `backend/rbac/models/permission_entities.py`, not `domains/security/models/rbac.py` | RBAC ORM models in `domains/security/models/rbac.py` per scope | RBAC ORM models (`PermissionCategory`, `Permission`, `RolePermissionAssignment`, `UserPermissionOverride`, `PermissionAuditLog`) are in `backend/rbac/models/`, not `domains/security/models/` (Law 12) | Move ORM models to `domains/security/models/rbac.py` or mark `backend/rbac/models/` as approved RBAC location | M (2h) | P3 | 4 | single | L0 | VERIFIED | backend/rbac/models/permission_entities.py:1 | `ls backend/rbac/models` | tests/architecture/test_domain_allowlist.py | Revert model location change | Permission CRUD, RBAC admin UI | none | no |
| LAW-4 | rbac | NEW | CLUSTER-missing-feature-atoms | backend/modules/customer/routers/reviews.py:63 | `require_feature("catalog.review.create")` | Atom defined in `domains/*/features.py` and present in `rbac/catalog.py` | `catalog.review.create` used in 1 endpoint but not defined in any `domains/*/features.py` (Law 4) | Add `catalog.review.create` to the owning domain's `features.py` | S (0.5h) | P3 | 5 | multiple | L0 | VERIFIED | backend/domains/catalog/features.py:1 | `grep -rn "catalog.review.create" backend/domains` | tests/architecture/test_feature_catalog.py | Revert added feature atom | Customer review photo uploads | none | yes |
| LAW-84 | rbac | NEW | CLUSTER-rbac-init-import-chain | backend/rbac/__init__.py:14 | `from infrastructure.utils.dependencies import get_current_user` | `rbac/__init__.py` has no heavy imports that crash test environment (Law 84) | `rbac/__init__.py` imports `infrastructure.utils.dependencies` which cascades to `infrastructure.utils.config` -> `config.py` -> `Settings()` instantiation, causing `test_feature_catalog.py` to crash (Law 84) | Make `rbac/__init__.py` imports lazy or remove heavy re-exports; keep `rbac/` self-contained | S (1h) | P3 | 4 | single | L0 | VERIFIED | backend/tests/architecture/test_feature_catalog.py:42 | `python -m pytest backend/tests/architecture/test_feature_catalog.py -q` | tests/architecture/test_feature_catalog.py | Revert rbac/__init__.py changes | RBAC test suite, all catalog tests | none | no |
| LAW-197 | rbac | NEW | CLUSTER-permissions-stale-seed | frontend/shared/src/permissions.ts:7 | 185 hardcoded feature atoms | 367 atoms dynamically fetched from `/api/v1/rbac/catalog` at runtime (Law 197) | `permissions.ts` contains 185 hardcoded atoms while backend catalog has 367; `FEATURE_GROUPS` and `FEATURE_SET` are stale, causing frontend to reject valid features and allow unknown ones (Law 197) | Regenerate `permissions.ts` via `scripts/generate-permissions.mjs` and wire into CI/build | M (2h) | P3 | 4 | multiple | L1 | VERIFIED | frontend/shared/src/permissions.ts:1 | `node scripts/generate-permissions.mjs` | tests/frontend/test_permissions_sync.py | Revert manual permissions.ts edits | UI gating, all frontend RBAC | none | no |
| LAW-167 | rbac | NEW | CLUSTER-public-employee-data | backend/modules/employee/routers/hr/employees.py:130 | `list_employees_public` with no auth dependency | Employee data endpoints require authentication (Law 167) | `list_employees_public` endpoint returns employee data without any auth dependency (no `require_feature`, `require_module`, `get_current_user`, or role check) (Law 167) | Add `require_feature("hr.read")` or `get_current_user` to `list_employees_public` | S (0.5h) | P3 | 5 | single | L0 | VERIFIED | backend/modules/employee/routers/hr/employees.py:130 | `grep -n "list_employees_public" backend/modules/employee/routers/hr/employees.py` | tests/modules/employee/test_hr_routers.py | Revert employees.py line 130 | Employee PII exposure | none | yes |
| LAW-4 | rbac | NEW | CLUSTER-catalog-empty-db_grants | backend/rbac/dependencies.py:49 | `db_grants=[]` hardcoded in `_resolve_effective_features` | `db_grants` populated from `RolePermissionAssignment` and `UserPermissionOverride` ORM tables (Law 4) | `_resolve_effective_features` passes `db_grants=[]` instead of querying `RolePermissionAssignment` (role + country + permission grants) and `UserPermissionOverride` (user + country + permission overrides) (Law 4) | Query `RolePermissionAssignment` and `UserPermissionOverride` filtered by user and country; pass results as `db_grants` | L (4h) | P3 | 3 | multiple | L1 | VERIFIED | backend/rbac/models/permission_entities.py:54 | `grep -n "db_grants" backend/rbac/dependencies.py` | tests/rbac/test_db_grants.py | Revert dependencies.py db_grants change | All database-backed permission grants | none | yes |
| LAW-42 | rbac | RESOLVED | CLUSTER-schema-validation | backend/modules/admin/routers/finance.py:40,52,75,89 | `payload: dict = Body(...)` on 4 write endpoints | Pydantic schema (`CommissionCategoryRateCreate` / `CommissionBadgeTierCreate`) used for Body validation (Law 42) | All 4 write endpoints used raw dict bodies without schema validation | Replaced all 4 `payload: dict = Body(...)` with typed Pydantic models; removed manual coercion blocks; added schemas import | S (1h) | P3 | 5 | single | L0 | RESOLVED | infrastructure/database/schemas.py:1079,1111 | `grep -n "dict = Body" backend/modules/admin/routers/finance.py` returns 0 | tests/modules/admin/test_finance_router.py | Revert to dict payloads if Pydantic breaks clients | Admin finance rate/badge-tier endpoints | none | none | no |

## Over all

### Problem(s)
1. Five feature atoms (`moderation.suppliers`, `support.read`, `support.reply`, `support.update`, `catalog.review.create`) are used in production routers but not defined in any `domains/*/features.py`, causing endpoints to return 403 for all users including admins.
2. `rbac/resolution.py` does not incorporate country into feature resolution despite ORM models (`RolePermissionAssignment`, `UserPermissionOverride`) supporting country-scoped grants; `db_grants` is always `[]`.
3. `backend/rbac/__init__.py` imports `infrastructure.utils.dependencies` which cascades to `config.py` -> `Settings()` instantiation, causing `test_feature_catalog.py` to crash in test environment.
4. `domains/media` exists as a domain with `services/` but no `features.py`, breaking catalog aggregation and causing architecture test failures.
5. `frontend/shared/src/permissions.ts` is a hardcoded static seed (185 features) while the backend catalog has 367 features; the generation script exists but is not wired into the build pipeline.
6. `employee/routers/hr/employees.py:130` `list_employees_public` returns employee data without any authentication dependency.
7. `require_module()` is defined in `rbac/dependencies.py` but not used in any production router; role-based deps (`require_admin`, `require_logistics`, `require_supplier`) are used instead, meaning the feature catalog does not govern these endpoints.
 8. ~~FILE-131/Law 42: `backend/modules/admin/routers/finance.py` used `payload: dict = Body(...)` at 4 write endpoints~~ → **RESOLVED**: All 4 endpoints now use `CommissionCategoryRateCreate` / `CommissionBadgeTierCreate` Pydantic schemas. Manual coercion blocks removed. Tests pass.

### Solution(s)
1. Add the 5 missing feature atoms to their respective domain `features.py` files and re-run `scripts/generate-permissions.mjs`.
2. Update `rbac/resolution.py` to accept a `country` parameter; query `RolePermissionAssignment` and `UserPermissionOverride` filtered by user and country; merge country-scoped grants into effective features.
3. Make `backend/rbac/__init__.py` imports lazy or remove heavy re-exports to prevent test environment crashes.
4. Add `features.py` to `domains/media/` or remove the domain if it is non-canonical.
5. Wire `scripts/generate-permissions.mjs` into the frontend build pipeline and regenerate `permissions.ts`.
6. Add `require_feature("hr.read")` or `get_current_user` to `list_employees_public`.
7. Document that role-based deps (`require_admin`, `require_logistics`, `require_supplier`) are the intended access control for module-level routes, and ensure `require_module()` is used where feature-level granularity is needed.

### Suggestion(s)
1. Add a CI test that fails when any `require_feature("...")` literal in `modules/` is not present in the catalog.
2. Add a CI test that fails when any domain directory lacks a `features.py`.
3. Add a CI test that fails when `frontend/shared/src/permissions.ts` feature count diverges from backend catalog.
4. Add a pre-commit hook that regenerates `permissions.ts` from the local backend catalog.
5. Document the intended split between role-based module access (`require_admin`, `require_logistics`) and feature-level access (`require_feature`, `require_module`).

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P3 | Add 5 missing feature atoms to domains/*/features.py | `backend/domains/{catalog,comms,suppliers}/features.py` | yes | S (1h) | 5 |
| P3 | Wire country into rbac/resolution.py and populate db_grants from ORM | `backend/rbac/resolution.py`, `backend/rbac/dependencies.py` | yes | L (4h) | 3 |
| P3 | Add auth to list_employees_public endpoint | `backend/modules/employee/routers/hr/employees.py:130` | yes | S (0.5h) | 5 |
| P3 | Fix rbac/__init__.py import chain to prevent test crashes | `backend/rbac/__init__.py` | no | S (1h) | 4 |
| P3 | Add features.py to domains/media or remove domain | `backend/domains/media/` | no | S (0.5h) | 5 |
| P3 | Wire generate-permissions.mjs into frontend build | `frontend/`, `scripts/` | no | M (2h) | 4 |
| P3 | Document role-based vs feature-based auth split | `TECHNOLOGY_STACK.md`, `ARCHITECTURE_STACK.md` | no | S (0.5h) | 3 |

## FILE-69 Resolution

- **File:** `backend/infrastructure/utils/category_tree.py`
- **Resolution:** RESOLVED — LAW-EXTRACT-018 cluster (infrastructure imports from `domains/` at line 21) fixed by moving `Category` import to lazy function-level imports.
- **Evidence:**
  - `ast.parse` confirms 0 top-level imports from `domains.` in `category_tree.py`
  - Paired test `tests/architecture/test_file69_category_tree_law1.py` PASSED (2/2)
  - App boots with 79 routes
- **Laws satisfied:** Law 1 (import direction)

## FILE-73 Resolution

- **File:** `backend/infrastructure/utils/free_image_tools.py`
- **Resolution:** RESOLVED — ALREADY_FIXED. The audit finding (LAW-EXTRACT-018 cluster, P1) raised a static upward provider import. This was fixed by a prior resolution session which replaced `from providers.image.free_image_tools import *` with a lazy `__getattr__` + `importlib.import_module("providers.image.free_image_tools")` proxy. Current file has zero static `ImportFrom` nodes targeting `providers/` (confirmed via `ast.parse`). The lazy proxy preserves full backward compatibility — all 12 image tools (TOOL_REGISTRY, auto_process_image, magic_erase, etc.) are reachable via the shim.
- **Evidence:**
  - `ast.parse` confirms 0 top-level imports from `providers/` in `free_image_tools.py`
  - Paired test `backend/tests/infrastructure/test_free_image_tools_law1.py` PASSED (4/4)
  - App boots with 82 routes (`PYTHONPATH=backend python -c "from backend.main import app; print(len(app.routes))"`)

## FILE-74 Resolution

- **File:** `backend/infrastructure/utils/image_ai_service.py`
- **Resolution:** RESOLVED — ALREADY_FIXED. The audit finding (LAW-EXTRACT-018 cluster, P1) flagged a static upward provider import from `providers.ai.image_ai_service`. This was fixed in a prior session by replacing the static star-import with a `__getattr__`-based lazy loader using `importlib.import_module("providers.ai.image_ai_service")`. Current file has zero static `ImportFrom` nodes targeting `providers/` (confirmed via `ast.parse`). The lazy proxy preserves full backward compatibility — all public names from the canonical provider module remain importable via `from infrastructure.utils.image_ai_service import *`.
- **Evidence:**
  - `ast.parse` confirms 0 top-level imports from `providers/` in `image_ai_service.py`
  - Paired test `backend/tests/infrastructure/test_image_ai_service_law1.py::test_no_static_provider_import` PASSED (1/1)
  - Paired test `backend/tests/infrastructure/test_image_ai_service_backward_compat.py` PASSED (3/3)
  - Nature check: `PYTHONPATH=backend python -c "from infrastructure.utils.image_ai_service import *; print('OK')"` → PASS (OK)
  - App boots with 82 routes
 - **Laws satisfied:** Law 1 (import direction — infrastructure does not statically import from providers)
 - **Disposition:** ALREADY_FIXED — no code change required

## FILE-71 Resolution

- **File:** `backend/infrastructure/utils/currency_service.py`
- **Resolution:** FALSE POSITIVE — no code fix required. The audit claimed an infrastructure import from `providers.geography.rates` at line 12. Counter-evidence: line 12 = `import importlib`. The provider is loaded exclusively via `importlib.import_module("providers.geography.rates")` inside the `_lazy()` function — a runtime dynamic dispatch pattern. Law 1 (Arrows point down) prohibits STATIC import arrows, not runtime module resolution. The file's own docstring (lines 1-9) explicitly documents this as the Law 1 compliance mechanism. Verify command confirmed 0 static matches for `providers.geography` in the file. Sibling exemplar `country_rls.py` (FILE-70) uses the identical lazy-load pattern and was accepted as Law 1-compliant.
- **Evidence:**
  - `Select-String` verify: 0 matches for `providers.geography` in `currency_service.py`
  - Line 12 confirmed as `import importlib` (not a providers import)
  - File docstring (lines 1-9) documents lazy-load as Law 1 compliance mechanism
  - No code change warranted; "fixing" this would break currency conversion
- **Laws satisfied:** Law 1 (dependency direction — already satisfied via lazy-load)
- **Disposition:** AUDIT_CLAIM_WRONG — FALSE POSITIVE

## FILE-134 Resolution

- **File:** `backend/modules/customer/routers/catalog.py`
- **Resolution:** AUDIT_CLAIM_WRONG for finding (1) PERF-021; RESOLVED for finding (2) WIR-014.
- **Evidence:**
  - Finding (1) PERF-021: Contract claimed `catalog.py:59` "uses `.offset(offset)` for pagination". Counter-evidence: `catalog.py:59` is `offset=offset,` — a parameter pass-through to `get_products()`. The actual SQL `.offset(offset)` call is at `products_service.py:277`, which is outside this contract's `allowed_files` scope. The service layer documents why offset is acceptable (lines 272-276: shallow browse, cached, 1-3 pages deep). No keyset-based function in `ports.py` supports the same filtering/sorting API. Therefore the claim is misattributed and unfixable within this contract.
  - Finding (2) WIR-014: Already stated RESOLVED in the contract. Verified: all 7 catalog routes correctly gate on `require_feature("catalog.list")` or `require_feature("catalog.read")`.
- **Tests:** 8 passed (catalog-specific keyset pagination, law 3 cross-domain, feature catalog). No regressions.
- **Files changed:** 0
- **Laws satisfied:** Law 1 (dependency direction), Law 3 (cross-domain rules)

## FILE-75 Resolution

- **File:** `backend/infrastructure/utils/media_service.py`
- **Resolution:** FALSE POSITIVE (ALREADY_FIXED) — The audit finding LAW-EXTRACT-018 claimed this backward-compat shim imports from `providers.storage.storage_backend` at line 2. Counter-evidence: line 2 = `import importlib` (stdlib only). The lazy import at line 8 uses `importlib.import_module("infrastructure.storage.storage")` — a runtime dynamic dispatch within the `infrastructure/` layer, not from `providers/`. The scanner misattributed the provider-side import chain in `infrastructure.storage.storage` (which legitimately imports `from providers.storage import create_s3_client`) to this shim. No code changes are required by this sub-agent; the lazy `__getattr__` proxy already in place is the correct long-term form for this shim. All 4 paired tests pass. Laws 1 and 3 satisfied.
- **Evidence:**
  - `Select-String` verify: 0 matches for `from infrastructure\.storage\.storage import` in `backend/infrastructure/utils/`
  - Line 2 confirmed as `import importlib` (not a providers import)
  - Lazy import at line 8 targets `infrastructure.storage.storage` (same infrastructure layer)
  - Paired test `tests/architecture/test_media_service_isolation.py` PASSED (4/4)
  - Boot smoke: 82 routes
- **Tests:** 4 passed (media service isolation architecture tests)
- **Files changed:** 0 (no fix required)
- **Laws satisfied:** Law 1 (dependency direction — already satisfied via lazy-load), Law 3 (cross-domain rules)
- **Disposition:** AUDIT_CLAIM_WRONG — FALSE POSITIVE, finding ALREADY_FIXED

## FILE-76 Resolution

- **File:** `backend/infrastructure/utils/media_storage.py`
- **Resolution:** FALSE POSITIVE — no code fix required. The audit claimed LAW-EXTRACT-018: "Backward-compat shim importing from `providers.storage.storage_backend` at line 2. Infrastructure isolation broken by provider import." Counter-evidence: line 2 is blank. The file's only top-level imports are `import importlib` (line 3) and `from typing import Any` (line 4). Provider access is via `importlib.import_module("infrastructure.storage.storage")` inside `__getattr__` — runtime dynamic dispatch, NOT a static import arrow. The module `providers/storage/storage_backend.py` does not exist in the codebase. The canonical target `infrastructure.storage.storage` is the correct infrastructure-layer module. This was already corrected by a prior sub-agent (log FILE-76-media-storage.log, 2026-09-30T19:19:19Z). All 4 paired tests pass. Law 1 satisfied.
- **Evidence:**
  - `ast.parse` confirms 0 top-level `ImportFrom` nodes targeting `providers/` in `media_storage.py`
  - Verify command: `PYTHONPATH=backend python -c "from backend.main import app; print(len(app.routes))"` → 82 (PASS)
  - Paired test `backend/tests/architecture/test_media_storage_isolation.py` PASSED (4/4)
  - Nature check: `grep "providers.storage.storage_backend"` → 0 matches across all backend/*.py
- **Tests:** 4 passed (media storage isolation architecture tests)
- **Files changed:** 0 (no fix required)
- **Laws satisfied:** Law 1 (dependency direction — already satisfied via lazy-load), Law 3 (cross-domain rules)
- **Disposition:** AUDIT_CLAIM_WRONG — FALSE POSITIVE, finding ALREADY_FIXED

## FILE-81 Resolution

- **File:** `backend/middleware/impossible_travel_middleware.py`
- **Resolution:** ALREADY_FIXED — no code change required. The audit claim (LAW-EXTRACT-015, P1) stated that line 16 imports `from providers.geography.geoip import lookup_coordinates`. Counter-evidence: line 16 is `from infrastructure.geography import lookup_coordinates`. The `infrastructure/geography/__init__.py` wrapper already exists and delegates to `providers.geography.geoip` (lines 8-9), so middleware complies with Law 104 (middleware restricted to `infrastructure/` + `rbac/` only). Verify command confirms 0 matches for `providers.geography` in the file. All 6 paired tests pass, including `test_impossible_travel_imports_from_infrastructure_only`. Import laws gate passes with zero violations.
- **Evidence:**
  - `Select-String` verify: 0 matches for `providers.geography` in `impossible_travel_middleware.py`
  - Line 16 confirmed as `from infrastructure.geography import lookup_coordinates`
  - `infrastructure/geography/__init__.py` exists as wrapper delegating to `providers.geography.geoip`
  - Paired test `backend/tests/security/test_middleware_pipeline.py::TestImpossibleTravelDetection` PASSED (6/6)
  - Nature check: `pytest backend/tests/architecture/test_import_laws.py -v` PASSED (2/2)
- **Tests:** 6 passed (impossible travel middleware tests)
- **Files changed:** 0 (no fix required)
- **Laws satisfied:** Law 1 (dependency direction — middleware imports from infrastructure only), Law 104 (middleware restricted to infrastructure/ + rbac/)
- **Disposition:** ALREADY_FIXED — no code change required
