# Architecture Audit Report — ZOZI Codebase

> Based on `ARCHITECTURE_DIAGRAM.md` and the Seven Laws.  
> Last updated: 2026-08-25 (Post Phase 1 + agent cleanup)

---

## Progress Summary

### Major Improvements ✅

| Law | Previous | Current | Change |
|-----|----------|---------|--------|
| Law 1A — Domains→modules | 43 | **0** | **✅ FIXED** |
| Law 1B — Cross-module imports | 84+ | **14** | **-70** |
| Law 1C — Infrastructure→domains | 167+ | **27** | **-140** |
| Law 1D — Kernel→domains | 1 | **1** | 0 |
| Law 2A — Routers with get_db | 1000+ | **0** | **✅ FIXED** |
| Law 2B — Routers importing models | 1000+ | **0** | **✅ FIXED** |
| Law 3 — Cross-domain imports | 500+ | **80+ files** | Reduced |
| Law 4 — Missing features.py | 4 | **2** | -2 |
| Law 5 — Country scope | 0 | **⚠️ Missing RLS file** | Regressed |
| Law 6 — Forbidden schema `core` | 14 | **0** | **✅ FIXED** |
| Structural — Invalid directories | 3 | **0** | **✅ FIXED** |

---

## Remaining Violations by Law

---

## LAW 1: Arrows Point Down Only

**Rule:** `modules → domains → infrastructure`. Domains never import modules. `infrastructure`/`kernel` import nothing above them.

---

### 1A. Domains Importing from `Modules/` — **0 violations** ✅ FIXED

All 43 domain→module imports have been resolved by other agents.

---

### 1B. Cross-Module Imports — **14 violations** [CRITICAL]

Modules importing from other modules. Each module should be self-contained.

| # | File | Line | Import |
|---|------|------|--------|
| 1 | `modules/employee/routers/cash_management.py` | 40 | `from modules.admin.routers.auth import get_current_user` |
| 2 | `modules/employee/routers/jobs.py` | 4 | `from modules.admin.routers.auth import get_current_user` |
| 3 | `modules/employee/routers/orders.py` | 22 | `from modules.admin.routers.auth import get_current_user` |
| 4 | `modules/employee/routers/invoices.py` | 13 | `from modules.admin.routers.auth import get_current_user` |
| 5 | `modules/employee/routers/finance.py` | 774, 1299-1348 | `from modules.admin.routers.auth import get_current_user` + self-ref |
| 6 | `modules/logistics/routers/logistics.py` | 359, 837, 1679 | `from modules.admin.routers.core_auth_routes import get_current_user` |
| 7 | `modules/logistics/routers/logistics_partner.py` | 13 | `from modules.admin.routers.auth import get_current_user` |
| 8 | `modules/logistics/routers/logistics_partner_verify.py` | 11 | `from modules.admin.routers.core_auth_routes import get_current_user` |
| 9 | `modules/logistics/routers/logistics_logistics_status.py` | 10 | `from modules.admin.routers.core_auth_routes import get_current_user` |
| 10 | `modules/logistics/routers/shipments.py.fixed_tmp` | 19 | `from modules.logistics.auth import ...` |
| 11 | `modules/admin/routers/country.py` | 422 | `from modules.employee.routers import employees_controller` |
| 12 | `modules/admin/routers/geography_configuration.py` | 13 | `from modules.employee.routers import employees_controller` |
| 13 | `modules/admin/routers/public_geography_configuration.py` | 13 | `from modules.employee.routers import employees_controller` |
| 14 | `modules/admin/routers/countries.py` | 11 | `from modules.employee.routers import employees_controller` |

**Root cause:** Shared auth (`get_current_user`) duplicated across modules instead of centralized.

**Fix:** Create `infrastructure/security/auth.py` with shared auth helpers, update all 14 files.

---

### 1C. Infrastructure Importing from `Domains/` — **27 violations** [CRITICAL]

Infrastructure must import NOTHING above it. Excludes 31 backward-compat shims.

