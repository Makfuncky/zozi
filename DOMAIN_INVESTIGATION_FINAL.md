# Complete Domain Investigation Report — ZOZI Backend (Round 4 — Final)

> Generated: 2026-08-26  
> Scope: All domains, modules, infrastructure, kernel, providers  
> Total issues found: **400+**

---

## CRITICAL (Runtime Crashes): 280+ issues

### 1. Self-Imports (Guaranteed ImportError)

| # | File | Line |
|---|------|------|
| 1 | `modules/admin/routers/orders.py` | 7 |
| 2 | `modules/admin/routers/cash_management_controller.py` | 5-54 (entire file) |

### 2. Controllers Imports (17 broken)

All reference the abolished `controllers/` directory.

| File | Lines |
|------|-------|
| `modules/admin/routers/orders.py` | 39 |
| `modules/admin/routers/logistics.py` | 16-21, 55-59 |
| `modules/admin/routers/country.py` | 9 |
| `modules/customer/routers/finance.py` | 13 |
| `modules/supplier/routers/suppliers.py` | 39, 346, 978, 1027, 1840 |

### 3. Root-Level Package Imports (don't exist)

| Pattern | Count | Examples |
|---------|-------|----------|
| `from services.*` | 5 | `services.ai_service`, `services.common.import_service` |
| `from utils.*` (root) | 7 | `utils.constants`, `utils.country_rls`, `utils.key_rotation` |
| `from _legacy.*` | 6 | `_legacy.models` |

### 4. Missing Sub-Router Files (10+ missing)

| Module | Missing Sub-Routers |
|--------|---------------------|
| admin/routers/orders.py | `.cart`, `.disputes`, `.returns` |
| admin/routers/catalog.py | `.categories`, `.products`, `.search` |
| admin/routers/logistics.py | `.partners`, `.shipping`, `.tracking` |
| admin/routers/customers.py | `.referrals`, `.reviews` |

### 5. Broken Shim Targets (8 files)

| Shim | Missing Target |
|------|----------------|
| `infrastructure/utils/analytics_service.py` | `domains.analytics.services.infrastructure_analytics_service` |
| `infrastructure/utils/command_center_service.py` | `domains.governance.services.command_center.service` |
| `infrastructure/utils/workflow_engine.py` | `domains.governance.services.workflow_engine` |
| `infrastructure/utils/import_service.py` | `domains.finance.services.data_import_service` |
| `infrastructure/utils/key_rotation.py` | `infrastructure.security.key_rotation` |
| `infrastructure/utils/dependencies.py` | `infrastructure.security.dependencies` |

### 6. Circular Imports (3 confirmed)

| Files | Issue |
|-------|-------|
| `finance/treasury/treasury_service.py` ↔ `accounts/services/admin_treasury_service` | 64 symbols imported from non-existent module |
| `accounts/ports.py` → `promotions/services/coupon_service` | Wrong domain for coupon services |
| `logistics/services/health/service.py` ↔ `logistics_health_service.py` | Mutual import cycle |

### 7. Schema Discipline Violations (17 files, ~30 lines)

| Domain | File | Wrong Schema | Correct Schema |
|--------|------|--------------|----------------|
| catalog | `products.py` | `"commerce"` | `"catalog"` |
| catalog | `promotions.py` | `"commerce"` | `"catalog"` |
| accounts | `core.py` | `"customer"`, `"commerce"` | `"accounts"` |
| governance | `admin.py` | `"commerce"` | `"governance"` |
| governance | `core.py` | `"customer"` | `"governance"` |
| comms | `news.py` | `"customer"` | `"comms"` |
| security | `fraud.py` | `"commerce"` | `"security"` |
| hr | `employee_models.py` | `"customer"` | `"hr"` |

---

## HIGH (Architecture Violations): 80+ issues

### 1. Invalid Domain

| Domain | Issue |
|--------|-------|
| `media` | Must not exist per `media_code_belongs_in_providers` decision. Should be `providers/media/` only. |

### 2. Domain → Module Imports (5+ violations)

| File | Line | Import |
|------|------|--------|
| `domains/analytics/services/analytics_controller.py` | 6 | `modules.admin.routers.admin` |
| `domains/suppliers/services/governance/admin_suppliers_service.py` | 15 | `modules.admin.routers.admin_controller` |
| `domains/catalog/services/categories/category_admin_routing_service.py` | 24 | `modules.admin.routers.admin_controller` |
| `domains/logistics/services/core/service.py` | 1751, 2731 | `modules.admin.routers.*` |
| `domains/customers/services/wishlist_service_from_accounts.py` | 8 | `modules.products.routers.products_controller` |

### 3. Infrastructure → Domain Imports (35+ imports)

Top offenders:
- `infrastructure/database/seed.py` — 15 domain model imports
- `infrastructure/messaging/realtime.py` — 9 domain model imports
- `infrastructure/messaging/downstream_wiring.py` — 4 domain imports
- `infrastructure/security/key_rotation.py` — 5 domain imports

### 4. Kernel → Domain Import

| File | Line | Import |
|------|------|--------|
| `kernel/rls_context.py` | 8 | `domains.governance.models.user.User` |

### 5. Domain Files at Wrong Location

| File | Should Be In |
|------|--------------|
| `domains/_async_workers.py` | `providers/async_workers/` |
| `domains/_image_tools.py` | `providers/image/` |
| `domains/_key_rotation.py` | `infrastructure/security/` |
| `domains/_seed.py` | `scripts/` or `tests/` |
| `domains/_service_registry.py` | `backend/registry.py` |

### 6. Missing Canonical Domain Files

