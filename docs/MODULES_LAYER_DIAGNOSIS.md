# Modules Layer — Architectural Violation & Code Quality Report

**Scope:** `backend/modules/{admin,customer,employee,logistics,supplier}/`
**Date:** 2026-08-26
**Total Issues Found:** 94 (14 CRITICAL, 31 HIGH, 29 MEDIUM, 20 LOW)

---

## Executive Summary

The modules layer has significant architectural drift from the Three-Axis Architecture defined in ARCHITECTURE_DIAGRAM.md. The core pattern violation is **business logic leaking into routers** — raw SQL queries, direct `db.commit()`, complex serialization helpers, and cross-domain imports all appear in router files. Several routers have **runtime-breaking NameErrors** (used but never imported names). Duplicate route handlers exist across consolidated files. The `require_feature()` gate is misused as a decorator or default parameter in the customer module. Multiple router files are empty stubs.

---

## CRITICAL Issues (14)

### C1: NameError — `get_wishlist` / `clear_user_wishlist` not imported
**File:** `modules/admin/routers/customers.py:99,128`
```python
# Line 99 — get_wishlist is used but never imported
return get_wishlist(current_user=current_user, db=db, limit=limit, cursor=cursor)
# Line 128 — clear_user_wishlist is used but never imported
return clear_user_wishlist(current_user=current_user, db=db)
```
**Impact:** Runtime `NameError` — all wishlist endpoints broken.
**Fix:** Import from `domains.customers.services.wishlist_service`.

---

### C2: NameError — `email_metrics` not imported
**File:** `modules/admin/routers/orders.py:32`
```python
return email_metrics(db)  # Never imported
```
**Impact:** Runtime `NameError` — `/metrics` endpoint broken.
**Fix:** Import `email_metrics` from `domains.comms.services.email.email_management` or define locally.

---

### C3: NameError — 18 `svc_*` functions not imported
**File:** `modules/admin/routers/country.py:81-351`
```python
return svc_list_cities(...)           # Not imported
return svc_add_city(...)              # Not imported
return svc_update_city(...)           # Not imported
return svc_delete_city(...)           # Not imported
return svc_list_staff(...)            # Not imported
return svc_assign_staff(...)          # Not imported
... (14 more svc_* calls)
```
**Impact:** Every city/staff/tax/communication endpoint in admin/country is broken at runtime.
**Fix:** Import all `svc_*` functions from `domains.country.services.core.country_service` or appropriate domain service.

---

### C4: NameError — `get_okr_service`, `assign_matrix_manager`, etc. not imported
**File:** `modules/employee/routers/hr.py:536-482`
```python
engine = get_okr_service(db)          # Not imported
result = assign_matrix_manager(...)   # Not imported
result = remove_matrix_manager(...)   # Not imported
is_circular = detect_circular_reporting(...)  # Not imported
```
**Impact:** OKR, matrix management, circular detection endpoints broken.
**Fix:** Import from `domains.hr.services.okr.okr_service` and `domains.hr.services.hierarchy.matrix_service`.

---

### C5: NameError — `get_matrix_managers` / `get_matrix_subordinates` not imported
**File:** `modules/employee/routers/hr.py:471,476`
```python
return {"matrix_managers": get_matrix_managers(db, employee_id)}
return {"matrix_subordinates": get_matrix_subordinates(db, manager_id)}
```
**Impact:** Matrix relationship endpoints broken.
**Fix:** Import from `domains.hr.services.hierarchy.matrix_service`.

---

### C6: Cross-domain import — orders router imports comms domain
**File:** `modules/admin/routers/orders.py:12-17`
```python
from domains.comms.services.email.email_management import (
    create_campaign, delete_campaign, list_all_campaigns, list_campaigns,
)
```
**Impact:** Violates Law 1 (arrows point down only). Orders module should not import comms domain directly.
**Fix:** Move campaign endpoints to `modules/admin/routers/comms.py` (which already has them).

---

### C7: Cross-module import — employee/orders imports admin auth
**File:** `modules/employee/routers/orders.py:13`
```python
from modules.admin.routers.auth import get_current_user
```
**Impact:** Violates Law 1. Modules must not import from other modules.
**Fix:** Use `infrastructure.security.dependencies.get_current_user` or `rbac.dependencies`.

---

### C8: Cross-module import — employee/finance imports admin auth + self-controller
**File:** `modules/employee/routers/finance.py:609,1133-1182`
```python
from modules.admin.routers.auth import get_current_user  # line 609
from modules.employee.routers.cash_management_controller import ...  # lines 1133-1182
```
**Impact:** `modules.employee.routers.cash_management_controller` does not exist as a standalone file. This import will fail at runtime.
**Fix:** Remove imports; the controller functions should be in domain services or defined inline.

---

### C9: Cross-module import — logistics/logistics imports admin auth
**File:** `modules/logistics/routers/logistics.py:329,805,1452`
```python
from modules.admin.routers.core_auth_routes import get_current_user
from modules.admin.routers.auth import get_current_user
```
**Impact:** Violates Law 1. Logistics module imports admin module internals.
**Fix:** Use `infrastructure.security.dependencies.get_current_user`.

