# Router System Correction Plan

> Generated: 2026-08-25
> Scope: Consolidate 476 router files → 75 (15 domain routers × 5 modules)
> Goal: Fix all broken imports, eliminate duplicates, enforce thin-router pattern

---

## 1 · Current State Analysis

### 1.1 Router Count by Module

| Module | Files On Disk | Registered in `__init__.py` | Unregistered (Dead) | Target |
|--------|--------------|---------------------------|---------------------|--------|
| admin | 270 | 228 | 42 | 15 |
| customer | 44 | 12 | 32 | 15 |
| employee | 80 | 50 | 30 | 15 |
| logistics | 32 | 12 | 20 | 15 |
| supplier | 50 | 25 | 25 | 15 |
| **TOTAL** | **476** | **327** | **149** | **75** |

### 1.2 The Core Problem

The **admin module** is a "god module" — its 228 registered routers cover every domain. This means:
- Admin routers duplicate logic that exists in other modules
- Endpoint ownership is unclear (is product admin in `admin/` or `supplier/`?)
- 149 router files are dead code (exist on disk but never imported)
- Cross-module route prefix conflicts are likely

### 1.3 Endpoint Patterns Found

| Pattern | Example | Count |
|---------|---------|-------|
| No prefix (relies on registration) | Most admin routers | ~300 |
| `/api/v1/admin/` prefix | admin_admin_*.py files | ~50 |
| `/api/v1/customer/` prefix | customer cart, coupons, etc. | ~10 |
| `/api/v1/employee/` prefix | employee comms | ~5 |
| `/api/v1/parcel-tracking/` prefix | logistics parcel_tracking | 1 |
| `/shipments` prefix | logistics shipments | 1 |
| `/users` prefix | admin users | 1 |

---

## 2 · Target Architecture

### 2.1 Domain Router Files (15 per module)

Each module gets exactly 15 router files — one per business domain:

| # | File Name | Domain | Admin Router Covers | Customer Router Covers |
|---|-----------|--------|--------------------|-----------------------|
| 1 | `accounts.py` | accounts | User CRUD, roles, permissions | My profile, login, sessions |
| 2 | `analytics.py` | analytics | Dashboard, reports, metrics | My activity stats |
| 3 | `audit.py` | audit | Audit logs, compliance trails | — (admin-only) |
| 4 | `catalog.py` | catalog | Products, categories, search, variants, uploads | Browse products, categories, search |
| 5 | `comms.py` | comms | Chat, email, tickets, notifications | Chat support, notifications |
| 6 | `country.py` | country | Country config, legal, tax | Country detection, localization |
| 7 | `customers.py` | customers | Customer insights, verification | My account, health |
| 8 | `finance.py` | finance | Ledger, payments, payouts, treasury | My wallet, transactions |
| 9 | `governance.py` | governance | Permissions, fraud, risk, compliance | — (admin-only) |
| 10 | `hr.py` | hr | Employees, payroll, hierarchy | — (admin-only) |
| 11 | `logistics.py` | logistics | Shipping partners, zones, tracking | Track my orders |
| 12 | `orders.py` | orders | Order management, refunds, disputes | My orders, cart, checkout |
| 13 | `promotions.py` | promotions | Coupons, banners, flash sales | My coupons, referral coins |
| 14 | `security.py` | security | Fraud detection, threat intel | — (admin-only) |
| 15 | `suppliers.py` | suppliers | Supplier verification, onboarding | — (admin-only) |

> **Note:** `media` is a **provider** (already in `providers/media/`), not a domain. `infrastructure` is a **platform layer**, not a domain. Neither gets a router file. Upload/AI/media-related admin endpoints go into `catalog.py` or `system.py`.

### 2.2 Module-Specific Router Files (15 per module)

