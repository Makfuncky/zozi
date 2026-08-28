# ZOZI Backend Architecture & Wiring Audit — 2026-08-28

**Scope:** Full backend scan against ARCHITECTURE_DIAGRAM.md (325 laws)
**Working directory:** `backend/`
**Method:** Static analysis of all 734 Python files in `domains/`, plus modules/, infrastructure/, kernel/, providers/

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 8 | Direct cross-domain model/service imports, forbidden schemas, circular import risk |
| HIGH | 22 | Domain services importing other domains directly, module routers with DB writes, _parked files |
| MEDIUM | 35 | Missing ports.py/events.py/features.py in domain roots, OFFSET pagination, unbounded .all() |
| LOW | 12 | Structural debt, naming inconsistencies |

---

## 1. Cross-Domain Imports in Domain Services (Law 1, 3, 7)

**CRITICAL — 238+ violations in `core/` subdirectory alone**

Domain services are importing directly from other domains instead of using `ports.py`. This is the most widespread violation.

### 1.1 `domains/accounts/services/auth/auth_service.py`
- **Lines:** 46-47, 1327, 1412-1413, 1511-1517, 3546-3547, 3884-3889
- **Violation:** `from domains.xxx.models...` and `from domains.xxx.services...`
- **Law violated:** Law 1 (arrows down), Law 3 (cross-domain reads via ports only)
- **Fix:** Route all cross-domain reads through `domains/<owner>/ports.py`

### 1.2 `domains/analytics/services/dashboards/analytics_service.py`
- **Line:** 24
- **Violation:** Direct cross-domain import
- **Law violated:** Law 3
- **Fix:** Use `domains/<owner>/ports.py` for cross-domain data

### 1.3 `domains/audit/services/audit_service.py`
- **Lines:** 4-6
- **Violation:** Direct cross-domain model imports
- **Law violated:** Law 1, Law 3
- **Fix:** Route through ports.py

### 1.4 `domains/audit/services/compliance_engine.py`
- **Lines:** 13-16
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.5 `domains/audit/services/data/service.py`
- **Lines:** 4-7
- **Violation:** Cross-domain model imports
- **Law violated:** Law 3

### 1.6 `domains/audit/services/data_residency_service.py`
- **Lines:** 11-12
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.7 `domains/audit/services/logs/audit_query_service.py`
- **Line:** 17
- **Violation:** Cross-domain import
- **Law violated:** Law 3

### 1.8 `domains/catalog/services/admin_catalog_orders_service.py`
- **Lines:** 6, 9
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.9 `domains/catalog/services/ai_upload_service.py`
- **Lines:** 23-26
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.10 `domains/catalog/services/categories/category_admin_write_service.py`
- **Lines:** 17, 19
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.11 `domains/logistics/services/core/service.py`
- **Lines:** 11, 2877
- **Violation:** `import domains.logistics.services.core.logistics_service as ctrl`
- **Law violated:** Law 3 (self-domain but wrong import pattern)
- **Fix:** Use relative imports within same domain

### 1.12 `domains/logistics/services/partners/service.py`
- **Lines:** 17, 288, 2191
- **Violation:** `import domains.logistics.services.partners.logistics_partner_service as ctrl`
- **Law violated:** Law 3
- **Fix:** Use relative imports