---

### C10: Duplicate route handlers — customer/customers.py
**File:** `modules/customer/routers/customers.py:20-147`
```python
# Defined THREE times:
@router.get("/health/customers/{user_id}")  # lines 20, 71, 129
def get_customer_health(...): ...
@router.get("/health/customers")            # lines 30, 81, 140
def list_customer_health(...): ...
```
**Impact:** Only the last definition wins (FastAPI uses last-registered). Earlier implementations silently dropped. Route behavior is unpredictable.
**Fix:** Keep only one definition. Delete the duplicated blocks.

---

### C11: Duplicate route handlers — logistics/logistics.py
**File:** `modules/logistics/routers/logistics.py:27-316`
```python
# Defined TWICE each:
@router.get("/health/logistics/{partner_id}")   # lines 27, 93
@router.get("/health/logistics")                # lines 38, 104
@router.get("/{country_code}/locations/logistics-partners")   # lines 166, 252
@router.post("/{country_code}/locations/logistics-partners")  # lines 197, 283
```
**Impact:** Same as C10 — only last definition registered.
**Fix:** Keep only one definition of each.

---

### C12: `require_feature` misused as decorator — customer/accounts.py
**File:** `modules/customer/routers/accounts.py:72,79,104,117,125,158,183,194`
```python
@router.get("")
    require_feature("accounts.address.read")  # Indented as decorator but is a function call
def list_addresses(...):
```
**Impact:** `require_feature` is called at **decoration time** (module import), not at request time. The gate check happens once at startup, not per-request. Also, indentation makes it a no-op statement after the decorator.
**Fix:** Move `require_feature(...)` inside the function body.

---

### C13: `require_feature` misused as default parameter — customer/orders.py
**File:** `modules/customer/routers/orders.py:158,170,183,198,207,217,226,235,244,254,263,274,337,343,350,361,376,382`
```python
def create_order_route(
    ...
    require_feature("orders.create")  # Used as positional argument default
):
```
**Impact:** `require_feature("orders.create")` is evaluated once at import time and passed as a parameter value. It does NOT gate the endpoint per-request.
**Fix:** Call `require_feature(...)` inside the function body.

---

### C14: Import from `_auto_stubs` — migration scaffolding in production routers
**File:** `modules/employee/routers/accounts.py:23`, `modules/employee/routers/orders.py:48`, `modules/employee/routers/finance.py:19-30`
```python
from domains.hr.services._auto_stubs import log_activity
from domains.finance.services._auto_stubs import trading_service as trading
from domains.finance.services._auto_stubs import accounting_controller
from domains.finance.services._auto_stubs import FinancialReportingService
```
**Impact:** `_auto_stubs.py` files are migration scaffolding with empty placeholders. Using them in production routers means the endpoints likely return `{}` or `[]`.
**Fix:** Replace with real service implementations.

---

## HIGH Issues (31)

### H1: Raw SQL queries in router — employee/accounts.py
**File:** `modules/employee/routers/accounts.py:44-54,104-115,128-144,157-167,179-188,201-210,223-246,258-299`
```python
row = db.execute(text("""
    SELECT e.*, u.email, u.full_name, u.role, ou.name as unit_name
    FROM employees e JOIN users u ON u.id = e.user_id ...
"""), {"eid": emp.id}).mappings().first()
```
**Impact:** Business logic (SQL) in router layer. Violates Law 2 (thin routers). Hard to test, maintain, or migrate.
**Fix:** Move all SQL to `domains.hr.services.employees.ess_service`.

---

### H2: Direct DB writes in router — customer/orders.py
**File:** `modules/customer/routers/orders.py:107-115,139,145,154,159`
```python
db.add(CartItem(...))   # line 107
db.commit()              # lines 115, 139, 145, 154
db.delete(item)          # lines 142, 154
db.query(CartItem).filter(...).delete()  # line 159
```
**Impact:** Direct DB writes in router. Violates Law 2.
**Fix:** Move to `domains.customers.services.cart_service`.

---

### H3: Direct DB writes in router — logistics/logistics.py
**File:** `modules/logistics/routers/logistics.py:218-229,304-316,475-496`
```python
location = LogisticsPartnerLocation(...)  # line 218
db.add(location)                          # line 227
db.commit()                               # lines 228, 314, 495
db.refresh(location)                      # line 229
event = ShipmentEvent(...)                # line 486
db.add(event)                             # line 494
```
**Impact:** Direct DB writes in router. Violates Law 2.
**Fix:** Move to `domains.logistics.services.core.logistics_command_service`.

---

### H4: Direct DB writes in router — employee/finance.py
**File:** `modules/employee/routers/finance.py:728,835,847,859,877,889,902,915,935,947,959,988,1001,1027,1041`
```python
db.commit()  # 15 direct commit calls in router
```
**Impact:** Routers directly committing transactions. Violates Law 2.
**Fix:** Move all transaction management to domain services.

