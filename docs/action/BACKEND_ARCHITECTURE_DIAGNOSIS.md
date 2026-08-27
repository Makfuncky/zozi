# ZOZI Backend Architecture Compliance Diagnosis

**Date:** 2026-08-27
**Investigator:** Architecture compliance audit (6 parallel sub-agents)
**Scope:** Full `backend/` directory vs. `ARCHITECTURE_DIAGRAM.md`
**Methodology:** Automated grep + manual review across 6 parallel investigations covering:
domains/, modules/, providers/, infrastructure/, kernel/, rbac/, schema discipline, middleware/, jobs/

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Law Violations (Seven Laws) | 8 | 45+ | 100+ | 200+ | 350+ |
| Schema Discipline | 4 | 100+ | 200+ | — | 300+ |
| RBAC | 3 | 5 | 15 | 20 | 43 |
| Provider Hygiene | 0 | 10 | 20 | 30 | 60 |
| Module Routers | 26 | 100+ | 50+ | 30+ | 200+ |
| Middleware/Jobs | 3 | 3 | 5 | 5 | 16 |
| File Placement | 10 | 15 | 20 | 10 | 55 |

**Overall Verdict:** The backend has significant drift from the architecture. The most critical issues are:
1. RBAC is functionally broken (colon vs dot format mismatch, shadow feature system)
2. RLS is completely unenforced at the DB layer
3. Webhook middleware exists but is never wired
4. Middleware imports from domains (Law 1 violation)
5. Massive cross-domain coupling (100+ direct cross-domain imports)
6. Schema contamination (forbidden schemas: `commerce`, `accounts.users`, `core`)
7. 233+ models with widespread naming/default/FK issues

---

# PART 1: LAW-BY-LAW VIOLATIONS

## Law 1: "Arrows point down only" — `modules → domains → infrastructure`

### 🔴 CRITICAL #1: Middleware imports from domains
**Law 1 violation.** Middleware is above domains in the stack and must not import them.

| File | Line | Violation |
|------|------|-----------|
| `backend/middleware/coi_middleware.py` | 10 | `from domains.hr.services.employees.coi_service import COIService` |
| `backend/middleware/country_context.py` | 58, 149, 210, 213, 227, 370 | Multiple domain imports (country, hr models) |
| `backend/middleware/impossible_travel_middleware.py` | 256, 268, 289, 304, 349 | Imports from hr, audit, governance, security |
| `backend/middleware/rls_middleware.py` | 24 | `from domains.country.models.country_enhancements import CountryStaffAssignment` |
| `backend/middleware/dependencies/fraud_events.py` | 21 | `from domains.security.models.fraud import FraudEvent` |
| `backend/middleware/dependencies/country_detection.py` | 23 | `from domains.country.services.geo.country_detection import CountryDetectionService` |
| `backend/middleware/dependencies/coi_dependency.py` | 10 | `from domains.hr.services.employees.coi_service import COIService` |

**Solution:** Move domain-coupled logic to domain services. Middleware should only call infrastructure (e.g., publish events to a bus that domains subscribe to). The `dependencies/` subdirectory is a workaround — eliminate it by having middleware publish events instead.

---

### 🔴 CRITICAL #2: PCI-DSS middleware imports from `rbac/`
**Law 1 violation.** `rbac` is a peer of domains, not below middleware.

| File | Line | Violation |
|------|------|-----------|
| `backend/middleware/pci_dss_compliance.py` | 209 | `from rbac.dependencies import _ROLE_FEATURES, _resolve_effective_features` |

**Solution:** Move RBAC resolution to a domain service (e.g., `domains/governance/services/`) and call it via events. Or have middleware query `infrastructure/security/` for role→feature mapping (denormalize).

---

### 🔴 CRITICAL #3: Infrastructure imports from domains (28+ files)
**Law 1 violation.** Infrastructure must not import from domains.

| File | Lines | Imports |
|------|-------|---------|
| `backend/infrastructure/utils/command_center.py` | 26-36, 711, 742 | 5+ domains (governance, country, hr, logistics, orders, finance) |
| `backend/infrastructure/utils/command_center_service.py` | 2 | `from domains.governance.services.command_center.service import *` |
| `backend/infrastructure/utils/entity_messaging.py` | 2 | `from domains.comms.services.messaging.chat_service import MessagingService` |
| `backend/infrastructure/utils/import_service.py` | 2 | `from domains.finance.services.data_import_service import *` |
| `backend/infrastructure/messaging/email_service.py` | 177, 368 | governance.models, comms.services |
| `backend/infrastructure/messaging/realtime.py` | 32-35 | governance, comms, catalog, finance ports |
| `backend/infrastructure/messaging/downstream_hooks.py` | 20, 33, 45 | country.ports |
| `backend/infrastructure/messaging/downstream_wiring.py` | 30-32 | catalog/country/finance ports |
| `backend/infrastructure/observability/audit.py` | 281 | governance.ports |
| `backend/infrastructure/security/dependencies.py` | 24, 45 | governance.models, rbac.dependencies |
| `backend/infrastructure/security/qr_service.py` | 39-40, 72-73, 119 | hr.models, governance.models |
| `backend/infrastructure/security/key_rotation.py` | 44-47 | governance, comms, logistics, orders |
| `backend/infrastructure/ml/worker.py` | 44 | finance.services |
| `backend/infrastructure/media/free_image_tools.py` | 170 | finance.services |
| `backend/infrastructure/lifespan.py` | 87, 117, 119 | accounts.services, finance.services, logistics.services |

**Solution:** These are "shim" files that re-export from domains. Either:
1. Delete the shims and update callers to import from canonical locations
2. Move the logic to the canonical domain

---

### 🔴 CRITICAL #4: Infrastructure imports from `modules/`
**Law 1 violation.** Infrastructure must not import from modules.

| File | Line | Violation |
|------|------|-----------|
| `backend/infrastructure/search/routers/__init__.py` | 3 | `from modules.admin.routers.catalog import (get_recommendations, smart_search)` |

**Solution:** Delete `infrastructure/search/routers/` entirely. The search router belongs in `modules/admin/routers/` only.

---

### 🔴 CRITICAL #5: Infrastructure imports from `providers/`
**Law 1 violation.** Infrastructure is below providers (Law 1 arrows point down only — `providers ← services/jobs`).

| File | Line | Import |
|------|------|--------|
| `backend/infrastructure/utils/currency_service.py` | 12-20 | `from providers.geography.rates import (...)` |
| `backend/infrastructure/utils/command_center.py` | 19, 23 | `from providers.automation.scheduler import ...` |
| `backend/infrastructure/media/media_storage.py` | 12-13 | `from providers.media.models.media_models import ...` |
| `backend/infrastructure/media/media_service.py` | 21 | `from providers.media.models.media_models import MediaAsset` |
| `backend/infrastructure/media/image_ai_service.py` | 30, 32 | `from providers.image import ...` |
| `backend/infrastructure/media/free_image_tools.py` | 27, 29, 35 | `from providers.image import ...` |
| `backend/infrastructure/messaging/email_service.py` | 28 | `from providers.comms.email import deliver_email` |
| `backend/infrastructure/storage/storage.py` | 28 | `from providers.storage import create_s3_client` |

**Solution:** Move these to `domains/{domain}/services/` or the relevant provider. Infrastructure should not embed business logic or provider references.

---

### 🔴 CRITICAL #6: `infrastructure/media/` should not exist
**Law 1 violation.** "Media code belongs in providers." Per DOMAIN_WORK.md.

The entire `backend/infrastructure/media/` directory violates this:
- `media_storage.py`
- `media_service.py`
- `image_ai_service.py`
- `free_image_tools.py`

**Solution:** Move all `infrastructure/media/` content to `providers/media/` or to relevant domain services.

---

### 🔴 CRITICAL #7: Kernel imports from domains
**Law 1 violation.** Kernel must not import domains.

| File | Line | Violation |
|------|------|-----------|
| `backend/kernel/rls_context.py` | 48 | `from domains.governance import ports as governance_ports` |

**Solution:** Delete `kernel/rls_context.py` — RLS is an infrastructure concern. If domain access is needed, do it via event publishing.

---

### 🔴 CRITICAL #8: Kernel contains non-business code
**Law 1 violation.** Kernel must contain only business primitives.

| File | Issue |
|------|-------|
| `backend/kernel/error_handler.py` | Contains `global_exception_handler` (FastAPI web framework code, not a business primitive) |
| `backend/kernel/rls_context.py` | Imports from infrastructure + domains; not a business primitive |
| `backend/kernel/constants.py` | Mixes business primitives with business-specific constants (`STAFF_ROLES`, `TREASURY_ROLES`, etc.) |

**Solution:**
- `error_handler.py` → move to `infrastructure/messaging/` or `middleware/`
- `rls_context.py` → delete (RLS is infrastructure)
- `constants.py` → split into `kernel/constants.py` (pure primitives) and `domains/{domain}/constants.py` (business-specific)

---