| # | File Name | Employee Router Covers | Logistics Router Covers | Supplier Router Covers |
|---|-----------|----------------------|------------------------|----------------------|
| 1 | `accounts.py` | My employee profile | My partner profile | My supplier profile |
| 2 | `analytics.py` | Team analytics | Delivery analytics | Sales analytics |
| 3 | `audit.py` | My audit trail | — | My audit trail |
| 4 | `catalog.py` | Product moderation | — | My products, pricing |
| 5 | `comms.py` | Internal chat, email | Partner comms | Supplier comms |
| 6 | `country.py` | Travel, country scope | Shipping zones | Operating countries |
| 7 | `customers.py` | Customer support view | — | Customer orders view |
| 8 | `finance.py` | Payroll, expenses | Partner payouts | My earnings, payouts |
| 9 | `governance.py` | Policies, compliance | — | — |
| 10 | `hr.py` | Self-service HR, leave | — | — |
| 11 | `logistics.py` | Internal logistics | Shipments, tracking, parcels | My shipments |
| 12 | `orders.py` | Order support | Delivery orders | My supplier orders |
| 13 | `promotions.py` | Promo approval | — | My promotions |
| 14 | `security.py` | Security operations | — | — |
| 15 | `suppliers.py` | Supplier management | — | — |

### 2.3 Route Prefix Convention

```
Admin:      /api/v1/admin/{domain}/...
Customer:   /api/v1/customer/{domain}/...
Employee:   /api/v1/employee/{domain}/...
Logistics:  /api/v1/logistics/{domain}/...
Supplier:   /api/v1/supplier/{domain}/...

Public:     /api/v1/public/{domain}/...    (no auth required)
Webhooks:   /api/v1/webhooks/{provider}/... (webhook callbacks)
```

---

## 3 · Execution Plan

### Phase A: Preparation (Do First)

#### A.1 Create Backup Branch
```bash
git checkout -b chore/router-system-correction
```

#### A.2 Create Directory Structure
For each module (admin, customer, employee, logistics, supplier):
```
modules/{m}/routers/
├── accounts.py      ← NEW (consolidated)
├── analytics.py     ← NEW
├── audit.py         ← NEW
├── catalog.py       ← NEW
├── comms.py         ← NEW
├── country.py       ← NEW
├── customers.py     ← NEW
├── finance.py       ← NEW
├── governance.py    ← NEW
├── hr.py            ← NEW
├── logistics.py     ← NEW
├── orders.py        ← NEW
├── promotions.py    ← NEW
├── security.py      ← NEW
├── suppliers.py     ← NEW
└── __init__.py      ← UPDATED
```

#### A.3 Fix Critical Blockers First
Before touching routers, fix the 7 critical middleware blockers so the app can start:
1. `middleware/country_context.py:39` → `domains.hr.services.employees.coi_service`
2. `middleware/coi_middleware.py:10` → `domains.hr.services.employees.coi_service`
3. `middleware/dependencies/coi_dependency.py:10` → `domains.hr.services.employees.coi_service`
4. `middleware/impossible_travel_middleware.py:156` → implement or remove
5. `middleware/impossible_travel_middleware.py:349` → `domains.security.services.fraud_detection_service`
6. `middleware/device_binding_middleware.py:69-70` → implement or remove
7. `middleware/dependencies/fraud_events.py:21` → `domains.governance.models.fraud`

---

### Phase B: Module-by-Module Consolidation

#### B.1 Admin Module (270 → 15 files)

**Most complex — requires reading and merging 228 registered router files.**