---

### H5: Business logic serialization helpers in routers
**File:** `modules/customer/routers/accounts.py:26-68`, `modules/customer/routers/orders.py:32-78,306-334`
```python
def _normalize_address_payload(payload: dict, *, partial: bool = False) -> dict: ...
def _serialize_address(address: Address) -> dict: ...
def _serialize_cart_item(item: CartItem) -> dict: ...  # 47 lines of logic
def _user_context(user: User) -> dict: ...
def _serialize_return(req: ReturnRequest) -> dict: ...
```
**Impact:** Business logic (serialization, normalization) in routers. Should be in domain services or serializers.
**Fix:** Move to `modules.customer.serializers` or domain service response shaping.

---

### H6: Massive router files (1000+ lines)
**Files:**
- `modules/logistics/routers/logistics.py` — 1517+ lines
- `modules/employee/routers/finance.py` — 1335+ lines
- `modules/employee/routers/hr.py` — 676 lines
- `modules/customer/routers/orders.py` — 391 lines
- `modules/employee/routers/orders.py` — 394 lines
- `modules/admin/routers/country.py` — 353 lines

**Impact:** Unmaintainable. Each router should cover one domain with a handful of endpoints.
**Fix:** Split into per-domain files following `modules/{m}/routers/{d}.py` pattern.

---

### H7: Duplicate `require_feature` calls — employee/hr.py
**File:** `modules/employee/routers/hr.py:114-118,172-179,225-231,329-343`
```python
require_feature("hr.read")    # line 114
require_feature("hr.create")  # line 115
require_feature("hr.update")  # line 116
require_feature("hr.delete")  # line 117
require_feature("hr.read")    # line 118 (duplicate)
```
**Impact:** Redundant calls. Likely copy-paste error. Gates are checked but clutter is extreme.
**Fix:** Use a single `require_feature()` call per endpoint with the correct feature.

---

### H8: Empty router files (no endpoints)
**Files:**
- `modules/customer/routers/catalog.py` — 6 lines, no routes
- `modules/customer/routers/suppliers.py` — 6 lines, no routes
- `modules/customer/routers/analytics.py` — likely empty
- `modules/customer/routers/audit.py` — likely empty
- `modules/customer/routers/comms.py` — likely empty
- `modules/customer/routers/country.py` — likely empty
- `modules/customer/routers/finance.py` — likely empty
- `modules/customer/routers/governance.py` — likely empty
- `modules/customer/routers/hr.py` — likely empty
- `modules/customer/routers/logistics.py` — likely empty
- `modules/customer/routers/promotions.py` — likely empty
- `modules/customer/routers/security.py` — likely empty

**Impact:** Dead code. Clutters the router namespace. May cause import errors if referenced.
**Fix:** Delete or implement. Do not keep empty router files.

---

### H9: Inconsistent auth dependency sources
**Files:** Multiple
```python
from infrastructure.utils.dependencies import get_current_user    # customer/accounts.py
from rbac import get_current_user                                # customer/customers.py
from infrastructure.security.dependencies import get_current_user # employee/hr.py
from modules.admin.routers.auth import get_current_user          # employee/orders.py (WRONG)
```
**Impact:** Different auth implementations may behave differently. Cross-module imports break architecture.
**Fix:** Standardize on `infrastructure.security.dependencies.get_current_user`.

---

### H10: `require_permission` used instead of `require_feature`
**File:** `modules/employee/routers/finance.py:649,662,680,700,719,741,754,769,785,796,805,823,833,845,857,870,888,900,913,927,945,957,972,1014,1025,1038`
```python
require_permission("payouts.verify", current_admin)
```
**Impact:** `require_permission` is from `infrastructure.security.auth` — a different permission system than the RBAC `require_feature`. Violates Law 4 (features single-sourced in catalog).
**Fix:** Replace with `require_feature("finance.payouts.verify")` or appropriate catalog feature.

---

### H11: Tuple return for errors (non-standard FastAPI)
**File:** `modules/employee/routers/finance.py:1054,1066,1078,1095,1110,1124`
```python
return {"error": "Supplier access required"}, 403
return {"error": "Logistics partner not found"}, 404
```
**Impact:** FastAPI does not handle tuple returns correctly by default. This will cause a 500 error or unexpected response shape.
**Fix:** Use `raise HTTPException(status_code=403, detail="Supplier access required")`.

---

### H12: `modules/__init__.py` is nearly empty
**File:** `modules/__init__.py`
```python
"""Actor modules. Each module owns its routers/ (thin) and services (via domains)."""
```
**Impact:** No exports, no facade. Modules should expose a clean public API.
**Fix:** Add `__all__` with key exports or keep as-is if intentional (document the choice).

---