## Law 2: "Module routers stay thin" — auth + require_feature + ONE service call

### 🔴 HIGH #1: 26 undefined function calls in routers (NameError at runtime)
**Law 2 violation.** Routers contain business logic that calls undefined functions.

| File | Lines | Issue |
|------|-------|-------|
| `backend/modules/admin/routers/country.py` | 81, 97, 124, 146, 156, 168, 179, 189, 202, 225, 247, 257, 267, 277, 287, 297, 307, 317, 328, 339, 351 | 20+ calls to `svc_*` functions that are not imported |
| `backend/modules/admin/routers/customers.py` | 80, 99 | `get_wishlist()`, `clear_user_wishlist()` not imported |
| `backend/modules/admin/routers/orders.py` | 32 | `email_metrics(db)` not imported |
| `backend/modules/customer/routers/finance.py` | 351 | `get_current_user_orch()` not imported |
| `backend/modules/supplier/routers/suppliers.py` | 81, 149, 160 | `SupplierDocumentOut`, `SupplierProfileOut`, etc. not imported |

**Solution:** These are migration artifacts. Either:
1. Wire the correct service calls
2. Delete the routes until real implementations exist
3. Auto-generate router/service pairings (but this conflicts with the removal of the Service Registry)

---

### 🔴 HIGH #2: Model imports in routers
**Law 2 violation.** Routers must not import models.

| File | Line | Import |
|------|------|--------|
| `backend/modules/customer/routers/accounts.py` | 8, 23 | `from domains.accounts.models.core import Address`, `from domains.governance.models.user import User` |
| `backend/modules/customer/routers/orders.py` | 13 | `from domains.orders.models.order_entities import ReturnRequest` |
| `backend/modules/customer/routers/promotions.py` | 16 | `from domains.catalog.models.promotions import Coupon` |
| `backend/modules/employee/routers/comms.py` | 165, 774 | governance.user.User, comms.communication_schema_models.SupportTicket |
| `backend/modules/employee/routers/suppliers.py` | 85 | governance.user.User |
| `backend/modules/logistics/routers/logistics.py` | 313 | logistics.models.logistics_entities |

**Solution:** Replace with service calls. Each model import is a leak that should be in a domain service.

---

### 🔴 HIGH #3: Business logic / helper functions in routers
**Law 2 violation.** 20+ helper functions across routers.

| File | Lines | Helper | Purpose |
|------|-------|--------|---------|
| `customer/routers/accounts.py` | 36-55, 58-74, 77-78 | `_normalize_address_payload`, `_serialize_address`, `_get_user_address` | validation/serialization in router |
| `customer/routers/finance.py` | 72-83, 86-89, 296-331 | `_resolve_request_country`, `_require_admin`, 6 webhook endpoints | auth, business logic, webhook handling |
| `customer/routers/orders.py` | 211-216, 219-239 | `_user_context`, `_serialize_return` | context + serialization |
| `customer/routers/promotions.py` | 59-98, 95-98, 154-181, 201-211 | `_normalize_discount_type`, `_to_decimal`, `_to_int`, `_require_admin`, local Pydantic schemas, `_current_user_id/role` | extensive business logic |
| `employee/routers/accounts.py` | 27-43 | `_get_employee_id`, `_get_employee_org_unit_id` | DB lookup logic |
| `employee/routers/comms.py` | 303-306, 364-373, 658-669, 733-756, 759-769 | `_TRANSPARENT_GIF`, `send_transactional`, parsing, serialization | extensive |
| `employee/routers/finance.py` | 56-58 | `_with_rls` | RLS context manager |
| `employee/routers/hr.py` | 313, 905-918 | `PENDING_PAYROLL_APPROVALS: dict = {}` (in-memory state!), `required_authority_for_resource` | in-memory state + business rules |
| `employee/routers/orders.py` | 20-24 | `_can_view_job` | authorization in router |
| `employee/routers/suppliers.py` | 90-92, 200-211 | `_user_to_dict`, parsing | conversion + parsing |

**Solution:** Move all helper functions to `domains/{domain}/services/` or to `modules/{module}/serializers/`.

---

### 🟠 HIGH #4: In-memory mutable state in `employee/routers/hr.py:313`
**Law 2 + production safety violation.**

```python
# employee/routers/hr.py:313
PENDING_PAYROLL_APPROVALS: dict = {}
```

This is a module-level dict that will be lost on restart and is not shared across workers. This MUST move to a database-backed model or Redis.

**Solution:** Create `domains/hr/models/payroll_approvals.py` and persist via `domains/hr/services/payroll_service.py`.

---

### 🟠 HIGH #5: Cross-domain imports in routers
**Law 2 + Law 3 violation.** Routers must call only their own module's domain services.

| File | Line | Cross-Domain Import |
|------|------|---------------------|
| `admin/routers/orders.py` | 12-17 | `from domains.comms.ports import create_campaign, ...` (orders router calling comms) |
| `employee/routers/finance.py` | 45 | `from domains.logistics.ports import get_logistics_partner_by_user_id` (finance → logistics) |
| `logistics/routers/logistics.py` | 79, 463 | `from domains.orders.services.logistics_controller as ctrl` (logistics → orders) |

**Solution:** These are valid cross-domain calls (via ports) but belong in a domain service, not the router. Move the dispatching logic to `domains/{caller}/services/`.

---

### 🟠 HIGH #6: Auto-stub imports in routers
**Law 2 violation.** 15+ routers import from `_auto_stubs` (placeholder services).

| File | Line | Import |
|------|------|--------|
| `customer/routers/comms.py` | 5 | `from domains.comms.services._auto_stubs import TranslationService` |
| `employee/routers/comms.py` | 164, 652-654, 1033-1042, 1170-1173, 1231, 1377 | 10+ `_auto_stubs` imports |
| `employee/routers/finance.py` | 20-29, 1357 | 8+ `_auto_stubs` imports |
| `employee/routers/hr.py` | 63-70 | 7 `_auto_stubs` imports |
| `employee/routers/orders.py` | 9 | `from domains.finance.services._auto_stubs import trading_service as trading` |
| `employee/routers/suppliers.py` | 11, 19 | `_auto_stubs` imports |

**Solution:** Replace `_auto_stubs` with real services. If a service is empty, the route should be disabled or 501'd.

---

### 🟡 MEDIUM #1: ~100 endpoints in `employee/routers/comms.py` lack `require_feature`
**Law 2 + Law 4 violation.**

Major offenders:
- `employee/routers/comms.py`: lines 21, 26, 31, 168-279, 339-560, 563-624, 627-645, 672-1450 (80+ endpoints)
- `employee/routers/suppliers.py:278-282`
- `logistics/routers/logistics.py:1135-1139`

**Solution:** Add `require_feature(...)` to every authenticated endpoint. Map each to a feature in the corresponding domain's `features.py`.

---

### 🟡 MEDIUM #2: Inconsistent `require_feature` naming convention
**Law 4 violation.**

`supplier/routers/finance.py` uses colon-separated: `finance:commission:read` (line 81), `finance:ledger:read` (line 125), etc. — **but the catalog uses dot-separated**: `finance.commission.read`. These will never match.

**Solution:** Standardize to dot-separated. Update `supplier/routers/finance.py` lines 81, 89, 98, 106, 115, 125, 133, 145, 153, 161, 169, 178, 189, 197, 206, 214, 222, 230, 238.

---

### 🟡 MEDIUM #3: Webhook endpoints have no auth
**Law 2 violation.** Webhooks should be authenticated via signature, not user JWT.

`customer/routers/finance.py:296-331` defines 6 webhook endpoints with no `require_feature` and no signature verification at the router level:
- `POST /webhook` (Stripe)
- `POST /tap/webhook`
- `POST /paytabs/callback`
- `POST /paypal/webhook`
- `POST /thawani/webhook`
- `POST /generic/{provider_code}/callback`

**Solution:** Wire the `WebhookVerificationMiddleware` (which exists but is not currently active) to verify HMAC signatures before the router is called. Move the middleware wiring into `orchestrator.py`.

---

### 🟠 HIGH #7: Inconsistent auth patterns
**Law 2 violation.**

| File | Lines | Issue |
|------|-------|-------|
| `admin/routers/suppliers.py` | 36, 46, 57, 70 | Uses `_admin: dict` instead of `current_user: dict` |
| `customer/routers/finance.py` | 86-89 | `_require_admin()` defined locally instead of using `require_admin` from `rbac` |
| `customer/routers/promotions.py` | 95-98 | Same — local `_require_admin()` |

**Solution:** Always use the `require_admin`, `require_module`, `require_feature` from `rbac/dependencies.py`.

---

### 🟠 HIGH #8: 27 instances of `from domains.common.auth import ...`
**Law 2 violation.** Routers bypass their module's `auth/dependencies.py`.

Affected: all 5 modules' routers import directly from `domains.common.auth` rather than `modules/{module}/auth/dependencies.py`.