| Step | Action | Source Files | Target File |
|------|--------|-------------|-------------|
| 1 | Merge all product/search/upload routers | `admin_admin_products.py`, `admin_products.py`, `admin_catalog_operations.py`, `admin_products_routes.py`, `products.py`, `store_products_routes.py`, `batch_upload.py`, `search.py`, `ai.py`, `ai_image.py`, `ai_research.py`, `ai_upload.py`, `upload.py`, `upload_jobs.py`, `admin_video.py`, `admin_video_routes.py`, `admin_media_geography.py` | `catalog.py` |
| 2 | Merge all order-related routers | `admin_admin_orders.py`, `admin_orders.py`, `admin_orders_routes.py`, `admin_orders_status.py`, `orders.py`, `store_orders_routes.py`, `flash_sales.py`, `disputes_controller.py` | `orders.py` |
| 3 | Merge all finance-related routers | `admin_finance_accounting.py`, `admin_finance_creation.py`, `admin_finance_geography.py`, `admin_finance_sub_ledger.py`, `admin_treasury*.py`, `admin_payouts*.py`, `admin_cash*.py`, `finance.py`, `payout_approval.py` | `finance.py` |
| 4 | Merge all user/account routers | `admin_admin_users_admin.py`, `admin_users.py`, `admin_users_routes.py`, `admin_identity_operations.py`, `users.py`, `auth.py`, `core_auth_routes.py`, `core_users_routes.py`, `iam.py` | `accounts.py` |
| 5 | Merge all supplier routers | `admin_admin_suppliers.py`, `admin_suppliers.py`, `admin_suppliers_routes.py`, `admin_supplier_reviews.py`, `admin_supplier_trading.py`, `suppliers.py`, `public_suppliers.py`, `public_suppliers_routes.py` | `suppliers.py` |
| 6 | Merge all HR routers | `core_hierarchy_routes.py`, `core_ess_routes.py`, `core_payroll_routes.py`, `core_lms_routes.py`, `public_hr.py`, `public_hr_hierarchy.py` | `hr.py` |
| 7 | Merge all promotion routers | `admin_admin_coupons.py`, `admin_promotions.py`, `admin_promotions_routes.py`, `admin_commerce_promotion_admin.py`, `banners.py`, `admin_banners.py`, `admin_banners_routes.py`, `store_banners_routes.py` | `promotions.py` |
| 8 | Merge all country routers | `countries.py`, `country_admin.py`, `country_admin_routes.py`, `country_auto_populate.py`, `country_communications.py`, `country_dropdown.py`, `country_maps.py`, `country_payouts.py`, `country_payouts_routes.py`, `country_research.py`, `country_staff.py`, `country_staff_routes.py`, `country_versioning.py`, `cross_border.py` | `country.py` |
| 9 | Merge all comms/notification routers | `admin_chat.py`, `admin_chat_routes.py`, `admin_comms_unified.py`, `admin_email.py`, `admin_email_routes.py`, `admin_admin_tickets.py`, `comms.py`, `admin_comms_messaging.py`, `system_comms_status.py`, `public_comms_status.py`, `public_comms_unified.py`, `escalation.py` | `comms.py` |
| 10 | Merge all analytics routers | `admin_admin_analytics.py`, `admin_analytics_fallback_dashboard.py`, `admin_analytics_routes.py`, `analytics.py` | `analytics.py` |
| 11 | Merge all security routers | `admin_security_detection.py`, `admin_security_health.py`, `admin_security_operations.py`, `admin_security_registration.py`, `fraud_detection.py`, `csp_reporting.py` | `security.py` |
| 12 | Merge all governance routers | `admin_governance_command_center.py`, `command_center.py`, `command_center_api.py`, `command_center_controller.py`, `compliance.py`, `admin_permissions_validation.py`, `permissions.py` | `governance.py` |
| 13 | Merge all audit routers | `admin_admin_audit.py`, `audit.py`, `admin_geography_audit.py`, `core_ediscovery_routes.py`, `ediscovery.py` | `audit.py` |
| 14 | Merge all customer routers | `customers.py`, `public_commerce_referrals.py`, `public_commerce_reviews.py`, `public_commerce_validation.py`, `public_commerce_wishlist.py` | `customers.py` |
| 15 | Merge all system/remaining routers | `admin_settings.py`, `admin_settings_routes.py`, `admin_configuration_operations.py`, `admin_core_routes.py`, `admin_commerce_configuration.py`, `core_jobs_routes.py`, `core_workflows_routes.py`, `workflows.py`, `export.py`, `frontend_errors.py`, `currency.py`, `admin_admin_bank_accounts.py`, `admin_logistics*.py`, `store_shipments_routes.py`, `operational_controller.py`, `mobile_controller.py`, `location_api.py`, `contact.py`, `csp_reporting.py` | `system.py` |

