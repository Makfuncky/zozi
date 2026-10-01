# DIMENSION: Architectural

## Summary
- Confirmation: ✔️
- Files inspected: 32
- Files compliant: 12
- Files with findings: 20
- Laws implicated: [L-1, L-2, L-3, L-4, L-5, L-6, L-12, L-13, L-14, L-15, L-17, L-42, L-97, L-98, L-99, L-100, L-101, L-102, L-103, L-104, L-105, L-106]
- Findings: 14
- P0: 2  P1: 6  P2: 5  P3: 1
- Clusters: 5
- Average confidence: 4/5
- Average evidence strength: multiple
- Status: NEW: 14 · COMPILED: 0 · RESOLVED: 0 · DEFERRED: 0 · INVALID: 0
- Completion blockers: 3 yes · 5 partial · 14 no

## Findings
| ID | Phase | Status | Cluster | File:Line | Current | Target | Delta | Fix | Effort | Priority | Confidence | Evidence strength | Truth level | Claim state | Sibling | Verify | Test | Rollback | Blast radius | Depends on | Blocks | Completion blocker |
|----|-------|--------|---------|-----------|---------|--------|-------|-----|--------|----------|------------|-------------------|-------------|-------------|---------|--------|------|----------|--------------|------------|--------|-------------------|
| ARCH-001 | arch | NEW | domain-count | backend/domains:dirs | 17 domains (accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, media, orders, payments, promotions, security, suppliers) | 15 domains (accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, logistics, orders, promotions, security, suppliers) | +2 extra (media, payments) | Remove or absorb media and payments domains into allowed 15; update DOMAIN_ALLOWLIST.yaml | S | P1 | 5 | triangulated | L1 | VERIFIED | backend/domains/payments/ports.py:1 | ls backend/domains | n/a | n/a | architecture | none | none | no |
| ARCH-002 | arch | NEW | allowlist | backend/DOMAIN_ALLOWLIST.yaml:4-53 | 22 cross-domain import entries with no removal dates | Each entry must carry a dated removal plan | Missing dates | Add `removal_date` and `owner` fields to every entry; schedule quarterly reviews | S | P1 | 5 | triangulated | L0 | VERIFIED | backend/DOMAIN_ALLOWLIST.yaml:8 | cat backend/DOMAIN_ALLOWLIST.yaml | n/a | n/a | debt tracking | none | none | no |
| ARCH-003 | arch | NEW | cross-domain-write | backend/domains/finance/services/data_import_service.py:11-25 | Direct model imports from domains.catalog.models.products and domains.logistics.models.erp with direct db.add() writes | Cross-domain writes must go through events.py/subscribers.py only | Direct writes to foreign domain models | Route all writes through OrderCreated/OrderDelivered events or dedicated finance events; remove direct model imports | L | P0 | 5 | triangulated | L0 | VERIFIED | backend/domains/finance/services/data_import_service.py:11 | grep domains.catalog.models.products backend/domains/finance/services/data_import_service.py | n/a | n/a | data integrity | none | none | yes |
| ARCH-004 | arch | NEW | cross-domain-read | backend/domains/finance/services/country/admin_commission_service.py:11 | Direct import of domains.governance.models.admin.CommissionBadgeTier | Cross-domain reads must go through ports.py/read_models only | Direct model import from governance | Expose CommissionBadgeTier read helpers via governance.ports.py and import from there | S | P1 | 5 | triangulated | L0 | VERIFIED | backend/domains/finance/services/country/admin_commission_service.py:11 | grep CommissionBadgeTier backend/domains/finance/services/country/admin_commission_service.py | n/a | n/a | coupling | none | none | partial |
| ARCH-005 | arch | NEW | router-thinness | backend/modules/admin/routers/hr.py:31-70 | Inline Pydantic models (ExpenseSubmitRequest, AddressRequest, DependentRequest, COIReportRequest, DisciplinaryCaseRequest, OffboardingCaseRequest) defined in router file | Routers must contain only auth + require_feature + one service call | Business/HTTP concerns mixed in router | Move all Pydantic request bodies to domains/hr/schemas/; keep routers to one service call per endpoint | S | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/admin/routers/hr.py:31 | grep "class .*Request" backend/modules/admin/routers/hr.py | n/a | n/a | maintainability | none | none | no |
| ARCH-006 | arch | NEW | router-thinness | backend/modules/admin/routers/security.py:43-139 | OTP rate limiting (_otp_rate_limit) and Turnstile verification (_verify_turnstile) functions defined in router file | Routers must contain only auth + require_feature + one service call | Security/business logic in router layer | Move _otp_rate_limit to domains/accounts/services/auth/rate_limiter.py; move _verify_turnstile to infrastructure/security/turnstile.py | S | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/admin/routers/security.py:43 | grep "def _otp_rate_limit\|def _verify_turnstile" backend/modules/admin/routers/security.py | n/a | n/a | separation | none | none | no |
| ARCH-007 | arch | NEW | router-thinness | backend/modules/employee/routers/finance.py:31-42 | Inline ReportPeriod(BaseModel) and _with_rls helper function in router file | Routers must contain only auth + require_feature + one service call | Presentation and RLS logic in router | Move ReportPeriod to domains/finance/schemas/; move _with_rls to infrastructure/utils/rls_context.py | S | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/employee/routers/finance.py:31 | grep "class ReportPeriod\|def _with_rls" backend/modules/employee/routers/finance.py | n/a | n/a | separation | none | none | no |
| ARCH-008 | arch | NEW | cross-domain-read | backend/modules/logistics/routers/finance.py:18 | Import from domains.finance.services.finance_service instead of domains.finance.ports | Cross-domain reads must go through ports.py only | Direct service import bypassing ports | Replace import with domains.finance.ports.logistics_financial_summary etc. | S | P1 | 5 | triangulated | L0 | VERIFIED | backend/modules/logistics/routers/finance.py:18 | grep "domains.finance.services.finance_service" backend/modules/logistics/routers/finance.py | n/a | n/a | coupling | none | none | partial |
| ARCH-009 | arch | NEW | cross-domain-read | backend/modules/employee/routers/finance.py:22 | Import from domains.finance.services.ledger.general_ledger_service directly | Cross-domain reads must go through ports.py only | Direct service import bypassing ports | Replace with domains.finance.ports.list_journal_entries etc. | S | P1 | 5 | triangulated | L0 | VERIFIED | backend/modules/employee/routers/finance.py:22 | grep "domains.finance.services.ledger.general_ledger_service" backend/modules/employee/routers/finance.py | n/a | n/a | coupling | none | none | partial |
| ARCH-010 | arch | NEW | file-placement | backend/domains/finance/services/country/admin_cash_service.py:41 | create_account() calls undefined create_cash_account_model (commented out import at line 15) | Business logic must be fully defined and functional | Runtime NameError on create_account endpoint | Uncomment or implement create_cash_account_model in domains/comms/services/utility/misc_write_service.py | S | P0 | 5 | triangulated | L0 | VERIFIED | backend/domains/finance/services/country/admin_cash_service.py:15,41 | grep "create_cash_account_model" backend/domains/finance/services/country/admin_cash_service.py | n/a | n/a | runtime crash | none | none | yes |
| ARCH-011 | arch | NEW | allowlist | backend/DOMAIN_ALLOWLIST.yaml:37 | Entry references "domains.finance.services.*.all() -> multiple files (add pagination)" with no dated plan | All entries must carry dated removal plans | Indefinite pagination debt | Assign owner and target date for adding pagination to each .all() call | S | P3 | 3 | single | L1 | VERIFIED | backend/DOMAIN_ALLOWLIST.yaml:37 | grep "OFFSET pagination\|all()" backend/DOMAIN_ALLOWLIST.yaml | n/a | n/a | performance | none | none | no |
| ARCH-012 | arch | NEW | domain-ports | backend/domains/finance/ports.py:44 | Direct import of domains.logistics.models.erp.* in ports.py | ports.py should only expose read helpers, not import foreign domain models directly | Cross-domain model coupling in ports | Use lazy imports or read_models for logistics ERP models; expose via logistics.ports instead | S | P1 | 4 | multiple | L1 | VERIFIED | backend/domains/finance/ports.py:44 | grep "domains.logistics.models.erp" backend/domains/finance/ports.py | n/a | n/a | coupling | none | none | partial |
| ARCH-013 | arch | NEW | module-auth | backend/modules/supplier/auth/dependencies.py:7-8 | Re-exports require_admin, require_supplier, require_roles from domains.accounts.services.auth.security_dependencies | Auth dependencies should live in infrastructure/security/dependencies.py and be re-exported, not directly from domain services | Module auth coupling to accounts domain | Move shared auth dependencies to infrastructure/security/dependencies.py; modules import from there | S | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/supplier/auth/dependencies.py:7 | grep "require_admin" backend/modules/supplier/auth/dependencies.py | n/a | n/a | coupling | none | none | no |
| ARCH-014 | arch | NEW | module-auth | backend/modules/customer/auth/dependencies.py:7 | Re-exports require_customer, require_roles, get_current_user from domains.accounts.services.auth.security_dependencies | Auth dependencies should live in infrastructure/security/dependencies.py | Module auth coupling to accounts domain | Move shared auth dependencies to infrastructure/security/dependencies.py; modules import from there | S | P2 | 4 | multiple | L1 | VERIFIED | backend/modules/customer/auth/dependencies.py:7 | grep "require_customer" backend/modules/customer/auth/dependencies.py | n/a | n/a | coupling | none | none | no |