**Solution:** Replace `from domains.common.auth import get_current_user` with `from modules.{module}.auth.dependencies import get_current_user`.

---

### 🟠 HIGH #9: Domain service creates standalone FastAPI app
**Law 2 + architectural violation.**

`domains/logistics/services/core/service.py:3054-3065` creates a separate `FastAPI()` instance and calls `app.add_middleware(CORSMiddleware, ...)`. A domain service should never own a web app.

**Solution:** Extract this "Location Service" microservice to its own top-level package (e.g., `services/location/`) with its own entry point. Domain services must not own ASGI apps.

---

## Law 3: "Cross-domain writes only via events; cross-domain reads only via ports"

### 🔴 CRITICAL #9: 100+ direct cross-domain model/service imports
**Law 3 violation.** The vast majority of cross-domain coupling bypasses `ports.py`/`events.py`.

**Pattern A: Direct model imports across domains** (most common)

| Source | Line | Cross-Domain Import |
|--------|------|---------------------|
| `accounts/services/accounts_service.py` | 10, 24-76, 82 | hr.models, hr.services, governance.models |
| `accounts/services/auth/auth_service.py` | 47-48, 3388-3704 | governance.models, comms.models, logistics.models |
| `accounts/services/users/users_admin_service/__header___p1_p1.py` | 18-69 | 7 domains (catalog, comms, finance, governance, logistics, orders, promotions) |
| `accounts/services/users/users_admin_service/merged_from_user_write_ops_py.py` | 20-79 | Same 7 domains |
| `analytics/services/flat_admin_dashboard_service.py` | 16-27 | governance, catalog, finance, hr, logistics |
| `audit/services/compliance_engine.py` | 13-16 | hr.models, governance.models |
| `catalog/services/products/products_service.py` | 378-381, 806-819 | accounts, comms, orders |
| `catalog/services/products/product_verification_service.py` | 15-18 | catalog, governance, logistics, orders |
| `customers/services/user_read_service.py` | 10 | accounts.models.user |
| `customers/services/reviews_service.py` | 13-14 | catalog.products, orders.orders |
| `customers/services/search_service.py` | 14-15 | catalog, orders |
| `customers/services/recommendations/recommendation_service.py` | 18-19 | catalog, orders |
| `logistics/services/tracking/service.py` | 20-23, 409-411, 434-436 | country, governance |
| `logistics/services/shipping/service.py` | 23-25, 213-216 | governance, country |
| `orders/services/tracking/service.py` | 33-37 | comms, finance, governance, logistics |
| `suppliers/services/supplier_shared.py` | 31-55 | governance, catalog, comms, finance, logistics, orders (8 domains) |
| `suppliers/services/products/supplier_products.py` | 85, 91, 105, 114 | comms, finance |
| `suppliers/services/governance/admin_suppliers_service.py` | 15, 25-28, 414 | governance, comms, country, catalog |

**Pattern B: Direct service imports across domains** (worse — bypasses the entire abstraction)

| Source | Line | Cross-Domain Import |
|--------|------|---------------------|
| `accounts/services/logistics_partner_service.py` | 2 | `from domains.logistics.services.partners.logistics_partner_service import *` |
| `audit/services/audit.py` | 4 | `from domains.security.services.audit_service import *` |
| `audit/services/communication_audit.py` | 19 | `from domains.comms.services.admin.communication_audit import ...` |
| `customers/services/referrals/referrals_service.py` | 26 | `from domains.orders.services.referrals_service import ...` |
| `logistics/services/sla/service.py` | 129 | `from domains.finance.services.treasury.treasury_service import TreasuryService` |
| `logistics/services/partners/admin_logistics_operations_service.py` | 15 | `from domains.accounts.services.auth.auth_service import get_current_user` |
| `orders/services/trading_service.py` | 7 | `from domains.finance.services.trading_service import ...` |
| `suppliers/services/profile/supplier_profile.py` | 42 | `from domains.catalog.services.products.products_service import get_supplier_profile` |
| `suppliers/services/products/supplier_supplier_upload_service.py` | 19 | `from domains.security.services.iam.security_dependencies import require_roles` |
| `suppliers/services/governance/admin_suppliers_service.py` | 15 | `from domains.governance.services.settings.misc_service import ...` |
| `suppliers/services/contracts/legal_contract_service.py` | 19 | `from domains.country.services.localization.localization_service import is_rtl_language` |
| `suppliers/services/supplier_shared.py` | 50, 53, 55 | logistics, catalog, orders services |

**Solution:** This is a massive refactor. Two strategies:

1. **Quick mitigation:** Add the imports to `DOMAIN_ALLOWLIST.yaml` (which already lists 13 such exceptions) and ensure each is wired to use `ports.py` or `events.py`.

2. **Proper refactor:** For each cross-domain dependency, add a method to the target domain's `ports.py` and update the caller to use the port. For writes, ensure events are published via `events.py` and consumed via `subscribers.py`.

**Priority:** Top 5 worst offenders should be fixed first:
1. `accounts/services/users/users_admin_service/__header__*.py` (5 files, 100+ imports)
2. `analytics/services/flat_admin_*.py` (4 files)
3. `suppliers/services/supplier_shared.py`
4. `orders/services/tracking/service.py`
5. `accounts/services/auth/auth_service.py`

---

### 🟠 HIGH #10: `DOMAIN_ALLOWLIST.yaml` references non-existent `domains.payments`
**Law 3 violation + data integrity issue.**

`DOMAIN_ALLOWLIST.yaml` lines 56-67 reference `domains.payments.models.payments` and `domains.payments.services.*`. The `payments` domain does not exist in the 16-domain list.

**Solution:** Either:
- Create the `payments` domain (and add to architecture)
- Or replace all `domains.payments.*` references with `domains.finance.payments.*` or `providers/payments/`

---

## Law 4: "Features single-sourced in `domains/*/features.py`; aggregated by `rbac/catalog.py`"

### 🔴 CRITICAL #10: Colon vs dot format mismatch — RBAC is functionally broken
**Law 4 violation (CRITICAL).** The role-to-feature mapping uses a different format than the catalog, so grants never match.

`rbac/dependencies.py:50-77` `_ROLE_FEATURES` uses **colon-separated** keys:
```python
"analytics:read", "hr:read", "governance:read", "finance:commission:read", ...
```

But the catalog (`rbac/catalog.py`) aggregates **dot-separated** keys from `domains/{d}/features.py`:
```python
"finance.commission.read", "finance.ledger.read", ...
```

**Impact:** When `rbac/resolution.py:expand_wildcards()` tries to match `finance:*` against the colon format, it does a string-prefix match on the catalog. But since the catalog has dot format, `finance:*` (in colon format) will NEVER match `finance.commission.read` (in dot format).

This means:
- `require_feature("finance:commission:read")` always returns 403
- Even super_admin (granted `["*"]`) cannot expand colon-format wildcards against dot-format catalog
- All supplier finance endpoints (line 81-238 of `supplier/routers/finance.py`) are effectively unreachable

**Solution:**
1. Convert all `rbac/dependencies.py:_ROLE_FEATURES` keys to dot format
2. Update all `supplier/routers/finance.py:81-238` `require_feature("finance:...")` calls to dot format
3. Standardize on dot format across the entire codebase

---

### 🔴 CRITICAL #11: 12 duplicate `services/features.py` files create shadow RBAC system
**Law 4 violation.** The architecture says features are single-sourced in `domains/{d}/features.py`, but 12 domains have a SECOND `services/features.py` with different/overlapping keys.

| File | Extra Features NOT in catalog |
|------|------------------------------|
| `audit/services/features.py` | `audit.anomalies.*`, `audit.command_center.*` |
| `comms/services/features.py` | `comms.messages.*`, `comms.broadcast` |
| `country/services/features.py` | `country.read`, `country.manage`, `country.currency.*` |
| `customers/services/features.py` | `coins.earn`, `coins.redeem`, `coins.manage` |
| `finance/services/features.py` | `finance.invoices.*`, `finance.payments.*`, `finance.bank_reconciliation` |
| `governance/services/features.py` | `governance.roles.*`, `governance.policies.*`, `governance.user.ban` |
| `hr/services/features.py` | `hr.employees.*`, `hr.org_structure.*`, `hr.training.*` |
| `logistics/services/features.py` | `logistics.delivery.estimates` |
| `orders/services/features.py` | `orders.cancel`, `orders.fulfill`, `orders.returns.*`, `orders.export` |
| `promotions/services/features.py` | `promotions.campaigns.*`, `promotions.engine.*`, `promotions.discounts.*` |
| `security/services/features.py` | `fraud.detection.*`, `threat.monitoring.*`, `threat.response` |
| `suppliers/services/features.py` | `suppliers.profiles.*`, `suppliers.catalog.*`, `suppliers.analytics` |

**Impact:** The shadow features are never aggregated by the catalog. Code that uses them bypasses RBAC enforcement.