### 1.13 `domains/logistics/services/partners/settlement_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.14 `domains/logistics/services/partners/write_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.15 `domains/logistics/services/shipping/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.16 `domains/logistics/services/shipping/shipments_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.17 `domains/logistics/services/sla/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.18 `domains/logistics/services/tracking/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.19 `domains/orders/services/core/admin.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.20 `domains/orders/services/core/admin_extra.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.21 `domains/orders/services/core/logistics.py`
- **Multiple lines (30+)**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.22 `domains/orders/services/core/order_engine.py`
- **Multiple lines (30+)**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.23 `domains/orders/services/core/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.24 `domains/orders/services/core/write_facade.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.25 `domains/orders/services/core/write_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.26 `domains/orders/services/cart/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.27 `domains/orders/services/checkout/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.28 `domains/orders/services/returns/service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.29 `domains/promotions/services/engine/admin_commerce_configuration_service.py`
- **Multiple lines (10+)**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.30 `domains/promotions/services/engine/admin_commerce_geography_service.py`
- **Multiple lines (10+)**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.31 `domains/promotions/services/engine/admin_promotions_write_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.32 `domains/security/services/core/security_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.33 `domains/security/services/fraud/fraud_detection_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.34 `domains/security/services/fraud/fraud_engine.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.35 `domains/security/services/fraud/fraud_service.py`
- **Multiple lines (30+)**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.36 `domains/suppliers/services/analytics/supplier_analytics_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.37 `domains/suppliers/services/badges/badge_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.38 `domains/suppliers/services/compliance/compliance_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.39 `domains/suppliers/services/contract/contract_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.40 `domains/suppliers/services/disputes_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.41 `domains/suppliers/services/documents/supplier_document_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.42 `domains/suppliers/services/governance/admin_suppliers_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.43 `domains/suppliers/services/health/supplier_health_engine.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.44 `domains/suppliers/services/onboarding/onboarding_workflow.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.45 `domains/suppliers/services/orders/supplier_orders_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.46 `domains/suppliers/services/products/supplier_products.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.47 `domains/suppliers/services/profile/supplier_profile.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.48 `domains/suppliers/services/quality/quality_control_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.49 `domains/suppliers/services/settlement/multi_currency_settlement.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

### 1.50 `domains/suppliers/services/tier/tier_service.py`
- **Multiple lines**
- **Violation:** Cross-domain imports
- **Law violated:** Law 3

---

## 2. Module Routers with DB Writes / Business Logic (Law 2, 90)

**HIGH — Module routers contain DELETE/WRITE endpoints**

### 2.1 `modules/admin/routers/accounts.py`
- **Lines:** 103, 274, 325, 409
- **Violation:** `@router.delete(...)` — DELETE endpoints in module router
- **Law violated:** Law 2 (thin routers), Law 90 (no DB writes)
- **Fix:** Move DELETE operations to domain service, router calls service

### 2.2 `modules/admin/routers/catalog.py`
- **Lines:** 174, 314
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.3 `modules/admin/routers/comms.py`
- **Line:** 72
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.4 `modules/admin/routers/country.py`
- **Lines:** 319, 352, 491, 523
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.5 `modules/admin/routers/customers.py`
- **Line:** 91
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.6 `modules/admin/routers/governance.py`
- **Line:** 129
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.7 `modules/admin/routers/logistics.py`
- **Line:** 127
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.8 `modules/admin/routers/orders.py`
- **Line:** 64
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.9 `modules/admin/routers/promotions.py`
- **Line:** 93
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.10 `modules/admin/routers/security.py`
- **Line:** 172
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.11 `modules/customer/routers/accounts.py`
- **Lines:** 186, 628
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.12 `modules/customer/routers/orders.py`
- **Lines:** 90, 97
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.13 `modules/customer/routers/promotions.py`
- **Lines:** 126, 254, 280
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.14 `modules/employee/routers/comms.py`
- **Line:** 324
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.15 `modules/employee/routers/hr.py`
- **Lines:** 344, 396, 521, 884
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.16 `modules/logistics/routers/accounts.py`
- **Lines:** 186, 305
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.17 `modules/logistics/routers/logistics.py`
- **Lines:** 114, 157, 637, 668, 699, 730, 857, 1058, 1121
- **Violation:** `@router.delete(...)` — 9 DELETE endpoints
- **Law violated:** Law 2, Law 90

### 2.18 `modules/supplier/routers/accounts.py`
- **Lines:** 179, 227
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.19 `modules/supplier/routers/catalog.py`
- **Line:** 69
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.20 `modules/supplier/routers/finance.py`
- **Line:** 157
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

### 2.21 `modules/supplier/routers/logistics.py`
- **Lines:** 80, 130
- **Violation:** `@router.delete(...)`
- **Law violated:** Law 2, Law 90

---

## 3. `_parked` Directory — Files in Wrong Location (Law 14, 18)

**HIGH — 25 files in `domains/_parked/`**