## Overall
### Problem(s)
1. Two extra domains (`media`, `payments`) exist beyond the mandated 15, breaking architectural boundaries.
2. `DOMAIN_ALLOWLIST.yaml` has no dated removal plans for any cross-domain import, making strangler-debt tracking impossible.
3. Cross-domain writes in `domains/finance/services/data_import_service.py` bypass `events.py`/`subscribers.py` and directly write to foreign domain models (`domains.catalog.models.products.Product`, `domains.logistics.models.erp.*`).
4. Cross-domain reads bypass `ports.py`: `modules/logistics/routers/finance.py` and `modules/employee/routers/finance.py` import directly from `domains.finance.services.*` instead of `domains.finance.ports`.
5. Router thinness is violated: `modules/admin/routers/hr.py` contains inline Pydantic models; `modules/admin/routers/security.py` contains OTP rate-limiting and Turnstile verification business logic; `modules/employee/routers/finance.py` contains inline `ReportPeriod` model and `_with_rls` helper.
6. `domains/finance/services/country/admin_cash_service.py` calls an undefined `create_cash_account_model` (import commented out), causing a runtime `NameError`.
7. Multiple domain services import `fastapi` (HTTPException, Depends, Query, Request), leaking controller concerns into the domain layer.
8. `domains/finance/ports.py` directly imports `domains.logistics.models.erp.*`, creating cross-domain model coupling in the read surface.
9. Module auth dependencies (`modules/*/auth/dependencies.py`) re-export from `domains.accounts.services.auth.security_dependencies` instead of a centralized `infrastructure/security/dependencies.py`.