| # | File | Domain Imports | Target |
|---|------|----------------|--------|
| 1 | `infrastructure/database/seed.py` | 21 imports (governance, catalog, comms, country, logistics, orders, hr) | `domains/governance/services/seed.py` |
| 2 | `infrastructure/database/treasury_seeder.py` | 3 imports (finance) | `domains/finance/services/treasury_seeder.py` |
| 3 | `infrastructure/database/permission_service.py` | 2 imports (governance) | `domains/governance/services/permission_service.py` |
| 4 | `infrastructure/lifespan.py` | 5 imports (accounts, finance, logistics) | `domains/governance/services/startup.py` |
| 5 | `infrastructure/messaging/downstream_wiring.py` | 5 imports (catalog, country, orders, finance) | `domains/finance/services/downstream_wiring.py` |
| 6 | `infrastructure/messaging/downstream_hooks.py` | 1 import (country) | `domains/country/services/downstream_hooks.py` |
| 7 | `infrastructure/messaging/email_service.py` | 2 imports (governance, comms) | `domains/comms/services/email_service.py` |
| 8 | `infrastructure/middleware/country_detection.py` | 1 import (country) | Use port abstraction |
| 9 | `infrastructure/middleware/rls.py` | 1 import (country) | Use port abstraction |
| 10 | `infrastructure/ml/worker.py` | 1 import (finance) | `providers/ml/worker.py` |
| 11 | `infrastructure/observability/audit.py` | 1 import (governance) | `domains/governance/services/observability_audit.py` |
| 12 | `infrastructure/search/routers/search_controller.py` | 2 imports (governance) | `domains/governance/services/search.py` |
| 13 | `infrastructure/security/dependencies.py` | 2 imports (governance) | `domains/governance/services/security_dependencies.py` |
| 14 | `infrastructure/security/key_rotation.py` | 6 imports (governance, comms, logistics, orders) | `domains/security/services/key_rotation.py` |
| 15 | `infrastructure/security/qr_service.py` | 2 imports (hr, governance) | `domains/security/services/qr_service.py` |
| 16 | `infrastructure/security/security_audit.py` | 1 import (governance) | `domains/governance/services/security_audit.py` |
| 17 | `infrastructure/security/vault.py` | 1 import (finance) | `domains/finance/services/vault.py` |
| 18 | `infrastructure/services/utils/translate_controller.py` | 1 import (governance) | `domains/governance/services/translate.py` |
| 19 | `infrastructure/services/utils/workflow_engine.py` | 1 import (governance) | `domains/governance/services/workflow_engine.py` |
| 20 | `infrastructure/utils/export_read.py` | 5 imports (governance, catalog, orders) | `domains/governance/services/export_read.py` |
| 21 | `infrastructure/utils/misc_write.py` | 5 imports (governance, catalog, finance) | `domains/governance/services/misc_write.py` |
| 22 | `infrastructure/utils/misc_write_service.py` | 5 imports (governance, catalog, finance) | `domains/governance/services/misc_write.py` |
| 23 | `infrastructure/utils/operations_service.py` | Many imports (governance, catalog, orders, comms, finance) | `domains/governance/services/operations.py` |
| 24 | `infrastructure/utils/realtime.py` | Many imports (governance, catalog, comms, finance) | `domains/governance/services/realtime.py` |
| 25 | `infrastructure/utils/user_context.py` | 1 import (governance, runtime) | `domains/governance/services/user_context.py` |
| 26 | `infrastructure/utils/workflow_engine.py` | 1 import (governance) | `domains/governance/services/workflow_engine.py` |
| 27 | `infrastructure/media/free_image_tools.py` | 1 import (finance) | Replace with provider call |

**New files discovered by other agents:**
- `infrastructure/utils/operations_service.py` — orchestration service with many domain imports
- `infrastructure/utils/misc_write_service.py` — duplicate of misc_write.py

---

### 1D. Kernel Importing from `Domains/` — **1 violation** [CRITICAL]

| # | File | Line | Import |
|---|------|------|--------|
| 1 | `kernel/rls_context.py` | 8 | `from domains.governance.models.user import User` |

**Fix:** Replace with `infrastructure/` platform primitive or protocol.

---

## LAW 2: Module Routers Stay Thin

**Rule:** auth context + `require_feature(...)` + one domain-service call. No DB writes, no business rules.

---

### 2A. Direct Database Access in Routers — **0 violations** ✅ FIXED

All router files that previously used `get_db` directly have been refactored by other agents.

---

### 2B. Direct Model Imports in Routers — **0 violations** ✅ FIXED

All router files that previously imported domain models directly have been refactored by other agents.

---

## LAW 3: Cross-Domain Writes via Events; Reads via Ports.py

**Rule:** Writes across domains go ONLY through `events.py`/`subscribers.py`. Reads across domains go ONLY through the publishing domain's `ports.py`.

---

### Direct Cross-Domain Imports in Services — **80+ files** [CRITICAL]

| Domain | Unique Files | Example Targets |
|--------|-------------|-----------------|
| analytics | ~8 | governance, catalog, finance, logistics, orders, hr, country |
| audit | ~8 | governance, country, finance, logistics, comms, hr |
| catalog | ~8 | governance, comms, country, finance, logistics, orders, hr |
| accounts | ~6 | governance, catalog, comms, finance, logistics, orders, country, hr |
| customers | ~8 | catalog, comms, governance, orders, finance |
| country | ~8 | comms, finance, governance, hr, logistics, orders |
| governance | ~8 | catalog, comms, country, finance, hr, logistics, orders, suppliers |
| hr | ~5 | governance, finance, logistics, orders |
| logistics | ~8 | governance, catalog, country, finance, hr, orders, suppliers |
| finance | ~8+ | accounts, comms, country, governance, hr, logistics, orders, suppliers |
| suppliers | ~8+ | catalog, comms, finance, governance, logistics, orders, country |
| security | ~3 | governance |
| comms | ~3 | accounts, governance |
| orders | ~5 | catalog, governance, logistics, comms |
| promotions | ~3 | comms, governance, finance, catalog |

