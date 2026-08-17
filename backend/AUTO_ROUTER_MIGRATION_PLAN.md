# ZOZI Auto-Router Migration — Complete Investigation & Plan

**Date:** 2026-08-16
**Scope:** All controllers in `backend/controllers/`
**Goal:** Convert all HTTP controllers to auto-router-compatible shape

---

## Executive Summary

The ZOZI backend has **152 real controller modules** (excluding delegators, router_bridges, and unknown). Of these:

- **152 controllers (100%)** are **ALREADY MIGRATED** — they use `core.route_contract` / `routers.generated.auto_router` decorators, and their generated routers exist in `backend/routers/`.
- **29 controllers (19%)** are **STUB modules** — they contain no route decorators, no HTTP handler functions. They are backward-compatible re-export aliases that simply import from `services/*` and define `__all__`. They are not real HTTP controllers and **cannot be migrated without first being converted into proper controllers**.
- **~50 hand-written routers** still exist in `backend/routers/`. These contain the actual route definitions and business logic for the remaining endpoints. Some share filenames with generated routers and are intentionally preserved.

**UPDATED 2026-08-16:** Actual state differs from initial scan. `controllers/comms/comm_controller.py`, `controllers/hr/lms_controller.py`, and `controllers/identity/iam_controller.py` were migrated after the initial investigation. The real remaining stubs are listed below with their actual router counts.

---

## Section A: Current State Summary

### Total Controller Files
- **334 total `.py` files** in `controllers/` (including subdirectories)
- **152 real decorated controller modules** (excluding `delegators/`, `router_bridges/`, `unknown/`)
- **29 stub modules** (not real controllers)

### Already Migrated Controllers (152)
These controllers use `from core.route_contract import ...` or `from routers.generated.auto_router import ...` decorators and have generated routers in `backend/routers/`.

**Examples:**
- `controllers.admin.admin_catalog_operations_controller` (11 routes)
- `controllers.admin.admin_commerce_configuration_controller` (31 routes)
- `controllers.commerce.reviews_controller` (6 routes)
- `controllers.commerce.wishlist_controller` (4 routes)
- `controllers.comms.comm_controller` (5 routes)
- `controllers.hr.lms_controller` (5 routes)
- `controllers.identity.iam_controller` (6 routes)
- `controllers.core.commission_controller` (16 routes)
- `controllers.core.admin_controller` (124 routes)
- `controllers.core.countries_controller` (67 routes)
- `controllers.public.public_geography_configuration_controller` (69 routes)
- ... and 141 more

**Total decorated functions:** 1,784 (as of 2026-08-16 verify run)

### Stub Modules (29 remaining)
These are NOT real HTTP controllers. They contain:
- Only `from services.* import ...` statements
- `__all__` definitions
- Sometimes `__getattr__` for lazy imports
- NO route decorators
- NO HTTP handler functions

**List (sorted alphabetically):**