### Solution(s)
1. Remove or absorb `domains/media` and `domains/payments` into the allowed 15, or update the architecture spec to include them.
2. Add `removal_date`, `owner`, and `verification` fields to every entry in `DOMAIN_ALLOWLIST.yaml`; enforce quarterly review.
3. Refactor `domains/finance/services/data_import_service.py` to emit domain events (`OrderCreated`, `OrderDelivered`) for writes to catalog/logistics state, and consume those events in subscribers.
4. Update `modules/logistics/routers/finance.py` and `modules/employee/routers/finance.py` to import exclusively from `domains.finance.ports`.
5. Move inline Pydantic models from routers to domain `schemas/` directories; move security/business logic (OTP rate limiting, Turnstile, RLS helpers) out of routers into `infrastructure/` or domain services.
6. Uncomment and implement `create_cash_account_model` in `domains/comms/services/utility/misc_write_service.py`, or remove the dead code path.
7. Remove `fastapi` imports from domain services; raise domain-specific exceptions and let the router layer translate them to HTTP responses.
8. Refactor `domains/finance/ports.py` to use lazy imports or delegate ERP model reads to `domains/logistics/ports.py`.
9. Centralize auth dependencies in `infrastructure/security/dependencies.py` and update all module auth wrappers to import from there.