**Fix:** Route all cross-domain reads through `ports.py`, writes through `events.py`/`subscribers.py`.

---

## LAW 4: Features Single-Sourced

**Rule:** Feature atoms defined once in `domains/{domain}/features.py`; aggregated by `rbac/catalog.py`.

---

### Missing `features.py` — **2 violations**

| # | Domain | Status |
|---|--------|--------|
| 1 | `domains/logistics/` | **MISSING** features.py |
| 2 | `domains/orders/` | **MISSING** features.py |

**Domains with features.py (15):** accounts, analytics, audit, catalog, comms, country, customers, finance, governance, hr, promotions, security, suppliers, media, providers

---

## LAW 5: Country Scope (RLS Enforcement)

**Status:** ⚠️ REGRESSED

- `infrastructure/database/security.py` — **NOT FOUND** (was supposed to be canonical RLS enforcer)
- `country_code` usage in domain services — **100+ matches** (implemented in domain services)

**Fix:** Create `infrastructure/database/security.py` as canonical RLS enforcer.

---

## LAW 6: Schema Discipline

**Rule:** Forbidden schemas: `core` / `platform` / `identity`. Every actor's user table lives in its own domain schema.

---

### Forbidden Schema `core` — **0 violations** ✅ FIXED

All 14 previous violations in `rbac/models/permissions.py`, `domains/accounts/models/user.py`, `domains/governance/models/core.py`, `domains/governance/models/admin.py` have been resolved.

---

## LAW 7: Allowlist Rule

**Rule:** Temporary cross-domain imports tracked in `DOMAIN_ALLOWLIST.yaml` and may only shrink.

---

### DOMAIN_ALLOWLIST.yaml Status

- **Location:** `backend/DOMAIN_ALLOWLIST.yaml` (77 lines)
- **References forbidden schemas:** YES — references `core.users` 3 times (lines 9-11)
- **Content:** 68 sanctioned cross-domain import patterns, mostly finance-related

**Fix:** Remove `core.users` references (schema `core` is forbidden).

---

## Structural Violations

### Invalid Paths — **0 violations** ✅ FIXED

| Path | Status |
|------|--------|
| `domains/infrastructure/` | REMOVED ✓ |
| `domains/providers/` | REMOVED ✓ |
| `domains/media/` | REMOVED ✓ |
| `modules/payments_controller.py` | REMOVED ✓ |
| `backend/utils/` | REMOVED ✓ |
| `backend/routers/` | REMOVED ✓ |
| `backend/controllers/` | REMOVED ✓ |
| `backend/services/` | REMOVED ✓ |
| `backend/models/` | REMOVED ✓ |
| `backend/db/` | REMOVED ✓ |

---

## Summary

| Law | Category | Violations | Status |
|-----|----------|------------|--------|
| Law 1A | Domains importing modules | 0 | ✅ FIXED |
| Law 1B | Cross-module imports | 14 | 🔴 CRITICAL |
| Law 1C | Infrastructure importing domains | 27 | 🔴 CRITICAL |
| Law 1D | Kernel importing domains | 1 | 🔴 CRITICAL |
| Law 2A | Routers with direct DB access | 0 | ✅ FIXED |
| Law 2B | Routers with direct model imports | 0 | ✅ FIXED |
| Law 3 | Cross-domain imports | 80+ files | 🔴 CRITICAL |
| Law 4 | Missing features.py | 2 | 🟡 MEDIUM |
| Law 5 | Country scope (RLS) | Missing file | ⚠️ REGRESSED |
| Law 6 | Forbidden schema `core` | 0 | ✅ FIXED |
| Law 7 | Allowlist references core | 3 | 🟡 MEDIUM |
| Structural | Invalid directories | 0 | ✅ FIXED |
| **TOTAL** | | **~120+ unique files** | |

---

## Recommended Fix Priority

1. **Phase 1 — Centralize auth (14 violations):** Create `infrastructure/security/auth.py` with `get_current_user`, `require_admin`, etc. Fix all 14 cross-module imports.
2. **Phase 2 — Move infrastructure→domain (27 violations):** Move files from infrastructure to their correct domain locations.
3. **Phase 3 — Fix cross-domain (80+ files):** Route all cross-domain reads through `ports.py`, writes through `events.py`.
4. **Phase 4 — Create RLS security.py:** Create `infrastructure/database/security.py` as canonical RLS enforcer.
5. **Phase 5 — Fix kernel (1 violation):** Remove domain import from `kernel/rls_context.py`.
6. **Phase 6 — Add missing features.py:** Create for logistics and orders domains.
7. **Phase 7 — Fix allowlist:** Remove `core.users` references from `DOMAIN_ALLOWLIST.yaml`.