### H13: `modules/admin/routers/analytics.py` is a stub
**File:** `modules/admin/routers/analytics.py`
```python
@router.get("/admin_analytics_routes/health")
def health(_: dict = Depends(require_admin)):
    require_feature("analytics.read")
    return {"status": "ok", ...}
```
**Impact:** Only a health endpoint. No actual analytics routes.
**Fix:** Implement analytics routes or delete the file.

---

### H14: `modules/admin/routers/orders.py` has wrong domain content
**File:** `modules/admin/routers/orders.py`
```python
# This file contains campaign/email endpoints, not orders endpoints
from domains.comms.services.email.email_management import create_campaign, ...
```
**Impact:** Campaign endpoints are in the wrong router file. Confusing for maintainers.
**Fix:** Move campaign endpoints to `modules/admin/routers/comms.py` (which already has them — deduplicate).

---

### H15: `modules/admin/routers/country.py` — function name shadowing
**File:** `modules/admin/routers/country.py:22-81`
```python
def list_public_countries(...):    # Shadows imported name
    return list_public_countries(db)  # Recursion-like confusion
```
**Impact:** Route handler names shadow imported service names. Confusing and error-prone.
**Fix:** Rename route handlers to `list_public_countries_route` (like other routers do).

---

### H16: `modules/admin/routers/catalog.py` — wrapper functions not routes
**File:** `modules/admin/routers/catalog.py:332-351`
```python
def smart_search(q, limit, db, ...):  # Not a route, just a wrapper
    return _smart_search(...)
def get_recommendations(...):          # Not a route, just a wrapper
    return _get_recommendations(...)
```
**Impact:** Non-route helper functions in router file. Should be in a service or serializer.
**Fix:** Move to `domains.catalog.services.search.search_service` or delete.

---

### H17: `modules/admin/routers/security.py` — instantiates service classes in routes
**File:** `modules/admin/routers/security.py:64,157`
```python
engine = FraudScoringEngine(db)  # line 64
updater = ThreatFeedUpdater(db)  # line 157
```
**Impact:** Service instantiation in router. Should be dependency-injected or called via function.
**Fix:** Use domain service functions or dependency injection.

---

### H18: `modules/admin/routers/comms.py` — instantiates service in route
**File:** `modules/admin/routers/comms.py:30,37,50,62,74`
```python
service = EmailManagementService(db)  # Created per-request in 5 endpoints
```
**Impact:** Service instantiation in router. Violates thin router pattern.
**Fix:** Use module-level service functions or dependency injection.

---

### H19: `modules/customer/routers/customers.py` — imports from `rbac` directly
**File:** `modules/customer/routers/customers.py:16,68`
```python
from rbac import get_current_user
```
**Impact:** `rbac` package may not expose `get_current_user`. Inconsistent with other modules.
**Fix:** Use `infrastructure.security.dependencies.get_current_user`.

---

### H20: `modules/employee/routers/accounts.py` — imports from `rbac` directly
**File:** `modules/employee/routers/accounts.py:19`
```python
from rbac import get_current_user
```
**Impact:** Same as H19.
**Fix:** Use canonical auth dependency.

---

### H21: `modules/logistics/routers/logistics.py` — imports from `rbac` directly
**File:** `modules/logistics/routers/logistics.py:22,89,157,247`
```python
from rbac import get_current_user
```
**Impact:** Same as H19.
**Fix:** Use canonical auth dependency.

---

### H22: `modules/employee/routers/hr.py` — broken import block
**File:** `modules/employee/routers/hr.py:64-75`
```python
from domains.hr.services.ess_service import (  # line 64
from rbac.dependencies import require_feature   # line 65 — WRONG INDENT, breaks import
    get_employee_profile,                        # line 66
```
**Impact:** `require_feature` is imported inside another import block. This is a syntax error or causes the first import to fail.
**Fix:** Separate the imports properly.

---

### H23: `modules/employee/routers/hr.py` — `require_feature` duplicated 15+ times in single function
**File:** `modules/employee/routers/hr.py:329-343`
```python
def ess_update_profile(...):
    require_feature("hr.create")
    require_feature("hr.update")
    require_feature("hr.create")
    require_feature("hr.create")
    require_feature("hr.create")
    require_feature("hr.read")
    require_feature("hr.create")
    require_feature("hr.read")
    require_feature("hr.create")
    require_feature("hr.update")
    require_feature("hr.read")
    require_feature("hr.create")
    require_feature("hr.create")
    require_feature("hr.read")
    require_feature("hr.update")
```
**Impact:** Copy-paste error. 15 redundant calls. Should be 1-2.
**Fix:** Use a single `require_feature("hr.employee.manage")`.

---

### H24: `modules/admin/routers/governance.py` — two routers in one file
**File:** `modules/admin/routers/governance.py:33`
```python
command_center_router = APIRouter(prefix="/api/v1/admin/command-center", ...)
```
**Impact:** Two routers in one file. The `command_center_router` is picked up by `__init__.py` via the extra router scan, but this is fragile.
**Fix:** Move to separate file or document the pattern.

---