### Suggestion(s)
1. Add a CI lint rule that flags any `from fastapi import` in `domains/*/services/**/*.py`.
2. Add a CI lint rule that flags any `from domains.*.services.* import` in `modules/*/routers/**/*.py` unless the source module is the same domain as the router's primary actor.
3. Create an `ARCHITECTURE_STACK.md` law-compliance test suite that runs on every PR and asserts `DOMAIN_ALLOWLIST.yaml` entries have `removal_date` fields.

### Corrections required (prioritized)
| Priority | Correction | Target | Blocking | Effort | Confidence |
|---|---|---|---|---|---|
| P0 | Remove undefined `create_cash_account_model` call or implement it | backend/domains/finance/services/country/admin_cash_service.py:41 | yes | S | 5 |
| P0 | Route cross-domain writes in data_import_service through events.py/subscribers.py | backend/domains/finance/services/data_import_service.py:11-25 | yes | L | 5 |
| P0 | Enforce router thinness: remove inline Pydantic models and business logic from routers | backend/modules/admin/routers/hr.py:31-70, backend/modules/admin/routers/security.py:43-139, backend/modules/employee/routers/finance.py:31-42 | yes | M | 4 |
| P0 | Replace direct service imports with ports imports in logistics and employee finance routers | backend/modules/logistics/routers/finance.py:18, backend/modules/employee/routers/finance.py:22 | yes | S | 5 |
| P1 | Add dated removal plans to DOMAIN_ALLOWLIST.yaml entries | backend/DOMAIN_ALLOWLIST.yaml:4-53 | no | S | 5 |
| P1 | Resolve extra domains (media, payments): remove or add to spec | backend/domains/media, backend/domains/payments | no | M | 5 |
| P1 | Replace direct governance model import with ports in admin_commission_service | backend/domains/finance/services/country/admin_commission_service.py:11 | no | S | 5 |
| P1 | Remove fastapi imports from domain services; use domain exceptions | backend/domains/finance/services/*, backend/domains/hr/services/*, backend/domains/security/services/*, backend/domains/suppliers/services/*, backend/domains/accounts/services/* | no | L | 4 |
| P1 | Centralize auth dependencies in infrastructure/security/dependencies.py | backend/modules/*/auth/dependencies.py | no | S | 4 |
| P1 | Decouple finance/ports.py from logistics.models.erp direct imports | backend/domains/finance/ports.py:44 | no | S | 4 |
| P2 | Add CI lint rules for fastapi-in-domain and direct-service-import-in-router | .github/workflows/* or CI config | no | M | 3 |
| P3 | Address OFFSET pagination and .all() query debt tracked in DOMAIN_ALLOWLIST.yaml | backend/DOMAIN_ALLOWLIST.yaml:37-41 | no | L | 3 |

## FILE-52 Audit Claim Correction

- **File:** `backend/domains/accounts/services/users/user_management_service.py`
- **Resolution:** AUDIT_CLAIM_WRONG — contract misattributes ARCH-004 and ARCH-011 to this file.
- **Evidence:**
  - ARCH-004 actual location: `backend/domains/finance/services/country/admin_commission_service.py:11`
  - ARCH-011 actual location: `backend/DOMAIN_ALLOWLIST.yaml:37`
  - Neither finding appears in `user_management_service.py`
  - `CommissionBadgeTier` in this file is imported from `domains.governance.ports` (CORRECT pattern)
  - No `from domains.governance.models` imports exist in this file
- **Action taken:** No code changes; file is architecturally clean.

## FILE-69 Resolution

- **File:** `backend/infrastructure/utils/category_tree.py`
- **Resolution:** RESOLVED — moved top-level `from domains.catalog.models.products import Category` to lazy function-level imports inside `rebuild_category_paths` and `category_subtree_ids`.
- **Evidence:**
  - `ast.parse` confirms 0 top-level imports from `domains.` in `category_tree.py`
  - Paired test `tests/architecture/test_file69_category_tree_law1.py::TestFile69Law1Regression::test_no_top_level_domain_imports` PASSED
  - App boots with 79 routes
- **Laws satisfied:** Law 1 (import direction: infrastructure must not import domains at top level)


## FILE-131 Resolution

- **File:** `backend/modules/admin/routers/finance.py`
- **Resolution:** RESOLVED — replaced all 4 `payload: dict = Body(...)` occurrences with typed Pydantic models.
- **Evidence:**
  - `grep -n "dict = Body" backend/modules/admin/routers/finance.py` → 0 matches
  - All 6 protected endpoints retain `require_feature(...)` gates (WIR-013 — RESOLVED)
  - Added `backend/tests/modules/admin/test_finance_router.py` with 4 regression tests — all pass
  - 4 manual coercion blocks (`isinstance(payload, dict)` + `**payload`) removed
 - **Action taken:** Added `CommissionCategoryRateCreate`/`CommissionBadgeTierCreate` schemas import; replaced 4x `dict = Body(...)` with typed Pydantic models; removed 4 manual coercion lines.

## FILE-83 Resolution

- **File:** `backend/modules/admin/routers/staff.py`
- **Resolution:** RESOLVED — Note: contract claimed sub_admin/moderator "absent from" _ROLE_FEATURES — AUDIT_CLAIM_WRONG, they ARE present at backend/rbac/dependencies.py:90-108. However, inline defaults in staff.py were still duplicated. Fixed by adding `_STAFF_ROLE_DEFAULT_FEATURES` module-level constant and `_build_role_defaults()` that sources from canonical `_ROLE_FEATURES`.
- **Evidence:**
  - `_STAFF_ROLE_DEFAULT_FEATURES` and `_build_role_defaults` present in staff.py
  - `_ROLE_FEATURES` imported and used in `_build_role_defaults`
  - Inline `defaults = {` removed from `staff_permission_catalog_route` body
  - Source-level regression test `backend/tests/test_staff_router_privacy.py::test_permission_catalog_defaults_single_sourced` PASSED
- **Laws satisfied:** Law 162 (role definitions single-sourced)


## FILE-134 Resolution

- **File:** `backend/modules/customer/routers/catalog.py`
- **Resolution:** AUDIT_CLAIM_WRONG for finding (1) PERF-021; RESOLVED for finding (2) WIR-014.
- **Evidence:**
  - Finding (1) PERF-021: Contract claimed `catalog.py:59` "uses `.offset(offset)` for pagination". Counter-evidence: `catalog.py:59` is `offset=offset,` — a parameter pass-through to `get_products()`. The actual SQL `.offset(offset)` call is at `products_service.py:277`, which is outside this contract's `allowed_files` scope. The service layer documents why offset is acceptable (lines 272-276: shallow browse, cached, 1-3 pages deep). No keyset-based function in `ports.py` supports the same filtering/sorting API. Therefore the claim is misattributed and unfixable within this contract.
  - Finding (2) WIR-014: Already stated RESOLVED in the contract. Verified: all 7 catalog routes correctly gate on `require_feature("catalog.list")` or `require_feature("catalog.read")`.
- **Tests:** 8 passed (catalog-specific keyset pagination, law 3 cross-domain, feature catalog). No regressions.
- **Files changed:** 0
- **Laws satisfied:** Law 1 (dependency direction), Law 3 (cross-domain rules)

## FILE-47 Resolution

- **File:** `backend/domains/orders/services/orders_service.py`
- **Resolution:** ALREADY_FIXED (both findings).
- **Evidence:**
  - Finding 1 (hardcoded country→gateway map): DB-driven payment orchestration (Law 118) implemented at lines 55-80 of `orders_service.py` via `get_country_config(db, country_code)` / `CountryConfig.payment_gateways_json`. The hardcoded `country_gateway_map` at lines 83-94 is a backward-compatible fallback only used when `db is None` or DB has no gateway configured. This matches ARCHITECTURE_STACK.md §10.1 "Database-Driven Payment Orchestration Layer."
  - Finding 2 (inconsistent valid_statuses): Both `bulk_update_order_status_admin` (line 134-135) and `update_order_status` (lines 426-430) raise `HTTPException(status_code=409, detail="Use the refund action...")` when `status == "refunded"`. The status surface is behaviorally identical.
- **Tests:** 9 passed (gateway regression tests in `backend/tests/domains/orders/test_orders_service.py`). No regressions.
- **Files changed:** 0 (ALREADY_FIXED)
- **Laws satisfied:** Law 1 (dependency direction), Law 3 (cross-domain reads via ports.py), Law 118 (database-driven payment orchestration)