#### B.2 Customer Module (44 → 15 files)

| Step | Action | Source Files | Target File |
|------|--------|-------------|-------------|
| 1 | Keep existing + merge stubs | `addresses.py` | `accounts.py` |
| 2 | Create placeholder | — | `analytics.py` |
| 3 | Create placeholder | — | `audit.py` |
| 4 | Merge catalog/search | `catalog.py` (if exists) | `catalog.py` |
| 5 | Merge comms | `chat.py`, `comms.py` | `comms.py` |
| 6 | Create placeholder | — | `country.py` |
| 7 | Merge customer health | `customer.py`, `customer_health.py`, `customer_health_list.py` | `customers.py` |
| 8 | Create placeholder | — | `finance.py` |
| 9 | Create placeholder | — | `governance.py` |
| 10 | Create placeholder | — | `hr.py` |
| 11 | Create placeholder | — | `logistics.py` |
| 12 | Merge orders | `cart.py`, `cart_controller.py`, `cart_controller_service.py`, `cart_controller__routers.py`, `orders.py`, `orders_controller.py`, `orders_controller__routers.py`, `customer_orders.py`, `returns.py`, `returns_controller.py`, `returns_controller_service.py`, `returns_controller__routers.py`, `disputes_controller.py`, `disputes_controller__routers.py` | `orders.py` |
| 13 | Merge promotions | `coupons.py`, `customer_coupons_create.py`, `customer_coupons_mgmt.py`, `referrals.py`, `reviews.py`, `wishlist.py`, `promotions.py` | `promotions.py` |
| 14 | Create placeholder | — | `security.py` |
| 15 | Merge payments + remaining | `payments.py`, `public_routers.py`, `analytics.py`, `audit.py`, `auth.py`, `finance.py`, `governance.py`, `health.py`, `hr.py`, `logistics.py`, `security.py`, `suppliers.py` | `system.py` |

#### B.3 Employee Module (80 → 15 files)

| Step | Action | Source Files | Target File |
|------|--------|-------------|-------------|
| 1 | Merge account/profile | `accounts.py` | `accounts.py` |
| 2 | Merge analytics | `analytics.py` | `analytics.py` |
| 3 | Create placeholder | — | `audit.py` |
| 4 | Create placeholder | — | `catalog.py` |
| 5 | Merge all comms | `chat.py`, `chat_api.py`, `chat_enrichment.py`, `chatbot.py`, `comm.py`, `comms.py`, `comms_chat.py`, `comms_unified.py`, `comms_video.py`, `email.py`, `email_controller.py`, `email_enrichment.py`, `entity_chat.py`, `entity_communication.py`, `internal_channels.py`, `internal_comms_channels.py`, `messaging.py`, `proxy_communication.py`, `ws_chat.py` | `comms.py` |
| 6 | Create placeholder | — | `country.py` |
| 7 | Create placeholder | — | `customers.py` |
| 8 | Merge finance | `finance.py`, `finance_automation.py`, `finance_erp.py`, `finance_package.py`, `treasury.py`, `treasury_api.py`, `treasury_router_service.py`, `accounting.py`, `accounting_controller.py`, `cash_management.py`, `cash_management_controller.py`, `cash_management_write_controller.py`, `expenses.py`, `expense_controller.py`, `invoices.py`, `invoice_controller.py`, `sub_ledger_controller.py` | `finance.py` |
| 9 | Create placeholder | — | `governance.py` |
| 10 | Merge HR | `hr.py`, `hr_controller.py`, `hr_dashboard.py`, `employees.py`, `employees_controller.py`, `employees_controller__routers.py`, `hierarchy.py`, `hierarchy_controller.py`, `hierarchy_controller__routers.py`, `lms.py`, `lms_controller.py`, `lms_controller__routers.py`, `okr.py`, `okr_controller.py`, `payroll.py`, `performance.py`, `succession.py`, `succession_controller.py`, `ess.py`, `shift_handover.py` | `hr.py` |
| 11 | Create placeholder | — | `logistics.py` |
| 12 | Merge orders/jobs | `orders.py`, `jobs.py`, `trading.py` | `orders.py` |
| 13 | Create placeholder | — | `promotions.py` |
| 14 | Merge security | `security.py`, `risk.py` | `security.py` |
| 15 | Merge remaining | `travel.py`, `tickets.py`, `video.py`, `video_controller.py`, `notifications.py`, `push_notifications.py` | `system.py` |