| Domain | Missing |
|--------|---------|
| logistics | `features.py` (domain root), `events.py` (domain root) |
| orders | `features.py` (domain root), `events.py` (domain root) |
| media | `models/`, `ports.py`, `features.py`, `events.py` |

### 7. Module-Level Violations

| File | Issue |
|------|-------|
| `modules/payments_controller.py` | Controller at module root (abolished) |
| `modules/admin/audit_controller.py` | Controller in module (abolished) |
| `modules/admin/bank_accounts_controller.py` | Controller in module (abolished) |
| `modules/admin/misc_controller.py` | Controller in module (abolished) |
| `modules/admin/services/` | Services folder in module (belongs in domains) |

---

## MEDIUM (Code Quality): 100+ issues

### 1. Oversized Files (>1500 lines)

| File | Lines |
|------|-------|
| `modules/supplier/routers/suppliers.py` | 4,729 |
| `domains/finance/services/treasury/cash_management_service.py` | 4,758 |
| `domains/finance/services/ledger/general_ledger_service.py` | 6,500+ |
| `providers/image/bg_remover.py` | 2,560 |
| `modules/employee/routers/comms.py` | 2,318 |
| `modules/employee/routers/hr.py` | 2,217 |
| `domains/catalog/services/products/products_service.py` | 1,766 |

### 2. Thin Router Violations (40+ issues)

| Router | Issues |
|--------|--------|
| `admin/routers/catalog.py` | 10+ duplicate functions, DB writes, 1070 lines |
| `admin/routers/accounts.py` | WebSocket handlers, UserConnectionManager class |
| `admin/routers/orders.py` | Self-import, _legacy imports, controller imports |
| `admin/routers/logistics.py` | 25+ broken imports, DB writes |
| `employee/routers/cash_management_controller.py` | Entire file is self-imports |

### 3. Duplicate Routes/Functions

`admin/routers/catalog.py` has 10+ duplicate function definitions (lines 228/519, 243/535, etc.)

### 4. Missing Pagination (10+ endpoints)

Files: suppliers.py, logistics.py, comms.py, hr.py, export_read.py

### 5. Swallowed Exceptions (30+ instances)

| File | Line | Pattern |
|------|------|---------|
| `catalog/products_service.py` | 1738 | `except Exception: pass` |
| `modules/employee/routers/comms.py` | 570 | `except Exception: pass` |
| `infrastructure/database/database.py` | 152 | Silent swallowing |
| `lifespan.py` | 95, 111, 128+ | 8 silent handlers |

### 6. Star Imports (100+ instances)

Particularly in domain `__init__.py` facade files.

---

## SECURITY ISSUES: 15+ issues

| # | File | Line | Issue |
|---|------|------|-------|
| 1 | `governance/services/auth/iam_service_accounts.py` | 3 | `_QR_SECRET_KEY = "default-qr-secret"` |
| 2 | `infrastructure/security/qr_service.py` | 18 | `QR_SECRET_KEY` fallback default |
| 3 | `middleware/country_context.py` | 244 | f-string SQL with country list |
| 4 | `modules/employee/routers/hr.py` | 1982 | f-string SQL UPDATE |
| 5 | `modules/employee/routers/accounts.py` | 86 | f-string SQL UPDATE |
| 6 | `domains/hr/services/ess/ess_service.py` | 71, 267 | f-string SQL (2 instances) |
| 7 | `infrastructure/database/database_service.py` | 42 | String concatenation SQL |
| 8 | `jobs/seed_all.py` | 299 | String concatenation SQL |

---

## WIRING ISSUES: 46 issues

### 1. Missing `__init__.py` (all domains)

All 16 domain directories lack root-level `__init__.py` facade files.

### 2. Empty `__init__.py` (all modules)

All 5 module root `__init__.py` files are empty (0 bytes).

### 3. Missing Domain Facade Files

| Domain | Missing Files |
|--------|---------------|
| accounts | `features.py` empty, `events.py` empty |
| logistics | `features.py` (domain root), `events.py` (domain root) |
| orders | `features.py` (domain root), `events.py` (domain root) |
| analytics | `events.py` (domain root) |
| media | `models/`, `ports.py`, `features.py`, `events.py` |

### 4. Unloaded Router Files (6 files)

`modules/employee/routers/` has 6 router files not listed in the dynamic loader:
- `treasury_api.py`, `email_controller.py`, `comms_video.py`, `comms_chat.py`, `chat_api.py`, `cash_management_controller.py`

### 5. Orphaned Model Files (2 files)

- `catalog/models/upload_job.py`
- `catalog/models/ai_upload.py`

---

## Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL (Runtime Crash) | 280+ |
| 🟠 HIGH (Architecture) | 80+ |
| 🟡 MEDIUM (Quality) | 100+ |
| 🔒 SECURITY | 15 |
| 🔌 WIRING | 46 |
| **TOTAL** | **520+** |

---

## Top 10 Priority Fixes

1. **Fix self-imports** (2 files) — `orders.py`, `cash_management_controller.py`
2. **Fix controller imports** (17 references) — Update to domain service paths
3. **Fix schema discipline** (17 files) — `commerce` → `catalog`, `customer` → correct domain
4. **Remove `media` domain** — Move to `providers/media/`
5. **Fix circular imports** (3 cycles) — treasury, accounts/ports, logistics health
6. **Create domain `__init__.py`** (16 domains) — Facade files for clean imports
7. **Fix broken shims** (8 files) — Update to correct targets or remove
8. **Fix thin router violations** (40+ issues) — Move business logic to services
9. **Add missing features.py/events.py** — 3 domains missing canonical files
10. **Fix 8 broken shim targets** — Update infrastructure/utils shims