| # | Controller | Hand-written Routers | Notes |
|---|-----------|---------------------|-------|
| 1 | `admin.admin_controller` | 40 | Re-export stub, imported by many routers |
| 2 | `admin.admin_dashboard_controller` | 0 | Stub, 0 handlers |
| 3 | `admin.admin_supplier_trading_controller` | 0 | Stub, 0 handlers |
| 4 | `admin.admin_treasury_payments_controller` | 0 | Stub, 0 handlers |
| 5 | `catalog.banner_controller` | 5 | Stub, 0 handlers |
| 6 | `catalog.categories_controller` | 2 | Stub, 0 handlers |
| 7 | `commerce.cart_controller` | 2 | Stub, 0 handlers |
| 8 | `commerce.coupons_controller` | 2 | Partially migrated |
| 9 | `commerce.flash_sale_controller` | 0 | Stub, 0 handlers |
| 10 | `commerce.promotion_controller` | 0 | Stub, 0 handlers |
| 11 | `comms.chatbot_controller` | 1 | Re-export stub, 0 handlers |
| 12 | `finance.commission_controller` | 0 | DEAD STUB — no routers import it |
| 13 | `finance.finance_controller` | 0 | Stub, 0 handlers |
| 14 | `finance.invoice_controller` | 3 | Stub, 0 handlers |
| 15 | `geography.country_communication_controller` | 0 | Stub, 0 handlers |
| 16 | `geography.country_controller` | 13 | Re-export stub, 0 handlers |
| 17 | `hr.employees_controller` | 0 | Stub, 0 handlers |
| 18 | `logistics.logistics_orders_list_controller` | 0 | Stub, 0 handlers |
| 19 | `logistics.logistics_orders_v2_controller` | 0 | Stub, 0 handlers |
| 20 | `orders.disputes_controller` | 0 | Stub, 0 handlers |
| 21 | `orders.logistics_controller` | 3 | Stub, 0 handlers |
| 22 | `orders.logistics_partner_controller` | 4 | Stub, 0 handlers |
| 23 | `orders.returns_controller` | 2 | Stub, 0 handlers |
| 24 | `products.products_controller` | 6 | Stub, 0 handlers |
| 25 | `security.auth_controller` | 57 | Auth utility module, not HTTP controller |
| 26 | `supplier.supplier_analytics_controller` | 0 | Stub, 0 handlers |
| 27 | `supplier.supplier_controller` | 3 | Stub, 0 handlers |
| 28 | `supplier.supplier_document_controller` | 2 | Stub, 0 handlers |
| 29 | `treasury.cash_management_controller` | 0 | Stub, 0 handlers |

**Dead stubs (no routers import them):**
- `finance.commission_controller`
- `commerce.flash_sale_controller`
- `commerce.promotion_controller`
- `finance.finance_controller`
- `geography.country_communication_controller`
- `hr.employees_controller`
- `logistics.logistics_orders_list_controller`
- `logistics.logistics_orders_v2_controller`
- `orders.disputes_controller`
- `supplier.supplier_analytics_controller`
- `treasury.cash_management_controller`

### Hand-Written Routers (294 remaining)
These are the actual route definitions. They import from:
- Services directly (`from services.* import ...`) — 196 imports
- Stub controllers (`from controllers.* import ...`) — 183 imports
- Models directly (`from models.* import ...`) — 65 imports
- DB directly (`from db.* import ...`) — 226 imports

**Top imported stub controllers:**
- `controllers.security.auth_controller` — 56 routers
- `controllers.admin.admin_controller` — 40 routers
- `controllers.catalog.banner_controller` — 13 routers
- `controllers.country_controller` — 13 routers
- `controllers.products.products_controller` — 9 routers
- `controllers.orders.orders_controller` — 9 routers

---

## Section B: Migration Eligibility Analysis

### Eligibility Criteria
A controller is eligible for migration ONLY if ALL of these are true:
1. **Single surface** — all routes share one surface prefix (admin/customer/supplier/logistics/public/system/internal)
2. **Exactly ONE router** — referenced by exactly one hand-written router
3. **No commits in controller** — no `db.commit()` / `session.commit()` / `flush` in controller body
4. **No self-defined router** — no `APIRouter` / `router = APIRouter(...)` in controller
5. **Safe to change signature** — no other module calls functions with positional args

### Analysis of 29 Stub Modules

| # | Controller | Functions | Self-Router | Commits | Has Test | Verdict |
|---|-----------|-----------|-------------|---------|----------|---------|
| 1 | `admin.admin_controller` | 1 (`__getattr__`) | No | No | Yes | **NOT ELIGIBLE** — re-export stub, 0 HTTP handlers, imported by 40 routers |
| 2 | `admin.admin_dashboard_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 3 | `admin.admin_supplier_trading_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 4 | `admin.admin_treasury_payments_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 5 | `catalog.banner_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 6 | `catalog.categories_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 7 | `commerce.cart_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 8 | `commerce.coupons_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 9 | `commerce.flash_sale_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 10 | `commerce.promotion_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 11 | `comms.chatbot_controller` | 1 (`__getattr__`) | No | No | No | **NOT ELIGIBLE** — re-export stub, 0 HTTP handlers |
| 12 | `finance.commission_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 13 | `finance.finance_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 14 | `finance.invoice_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 15 | `geography.country_communication_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 16 | `geography.country_controller` | 1 (`__getattr__`) | No | No | No | **NOT ELIGIBLE** — re-export stub, 0 HTTP handlers |
| 17 | `hr.employees_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 18 | `logistics.logistics_orders_list_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 19 | `logistics.logistics_orders_v2_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 20 | `orders.disputes_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 21 | `orders.logistics_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 22 | `orders.logistics_partner_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 23 | `orders.returns_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 24 | `products.products_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 25 | `security.auth_controller` | 0 | No | No | Yes | **NOT ELIGIBLE** — stub, 0 handlers |
| 26 | `supplier.supplier_analytics_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 27 | `supplier.supplier_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 28 | `supplier.supplier_document_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |
| 29 | `treasury.cash_management_controller` | 0 | No | No | No | **NOT ELIGIBLE** — stub, 0 handlers |