#### B.4 Logistics Module (32 → 15 files)

| Step | Action | Source Files | Target File |
|------|--------|-------------|-------------|
| 1 | Create placeholder | — | `accounts.py` |
| 2 | Create placeholder | — | `analytics.py` |
| 3 | Create placeholder | — | `audit.py` |
| 4 | Create placeholder | — | `catalog.py` |
| 5 | Merge comms | `comms.py` | `comms.py` |
| 6 | Create placeholder | — | `country.py` |
| 7 | Create placeholder | — | `customers.py` |
| 8 | Create placeholder | — | `finance.py` |
| 9 | Create placeholder | — | `governance.py` |
| 10 | Create placeholder | — | `hr.py` |
| 11 | Merge ALL logistics | `logistics.py`, `logistics_controller.py`, `logistics_controller__routers.py`, `logistics_health.py`, `logistics_health_list.py`, `logistics_locations.py`, `logistics_locations_create.py`, `logistics_logistics_status.py`, `logistics_orders_list.py`, `logistics_orders_v2.py`, `logistics_partner.py`, `logistics_partner_controller.py`, `logistics_partner_controller__routers.py`, `logistics_partner_verify.py`, `shipments.py`, `parcel_tracking.py` | `logistics.py` |
| 12 | Create placeholder | — | `orders.py` |
| 13 | Create placeholder | — | `promotions.py` |
| 14 | Create placeholder | — | `security.py` |
| 15 | Merge remaining | `accounts.py`, `analytics.py`, `audit.py`, `auth.py`, `country.py`, `customers.py`, `finance.py`, `governance.py`, `hr.py`, `orders.py`, `promotions.py`, `public_routers.py`, `security.py`, `suppliers.py` | `system.py` |

#### B.5 Supplier Module (50 → 15 files)

| Step | Action | Source Files | Target File |
|------|--------|-------------|-------------|
| 1 | Create placeholder | — | `accounts.py` |
| 2 | Merge analytics | `supplier_analytics.py`, `supplier_analytics_analytics.py` | `analytics.py` |
| 3 | Create placeholder | — | `audit.py` |
| 4 | Merge catalog/products | `catalog.py`, `products.py`, `product_moderation.py`, `product_verification.py`, `product_videos.py`, `supplier_products.py`, `supplier_products_upload.py` | `catalog.py` |
| 5 | Merge comms | `comms.py` | `comms.py` |
| 6 | Create placeholder | — | `country.py` |
| 7 | Create placeholder | — | `customers.py` |
| 8 | Merge finance | `supplier_finance.py`, `supplier_finance_status.py`, `supplier_payouts.py`, `supplier_payouts_pay.py`, `commission.py` | `finance.py` |
| 9 | Create placeholder | — | `governance.py` |
| 10 | Create placeholder | — | `hr.py` |
| 11 | Create placeholder | — | `logistics.py` |
| 12 | Create placeholder | — | `orders.py` |
| 13 | Create placeholder | — | `promotions.py` |
| 14 | Create placeholder | — | `security.py` |
| 15 | Merge remaining | `supplier.py`, `supplier_core_routes.py`, `supplier_controller.py`, `supplier_documents.py`, `supplier_documents_review.py`, `supplier_document_controller_service.py`, `supplier_health.py`, `supplier_health_controller.py`, `supplier_health_list.py`, `supplier_profile.py`, `supplier_profile_create.py`, `onboarding.py`, `supplier_supplier_supplier_health.py`, `supplier_supplier_sync.py`, `supplier_supplier_upload.py`, `supplier_sync.py`, `supplier_upload.py`, `supplier_bg_ab_test.py`, `supplier_orders.py`, `supplier_orders_verify.py` | `system.py` |

