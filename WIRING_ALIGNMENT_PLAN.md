# WIRING ALIGNMENT PLAN — Updated

## Current State Summary

| Component | Count | Status |
|-----------|-------|--------|
| Canonical router files | 75 (15/module × 5 modules) | ✅ Consolidated |
| Extra router files | 8 | ⚠️ Need cleanup |
| Routes registered in app | 2176 | ✅ No regression |
| Actual domain services | 386 | ✅ Exist |
| Missing domain services | 142 | ❌ Need creation |
| Actual infrastructure services | 149 | ✅ Exist |
| Actual provider services | 78 | ✅ Exist |
| Broken imports in routers | ~190 | ⚠️ Need fixing |

---

## Phase 1: Fix Critical Blockers (App Can't Start)

These broken imports prevent the app from starting at all.

| # | File | Broken Import | Fix |
|---|------|--------------|-----|
| 1 | `middleware/country_context.py:39` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 2 | `middleware/coi_middleware.py:10` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 3 | `middleware/dependencies/coi_dependency.py:10` | `domains.hr.services.coi_service` | → `domains.hr.services.employees.coi_service` |
| 4 | `middleware/impossible_travel_middleware.py:156` | `domains.governance.services.security.impossible_travel_write_service` | Implement or remove |
| 5 | `middleware/impossible_travel_middleware.py:349` | `domains.governance.services.fraud.fraud_detection_service` | → `domains.security.services.fraud_detection_service` |
| 6 | `middleware/device_binding_middleware.py:69-70` | `ServiceMeshSecurity()` / `NetworkPolicy()` | Implement or remove |
| 7 | `middleware/dependencies/fraud_events.py:21` | `infrastructure.database.models.FraudEvent` | → `domains.governance.models.fraud.FraudEvent` |

### Stub Function Issues in Routers

In `admin/country.py`:
- `auto_populate_router = (lambda *a, **k: None)` → Replace with `APIRouter(prefix="...")`
- `versioning_router = (lambda *a, **k: None)` → Replace with `APIRouter(prefix="...")`

---

## Phase 2: Domain Service Stub Creation (Prioritized)

Create minimal stubs for missing domain services. Each stub returns empty data with TODO comment.

### Priority P0 (Used by 50+ routers — blocks most routes)

| Service | Routers Using | Domain | Suggested Path |
|---------|---------------|--------|----------------|
| `hr.hierarchy_service` | 135 | `domains/hr/` | `services/core/hierarchy_service.py` |
| `catalog.services.banner_controller` | 96 | `domains/catalog/` | `services/banners/banner_service.py` |
| `governance.core.approval_matrix_service` | 65 | `domains/governance/` | `services/core/approval_matrix_service.py` |
| `catalog.admin_products_service` | 26 | `domains/catalog/` | `services/products/product_admin_service.py` |
| `orders.customer_coupons_create_service` | 26 | `domains/orders/` | `services/coupons/coupon_service.py` |

### Priority P1 (Used by 10-49 routers)

| Service | Routers Using | Domain |
|---------|---------------|--------|
| `governance.models.fraud` | 6 | governance |
| `catalog.admin_promotions_service` | 13 | catalog |
| `hr.payroll_service` | 13 | hr |
| `orders.services.coupons_service` | 8 | orders |
| `orders.services.coupons_write_service` | 17 | orders |
| `finance.models.finance` | 36 | finance |
| `orders.models.orders` | 36 | orders |
| `finance.models.payments` | 34 | finance |

### Priority P2 (Used by <10 routers)

All remaining 120+ missing services. Batch create stubs.

---

## Phase 3: Import Path Remapping

Many imports reference old paths that have been restructured. Map old → new:

### Catalog Domain

| Old Import | New Path |
|------------|----------|
| `domains.catalog.services.products_controller` | `domains.catalog.services.products.product_service` |
| `domains.catalog.services.banner_controller` | `domains.catalog.services.banners.banner_service` |
| `domains.catalog.admin_products_service` | `domains.catalog.services.products.product_admin_service` |
| `domains.catalog.admin_promotions_service` | `domains.promotions.services.promotion_service` |

### Finance Domain

| Old Import | New Path |
|------------|----------|
| `domains.finance.services.finance` | `domains.finance.services.core.finance_service` |
| `domains.finance.services.ledger.sub_ledger_controller` | `domains.finance.services.ledger.sub_ledger_service` |
| `domains.finance.services.commission.commission_engine` | `domains.finance.services.commissions.commission_engine` |

### HR Domain

| Old Import | New Path |
|------------|----------|
| `domains.hr.services.hr_controller` | `domains.hr.services.core.hr_service` |
| `domains.hr.hierarchy_service` | `domains.hr.services.core.hierarchy_service` |
| `domains.hr.payroll_service` | `domains.hr.services.payroll.payroll_service` |
| `domains.hr.performance_service` | `domains.hr.services.performance.performance_service` |

### Orders Domain

| Old Import | New Path |
|------------|----------|
| `domains.orders.services.orders_controller` | `domains.orders.services.core.order_service` |
| `domains.orders.services.coupons_service` | `domains.promotions.services.coupons.coupon_service` |

### Governance Domain