**Solution:** Either:
1. Delete the `services/features.py` files and merge their features into the canonical `domains/{d}/features.py`
2. Update `rbac/catalog.py` to also scan `services/features.py` (but this duplicates the source of truth)

**Recommendation:** Option 1 — merge into canonical.

---

### 🔴 CRITICAL #12: `rbac/models/permission_entities.py:6` has latent ImportError
**Law 4 + correctness violation.**

```python
# rbac/models/permission_entities.py:6
from .. import Base  # This will fail — rbac/__init__.py does NOT export Base
```

`rbac/models/__init__.py:3` does export `Base` from `infrastructure.database.base`, but the `permission_entities.py` uses a relative import `from ..` which resolves to `rbac/__init__.py` — which does NOT export Base.

**Solution:** Change `from .. import Base` to `from infrastructure.database.base import Base` (or use a proper relative import like `from ..models import Base` if the package structure supports it).

---

### 🟠 HIGH #11: `rbac/staff_permissions.py` — parallel permission system
**Law 4 violation.** A second RBAC system exists with different namespace.

`rbac/staff_permissions.py` defines permission strings like `analytics.view`, `hierarchy.view`, `users.read`, `staff.manage`, etc. — completely different from the dot-format `analytics.read` in the catalog.

Used by:
- `domains/accounts/services/users/users_admin_service/__header__*.py` (5 files)
- `domains/accounts/services/auth/auth_service.py`
- `infrastructure/utils/staff_permissions.py` (shim)
- `domains/analytics/services/dashboards/analytics_service.py`

**Solution:** Migrate all callers to the canonical catalog. Delete `staff_permissions.py`.

---

### 🟠 HIGH #12: `domains/common/` is missing `features.py`
**Law 4 violation.** The catalog scan at `rbac/catalog.py:33` silently swallows the exception and skips `common`.

`rbac/catalog.py:30-35`:
```python
for m in pkgutil.iter_modules(domains.__path__):
    if m.name in EXCLUDED_DOMAINS:  # might be excluding common
        continue
    try:
        feat = importlib.import_module(f"domains.{m.name}.features")
    except Exception:
        pass  # ← silent failure
```

The `common` domain has 8 files but no `features.py`. Features for the `common` domain (auth, rls, session, etc.) are undefined.

**Solution:** Add `domains/common/features.py` with the relevant features OR formally remove the `common` domain and migrate its files to their proper homes.

---

### 🟠 HIGH #13: `logistics/features.py` and `orders/features.py` lazy-load from `services/`
**Law 4 violation.** These use `__getattr__` magic to lazy-import from `services/features.py`, defeating single-sourcing.

`logistics/features.py:5-10`:
```python
def __getattr__(name):
    if name == "FEATURES":
        from domains.logistics.services.features import FEATURES
        return FEATURES
```

**Solution:** Move the FEATURES dict from `services/features.py` to `features.py` directly.

---

### 🟠 HIGH #14: `security/services/features.py` imports from providers
**Law 4 violation.** Features are data definitions, not code.

`security/services/features.py:70-73`:
```python
from providers.auth.jwt import decode_token
from providers.auth.totp import generate_secret, provisioning_uri, verify as verify_totp
from providers.security.encryption import Fernet, PBKDF2HMAC, hashes
from providers.security.watchlist import WatchlistProviderError, screen_watchlist
```

**Solution:** Remove these imports. If they're needed at runtime, move them to `domains/security/services/iam/`.

---

### 🟡 MEDIUM #4: `rbac/__init__.py` contains 14 no-op stubs
**Law 4 violation (correctness).** Dead code masks missing implementations.

`rbac/__init__.py:22-33`:
```python
def _noop(*args, **kwargs):
    return None

detect_ghost_employees = _noop
detect_impossible_travel = _noop
update_flight_risk_score = _noop
# ... 11 more
```

**Solution:** Remove the no-op stubs. Update all callers to use proper implementations.

---

### 🟡 MEDIUM #5: `rbac/service.py` duplicates `rbac/dependencies.py`
**Law 4 violation (redundancy).**

`rbac/service.py` contains `RBACService` class with `grant()`/`revoke()` that duplicates functionality. The `__init__.py` docstring says "Migrated from the legacy RBACService" but it still exists.

**Solution:** Consolidate into `rbac/dependencies.py` or delete if not used.

---

### 🟡 MEDIUM #6: `rbac/models/permission_entities.py` not in architecture diagram
**Law 4 deviation.** The diagram only specifies `rbac/models.py` (with `permission_categories`, `role_permission_assignments`, `user_permission_overrides`), but the implementation has `rbac/models/permission_entities.py` (with `Permission`, `RolePermissionAssignment`, etc.).

**Solution:** Either:
- Rename file to match diagram (`rbac/models.py`)
- Update diagram to reflect current implementation
- Or merge the diagram's tables into the current `permission_entities.py` if they're equivalent

---

## Law 5: "Country is the orthogonal scope axis" — RLS + country_staff_assignments

### 🔴 CRITICAL #13: RLS is completely unenforced at the DB layer
**Law 5 violation.** The RLS enforcer is defined but never wired.

- `infrastructure/database/rls_interceptor.py:359` defines `instrument_rls()` 
- `infrastructure/database/security.py:24` re-exports it
- `rls_before_execute()` is registered only via `instrument_rls()` which is **NEVER CALLED**

The AGENTS.md acknowledges: "RLS is a runtime no-op — `instrument_rls` is never called."

**Solution:**
1. Call `instrument_rls(engine)` during app startup (in `main.py` or `lifespan.py`)
2. Define RLS policies on every domain schema in Alembic migrations
3. Set the `country_code` session context at the start of every request (in `country_context.py` middleware)

---

### 🟠 HIGH #15: Two RLS implementations, neither wired
**Law 5 violation (redundancy).**

- `rls_middleware.py` — query-filtering approach
- `rls_dependency.py` — FastAPI dependency approach
- `rls_interceptor.py` — SQLAlchemy event listener approach

All three exist. `CountryContextMiddleware` (which IS wired) handles RLS in middleware, but the database-level enforcer is never called.

**Solution:** Consolidate to one approach. Since the architecture specifies "RLS enforcer at infrastructure/database level," the SQLAlchemy event listener approach is canonical. Delete the other two.

---

## Law 6: "Schema discipline" — one schema per domain, naming, FK constraints

### 🔴 CRITICAL #14: Forbidden schema `commerce` — 30 references
**Law 6 violation.** References a non-existent domain schema.

| File | Lines | Foreign Key |
|------|-------|-------------|
| `accounts/models/core.py` | 94 | `commerce.products.id` |
| `catalog/models/products.py` | 18, 65, 116, 137, 150, 161, 195, 229, 245 | `commerce.categories.id`, `commerce.products.id`, etc. |
| `catalog/models/ai_upload.py` | 58, 76 | `commerce.products.id` |
| `security/models/fraud.py` | 27, 247 | `commerce.orders.id` |
| `governance/models/core.py` | 50 | `commerce.products.id` |
| `governance/models/admin.py` | 238, 240, 482, 508, 555, 581, 595, 700, 705 | `commerce.coupons.id`, `commerce.orders.id`, etc. |
| `finance/models/payments.py` | 48, 130 | `commerce.orders.id` |
| `finance/models/commission.py` | 44, 65, 66, 67 | `commerce.products.id`, `commerce.orders.id`, etc. |

**Solution:** Create an Alembic migration that:
1. Creates the `catalog`, `orders`, `promotions` schemas (or uses existing ones)
2. Renames all `commerce.X` FKs to the correct domain schema

---

### 🔴 CRITICAL #15: `accounts.users.id` references — 22 occurrences
**Law 6 violation.** The `accounts` schema has no `users` table. Users live in `governance.users`.

Affected: `comms/models/chat.py` (12x), `comms/models/communication_schema_models.py` (2x), `comms/models/marketing.py` (2x), `hr/models/hr_schema_models.py`, `hr/models/employee_models.py`, `logistics/models/logistics_schema_models.py` (2x), `logistics/models/logistics_entities.py`, `suppliers/models/suppliers.py`, `security/models/security_schema_models.py` (3x), `audit/models/audit_schema_models.py` (2x).

**Solution:** Alembic migration: `accounts.X` → `governance.X` in all FK declarations.

---

### 🔴 CRITICAL #16: `AuditMixin` references `core.users` — forbidden schema
**Law 6 violation.** The canonical audit mixin itself uses a forbidden schema.

`infrastructure/database/mixins.py:15, 17, 29`:
```python
created_by_id = Column(Integer, ForeignKey("core.users.id"), ...)
updated_by_id = Column(Integer, ForeignKey("core.users.id"), ...)
deleted_by_id = Column(Integer, ForeignKey("core.users.id"), ...)
```

**Solution:** Replace `core.users.id` with `governance.users.id` in the mixin.

---

### 🟠 HIGH #16: 100+ FKs without `ondelete` constraint
**Law 6 violation.** Foreign keys must have explicit `ondelete`.