**Summary:** NONE of the 29 non-decorated controllers are eligible for migration. They are all stub/re-export modules with 0 HTTP handler functions.

---

## Section C: What Needs to Be Done

### Reality Check
The 29 non-decorated "controllers" are **not real controllers**. They are module organization artifacts. The actual route logic lives in:
1. The 152 already-decorated controllers (migrated)
2. The ~50 hand-written routers (still need migration)

### The Real Migration Task
To complete the auto-router migration, we need to:

1. **For each hand-written router:**
   - Identify the actual service functions it calls
   - Create a proper controller module with route decorators
   - Move the route logic into the controller
   - Delete the hand-written router
   - Regenerate

2. **OR** — convert the stub controllers into proper controllers by:
   - Adding route decorators
   - Moving the route definitions from the hand-written router into the controller
   - This requires rewriting the stub to be a real controller

### Challenges
- **~50 hand-written routers** remain
- Many routers import directly from services (violating the controllers→services layering)
- Many routers contain inline business logic and `db.commit()` calls
- Some routers are very large (e.g., `admin_logistics_operations.py` is 1794 lines)
- Some routers define WebSocket routes, middleware, or other non-controller logic

---

## Section D: Recommended Migration Strategy

### Phase 1: Low-Hanging Fruit (Already Done ✅)
- 152 controllers already migrated
- These were the controllers that already had route decorators
- Generated routers exist and are working

### Phase 2: Stub Controller Conversion (Remaining Work)
For each of the 29 stub controllers:

**Approach A: Convert stub to controller + migrate router**
1. Read the hand-written router(s) that use this stub
2. Extract the route definitions
3. Add route decorators to the stub controller
4. Move handler logic into the controller (delegating to services)
5. Delete the hand-written router
6. Regenerate