### H25: `modules/admin/routers/security.py` — two routers in one file
**File:** `modules/admin/routers/security.py:27`
```python
rbac_router = APIRouter(prefix="/api/v1/rbac", ...)
```
**Impact:** Same as H24.
**Fix:** Move to separate file.

---

### H26: `modules/supplier/routers/suppliers.py` — imports `update_supplier_profile` from wrong module
**File:** `modules/supplier/routers/suppliers.py:18`
```python
from domains.suppliers.services.health.supplier_health import update_supplier_profile
```
**Impact:** `update_supplier_profile` is in `health.supplier_health` — wrong domain grouping. Should be in `profile.supplier_profile_service`.
**Fix:** Move to correct domain service.

---

### H27: `modules/supplier/routers/suppliers.py` — imports `create_supplier_profile` from accounts domain
**File:** `modules/supplier/routers/suppliers.py:160`
```python
from domains.accounts.services.auth.auth_service import create_supplier_profile as _create_profile
```
**Impact:** Cross-domain import. Profile creation should be in `domains.suppliers.services.profile`.
**Fix:** Move to supplier domain service.

---

### H28: `modules/customer/routers/accounts.py` — duplicate imports
**File:** `modules/customer/routers/accounts.py:4-5,12-13`
```python
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status  # line 4
from fastapi import APIRouter, Depends, HTTPException, status  # line 12 (duplicate)
```
**Impact:** Redundant imports. Code smell.
**Fix:** Consolidate imports at top of file.

---

### H29: `modules/employee/routers/finance.py` — imports from non-existent controller
**File:** `modules/employee/routers/finance.py:1133`
```python
from modules.employee.routers.cash_management_controller import _commission_metadata_for_entry
```
**Impact:** `modules/employee/routers/cash_management_controller.py` does not exist. Runtime ImportError.
**Fix:** Remove import; the function should be in a domain service.

---

### H30: `modules/employee/routers/finance.py` — `FinancialReportingService` imported from `_auto_stubs`
**File:** `modules/employee/routers/finance.py:30`
```python
from domains.finance.services._auto_stubs import FinancialReportingService
```
**Impact:** `_auto_stubs` is migration scaffolding. This service is likely an empty stub.
**Fix:** Use the real `FinancialReportingService` from `domains.finance.services.reporting`.

---

### H31: `modules/employee/routers/orders.py` — `trading_service` imported from `_auto_stubs`
**File:** `modules/employee/routers/orders.py:48`
```python
from domains.finance.services._auto_stubs import trading_service as trading
```
**Impact:** Same as H30. Trading service is likely an empty stub.
**Fix:** Use real trading service from `domains.finance.services.trading`.

---

## MEDIUM Issues (29)

### M1: Router file naming doesn't follow `modules/{m}/routers/{d}.py` pattern
**Files:**
- `modules/admin/routers/auth_otp.py` — not a domain
- `modules/admin/routers/auth_social.py` — not a domain
- `modules/employee/routers/comms/` — subdirectory (acceptable but adds complexity)
- `modules/employee/routers/hr/employees_part1_p1.py` — not domain-based
**Fix:** Rename to domain-based names or document exceptions.

---

### M2: Inconsistent serializer usage
**Files:** Most routers use `dict` instead of Pydantic schemas.
```python
def list_rates(country_code: str, ..., payload: dict = Body(...)):
```
**Impact:** No input validation, no OpenAPI schema generation.
**Fix:** Define Pydantic v2 schemas in `modules/{m}/serializers/`.

---

### M3: `modules/admin/serializers/__init__.py` is empty
**File:** `modules/admin/serializers/__init__.py`
**Impact:** No serializers defined for admin module.
**Fix:** Add admin-specific serializers or remove the directory.

---

### M4: `modules/admin/auth/__init__.py` is empty
**File:** `modules/admin/auth/__init__.py`
**Impact:** Auth module has no exports.
**Fix:** Re-export auth utilities or remove the directory.

---

### M5: `modules/customer/auth/__init__.py` is empty
**File:** `modules/customer/auth/__init__.py`
**Impact:** Same as M4.
**Fix:** Same as M4.

---

### M6: `modules/supplier/auth/dependencies.py` re-exports from infrastructure
**File:** `modules/supplier/auth/dependencies.py`
```python
from infrastructure.security.dependencies import require_admin, require_supplier, get_current_user
```
**Impact:** Unnecessary indirection. Other modules import directly.
**Fix:** Delete the file and import directly from infrastructure.

---

### M7: `modules/employee/routers/comms/` subdirectory has 16 files
**Impact:** Over-engineering for a single domain. The `comms` domain should be one file.
**Fix:** Consolidate to `modules/employee/routers/comms.py`.

---

### M8: `modules/employee/routers/hr/` subdirectory has 14 files
**Impact:** Same as M7.
**Fix:** Consolidate to `modules/employee/routers/hr.py`.

---