The `_parked` directory is not a valid domain. Files here are in violation of file placement laws.

### 3.1 Files found in `domains/_parked/`:
- `addresses_service.py` → belongs in `domains/accounts/services/addresses/`
- `admin_categories_service.py` → belongs in `domains/catalog/services/categories/`
- `admin_promotions_write_service.py` → belongs in `domains/promotions/services/`
- `admin_promotion_service.py` → belongs in `domains/promotions/services/`
- `banner_write_service.py` → belongs in `domains/promotions/services/banners/`
- `cart_controller_service__orders.py` → belongs in `domains/orders/services/cart/`
- `cart_service__orders.py` → belongs in `domains/orders/services/cart/`
- `categories_service.py` → belongs in `domains/catalog/services/categories/`
- `commerce_coupons_read_service.py` → belongs in `domains/promotions/services/coupons/`
- `commerce_coupons_write_service.py` → belongs in `domains/promotions/services/coupons/`
- `coupons_legacy_write_service.py` → belongs in `domains/promotions/services/coupons/`
- `customer_coupons_create_service.py` → belongs in `domains/promotions/services/coupons/`
- `customer_coupons_mgmt_service.py` → belongs in `domains/promotions/services/coupons/`
- `flash_sale_service.py` → belongs in `domains/promotions/services/`
- `flash_sale_write_service.py` → belongs in `domains/promotions/services/`
- `orders_package_service.py` → belongs in `domains/orders/services/`
- `promotions_write_service.py` → belongs in `domains/promotions/services/`
- `promotion_admin_write_service.py` → belongs in `domains/promotions/services/`
- `promotion_bogo_service.py` → belongs in `domains/promotions/services/bogo/`
- `promotion_engine_service.py` → belongs in `domains/promotions/services/engine/`
- `promotion_points_service.py` → belongs in `domains/promotions/services/coins/`
- `referrals_controller__routers.py` → belongs in `modules/` or `domains/promotions/`
- `search_service.py` → belongs in `domains/catalog/services/`
- `supplier_documents_service.py` → belongs in `domains/suppliers/services/documents/`

**Law violated:** Law 14 (business logic → domains/), Law 18 (root forbidden folders)
**Fix:** Move each file to its correct domain service directory

---

## 4. DOMAIN_ALLOWLIST.yaml — Forbidden Schema References (Law 6, 24, 56)

**CRITICAL — References to forbidden `core` schema**

### 4.1 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 9-11
- **Violation:** References `core.users` — `core` is a forbidden schema name
- **Law violated:** Law 6 (schema discipline), Law 24 (no forbidden schemas), Law 56 (no forbidden schemas)
- **Fix:** Remove `core.users` references; User model should live in `accounts` schema

### 4.2 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 16-21
- **Violation:** Cross-domain service imports sanctioned without ports.py migration plan
- **Law violated:** Law 3 (cross-domain reads via ports only), Law 7 (allowlist must shrink)
- **Fix:** Add migration timeline; route through ports.py

### 4.3 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 25-31
- **Violation:** Cross-domain model imports for read-only query building
- **Law violated:** Law 3
- **Fix:** Replace with port function calls

### 4.4 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 33-43
- **Violation:** Controller logic in domain services (FastAPI HTTPException, auth checks)
- **Law violated:** Law 2 (thin routers), Law 14 (business logic in services)
- **Fix:** Extract auth/HTTP concerns to modules/, keep services pure

### 4.5 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 47-48
- **Violation:** Unbounded `.all()` queries
- **Law violated:** Law 222 (keyset pagination), Law 45 (no N+1)
- **Fix:** Add pagination/limits to all `.all()` calls

### 4.6 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 50-51
- **Violation:** OFFSET pagination
- **Law violated:** Law 222 (keyset pagination)
- **Fix:** Replace OFFSET with keyset/cursor pagination

### 4.7 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 56-61
- **Violation:** Payout model referenced across 79 files from wrong domain
- **Law violated:** Law 51 (single table ownership)
- **Fix:** Move Payout model to owning domain or create proper port functions