**Approach B: Delete stub + update routers to import from services directly**
1. Delete the stub controller (it's just a re-export)
2. Update all hand-written routers to import from `services/*` directly
3. This doesn't complete the auto-router migration but cleans up dead code

### Recommended Order
Start with the simplest routers first:

**Tier 1 — Simple, single-route routers:**
- `controllers/catalog/banner_controller.py` → migrate `banners.py`, `admin_banners.py`, etc.
- `controllers/catalog/categories_controller.py` → migrate `categories.py`, `admin_categories_routes.py`
- `controllers/comms/comm_controller.py` → migrate `comm.py`
- `controllers/finance/commission_controller.py` → migrate `commission.py`
- `controllers/hr/lms_controller.py` → migrate `lms.py`

**Tier 2 — Medium complexity:**
- `controllers/commerce/cart_controller.py` → migrate `cart.py` (has inline logic)
- `controllers/commerce/coupons_controller.py` → migrate `customer_coupons_create.py`
- `controllers/products/products_controller.py` → migrate `products.py`
- `controllers/orders/returns_controller.py` → migrate `returns.py`
- `controllers/orders/disputes_controller.py` → migrate dispute-related routers

**Tier 3 — Complex, multi-route routers:**
- `controllers/admin/admin_controller.py` → migrate 40+ routers (monolith)
- `controllers/security/auth_controller.py` → migrate 56 routers (auth is complex)
- `controllers/geography/country_controller.py` → migrate 13+ routers
- `controllers/orders/logistics_controller.py` → migrate 9+ routers

---

## Section E: Detailed Todo List

### Investigation Todos
- [x] Read `auto_router.py` to understand requirements
- [x] Read canonical template (`wishlist_controller.py` + generated router)
- [x] List all controllers (334 files, 152 real)
- [x] Categorize controllers (152 decorated, 29 stubs)
- [x] Analyze eligibility of non-decorated controllers
- [x] Map hand-written routers to controllers
- [x] Identify import patterns in hand-written routers
- [x] Document findings

### Migration Todos (In Order)

#### Tier 1: Simple Controllers
1. **`controllers/comms/comm_controller.py`** ✅ ALREADY MIGRATED
   - Generated router: `routers/public_comms_comm.py`

2. **`controllers/hr/lms_controller.py`** ✅ ALREADY MIGRATED
   - Generated router: `routers/public_hr_lms.py`

3. **`controllers/identity/iam_controller.py`** ✅ MIGRATED 2026-08-16
   - Read `routers/iam.py`, `routers/core_iam_routes.py`
   - Added route decorators to `iam_controller.py`
   - Deleted `routers/iam.py`
   - Generated `routers/public_identity_iam.py` (6 routes, 1 skipped due to pre-existing collision with `employees.py`)
   - `routers/core_iam_routes.py` still works

4. **`controllers/catalog/banner_controller.py`**
    - [ ] Read `routers/banners.py`, `routers/admin_banners.py`, `routers/admin_commerce_geography.py`, `routers/admin_logistics_operations.py`, `routers/admin.py`
    - [ ] Add route decorators to `banner_controller.py`
    - [ ] Move handler logic into controller (delegate to services)
    - [ ] Delete hand-written routers
    - [ ] Regenerate and verify

5. **`controllers/finance/commission_controller.py`** (DEAD STUB — no routers import it; real controller is `controllers.core.commission_controller`)
    - [ ] Consider deleting dead stub

#### Tier 2: Medium Complexity
6. **`controllers/commerce/cart_controller.py`**
   - [ ] Read `routers/cart.py`, `routers/store_cart_routes.py`
   - [ ] Add route decorators to `cart_controller.py`
   - [ ] Move handler logic into controller (delegate to `services.commerce.cart_controller_service`)
   - [ ] Delete hand-written routers
   - [ ] Regenerate and verify

7. **`controllers/commerce/coupons_controller.py`**
   - [ ] Read `routers/customer_coupons_create.py`, `routers/customer_coupons_mgmt.py`
   - [ ] Add route decorators to `coupons_controller.py`
   - [ ] Move handler logic into controller
   - [ ] Delete hand-written routers
   - [ ] Regenerate and verify

8. **`controllers/products/products_controller.py`**
   - [ ] Read `routers/products.py`, `routers/admin_products.py`, `routers/admin_products_routes.py`, `routers/store_products_routes.py`, `routers/cart.py`
   - [ ] Add route decorators to `products_controller.py`
   - [ ] Move handler logic into controller
   - [ ] Delete hand-written routers
   - [ ] Regenerate and verify

9. **`controllers/orders/returns_controller.py`**
   - [ ] Read `routers/returns.py`, `routers/store_returns_routes.py`
   - [ ] Add route decorators to `returns_controller.py`
   - [ ] Move handler logic into controller
   - [ ] Delete hand-written routers
   - [ ] Regenerate and verify

10. **`controllers/orders/disputes_controller.py`**
    - [ ] Find and read dispute-related routers
    - [ ] Add route decorators to `disputes_controller.py`
    - [ ] Move handler logic into controller
    - [ ] Delete hand-written routers
    - [ ] Regenerate and verify

#### Tier 3: Complex Controllers
11. **`controllers/admin/admin_controller.py`** (40 routers!)
    - [ ] This is a massive undertaking — consider keeping as-is
    - [ ] Or migrate in sub-modules (create `controllers/admin/operations_controller.py`, etc.)

12. **`controllers/security/auth_controller.py`** (56 routers!)
    - [ ] This is the auth module — extremely critical
    - [ ] Consider keeping hand-written or migrating very carefully

13. **`controllers/geography/country_controller.py`** (13 routers)
    - [ ] Read all country-related routers
    - [ ] Add route decorators to `country_controller.py`
    - [ ] Move handler logic into controller
    - [ ] Delete hand-written routers
    - [ ] Regenerate and verify

14. **`controllers/orders/logistics_controller.py`** (9 routers)
    - [ ] Read logistics-related routers
    - [ ] Add route decorators to `logistics_controller.py`
    - [ ] Move handler logic into controller
    - [ ] Delete hand-written routers
    - [ ] Regenerate and verify

### Housekeeping Todos
- [ ] Delete or archive the analysis scripts (`_analyze_controllers.py`, `_eligibility.py`, `_map.py`, `_map2.py`, `_extract.py`, `_migrate_reviews.py`, `_write_reviews.py`)
- [ ] Run `auto_router.py --verify` to confirm 152 migrated controllers are in sync
- [ ] Run `auto_router.py --validate` to check for forbidden patterns
- [ ] Run tests to confirm no regressions
- [ ] Update `AGENTS.md` with migration status

---

## Section F: Risks and Caveats

### Pre-existing Issues
1. **Duplicate routes:** Both `wishlist` and `reviews` controllers define `GET /api/v1` — this existed before migration
2. **Forbidden patterns in hand-written routers:** Many routers import from `models` and `services` directly, and use `db.commit()` — these violate the architecture but are in hand-written routers, not generated ones
3. **Some controllers are shared across multiple routers** — migrating them could break other routers

### Migration Risks
1. **Breaking changes:** Moving logic from routers to controllers changes the call signature
2. **Service layer gaps:** Some routers call services that don't exist yet or have different signatures
3. **Auth dependency changes:** The auto-router uses different auth dependency injection than hand-written routers
4. **Test coverage:** Many stub controllers have no tests
5. **Large routers:** Some routers are 1000+ lines — migrating them is error-prone

### Recommendations
1. **Start with Tier 1** (simple, single-route controllers) to build confidence
2. **Run `auto_router.py --verify` after each migration** to catch issues early
3. **Keep hand-written routers for complex controllers** (admin_controller, auth_controller) — the risk may not be worth it
4. **Consider deleting stub controllers** that are truly dead code (Approach B above)
5. **Document any signature changes** so frontend and test teams can update

---

## Appendix: Key Files

### Canonical Template (Already Migrated)
- `backend/controllers/commerce/wishlist_controller.py` — 75 lines, 4 routes
- `backend/routers/public_commerce_wishlist.py` — 44 lines, generated

### Another Migrated Example
- `backend/controllers/commerce/reviews_controller.py` — 148 lines, 6 routes
- `backend/routers/public_commerce_reviews.py` — generated

### Newly Migrated (2026-08-16)
- `backend/controllers/identity/iam_controller.py` — 45 lines, 6 routes
- `backend/routers/public_identity_iam.py` — 58 lines, generated
- `backend/routers/iam.py` — DELETED

### Non-Migrated Examples (Stubs)
- `backend/controllers/catalog/banner_controller.py` — 15 lines, 0 routes (5 routers import it)
- `backend/controllers/commerce/coupons_controller.py` — 15 lines, 0 routes (partially migrated)
- `backend/controllers/security/auth_controller.py` — 43 lines, 0 routes (57 routers import it)

### Hand-Written Router Example (Needs Migration)
- `backend/routers/cart.py` — 152 lines, defines routes inline, imports from services directly

### Recently Migrated (2026-08-16)
- `backend/controllers/identity/iam_controller.py` — 45 lines, 6 routes
- `backend/routers/public_identity_iam.py` — 58 lines, generated (1 route skipped due to pre-existing collision with `employees.py`)
- `backend/routers/iam.py` — DELETED

### Generator
- `backend/routers/generated/auto_router.py` — 1050 lines, AST-based router generator
- `backend/core/route_contract.py` — 69 lines, decorator definitions

**2026-08-16 fix:** `--verify` now skips hand-written routers (files without the AUTO-GENERATED marker) so CI no longer reports false drift on intentionally preserved routers like `admin_geography_configuration.py`, `admin_logistics_operations.py`, `admin_orders.py`, `admin_products.py`, `admin_suppliers.py`, and `supplier_orders_verify.py`.

---

*End of Investigation Report*