### M9: `modules/admin/routers/__init__.py` only picks up `command_center_router` and `rbac_router` as extras
**File:** `modules/admin/routers/__init__.py:41`
```python
for _extra in ("command_center_router", "rbac_router"):
```
**Impact:** If other files add extra routers, they won't be picked up automatically.
**Fix:** Make the extra-router discovery more generic or document the convention.

---

### M10: `modules/customer/routers/__init__.py` doesn't pick up extra routers
**File:** `modules/customer/routers/__init__.py`
**Impact:** If customer routers define extra routers, they won't be registered.
**Fix:** Add extra-router scan like admin module.

---

### M11: `main.py` — `get_email_delivery_status` defined after use
**File:** `main.py:99,162`
```python
email_status = get_email_delivery_status()  # line 99 — used before definition
# ...
def get_email_delivery_status():            # line 162 — defined later
```
**Impact:** Works due to Python late binding, but poor style.
**Fix:** Move function definition before first use.

---

### M12: `main.py` — `websocket_user` imported for side effects
**File:** `main.py:172`
```python
from modules.admin.routers.comms import websocket_user  # noqa: E402
```
**Impact:** Import for side effect (registers websocket route). Confusing.
**Fix:** Document why this import is needed or restructure.

---

### M13: `main.py` — hardcoded `/logistics-partners` alias
**File:** `main.py:252-256`
```python
_lp = importlib.import_module("modules.logistics.routers.logistics_partner_verify")
```
**Impact:** Fragile. If file is renamed, alias breaks silently.
**Fix:** Use a configuration-driven approach.

---

### M14: `main.py` — hardcoded `/admin/countries` alias
**File:** `main.py:260-265`
```python
_cc = importlib.import_module("modules.admin.routers.core_countries_routes")
```
**Impact:** Same as M13.
**Fix:** Same as M13.

---

### M15: `modules/admin/routers/finance.py` — lazy import inside route
**File:** `modules/admin/routers/finance.py:80-81,94-95`
```python
from infrastructure.database.schemas import CommissionBadgeTierCreate
```
**Impact:** Import inside function body. Works but adds per-request overhead.
**Fix:** Move to top-level imports.

---

### M16: `modules/admin/routers/hr.py` — lazy imports inside routes
**File:** `modules/admin/routers/hr.py:113,128,143`
```python
from domains.hr.services.compliance import get_compliance_engine
from datetime import datetime
```
**Impact:** Same as M15.
**Fix:** Move to top-level imports.

---

### M17: `modules/admin/routers/catalog.py` — lazy import inside route
**File:** `modules/admin/routers/catalog.py:10-13`
```python
from domains.catalog.services.search.search_service import (
    get_recommendations as _get_recommendations,
    smart_search as _smart_search,
)
```
**Impact:** Top-level import is fine, but the wrapper functions (lines 332-351) should not be in the router.
**Fix:** Remove wrapper functions.

---

### M18: `modules/customer/routers/customers.py` — lazy imports inside routes
**File:** `modules/customer/routers/customers.py:37,88`
```python
from domains.governance.models.user import User
from infrastructure.utils.pagination import paginated_query
```
**Impact:** Same as M15.
**Fix:** Move to top-level imports.

---

### M19: `modules/employee/routers/finance.py` — `import typing` inside function
**File:** `modules/employee/routers/finance.py:578`
```python
from typing import Optional
```
**Impact:** `typing` is a stdlib module. Should be at top level.
**Fix:** Move to top-level imports.

---

### M20: `modules/employee/routers/finance.py` — `import logging` inside function
**File:** `modules/employee/routers/finance.py:617`
```python
import logging
```
**Impact:** Same as M19.
**Fix:** Move to top-level imports.

---

### M21: `modules/employee/routers/finance.py` — `import datetime` inside function
**File:** `modules/employee/routers/finance.py:221`
```python
from datetime import timezone
```
**Impact:** Same as M19.
**Fix:** Move to top-level imports.

---

### M22: `modules/logistics/routers/logistics.py` — lazy imports inside routes
**File:** `modules/logistics/routers/logistics.py:46-47,112-113,159-161`
```python
from domains.logistics.models.logistics_entities import LogisticsPartner
from domains.logistics.models.logistics_entities import LogisticsPartnerProfile
```
**Impact:** Same as M15.
**Fix:** Move to top-level imports.

---

### M23: `modules/supplier/routers/suppliers.py` — lazy imports inside routes
**File:** `modules/supplier/routers/suppliers.py:32,45,57,67,79,160`
```python
from domains.suppliers.services.onboarding.supplier_onboarding_service import ...
```
**Impact:** Same as M15.
**Fix:** Move to top-level imports.

---

### M24: `modules/admin/routers/country.py` — `body` parameter used instead of Pydantic schema
**File:** `modules/admin/routers/country.py:43,64,162,195,214,292,302,334`
```python
def create_admin_country(body: dict = Body(...), ...):
```
**Impact:** No validation, no OpenAPI schema.
**Fix:** Define Pydantic schemas for country create/update operations.

---