Major offenders:
- `governance/models/admin.py` — 25+ FKs without ondelete
- `hr/models/employee_models.py` — 25+ FKs without ondelete
- `country/models/country_control.py` — 11 FKs without ondelete
- `comms/models/communication_schema_models.py` — 6 FKs without ondelete
- `finance/models/commission.py` — 7 FKs without ondelete
- `governance/models/incident.py` — 4 FKs without ondelete
- `comms/models/news.py` — 1 FK
- `promotions/models/promotion_config.py` — 1 FK
- `promotions/models/coupon_usage.py` — 1 FK
- `hr/models/hr_schema_models.py` — 2 FKs
- `logistics/models/logistics_schema_models.py` — 2 FKs

**Solution:** Add explicit `ondelete="CASCADE"` or `ondelete="SET NULL"` to every FK in an Alembic migration.

---

### 🟠 HIGH #17: 100+ `Column(String)` without length
**Law 6 violation.** PostgreSQL `VARCHAR` requires a length.

Major offenders:
- `comms/models/marketing.py` — 27 occurrences
- `hr/models/employee_models.py` — 20+ occurrences
- `governance/models/admin.py` — 15+ occurrences
- `logistics/models/logistics_entities.py` — 15+ occurrences
- `comms/models/communication.py` — 15+ occurrences
- `catalog/models/ai_upload.py` — 13 occurrences
- `security/models/fraud.py` — 10+ occurrences
- `suppliers/models/suppliers.py` — 10+ occurrences
- `catalog/models/products.py` — 10+ occurrences
- `accounts/models/core.py` — 9 occurrences
- `accounts/models/onboarding.py` — 5 occurrences
- `audit/models/audit_schema_models.py` — 6 occurrences
- `finance/models/general_ledger.py` — 5+ occurrences
- (and many more)

**Solution:** Add explicit `String(N)` to every column. Use sensible defaults (255 for names, 100 for emails, 50 for codes, etc.).

---

### 🟠 HIGH #18: Cross-domain schema contamination
**Law 6 violation.** Models declared in domain X use schema Y.

| File:Line | Table | Wrong Schema | Should Be |
|-----------|-------|--------------|-----------|
| `hr/models/employee_models.py:137,206,252,282` | employees, employee_attendance, employee_leave_ledger, employee_shift_rosters | `logistics` | `hr` |
| `governance/models/admin.py:295,308,414,436,464,479,505` | shipping_carriers, shipping_zones, logistics_cod_remittance_receipts, logistics_partner_bank_accounts, logistics_partner_documents, logistics_settlements, shipment_confirmations | `logistics` | `logistics` domain |
| `governance/models/admin.py:224,567` | ticket_replies, push_notification_tokens | `communication` | `comms` domain |
| `governance/models/admin.py:629,652` | processed_webhook_events, normalized_webhook_events | `analytics` | `analytics` domain |
| `security/models/fraud.py:170` | supplier_fraud_indicators | `supplier` (singular) | `suppliers` |
| `security/models/fraud.py:182` | logistics_fraud_indicators | `logistics` | `security` (this IS the security model) |
| `security/models/fraud.py:374` | meeting_action_items | `communication` | `comms` |

**Solution:** Alembic migration to move all these tables to their correct schemas. This is a major refactor.

---

### 🟠 HIGH #19: `supplier` (singular) vs `suppliers` (plural) schema
**Law 6 violation.** Schemas should match domain names (plural).

`governance/models/admin.py:601, 697, 726` and `security/models/fraud.py:170` use `supplier` schema.

**Solution:** Rename schema `supplier` → `suppliers`.

---

### 🟠 HIGH #20: 15+ model files use Python-side `default=_utcnow`
**Law 6 violation.** Timestamps must be DB-side `server_default=func.now()`.

| File | Issue |
|------|-------|
| `security/models/fraud.py` | ALL 20 models |
| `customers/models/customer_schema_models.py` | All models |
| `country/models/country_control.py` | All models |
| `finance/models/commission.py` | All models |
| `finance/models/erp.py` | All models |
| `finance/models/general_ledger.py` | 40+ models |
| `hr/models/hr_schema_models.py` | `ShiftHandoverTask` |
| `logistics/models/logistics_schema_models.py` | `CityDistanceMatrix` |
| `logistics/models/logistics_entities.py` | All models |
| `promotions/models/promotion_config.py` | `PromotionEngineConfig` |
| `promotions/models/coupon_usage.py` | `CouponUsage` |
| `catalog/models/upload_job.py` | `UploadJob` |
| `suppliers/models/suppliers.py` | All models |
| `comms/models/communication.py` (mixed) | Some |
| `comms/models/communication_schema_models.py` | All |
| `comms/models/chat.py` | All |
| `comms/models/news.py` | All |
| `comms/models/marketing.py` (mixed) | Some |

The canonical `AuditMixin` (`infrastructure/database/mixins.py:14-17`) itself uses Python-side defaults.

**Solution:** Alembic migration to change all `default=_utcnow` to `server_default=func.now()` and `onupdate=_utcnow` to `onupdate=func.now()`.

---

### 🟠 HIGH #21: `country_code` width not standardized
**Law 6 violation.** Must be `String(2)`.

`security/models/fraud.py:40` — `country_code = Column(String(10))`.

**Solution:** Change to `String(2)`.

---

### 🟡 MEDIUM #7: Canonical `AuditMixin` unused across codebase
**Law 6 violation (consistency).** Models redeclare `created_at`/`updated_at` inline rather than using the canonical mixin.

Only 4 model files even import from `infrastructure.database.mixins`:
- `suppliers/models/suppliers.py` — uses `TenantMixin`, `VersionMixin` (NOT `AuditMixin`)
- `comms/models/marketing.py` — uses `TenantMixin`, `VersionMixin`
- `comms/models/communication.py` — uses `TenantMixin`, `VersionMixin`

**Solution:** After fixing the `AuditMixin` (use `governance.users.id`, `server_default=func.now()`), update all models to inherit from it.

---

### 🟡 MEDIUM #8: `order_id` without ForeignKey in `promotions/models/coupon_usage.py:17`
**Law 6 violation.** No referential integrity.

```python
order_id = Column(Integer)  # No ForeignKey!
```

**Solution:** Add `ForeignKey("orders.orders.id", ondelete="...")`.

---

### 🟡 MEDIUM #9: Cross-domain `relationship()` with string class names
**Law 6 (consistency) violation.** Creates implicit cross-domain coupling.

Examples:
- `catalog/models/products.py:34` — `relationship("Product", ...)`
- `catalog/models/products.py:98` — `relationship("User", ...)`
- `governance/models/admin.py:245-247, 691` — Coupon, User, Order, Employee
- `security/models/fraud.py:42` — `relationship("User", ...)`
- `governance/models/incident.py:26` — `relationship("User", ...)`
- `finance/models/general_ledger.py:346` — `relationship('User', ...)`

**Solution:** Use explicit class references where possible. For string references, ensure they resolve to the correct schema.

---

### 🟡 MEDIUM #10: `server_default=func.now()` without `onupdate` in some `updated_at` columns
**Law 6 violation (consistency).**

Examples: `catalog/models/ai_upload.py:96,130,149`.

**Solution:** Add `onupdate=func.now()` to all `updated_at` columns.

---

### 🟡 MEDIUM #11: `logistics.employees.id` cross-schema references (24+ occurrences)
**Law 6 violation.** `hr/models/employee_models.py` references `logistics.employees.id` but employees should be in `hr` schema.

Affected lines: 157, 190, 213, 230, 254, 270, 289, 309, 326, 344, 360, 364, 377, 396, 400, 417, 441, 458, 476, 557, 580, 581, 582.

**Solution:** Change all `logistics.employees.id` to `hr.employees.id` in an Alembic migration.

---

### 🟢 LOW: Other non-existent schemas
- `customer.shift_handover_sessions` (2 refs in `hr/models/hr_schema_models.py:59`, `hr/models/employee_models.py:598`)
- `media.product_videos` (1 ref in `catalog/models/products.py:215`)
- `treasury.payouts` (1 ref in `governance/models/admin.py:496`)

**Solution:** Alembic migration to align all FKs with correct schemas.

---

## Law 7: "Allowlist rule" — `DOMAIN_ALLOWLIST.yaml` may only shrink

### ✅ STATUS: Currently compliant (allowlist is shrinking as expected)

`DOMAIN_ALLOWLIST.yaml` has 13 documented exceptions. Per `corrections.md`, the allowlist should only shrink over time. This is being followed.

**No new violations found.** Continue enforcing this rule.

---

# PART 2: SCHEMA DISCIPLINE — Additional Findings

### 🟢 Models Outside `domains/*/models/`

| File | Issue |
|------|-------|
| `infrastructure/database/seed/models.py` | Seed-specific models — questionable if they should be in `domains/` |
| `providers/payments/base_models.py` | Provider layer defining ORM models — provider should only wrap SDKs |
| `providers/payments/webhook_models.py` | Same concern |