---

### Phase C: Update `__init__.py` for Each Module

After consolidation, each `modules/{m}/routers/__init__.py` should list exactly 15 files:

```python
"""Routers for the {module} module — 15 domain routers."""
import importlib

routers = []
public_routers = []

_module_names = [
    "accounts",
    "analytics",
    "audit",
    "catalog",
    "comms",
    "country",
    "customers",
    "finance",
    "governance",
    "hr",
    "logistics",
    "orders",
    "promotions",
    "security",
    "suppliers",
]

for _n in _module_names:
    try:
        _m = importlib.import_module(f"modules.{module}.routers.{_n}")
    except Exception as _e:
        import logging as _logging
        _logging.getLogger(__name__).error("Skipping router %s: %s", _n, _e)
        continue
    _r = getattr(_m, "router", None)
    if _r is not None:
        routers.append(_r)
    _pr = getattr(_m, "public_router", None)
    if _pr is not None:
        public_routers.append(_pr)
```

---

### Phase D: Validation & Testing

#### D.1 Import Check
```bash
python -c "import backend.main"
```

#### D.2 Route Count Check
```bash
python -c "
from main import app
routes = [r.path for r in app.routes if hasattr(r, 'path')]
print(f'Total routes: {len(routes)}')
for r in sorted(routes)[:50]:
    print(r)
"
```

#### D.3 Verify All Endpoints Accessible
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

#### D.4 Run Test Suite
```bash
pytest backend/tests/ -x -v --tb=short
```

---

## 4 · Execution Order

| Step | Module | Source Files | Target | Risk | Agent |
|------|--------|-------------|--------|------|-------|
| 1 | — | Fix 7 critical blockers | App starts | Critical | Main |
| 2 | admin | 228 → 15 | `modules/admin/routers/` | High | Agent-1 |
| 3 | customer | 44 → 15 | `modules/customer/routers/` | Medium | Agent-2 |
| 4 | employee | 80 → 15 | `modules/employee/routers/` | Medium | Agent-3 |
| 5 | logistics | 32 → 15 | `modules/logistics/routers/` | Low | Agent-4 |
| 6 | supplier | 50 → 15 | `modules/supplier/routers/` | Medium | Agent-5 |
| 7 | — | Update `__init__.py` × 5 | Registration | Low | Main |
| 8 | — | Validate imports + routes | Verification | Low | Main |

---

## 5 · Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Lost endpoints during merge | Use `grep` to find all `@router.` decorators before/after |
| Route prefix conflicts | Standardize on `/api/v1/{module}/{domain}/` pattern |
| Broken imports in new files | Test each new file with `python -c "from modules.{m}.routers.{d} import router"` |
| Dead code in deprecated stubs | Old files become deprecated stubs that re-export from new location |
| Test failures | Run `pytest backend/tests/` after each module consolidation |

---

## 6 · Deprecated Stub Pattern

Old router files should become deprecated stubs:

```python
# DEPRECATED: Consolidated into modules.admin.routers.catalog
# This stub exists for backward compatibility. See DOMAIN_WORK.md.
from modules.admin.routers.catalog import *  # noqa: F401,F403
```

---

## 7 · Success Criteria

- [ ] `python -c "import backend.main"` succeeds
- [ ] Exactly 15 router files per module (75 total)
- [ ] All 327 currently-registered endpoints still accessible
- [ ] No duplicate endpoints
- [ ] All `__init__.py` files list exactly 15 modules
- [ ] Route prefix convention: `/api/v1/{module}/{domain}/...`
- [ ] `pytest backend/tests/` passes