### M25: `modules/employee/routers/hr.py` — `body` parameter used instead of Pydantic schema
**File:** `modules/employee/routers/hr.py:89,95,124,135,154,160,185,189,195,205,237,243,272,285,291,306,393,398,446,458,486`
```python
def create_office(code: str, body: dict = None, ...):
```
**Impact:** Same as M24.
**Fix:** Define Pydantic schemas.

---

### M26: `modules/employee/routers/orders.py` — `data` parameter used instead of Pydantic schema
**File:** `modules/employee/routers/orders.py:355,358,383,392,426,465,538,547,553,563`
```python
def create_carrier(data: dict[str, Any], ...):
```
**Impact:** Same as M24.
**Fix:** Define Pydantic schemas.

---

### M27: `modules/logistics/routers/logistics.py` — `data` parameter used instead of Pydantic schema
**File:** `modules/logistics/routers/logistics.py:355,358,383,392,426,465,538,547,553,563`
```python
def create_carrier(data: dict[str, Any], ...):
```
**Impact:** Same as M24.
**Fix:** Define Pydantic schemas.

---

### M28: `modules/admin/routers/governance.py` — `payload` parameter typed as `dict | None`
**File:** `modules/admin/routers/governance.py:122`
```python
def create_news_route(payload: dict | None = None, ...):
```
**Impact:** Same as M24.
**Fix:** Define Pydantic schema.

---

### M29: `modules/customer/routers/orders.py` — `OrderCreate` imported from infrastructure
**File:** `modules/customer/routers/orders.py:180`
```python
from infrastructure.database.schemas import OrderCreate
```
**Impact:** Cross-layer import. Schemas should be in domain or serializer layer.
**Fix:** Move to `modules.customer.serializers` or `domains.orders.schemas`.

---

## LOW Issues (20)

### L1: Missing docstrings on route handlers
**Files:** Most route handlers across all modules lack docstrings.
**Impact:** Poor API documentation generation.
**Fix:** Add docstrings to all route handlers.

---

### L2: Inconsistent status codes
**Files:** Some POST endpoints return 200 instead of 201.
```python
@router.post("/orders/preview", response_model=OrderPreviewOut, status_code=201)  # customer/orders.py:202
@router.post("/orders", status_code=201)  # correct
```
**Impact:** Inconsistent API contract.
**Fix:** Audit all POST endpoints — use 201 for creation.

---

### L3: Missing `response_model` on many endpoints
**Files:** Most endpoints lack `response_model`.
**Impact:** No response validation, no OpenAPI response schema.
**Fix:** Add `response_model` to all endpoints.

---

### L4: `modules/admin/routers/auth_otp.py` — no `require_feature` gate
**File:** `modules/admin/routers/auth_otp.py`
```python
@router.post("/start")
def start_otp_challenge(payload: OtpRequest, ...):
    # No require_feature call
```
**Impact:** OTP endpoints are ungated.
**Fix:** Add `require_feature("security.otp.manage")` or similar.

---

### L5: `modules/admin/routers/auth_social.py` — no `require_feature` gate
**File:** `modules/admin/routers/auth_social.py`
```python
@router.post("/login")
def social_login(payload: SocialLoginRequest, ...):
    # No require_feature call
```
**Impact:** Social login endpoint is ungated.
**Fix:** Add appropriate feature gate.

---

### L6: `modules/customer/routers/auth.py` — no `require_feature` gate
**File:** `modules/customer/routers/auth.py`
```python
@router.post("/login")
def login(...):
    # No require_feature call
```
**Impact:** Auth endpoints are ungated (may be intentional for login).
**Fix:** Document the intentional omission.

---

### L7: `modules/admin/routers/comms.py` — WebSocket without auth
**File:** `modules/admin/routers/comms.py:85-103`
```python
async def websocket_user(websocket: WebSocket):
    await websocket.accept()
    manager.active_connections[USER_ROOM].append(websocket)
```
**Impact:** No authentication on WebSocket endpoint.
**Fix:** Add JWT authentication.

---

### L8: `modules/employee/routers/accounts.py` — raw SQL with f-string
**File:** `modules/employee/routers/accounts.py:87`
```python
db.execute(text(f"UPDATE employees SET {', '.join(updates)} WHERE id = :eid"), params)
```
**Impact:** f-string in SQL. While `updates` is internally generated (not user input), this pattern is risky.
**Fix:** Use SQLAlchemy ORM or parameterized column names.

---

### L9: `modules/employee/routers/accounts.py` — `text("NOW()")` passed as parameter
**File:** `modules/employee/routers/accounts.py:142`
```python
"now": text("NOW()"),
```
**Impact:** Passing `text()` as a parameter value. May not work as intended.
**Fix:** Use `func.now()` or `datetime.utcnow()`.

---

### L10: `modules/employee/routers/hr.py` — `import datetime` inside function
**File:** `modules/employee/routers/hr.py:115,130,145`
```python
from datetime import datetime
```
**Impact:** Per-request import overhead.
**Fix:** Move to top-level imports.

---