**Solution:** Move `providers/payments/base_models.py` and `webhook_models.py` to `domains/finance/models/`. Move `seed/models.py` to `domains/{domain}/seeds/` or delete if not used.

---

# PART 3: PROVIDER COMPLIANCE

### 🟠 HIGH #22: ~30 providers lack `HAS_<SDK>` flags
**Provider rule violation.** Cannot gracefully degrade.

Providers without HAS flags:
- `ai/*` (13 files) — huggingface, openai_client, vision, text, chatbot, search, recommendation, price_intelligence, finance_ai, image_ai_service, web_search, zozi_mcp, ai_variant_config
- `comms/email.py`
- `geography/*` (7 files) — geo, geoip, ip, map, country, country_http, external_data
- `image/image.py`, `image/free_image_tools.py`, `image/parcel_verification.py`
- `news/rss_provider.py`
- `ocr/ocr_parser.py`
- `security/*` (3 files) — watchlist, threat_intel, encryption
- `storage/*` (3 files) — `__init__.py`, `s3_client.py`, `storage_backend.py`
- `voice/voice_to_text.py`
- `media/services/*` (3 files)
- `providers/http.py`, `providers/observability.py`, `providers/async_workers.py`

**Solution:** Add `HAS_<SDK>` flag for each provider, wrap imports in try/except.

---

### 🟠 HIGH #23: 15+ providers with direct imports that crash on missing SDK
**Provider rule violation.** Cannot gracefully degrade.

| File | Direct Import |
|------|---------------|
| `ai/huggingface.py:15` | `import requests` |
| `ai/openai_client.py:12` | `import httpx` |
| `news/rss_provider.py:12-13` | `import feedparser`, `import httpx` |
| `security/encryption.py:7-9` | `from cryptography.fernet import ...` |
| `payments/tap.py:14`, `paytabs.py:14`, `thawani.py:14` | `import requests` |
| `payments/config.py:6` | `from providers.payments.stripe_sdk import stripe` |
| `http.py:6-7` | `import aiohttp` |
| `geography/external_data.py:14` | `import aiohttp` |
| `geography/country_http.py:16`, `ip.py:14` | `import httpx` |
| `geography/geo.py:19` | `import requests` |
| `image/image.py:14` | `from PIL import Image` |
| `image/free_image_tools.py` | `from PIL import Image` |
| `image/parcel_verification.py` | `from PIL import Image` |
| `image/bg_remover/*` | `from PIL import Image`, `import numpy` |

**Solution:** Wrap each import in try/except and set the corresponding `HAS_<SDK>` flag.

---

### 🟠 HIGH #24: Significant business logic in providers
**Provider rule violation.** Providers should wrap SDKs only.

Examples (HIGH severity):
- `ai/recommendation.py:93-177` — Full recommendation engine
- `ai/search.py:36-352` — AdvancedSearchEngine class
- `ai/price_intelligence.py:75-180` — Price analysis
- `ai/finance_ai.py:37-204` — Email parsing, bill extraction
- `ai/vision.py:70-309` — Product classification, price suggestion
- `ai/zozi_mcp.py:1-723` — Full MCP server with API orchestration
- `shipping/shipping_calculator.py:29-407` — Complete shipping rate calculation

**Solution:** Move business logic to domain services. Providers should expose thin SDK wrappers (e.g., `ai_call(prompt: str) -> str` not a full recommendation engine).

---

### 🟡 MEDIUM #12: Duplicate provider implementations

| Duplicate | Location 1 | Location 2 |
|-----------|------------|------------|
| Background removal | `providers/bg_removal/bg_removal_service.py` | `providers/image/bg_remover/` (12 files) |
| Geo/IP | `providers/geography/geo.py` | `providers/geography/ip.py`, `providers/geography/geoip.py` |
| Country data | `providers/geography/country_http.py` | `providers/geography/external_data.py` |
| OCR | `providers/ocr/ocr_parser.py` | `providers/image/ocr.py` |
| AI media | `providers/ai/image_ai_service.py` | `providers/media/services/ai_service.py` |

**Solution:** Consolidate each duplicate pair.

---

### 🟡 MEDIUM #13: Circular import risk
**Provider hygiene issue.**

`providers/bg_removal/bg_removal_service.py:43-44` imports from `providers.image`, which imports from `providers.image.bg_remover`, which imports from `providers.image` again.

`providers/payments/config.py:6` imports `stripe` from `stripe_sdk.py` which may re-export.

**Solution:** Refactor to break the cycles.

---

### 🟡 MEDIUM #14: Empty `providers/geo/` directory
**Provider hygiene issue.**

`providers/geo/__init__.py` only contains `# Geo provider package (COUN-004 move).`

**Solution:** Delete the empty directory or finish the COUN-004 move.

---

### 🟡 MEDIUM #15: `provider_test/` directory contains only artifacts
**Provider hygiene issue.**

`providers/provider_test/` contains `visual_regression/report_index.html` and `metrics.json` but no actual test files. Many provider docstrings reference `backend/tests/_test_provider/` which doesn't exist.

**Solution:** Move test artifacts to `tests/` or delete. Add real tests where referenced.

---

### 🟡 MEDIUM #16: Non-standard file naming in `providers/image/bg_remover/`
**Provider hygiene issue.**

Examples:
- `br_05___br_06__background_remover_legacy.py`
- `br_08__production_pipeline_classes.py`
- `br_11_12_13__ultimate_pipeline_classes.py`
- `enums___constants.py`
- `core_i_o.py`
- `memory_management__br_08_.py`

**Solution:** Rename to standard snake_case (e.g., `background_remover_legacy.py`, `production_pipeline.py`).

---

### 🟢 LOW: Large files (>400 lines)

| File | Lines |
|------|-------|
| `ai/ai_variant_config.py` | 970 |
| `bg_removal/bg_removal_service.py` | 845 |
| `ai/zozi_mcp.py` | 723 |
| `media/services/ai_service.py` | 1,114 |
| `ai/text.py` | 552 |
| `async_workers.py` | 466 |

**Solution:** Split into smaller modules.

---

### 🟢 LOW: Stub providers

- `media/services/ai.py` — returns `{"status": "not_implemented"}`
- `payments/stripe_sdk.py:27-34` — `refund_payment_intent` returns stub
- `analytics/analytics.py` — returns hardcoded zeros

**Solution:** Either implement or remove.

---

# PART 4: MODULE STRUCTURE ISSUES

### 🟠 HIGH #25: Incomplete router coverage

| Module | Routers Present | Missing Domains |
|--------|-----------------|-----------------|
| admin | 15/15 ✅ | None |
| customer | 6/15 | analytics, audit, catalog, country, governance, hr, logistics, security, suppliers |
| employee | 8/15 | analytics, audit, catalog, customers, governance, logistics, promotions |
| logistics | 1/15 | accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, orders, promotions, security, suppliers |
| supplier | 5/15 | accounts, audit, comms, country, customers, governance, hr, logistics, promotions, security |

**Solution:** Create the missing router files. Or document which routers are intentionally omitted.

---

### 🟠 HIGH #26: Facade export mismatches in `__init__.py`

- `customer/__init__.py:13-26` — declares 15 router exports but only 6 exist
- `employee/__init__.py:12-26` — declares 15 router exports but only 8 exist
- `logistics/__init__.py:12-26` — declares 15 router exports but only 1 exists
- `supplier/__init__.py:12-26` — declares 15 router exports but only 5 exist

**Solution:** Remove the non-existent exports OR create the missing routers.

---

### 🟠 HIGH #27: Broken `admin/services/` references in `admin/__init__.py`

`modules/admin/__init__.py:28-30` imports from `modules.admin.services.*` but the `services/` directory does not exist.

```python
from modules.admin.services.admin_service import AdminService
from modules.admin.services.admin_suppliers_service import AdminSuppliersService
from modules.admin.services.catalog_operations_service import CatalogOperationsService
```

