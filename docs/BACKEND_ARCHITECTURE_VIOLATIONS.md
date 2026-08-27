# ZOZI Backend Architecture Violation Report

**Date:** 2026-08-26
**Scope:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend`
**Reference:** ARCHITECTURE_DIAGRAM.md — The Seven Laws

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 37 |
| HIGH | 145 |
| MEDIUM | 15 |
| LOW | 11 |
| **TOTAL** | **208** |

---

## LAW 1: Arrows Point Down Only (modules → domains → infrastructure)

### CRITICAL: infrastructure/ importing domains/ (37 violations)

Infrastructure must import nothing above it. The following files violate this:

| # | File | Line | Import |
|---|------|------|--------|
| 1 | `infrastructure/lifespan.py` | 87 | `from domains.accounts.services.permissions.permission_service import load_role_permission_settings` |
| 2 | `infrastructure/lifespan.py` | 109 | `import domains._service_registry` |
| 3 | `infrastructure/lifespan.py` | 117 | `from domains.finance.services.payments.payments import _event_publisher` |
| 4 | `infrastructure/lifespan.py` | 119 | `from domains.logistics.services.fulfillment_service import FulfillmentService` |
| 5 | `infrastructure/messaging/email_service.py` | 177 | `from domains.governance.models.admin import EmailProviderConfig` |
| 6 | `infrastructure/messaging/email_service.py` | 368 | `from domains.comms.services.email_event_service import ...` |
| 7 | `infrastructure/messaging/downstream_hooks.py` | 20 | `from domains.country import ports as country_ports` |
| 8 | `infrastructure/messaging/downstream_hooks.py` | 33 | `from domains.country import ports as country_ports` |
| 9 | `infrastructure/messaging/downstream_hooks.py` | 45 | `from domains.country import ports as country_ports` |
| 10 | `infrastructure/messaging/downstream_wiring.py` | 30 | `from domains.catalog import ports as _catalog_ports` |
| 11 | `infrastructure/messaging/downstream_wiring.py` | 31 | `from domains.country import ports as _country_ports` |
| 12 | `infrastructure/messaging/downstream_wiring.py` | 32 | `from domains.finance import ports as _finance_ports` |
| 13 | `infrastructure/messaging/realtime.py` | 32 | `from domains.governance import ports as _governance_ports` |
| 14 | `infrastructure/messaging/realtime.py` | 33 | `from domains.comms import ports as _comms_ports` |
| 15 | `infrastructure/messaging/realtime.py` | 34 | `from domains.catalog import ports as _catalog_ports` |
| 16 | `infrastructure/messaging/realtime.py` | 35 | `from domains.finance import ports as _finance_ports` |
| 17 | `infrastructure/security/dependencies.py` | 24 | `from domains.governance.models.user import User` |
| 18 | `infrastructure/security/key_rotation.py` | 44 | `from domains.governance.models.user import User` |
| 19 | `infrastructure/security/key_rotation.py` | 45 | `from domains.comms.models.suppliers import SupplierProfile` |
| 20 | `infrastructure/security/key_rotation.py` | 46 | `from domains.logistics.models.logistics import Shipment, ShipmentEvent, LogisticsPartner` |
| 21 | `infrastructure/security/key_rotation.py` | 47 | `from domains.orders.models.orders import Order` |
| 22 | `infrastructure/security/qr_service.py` | 39 | `from domains.hr.models.employee_models import Employee` |
| 23 | `infrastructure/security/qr_service.py` | 40 | `from domains.governance.models.user import User` |
| 24 | `infrastructure/security/qr_service.py` | 72 | `from domains.hr.models.employee_models import Employee` |
| 25 | `infrastructure/security/qr_service.py` | 73 | `from domains.governance.models.user import User` |
| 26 | `infrastructure/security/qr_service.py` | 119 | `from domains.hr.models.employee_models import Employee` |
| 27 | `infrastructure/security/security_audit.py` | 67 | `from domains.governance import ports as governance_ports` |
| 28 | `infrastructure/media/free_image_tools.py` | 170 | `from domains.finance.services.shared.bg_removal_service import magic_erase` |
| 29 | `infrastructure/ml/worker.py` | 44 | `from domains.finance.services.shared.bg_removal_service import remove_background` |
| 30 | `infrastructure/utils/analytics_service.py` | 2 | `from domains.analytics.services.infrastructure_analytics_service import *` |
| 31 | `infrastructure/utils/command_center_service.py` | 2 | `from domains.governance.services.command_center.service import *` |
| 32 | `infrastructure/utils/command_center_background.py` | 2 | `from domains.governance.services.command_center.background import *` |
| 33 | `infrastructure/utils/import_service.py` | 2 | `from domains.finance.services.data_import_service import *` |
| 34 | `infrastructure/utils/entity_messaging.py` | 2 | `from domains.comms.services.messaging.chat_service import MessagingService` |
| 35 | `infrastructure/utils/export_read.py` | 8 | `from domains.governance.services.export_read_service import ...` |
| 36 | `infrastructure/utils/misc_write.py` | 13 | `from domains.governance.services.misc_write_service import ...` |
| 37 | `infrastructure/utils/workflow_engine.py` | 2 | `from domains.governance.services.workflow_engine import *` |
| 38 | `infrastructure/utils/user_context.py` | 5 | `from domains.governance.models.user import User` (TYPE_CHECKING) |
| 39 | `infrastructure/services/utils/translate_controller.py` | 7 | `from domains.governance.services.translation_service import ...` |
| 40 | `infrastructure/services/utils/workflow_engine.py` | 7 | `from domains.governance.services.workflow_engine import ...` |
| 41 | `infrastructure/database/seed/_common.py` | 326 | `from domains.logistics.services.partners.service import quote_shipping_for_destination` |
| 42 | `infrastructure/observability/audit.py` | 281 | `from domains.governance import ports as governance_ports` |

**Recommended Fix:** All infrastructure→domain imports must be inverted. Domain services should call infrastructure via dependency injection or lazy resolution through a service locator. The `infrastructure/utils/*` files that re-export from domains are backward-compat shims that should be deleted and callers updated to import from domains directly.

---

## LAW 2: Module Routers Stay Thin (auth + require_feature + ONE service call)

### HIGH: Module routers with direct DB writes (78 violations)

Module routers must not perform `db.add()`, `db.commit()`, or `db.delete()`. Business logic belongs in domain services.

| # | File | Lines | Violations |
|---|------|-------|------------|
| 1 | `modules/customer/routers/orders.py` | 104,112,133,134,137,140,148,153,365 | 9 DB writes |
| 2 | `modules/customer/routers/promotions.py` | 175,177,184,185,197,198 | 6 DB writes |
| 3 | `modules/logistics/routers/logistics.py` | 227,228,313,314,494,495,2124,2132,2140 | 9 DB writes |
| 4 | `modules/employee/routers/accounts.py` | 90,146 | 2 DB writes |
| 5 | `modules/employee/routers/finance.py` | 728,835,847,859,877,889,902,915,935,947,959,988,1001,1027,1040 | 15 DB writes |
| 6 | `modules/employee/routers/comms/email.py` | 218,247,248,272,273,296,310,311,364,365,379,397 | 12 DB writes |
| 7 | `modules/employee/routers/comms/tickets.py` | 75,78,79,106,107,127,128 | 7 DB writes |
| 8 | `modules/employee/routers/suppliers.py` | 146,149,150,177,178,198,199 | 7 DB writes |
| 9 | `modules/employee/routers/hr/ess.py` | 84,140 | 2 DB writes |
| 10 | `modules/employee/routers/hr/employees_part2.py` | 47 | 1 DB write |
| 11 | `modules/employee/routers/hr/hierarchy.py` | 121,124,156,202,249,259,281,292 | 8 DB writes |

**Recommended Fix:** Extract all DB write operations into domain service methods. Routers should only call `service.do_operation(db, ...)` and return the result.

---

## LAW 3: Cross-Domain Writes via Events, Reads via ports.py/read_models

### HIGH: Direct cross-domain imports (67 violations)

Domains must not import from other domains except through `ports.py` (reads) or `events.py`/`subscribers.py` (writes).

| # | File | Line | Cross-Domain Import |
|---|------|------|---------------------|
| 1 | `domains/orders/services/trading_service.py` | 7-26 | `from domains.finance.services.trading_service import ...` (20 symbols) |
| 2 | `domains/analytics/services/flat_admin_dashboard_service.py` | 16-27 | 11 cross-domain model imports (governance, catalog, finance, hr, logistics) |
| 3 | `domains/analytics/services/flat_ai_upload_controller.py` | 7 | `from domains.comms.services.shared.utility.shared_utils import create_job` |
| 4 | `domains/accounts/services/users/users_admin_service/__header___p3.py` | 9-20 | 12 cross-domain model imports (governance, catalog, comms) |
| 5 | `domains/accounts/services/users/users_admin_service/__header___p2_p2.py` | 10-20 | 11 cross-domain model imports (governance, catalog) |
| 6 | `domains/accounts/services/users/users_admin_service/__header___p2_p1.py` | 9-30 | 21 cross-domain model imports (governance, catalog, comms, finance) |
| 7 | `domains/analytics/services/dashboards/analytics_service.py` | 13-18 | 6 cross-domain model imports (governance, catalog, orders) |
| 8 | `domains/accounts/ports.py` | 34 | `from domains.security.models.security_schema_models import ...` |
| 9 | `domains/accounts/models/onboarding.py` | 10 | `from domains.security.models.security_schema_models import ...` |
| 10 | `domains/analytics/services/system_comms_status_service.py` | 3-6 | `from domains.customers.services.public_comms_status_service import ...` |
| 11 | `domains/analytics/services/system_comms_status_service.py` | 25-29 | `from domains.comms.services.messaging.chat.chat_write_service import ...` |

**Recommended Fix:** Route all cross-domain reads through the owning domain's `ports.py`. For example, `domains/finance/services/trading_service` should be accessed via `domains/finance/ports.py`. Cross-domain writes should use `events.py`/`subscribers.py`.

---

## LAW 1 (continued): Domains Importing Modules

### CRITICAL: Domain service importing modules (1 violation in comment only)

The search found only one reference in `domains/accounts/services/auth/auth_service.py:1374` which is a **comment**, not an active import. No active violations found.

---

## Controllers in Domain Layer (Law 1 structural violation)

### MEDIUM: Controller files in domains/ (8 violations)

Per ARCHITECTURE_DIAGRAM.md, domain layer must not contain controller files. Controllers belong only in modules layer.

| # | File | Issue |
|---|------|-------|
| 1 | `domains/analytics/services/analytics_controller.py` | Controller shim in domain services |
| 2 | `domains/analytics/services/ai_upload_controller.py` | Controller with FastAPI UploadFile import |
| 3 | `domains/analytics/services/flat_ai_upload_controller.py` | Controller shim in domain services |
| 4 | `domains/security/services/health/risk_controller.py` | Controller with route decorators (`@get`, `@post`) |
| 5 | `domains/orders/services/logistics_partner_controller.py` | Controller re-export shim |
| 6 | `domains/accounts/services/users/users_admin_service/__header___p3.py` | Controller (docstring: "Admin users controller") |
| 7 | `domains/accounts/services/users/users_admin_service/__header___p2_p2.py` | Controller (docstring: "Admin users controller") |
| 8 | `domains/accounts/services/users/users_admin_service/__header___p2_p1.py` | Controller (docstring: "Admin users controller") |

**Recommended Fix:** Move controller logic to `modules/{module}/routers/{domain}.py`. Domain services should return data, not HTTP responses.

---

## Domains Importing FastAPI (Architectural Smell)

### MEDIUM: Domain services importing FastAPI primitives (7 violations)

Domain services should not import `HTTPException`, `Depends`, `Query`, or `WebSocket` from FastAPI. These are HTTP concerns that belong in the module layer.

| # | File | Line | Import |
|---|------|------|--------|
| 1 | `domains/accounts/services/users/users_admin_service/__header___p3.py` | 6 | `from fastapi import HTTPException` |
| 2 | `domains/accounts/services/users/users_admin_service/__header___p2_p2.py` | 7 | `from fastapi import HTTPException` |
| 3 | `domains/accounts/services/users/users_admin_service/__header___p2_p1.py` | 6 | `from fastapi import HTTPException` |
| 4 | `domains/analytics/services/dashboards/analytics_service.py` | 9 | `from fastapi import HTTPException` |
| 5 | `domains/analytics/services/ai_upload_controller.py` | 4 | `from fastapi import UploadFile` |
| 6 | `domains/analytics/services/flat_ai_upload_controller.py` | 8 | `from fastapi import UploadFile` |
| 7 | `domains/analytics/services/system_comms_status_service.py` | 15 | `from fastapi import WebSocket, WebSocketDisconnect, Depends, Query` |

**Recommended Fix:** Domain services should raise domain exceptions (e.g., `NotFoundError`, `ValidationError`). Module routers catch these and convert to `HTTPException`.

---

## LAW 7: Allowlist Rule — DOMAIN_ALLOWLIST.yaml

### LOW: 37 temporary cross-domain import entries

The `DOMAIN_ALLOWLIST.yaml` contains 37 entries of sanctioned temporary cross-domain imports. Per Law 7, this list must only shrink.

Key categories:
- 3 entries: `core.users` FK references (sanctioned)
- 5 entries: Cross-domain service imports (finance → comms, governance, logistics, suppliers)
- 6 entries: Cross-domain model imports for read-only query building
- 5 entries: Controller logic in domain services (FastAPI imports)
- 1 entry: Unbounded `.all()` queries
- 2 entries: OFFSET pagination
- 11 entries: Cross-domain Payout model references
- 3 entries: Payment gateway base classes
- 1 entry: Notes

**Recommended Fix:** Create a migration plan to eliminate entries systematically. Priority: controller logic in domain services (5 entries), cross-domain service imports (5 entries), then model imports.

---

## infrastructure/utils/ Backward-Compat Shims

### LOW: 10 infrastructure/utils/ files re-exporting from domains

These files violate Law 1 by importing from domains. They are backward-compat shims that should be deleted.

| # | File | Re-exports From |
|---|------|-----------------|
| 1 | `infrastructure/utils/analytics_service.py` | `domains.analytics.services.infrastructure_analytics_service` |
| 2 | `infrastructure/utils/command_center_service.py` | `domains.governance.services.command_center.service` |
| 3 | `infrastructure/utils/command_center_background.py` | `domains.governance.services.command_center.background` |
| 4 | `infrastructure/utils/import_service.py` | `domains.finance.services.data_import_service` |
| 5 | `infrastructure/utils/entity_messaging.py` | `domains.comms.services.messaging.chat_service` |
| 6 | `infrastructure/utils/export_read.py` | `domains.governance.services.export_read_service` |
| 7 | `infrastructure/utils/misc_write.py` | `domains.governance.services.misc_write_service` |
| 8 | `infrastructure/utils/workflow_engine.py` | `domains.governance.services.workflow_engine` |
| 9 | `infrastructure/services/utils/translate_controller.py` | `domains.governance.services.translation_service` |
| 10 | `infrastructure/services/utils/workflow_engine.py` | `domains.governance.services.workflow_engine` |

**Recommended Fix:** Update all callers to import from the canonical domain location, then delete these shim files.

---

## Two DeclarativeBase Classes Issue

### INFO: Only one DeclarativeBase found

Only one `DeclarativeBase` was found at `infrastructure/database/base.py:6`. The empty `db.base.Base` mentioned in AGENTS.md was not found at the expected location. The `infrastructure/database/models.py` is now an empty facade that correctly does NOT walk the domains package.

---

## _auto_stubs.py Files

### INFO: No _auto_stubs.py files found

No `_auto_stubs.py` files were found in the codebase. Either they have been cleaned up or were already replaced with real implementations.

---

## Root-Level Forbidden Directories

### INFO: No forbidden root-level directories found

The backend root contains only the canonical packages: `alembic/`, `domains/`, `infrastructure/`, `jobs/`, `kernel/`, `middleware/`, `modules/`, `providers/`, `rbac/`, `scripts/`, `tests/`. No root-level `utils/`, `routers/`, `controllers/`, `services/`, `models/`, or `db/` directories exist.

---

## Middleware Location

### INFO: Middleware correctly located

All middleware files are correctly located at `backend/middleware/` (23 files). No middleware found at `backend/infrastructure/middleware/`.

---

## Providers Importing Domains

### INFO: No active domain imports in providers

Only one comment reference found in `providers/ai/text.py:393`. No active domain imports in providers. Providers correctly wrap SDKs only.

---

## Summary by Severity

| Severity | Category | Count |
|----------|----------|-------|
| CRITICAL | infrastructure/ importing domains/ | 42 |
| HIGH | Module routers with DB writes | 78 |
| HIGH | Direct cross-domain imports | 67 |
| MEDIUM | Controllers in domain layer | 8 |
| MEDIUM | Domains importing FastAPI | 7 |
| LOW | infrastructure/utils/ backward-compat shims | 10 |
| LOW | DOMAIN_ALLOWLIST.yaml entries | 37 |
| **TOTAL** | | **249** |

---

## Top Priority Fixes

1. **Module routers with DB writes (78 violations)** — Extract all `db.add/commit/delete` calls into domain service methods. This is the largest single category of violations.

2. **infrastructure/ importing domains/ (42 violations)** — The `infrastructure/lifespan.py`, `infrastructure/messaging/*`, and `infrastructure/security/*` files must be refactored to use lazy resolution or dependency injection instead of direct domain imports.

3. **Direct cross-domain imports (67 violations)** — The `domains/accounts/services/users/users_admin_service/__header__*.py` files are the worst offenders, importing from 4+ other domains. These must be refactored to use `ports.py`.

4. **Controllers in domain layer (8 violations)** — Move controller logic (route decorators, HTTP concerns) to `modules/{module}/routers/`.

5. **infrastructure/utils/ backward-compat shims (10 violations)** — Delete these files and update callers to import from canonical domain locations.