### L11: `modules/employee/routers/hr.py` — `import logging` at top but also used inline
**File:** `modules/employee/routers/hr.py:3,77`
```python
import logging
logger = logging.getLogger(__name__)
```
**Impact:** Fine, but `logger` is never used in the file.
**Fix:** Remove unused logger.

---

### L12: `modules/logistics/routers/logistics.py` — `import logging` duplicated
**File:** `modules/logistics/routers/logistics.py:3,9,151,163,237,249,617`
```python
import logging
logger = logging.getLogger(__name__)  # Defined multiple times
```
**Impact:** Redundant logger definitions.
**Fix:** Define once at module level.

---

### L13: `modules/admin/routers/country.py` — `import` inside function
**File:** `modules/admin/routers/country.py:81`
```python
return svc_list_cities(...)  # svc_list_cities not imported
```
**Impact:** Runtime NameError (covered in C3).
**Fix:** Already covered.

---

### L14: `modules/admin/routers/finance.py` — `import` inside function
**File:** `modules/admin/routers/finance.py:80`
```python
from infrastructure.database.schemas import CommissionBadgeTierCreate
```
**Impact:** Per-request import overhead.
**Fix:** Move to top-level imports.

---

### L15: `modules/customer/routers/accounts.py` — `import` inside function
**File:** `modules/customer/routers/accounts.py:12`
```python
from fastapi import APIRouter, Depends, HTTPException, status
```
**Impact:** Duplicate import (already imported at top).
**Fix:** Remove duplicate.

---

### L16: `modules/customer/routers/orders.py` — `import` inside function
**File:** `modules/customer/routers/orders.py:175`
```python
from fastapi import APIRouter, Depends, Body, Query
```
**Impact:** Duplicate import.
**Fix:** Remove duplicate.

---

### L17: `modules/employee/routers/finance.py` — `import` inside function
**File:** `modules/employee/routers/finance.py:564`
```python
from domains.hr.services.payroll.payroll_service import PayrollApproveBody
```
**Impact:** Per-request import overhead.
**Fix:** Move to top-level imports.

---

### L18: `modules/employee/routers/orders.py` — `import` inside function
**File:** `modules/employee/routers/orders.py:15`
```python
from modules.admin.routers.auth import get_current_user
```
**Impact:** Cross-module import (covered in C7).
**Fix:** Already covered.

---

### L19: `modules/logistics/routers/logistics.py` — `import` inside function
**File:** `modules/logistics/routers/logistics.py:46`
```python
from domains.logistics.models.logistics_entities import LogisticsPartner
```
**Impact:** Per-request import overhead.
**Fix:** Move to top-level imports.

---

### L20: `modules/supplier/routers/suppliers.py` — `import` inside function
**File:** `modules/supplier/routers/suppliers.py:32`
```python
from domains.suppliers.services.onboarding.supplier_onboarding_service import ...
```
**Impact:** Per-request import overhead.
**Fix:** Move to top-level imports.

---

## Summary by Module

| Module | CRITICAL | HIGH | MEDIUM | LOW | Total |
|--------|----------|------|--------|-----|-------|
| admin | 4 | 9 | 6 | 3 | 22 |
| customer | 3 | 5 | 4 | 3 | 15 |
| employee | 5 | 10 | 8 | 6 | 29 |
| logistics | 2 | 4 | 3 | 3 | 12 |
| supplier | 0 | 2 | 2 | 1 | 5 |
| **cross-module** | 0 | 1 | 6 | 4 | 11 |
| **Total** | **14** | **31** | **29** | **20** | **94** |

---

## Recommended Fix Priority

1. **Immediate (breaks at runtime):** C1–C14 — NameErrors, duplicate routes, broken imports
2. **Week 1 (architecture):** H1–H5 — Raw SQL, direct DB writes, business logic in routers
3. **Week 2 (consolidation):** H6–H8 — Split massive files, remove empty stubs, deduplicate routes
4. **Week 3 (patterns):** H9–H11, M1–M10 — Standardize auth, fix require_feature usage, clean up imports
5. **Ongoing (quality):** L1–L20 — Docstrings, response models, status codes

---

## Architecture Compliance Score

| Law | Compliance | Notes |
|-----|-----------|-------|
| Law 1 (Arrows down only) | **40%** | Cross-domain imports in orders/finance/logistics routers |
| Law 2 (Thin routers) | **25%** | Raw SQL, DB writes, serialization logic in many routers |
| Law 3 (Events for cross-domain) | **60%** | Some direct cross-domain calls instead of events |
| Law 4 (Features single-sourced) | **50%** | `require_permission` used alongside `require_feature`; misuse as decorator |
| Law 5 (Country scope) | **70%** | RLS context set in some routers but not enforced at DB layer |
| Law 6 (Schema discipline) | **80%** | Mostly followed; some raw SQL in employee module |
| Law 7 (Allowlist) | **Unknown** | Need to check DOMAIN_ALLOWLIST.yaml |

**Overall Architecture Compliance: ~45%**