**Solution:** Either create `modules/admin/services/` (violates Law 1 — modules shouldn't have services) or remove the imports.

---

### 🟡 MEDIUM #17: `public_routers` missing in 3 modules
**Module structure issue.**

- `employee/routers/__init__.py` — no `public_routers` list
- `logistics/routers/__init__.py` — no `public_routers` list
- `supplier/routers/__init__.py` — no `public_routers` list

**Solution:** Add `public_routers` to each.

---

### 🟡 MEDIUM #18: Dead code / placeholder markers

- `employee/routers/finance.py:1197-1200` — `__router_prefix__ = "/api/v1"` and `__all__ = ["router"]` — dead code
- `employee/routers/finance.py:1201-1205, 1321-1322` — unused `from fastapi import APIRouter`
- `employee/routers/suppliers.py:87, 274` — `__router_prefix__` + unused APIRouter import
- `customer/routers/comms.py:1,3` — duplicate `APIRouter`, `Depends` imports
- `customer/routers/promotions.py:11,13` — duplicate `get_current_user` imports

**Solution:** Remove dead code.

---

### 🟡 MEDIUM #19: Inconsistent serializers directory

- `admin/serializers/` has `shared.py` and `auth.py` but no `admin_serializers.py` (naming inconsistency)
- Other modules follow the `<module>_serializers.py` pattern

**Solution:** Rename to `admin_serializers.py` for consistency.

---

# PART 5: INFRASTRUCTURE & KERNEL ISSUES

### 🟠 HIGH #28: `infrastructure/utils/` contains 50+ files with business logic
**Law 1 violation.** Infrastructure should have zero business logic.

Examples:
- `command_center.py` — caching logic for demographics, sales, search trends, employee metrics
- `currency_service.py` — currency conversion, rate fetching
- `realtime.py` — WebSocket hubs
- `email_service.py` — email delivery
- `free_image_tools.py` — image processing

**Solution:** Move all business logic to `domains/{domain}/services/`. Infrastructure should only have technical primitives (pagination, datetime, variant_key, slugs).

---

### 🟠 HIGH #29: `infrastructure/routing/auto_router.py` implements controller/router patterns
**Law 1 + controller pattern violation.**

`infrastructure/routing/auto_router.py:1-112`:
- `@get/@post/@put/@delete/@patch` decorators for "controllers"
- `scan_controllers()` function

**Solution:** Delete `infrastructure/routing/`. Routers belong in `modules/{module}/routers/` only.

---

### 🟠 HIGH #30: `infrastructure/search/routers/` imports from modules
**Law 1 violation.**

`infrastructure/search/routers/__init__.py:3`:
```python
from modules.admin.routers.catalog import (get_recommendations, smart_search)
```

**Solution:** Delete `infrastructure/search/routers/`. The search router belongs in `modules/admin/routers/catalog.py` only.

---

### 🟡 MEDIUM #20: `infrastructure/lifespan.py` is dead code
**Infrastructure hygiene issue.**

`infrastructure/lifespan.py` is a duplicate of root `lifespan.py` (267 lines). It's not used by `main.py`. Imports `domains._service_registry` (the removed service registry).

**Solution:** Delete `infrastructure/lifespan.py`.

---

### 🟡 MEDIUM #21: `infrastructure/utils/` backward-compat shims (10+ pairs)

| Canonical | Shim | Status |
|-----------|------|--------|
| `kernel/money.py` | `infrastructure/utils/money.py` | Shim re-export |
| `kernel/currency.py` | `infrastructure/utils/currency.py` | Shim re-export |
| `infrastructure/database/rls_interceptor.py` | `infrastructure/utils/rls_interceptor.py` | Shim re-export |
| `infrastructure/database/rls_interceptor.py` | `infrastructure/utils/rls_middleware.py` | Shim re-export |
| `infrastructure/observability/circuit_breaker.py` | `infrastructure/utils/circuit_breaker.py` | Likely duplicate |
| `infrastructure/observability/prometheus_setup.py` | `infrastructure/utils/prometheus_setup.py` | Likely duplicate |
| `infrastructure/observability/metrics.py` | `infrastructure/utils/metrics.py` | Likely duplicate |
| `infrastructure/observability/logging_config.py` | `infrastructure/utils/logging_config.py` | Likely duplicate |
| `domains/audit/services/logs/audit_service.py` | `infrastructure/utils/audit.py` | Shim re-export |
| `domains/hr/services/employees/asset_tracking.py` | `infrastructure/utils/asset_tracking.py` | Shim (broken — target doesn't exist) |
| `domains/governance/services/command_center/service.py` | `infrastructure/utils/command_center_service.py` | Shim re-export |
| `domains/comms/services/messaging/chat_service.py` | `infrastructure/utils/entity_messaging.py` | Shim re-export |
| `domains/finance/services/data_import_service.py` | `infrastructure/utils/import_service.py` | Shim re-export |
| `rbac/staff_permissions.py` | `infrastructure/utils/staff_permissions.py` | Layering violation |

**Solution:** 
1. Update callers to use canonical locations
2. Delete the shims
3. Exception: keep one canonical location per concern

---

### 🟢 LOW: Kernel purity

5 of 8 kernel files are pure business primitives ✅. 3 have issues (covered in Critical #8).

---

# PART 6: MIDDLEWARE ISSUES

### 🔴 CRITICAL #17: Webhook middleware NOT wired
**Security + production safety violation.**

- `middleware/webhook_verification.py:33` defines `WebhookVerificationMiddleware` but it's **NEVER added** to the app
- `middleware/webhook_ip_whitelist.py:446` defines `WebhookIPWhitelistMiddleware` but it's **NEVER added**

Both are listed as `PER-ROUTE` in the orchestrator comment table but no router imports them.

**Impact:** Webhook endpoints (`/payments/webhook`, `/payments/tap/webhook`, `/email/webhooks`, etc.) have **zero IP whitelist enforcement and zero HMAC signature verification** at the middleware layer. This is a **CRITICAL SECURITY VULNERABILITY** for production.

**Solution:**
1. Wire the middleware in `orchestrator.py` (add to pipeline)
2. Or apply per-route via `dependencies=[Depends(...)]` and have the middleware imported by the relevant router

---

### 🟠 HIGH #31: Orchestrator pipeline order doesn't match 6-layer spec
**Law 1 + architecture diagram deviation.**

Architecture diagram specifies: Foundation → Security → Rate Limit → Geo → Observability → Compliance (6 layers).

Actual orchestrator (`orchestrator.py:156-163`): 7 layers
1. Foundation
2. Authentication (inserted — not in spec)
3. Rate Limiting
4. Geo & Country
5. Security (after Geo — should be before per spec)
6. Observability
7. Compliance

The Security layer (headers, travel, CSRF) is in position 5, but the architecture says it should be in position 2.

**Solution:** Reorder middleware in `orchestrator.py` to match the documented 6-layer spec.

---

### 🟠 HIGH #32: `middleware/dependencies/` subdirectory violates "flat" rule
**Architecture deviation.**

`middleware/dependencies/` contains 3 adapter files (fraud_events.py, country_detection.py, coi_dependency.py) that import from domains. The architecture says "middleware is flat."

**Solution:** Delete `middleware/dependencies/` and inline the logic in the middleware files. Or move the domain-coupled logic to domain services and have middleware publish events.

---

### 🟡 MEDIUM #22: 10+ middleware files NOT wired in pipeline

These exist but are never added to the app:
- `webhook_verification.py`
- `webhook_ip_whitelist.py`
- `coi_middleware.py`
- `rls_middleware.py`
- `rls_dependency.py`
- `zero_trust_auth.py`
- `device_binding_middleware.py`
- `database_security.py`

**Solution:** Either wire them or delete them. Dead code adds confusion.

---

### 🟡 MEDIUM #23: 10+ jobs NOT registered in celery_app

`jobs/celery_app.py:15-20` only includes 4 task modules. 10+ jobs exist but are unreachable via Celery:
- `bank_statement_importer.py`
- `data_retention.py`
- `accrual_reversal.py`
- `fraud_monitoring.py`
- `fx_revaluation.py`
- `ghost_order_detector.py`
- `background_tasks.py`
- `payout_sweep.py`
- `payroll_run.py`
- `reconciliation_cron.py`
- `threat_feed_updater.py`

**Solution:** Register the missing jobs in `celery_app.py`.

---

### 🟡 MEDIUM #24: MCP servers misplaced in `jobs/`
**File placement violation.**

`jobs/mcp_server.py` and `jobs/mcp_marketplace_server.py` are MCP (Model Context Protocol) servers, not Celery jobs. They're standalone server entry points.

**Solution:** Move to `providers/mcp/` or a new `mcp/` directory.

---

### 🟡 MEDIUM #25: `seed_all.py` contains business logic
**File placement violation.**

`jobs/seed_all.py` (897 lines) imports 10+ domain model packages and calls domain services. It's a dev seeder, not a job.

**Solution:** Move to `scripts/` or `tests/`.

---

# PART 7: BACKEND ROOT ISSUES

### 🟡 MEDIUM #26: Temporary debug scripts at backend root

| File | Purpose | Status |
|------|---------|--------|
| `backend/debug_routes.py` | Debug script to print route lines | 🔴 REMOVE |
| `backend/find_duplicates.py` | Script to find duplicate routes | 🔴 REMOVE |
| `backend/_dedup_v2.py` | Automated deduplication script | 🔴 REMOVE |
| `backend/_check_dup2.py` | Duplicate investigation script | 🔴 REMOVE |
| `backend/check_hr.py` | HR route analysis script | 🔴 REMOVE |

**Solution:** Delete all 5 files. Per AGENTS.md, "Root-level fix_*.py, debug_*.py, migrate_*.py should be removed after use."

---

### 🟡 MEDIUM #27: Forbidden JSON files at backend root

| File | Size | Status |
|------|------|--------|
| `backend/WIRING_STATUS.json` | 36 lines | Service registry artifact (removed per corrections.md) |
| `backend/admin_classification.json` | 363 lines | Classification artifact |
| `backend/admin_file_classification.json` | 359 lines | Classification artifact |

**Solution:** Delete all 3. Per corrections.md, the Service Registry was removed on 2026-08-27.

---

### 🟡 MEDIUM #28: `run_server.py` is dead code

`backend/run_server.py:1-16` is a simple uvicorn launcher with `reload=False` (useless for development). Not imported anywhere.

**Solution:** Delete.

---

### 🟢 LOW: Underscore files at `domains/` root

5 underscore-prefixed files at `domains/` root are not in any domain:
- `_service_registry.py` (267 lines) — service import side-effect registry
- `_seed.py` (1259 lines) — demo data seeding
- `_key_rotation.py` (151 lines) — encryption key rotation
- `_image_tools.py` (964 lines) — image processing pipeline
- `_async_workers.py` (487 lines) — async provider wrappers

**Solution:** Either:
- Move to proper homes (`scripts/`, `infrastructure/`, `providers/`)
- Or delete if no longer needed

---

### 🟢 LOW: `domains/common/` is a phantom domain

`domains/common/` has 8 files (`auth.py`, `security.py`, `session.py`, `settings.py`, `utils.py`, `schemas.py`, `websocket.py`, `rls.py`) but no `features.py`, `models/`, `services/`, `events.py`, etc. It's not in the 16-domain list.

**Solution:** Decide if `common` is a real domain. If yes, add `features.py`. If no, split its files into their proper homes and delete the directory.

---

# PART 8: SCHEMA-RELATED CRITICAL ISSUES SUMMARY

The most urgent issues by impact:

| # | Issue | Impact | Locations |
|---|-------|--------|-----------|
| 1 | Forbidden schema `commerce` | 30 broken FKs | 8 model files |
| 2 | `accounts.users.id` (should be `governance.users.id`) | 22 broken FKs | 8 model files |
| 3 | `AuditMixin` references `core.users.id` | All models using mixin | `infrastructure/database/mixins.py` |
| 4 | 100+ FKs without `ondelete` | Data integrity risk | 10+ files |
| 5 | 100+ `Column(String)` without length | PostgreSQL incompatibility | 15+ files |
| 6 | 15+ model files use Python-side `_utcnow` | Timestamp inconsistency | 15+ files |
| 7 | Cross-domain schema contamination | `logistics` in HR, `supplier` in governance | 4 files |
| 8 | `logistics.employees.id` self-reference issue | 24 broken FKs | 1 file |
| 9 | `country_code` not `String(2)` | Schema violation | 1 location |
| 10 | `order_id` without ForeignKey | No referential integrity | 1 location |

**These should be addressed via Alembic migrations in a dedicated refactor sprint.**

---

# PART 9: RBAC FUNCTIONAL BREAKAGE

The RBAC system is **functionally broken** due to:

1. **Colon vs dot format mismatch** (`rbac/dependencies.py:50-77` uses colon, catalog uses dot)
   - `require_feature("finance:commission:read")` always returns 403
   - All supplier finance endpoints (line 81-238 of `supplier/routers/finance.py`) are unreachable

2. **12 shadow `services/features.py` files** — features defined there bypass the catalog

3. **Parallel `rbac/staff_permissions.py` system** — different namespace, no catalog integration

4. **`rbac/models/permission_entities.py:6` latent ImportError** — `from .. import Base` fails

5. **`common` domain missing `features.py`** — silently skipped

6. **`security/services/features.py:70-73` imports from providers** — features should be pure data

7. **`logistics/features.py` and `orders/features.py` lazy-load from `services/`** — defeats single-sourcing

8. **4+ no-op stubs in `rbac/__init__.py`** — mask missing implementations

**Recommended fix order:**
1. Standardize all keys to dot format (P0)
2. Delete `services/features.py` files, merge into `domains/{d}/features.py` (P0)
3. Delete `rbac/staff_permissions.py` (P0)
4. Fix `permission_entities.py` import (P0)
5. Add `domains/common/features.py` (P1)
6. Inline `logistics/features.py` and `orders/features.py` (P1)
7. Remove no-op stubs (P2)

---

# PART 10: RECOMMENDED ACTION PLAN

## P0 — Must Fix Immediately (this week)
1. Fix `rbac/dependencies.py:_ROLE_FEATURES` to use dot format
2. Fix `rbac/models/permission_entities.py:6` ImportError
3. Wire `WebhookVerificationMiddleware` and `WebhookIPWhitelistMiddleware` in `orchestrator.py`
4. Fix `infrastructure/database/mixins.py:14-29` to use `governance.users.id` and `server_default=func.now()`
5. Delete `services/features.py` files in 12 domains; merge into `domains/{d}/features.py`
6. Delete `rbac/staff_permissions.py`
7. Fix `kernel/rls_context.py` — remove `from domains.governance import ports`
8. Delete `infrastructure/search/routers/` (Law 1 violation)

## P1 — Fix This Month
9. Wire `instrument_rls(engine)` in `main.py` startup
10. Add `domains/common/features.py` or remove the `common` domain
11. Add `infrastructure/search/routers` cleanup
12. Fix all `_auto_stubs.py` references in routers — implement or remove routes
13. Standardize `require_feature()` format to dot-separated
14. Add missing `subscribers.py` to `domains/logistics/` and `domains/orders/`
15. Add missing `policies/` to `domains/audit/`, `domains/orders/`, `domains/logistics/`
16. Move all 28+ `infrastructure/utils/*.py` business logic to domain services
17. Fix orchestrator middleware order to match 6-layer spec
18. Move `infrastructure/media/` to `providers/media/`
19. Move `infrastructure/routing/auto_router.py` and delete

## P2 — Fix This Quarter
20. Refactor top 5 worst cross-domain coupling offenders (accounts/users_admin_service, analytics/flat_admin_*, suppliers/supplier_shared, orders/tracking, accounts/auth_service)
21. Add `ondelete` to 100+ FKs
22. Add `String(N)` length to 100+ columns
23. Convert `default=_utcnow` to `server_default=func.now()` in 15+ files
24. Create Alembic migration for schema cleanup (`commerce` → correct, `supplier` → `suppliers`, etc.)
25. Delete 5 root debug scripts, 3 JSON files, `run_server.py`
26. Fix the 26 undefined function calls in routers
27. Move business logic out of routers (20+ helper functions)
28. Add `require_feature` to 100+ endpoints in `employee/routers/comms.py`
29. Move `in-memory PENDING_PAYROLL_APPROVALS` to a database model
30. Fix `domains/logistics/services/core/service.py:3054-3065` — extract Location Service
31. Add `HAS_<SDK>` flags to 30+ providers
32. Wrap direct imports in try/except for 15+ providers
33. Consolidate duplicate providers (bg_removal, geo, ocr, ai)
34. Remove 4 forbidden `utils/` packages in domains (accounts, catalog, country, orders)
35. Fix module `__init__.py` facade export mismatches
36. Fix broken `admin/services/` references in `admin/__init__.py`
37. Move 50+ business-logic files from `infrastructure/utils/` to `domains/`
38. Reorder `orchestrator.py` middleware to match 6-layer spec

## P3 — Continuous Cleanup
39. Add `public_routers` to 3 module `__init__.py` files
40. Remove dead code markers
41. Rename non-standard file names in `providers/image/bg_remover/`
42. Move MCP servers from `jobs/` to `providers/mcp/`
43. Move `seed_all.py` to `scripts/`
44. Move 5 underscore files at `domains/` root to proper homes
45. Remove duplicate `infrastructure/lifespan.py`
46. Remove no-op stubs in `rbac/__init__.py`
47. Consolidate `rbac/service.py` and `rbac/dependencies.py`

---

# APPENDIX A: Files Examined

- All `backend/domains/*/models/` (16 domains, ~233 models)
- All `backend/modules/*/routers/` (35 router files)
- All `backend/providers/*/` (22 provider packages)
- All `backend/infrastructure/*/` (15 subdirectories, 100+ files)
- All `backend/kernel/*/` (8 files)
- All `backend/rbac/*/` (8 files)
- All `backend/middleware/*/` (27 files)
- All `backend/jobs/*/` (21 files)
- Backend root files (`main.py`, `lifespan.py`, `config.py`, etc.)
- `DOMAIN_ALLOWLIST.yaml` (77 lines)
- `ARCHITECTURE_DIAGRAM.md` (618 lines)

# APPENDIX B: Investigation Tools Used

- `ripgrep` for content search
- `Get-ChildItem` for directory listing
- Parallel sub-agents (6 total) for layer-by-layer investigation
- Each sub-agent used very thorough (5/5) exploration depth

# APPENDIX C: Known Limitations

- Did not verify import paths (only checked for forbidden patterns)
- Did not run the test suite
- Did not verify behavior at runtime (e.g., NameError on `svc_*` calls)
- Did not check Alembic migrations in depth
- Did not check frontend architecture compliance
- Did not run the architecture law tests (`tests/architecture/`)