| Old Import | New Path |
|------------|----------|
| `domains.governance.core.approval_matrix_service` | `domains.governance.services.core.approval_matrix_service` |
| `domains.governance.incident.incident_service` | `domains.governance.services.incident.incident_service` |
| `domains.governance.models.fraud` | `domains.governance.models.fraud` (exists, check path) |

---

## Phase 4: Frontend-Backend Path Alignment

### Problem
- Frontend uses: `/admin/products`, `/admin/orders`, etc.
- Backend has: `/api/v1/admin/catalog/...`, `/api/v1/admin/orders/...`
- Next.js rewrites send `/admin/:path*` to backend as-is
- **No routers exist at `/admin/`** — they're all at `/api/v1/admin/`

### Solution: Backend Legacy Alias Routes

Create `backend/modules/admin/routers/_legacy_aliases.py`:

```python
"""Legacy path aliases for backward compatibility with frontend."""
from fastapi import APIRouter
from . import catalog, orders, accounts, customers, promotions

legacy_router = APIRouter()

# Map legacy paths to canonical routers
legacy_router.include_router(catalog.router, prefix="/products")    # /admin/products → catalog
legacy_router.include_router(orders.router, prefix="/orders")      # /admin/orders → orders
legacy_router.include_router(accounts.router, prefix="/users")     # /admin/users → accounts
legacy_router.include_router(customers.router, prefix="/customers") # /admin/customers → customers
legacy_router.include_router(promotions.router, prefix="/coupons") # /admin/coupons → promotions
```

Register in `main.py`:
```python
from modules.admin.routers._legacy_aliases import legacy_router
app.include_router(legacy_router, prefix="/admin")
```

---

## Phase 5: Cleanup Extra Router Files

Remove or consolidate extra router files that aren't part of the canonical 15:

| Module | Extra File | Action |
|--------|------------|--------|
| admin | `core_countries_routes.py` | Keep (needed for /admin/countries) |
| admin | `public_comms_status.py` | Keep (public health endpoint) |
| employee | `cash_management_controller.py` | Merge into `finance.py` |
| employee | `chat_api.py` | Merge into `comms.py` |
| employee | `comms_chat.py` | Merge into `comms.py` |
| employee | `comms_video.py` | Merge into `comms.py` |
| employee | `email_controller.py` | Merge into `comms.py` |
| employee | `treasury_api.py` | Merge into `finance.py` |

---

## Phase 6: Validation & Testing

### Verification Steps

1. **Import check**: `python -c "from main import app"` succeeds
2. **Route count**: ≥ 2176 routes registered (no regression)
3. **Syntax check**: All 75 canonical files pass `ast.parse()`
4. **Frontend test**: `/admin/products` returns 200 (not 404)
5. **No function errors**: No "'function' object has no attribute" errors

### Success Criteria

- ✅ App boots without import errors
- ✅ Frontend API calls return valid responses
- ✅ All 2176 routes still registered
- ✅ No lambda stubs in `include_router()` calls
- ✅ All domain imports resolve to actual files

---

## Execution Order

| Phase | Description | Effort | Dependencies |
|-------|-------------|--------|--------------|
| 1 | Fix critical blockers | 2h | None |
| 2 | Create domain service stubs | 4h | Phase 1 |
| 3 | Remap import paths | 3h | Phase 2 |
| 4 | Frontend path alignment | 2h | None |
| 5 | Cleanup extra router files | 1h | Phase 3 |
| 6 | Validation | 2h | All |
| **Total** | | **14h** | |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Creating too many stubs | Hides real bugs | Mark all stubs with TODO comments |
| Frontend still broken after aliases | UX issues | Add logging, verify rewrite rules |
| Import remapping errors | App won't boot | Test each remap individually |
| Stub functions in include_router | Runtime errors | Scan all files for lambda stubs |

---

## Architecture Compliance

After this plan is executed, the architecture will match `ARCHITECTURE_DIAGRAM.md`:

```
Frontend (Next.js)
    ↓ /admin/products → /api/v1/admin/catalog
Middleware (orchestrator.py)
    ↓ 6-layer pipeline
Module Routers (modules/{m}/routers/{d}.py) — 75 files
    ↓ auth + require_feature + ONE service call
Domain Services (domains/{d}/services/) — 386+ files
    ↓ business logic
Infrastructure (infrastructure/) — 149 files
    ↓ database
PostgreSQL (one schema per domain)
```

---

## Files to Create

### Domain Service Stubs (Phase 2)
- `domains/hr/services/core/hierarchy_service.py`
- `domains/catalog/services/banners/banner_service.py`
- `domains/governance/services/core/approval_matrix_service.py`
- `domains/catalog/services/products/product_admin_service.py`
- `domains/orders/services/coupons/coupon_service.py`
- Plus ~137 more stub files

### Legacy Aliases (Phase 4)
- `modules/admin/routers/_legacy_aliases.py`

## Files to Modify

- `backend/main.py` — Register legacy aliases
- `backend/middleware/country_context.py` — Fix import path
- `backend/middleware/coi_middleware.py` — Fix import path
- `backend/middleware/dependencies/coi_dependency.py` — Fix import path
- `backend/middleware/impossible_travel_middleware.py` — Fix imports
- `backend/middleware/device_binding_middleware.py` — Fix imports
- `backend/middleware/dependencies/fraud_events.py` — Fix import
- `backend/modules/admin/routers/country.py` — Fix lambda stubs
- ~50 router files with broken imports