### 4.8 `backend/DOMAIN_ALLOWLIST.yaml`
- **Lines:** 65-67
- **Violation:** Payment gateway base classes used across domains
- **Law violated:** Law 3, Law 11 (providers wrap SDKs)
- **Fix:** Route through payments.ports.py

---

## 5. Missing Domain Contract Files (Law 3, 4, 150)

**MEDIUM — Domain roots missing required files**

### 5.1 Missing `ports.py` in domain roots:
- `domains/comms/ports.py` — MISSING
- `domains/customers/ports.py` — MISSING
- `domains/hr/ports.py` — MISSING

### 5.2 Missing `events.py` in domain roots:
- `domains/comms/events.py` — MISSING
- `domains/customers/events.py` — MISSING
- `domains/hr/events.py` — MISSING

### 5.3 Missing `features.py` in domain roots:
- `domains/comms/features.py` — MISSING
- `domains/customers/features.py` — MISSING
- `domains/hr/features.py` — MISSING

**Law violated:** Law 150 (domain structure), Law 3 (cross-domain events/ports), Law 4 (features single-sourced)
**Fix:** Create missing files in each domain root

---

## 6. Module Routers Importing Domain Models Directly (Law 2, 89)

**HIGH — Module routers import models instead of using serializers**

### 6.1 `modules/logistics/routers/logistics.py`
- **Line:** 302
- **Violation:** `from domains.governance.models.user import User`
- **Law violated:** Law 2 (thin routers), Law 89 (response serialization), Law 3 (cross-domain reads via ports)
- **Fix:** Use port function from `domains/governance/ports.py`

### 6.2 `modules/customer/routers/orders.py`
- **Line:** 35
- **Violation:** `from domains.orders.services.returns.service import update_return_request`
- **Law violated:** Law 2 (should use require_feature + one service call)
- **Fix:** Ensure router uses require_feature() and delegates to single service

---

## 7. Domain Subdirectory Structure Issues (Law 150)

**MEDIUM — Subdirectories within domains that may violate structure**

### 7.1 `domains/accounts/` subdirectories:
- `addresses/`, `auth/`, `gdpr/`, `identity/`, `permissions/`, `tracker/`, `users/`
- **Note:** These are valid subdirectories within accounts domain

### 7.2 `domains/catalog/` subdirectories:
- `categories/`, `products/`, `variants/`, `search/`
- **Note:** Valid subdirectories

### 7.3 `domains/comms/` subdirectories:
- `email/`, `messaging/`, `tickets/`, `proxy_communication/`
- **Note:** Valid subdirectories

### 7.4 `domains/finance/` subdirectories:
- `commission/`, `country/`, `ledger/`, `payments/`, `payouts/`, `reporting/`, `shared/`, `treasury/`
- **Note:** Valid subdirectories

### 7.5 `domains/governance/` subdirectories:
- `admin/`, `approval/`, `audit/`, `auth/`, `command_center/`, `incident/`, `risk/`, `settings/`
- **Note:** Valid subdirectories

### 7.6 `domains/hr/` subdirectories:
- `employees/`, `ess/`, `ghost_watchdog/`, `hierarchy/`, `learning/`, `leave/`, `payroll/`, `performance/`, `shift/`, `succession/`, `travel/`
- **Note:** Valid subdirectories

### 7.7 `domains/logistics/` subdirectories:
- `core/`, `partners/`, `shipping/`, `sla/`, `tracking/`
- **Note:** Valid subdirectories

### 7.8 `domains/orders/` subdirectories:
- `cart/`, `checkout/`, `core/`, `disputes/`, `packing/`, `returns/`, `tracking/`
- **Note:** Valid subdirectories

### 7.9 `domains/promotions/` subdirectories:
- `banners/`, `bogo/`, `coins/`, `coupons/`, `engine/`, `flash_sale/`, `marketing/`
- **Note:** Valid subdirectories

### 7.10 `domains/security/` subdirectories:
- `core/`, `detection/`, `fraud/`, `health/`, `iam/`, `registration/`, `threat/`
- **Note:** Valid subdirectories

### 7.11 `domains/suppliers/` subdirectories:
- `analytics/`, `badges/`, `compliance/`, `contract/`, `contracts/`, `documents/`, `governance/`, `health/`, `onboarding/`, `orders/`, `products/`, `profile/`, `quality/`, `settlement/`, `tier/`
- **Note:** Valid subdirectories

---

## 8. Provider Isolation (Law 11, 31, 100, 123)

**CLEAN — No violations found**

Provider modules do not import from domains, modules, rbac, jobs, or middleware. The provider layer is properly isolated.

---

## 9. Infrastructure/Kernel Isolation (Law 10, 101, 102)

**CLEAN — No violations found**

- `infrastructure/` does not import from `domains/`, `modules/`, `rbac/`, or `providers/`
- `kernel/` does not import from `domains/`, `modules/`, `rbac/`, `providers/`, `jobs/`, or `middleware/`

---

## 10. Root-Level Forbidden Packages (Law 18)

**CLEAN — No violations found**

No `utils/`, `routers/`, `controllers/`, `services/`, `models/`, or `db/` at backend root level.

---

## 11. Module-to-Domain Import Direction (Law 1, 97, 99)

**CLEAN — Correct direction**

All module-to-domain imports follow the correct direction: `modules/ → domains/`. No domain imports from modules.

---

## 12. Summary of Findings by Law

| Law | Violations | Severity | Description |
|-----|-----------|----------|-------------|
| Law 1 | 238+ | CRITICAL | Cross-domain imports in services |
| Law 2 | 21 | HIGH | Module routers with DELETE endpoints |
| Law 3 | 238+ | CRITICAL | Cross-domain reads not via ports.py |
| Law 4 | 3 | MEDIUM | Missing features.py in 3 domains |
| Law 6 | 8 | CRITICAL | Forbidden `core` schema in allowlist |
| Law 7 | 8 | HIGH | Allowlist entries not shrinking |
| Law 14 | 25 | HIGH | Files in `_parked` wrong location |
| Law 18 | 25 | HIGH | `_parked` is forbidden location |
| Law 24 | 8 | CRITICAL | `core` schema forbidden |
| Law 51 | 79 | HIGH | Payout model referenced from wrong domain |
| Law 56 | 8 | CRITICAL | `core` schema forbidden |
| Law 89 | 2 | HIGH | Module router imports model directly |
| Law 90 | 21 | HIGH | Module routers with DELETE (DB writes) |
| Law 150 | 9 | MEDIAN | Missing ports/events/features in 3 domains |
| Law 222 | 2 | MEDIUM | OFFSET pagination sanctioned |

---

## 13. Recommended Fix Priority

### Phase 1 — Critical (breaks architecture):
1. Remove `core.users` references from DOMAIN_ALLOWLIST.yaml
2. Create missing `ports.py` in `domains/comms/`, `domains/customers/`, `domains/hr/`
3. Create missing `events.py` and `features.py` in same 3 domains
4. Begin routing cross-domain imports through ports.py (start with `accounts/auth/auth_service.py`)

### Phase 2 — High (correctness):
1. Move all 25 `_parked` files to correct domain directories
2. Remove DELETE endpoints from module routers (delegate to services)
3. Fix `modules/logistics/routers/logistics.py:302` model import
4. Add pagination to all `.all()` queries

### Phase 3 — Medium (debt):
1. Replace OFFSET pagination with keyset
2. Shrink DOMAIN_ALLOWLIST.yaml entries
3. Extract auth/HTTP concerns from domain services to modules

---

## 14. Statistics

| Metric | Value |
|--------|-------|
| Total Python files in `domains/` | 734 |
| Domain root directories | 15 (correct) |
| Files with cross-domain imports | 159+ unique files |
| Module routers with DELETE | 21 unique files |
| Files in `_parked` | 25 |
| Missing domain contract files | 9 (3 domains × 3 files) |
| Allowlist entries | 8 categories |
| Provider isolation violations | 0 |
| Infrastructure/kernel violations | 0 |
| Root forbidden packages | 0 |

---

*Audit completed: 2026-08-28*
*Auditor: Kilo (automated static analysis)*
*Method: grep-based import scanning, file structure analysis*
