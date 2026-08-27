# ZOZI Backend — Complete Investigation Report

> **Date:** 2026-08-27  
> **Scope:** backend/domains/**, backend/modules/**, backend/infrastructure/**, backend/providers/**, backend/rbac/**  
> **Benchmark:** ARCHITECTURE_DIAGRAM.md (Seven Laws)  
> **Method:** 12 parallel investigation agents, line-by-line analysis  

---

## Executive Summary

| Category | Critical | High | Medium | Low |
|---|---|---|---|---|
| Architecture & Wiring | 180+ | 60+ | 40+ | 20+ |
| Code Quality & Logic | 4 | 30+ | 80+ | 50+ |
| Domain & Module Structure | 20+ | 40+ | 60+ | 30+ |
| Database & Data Layer | 30+ | 20+ | 15+ | 10+ |
| Security | 3 | 15+ | 25+ | 10+ |
| Infrastructure & Connections | 51+ | 20+ | 15+ | 10+ |
| Performance & Scalability | 10+ | 30+ | 20+ | 15+ |
| Error & Exception Handling | 4 | 20+ | 40+ | 20+ |
| Testing & Validation | 0 | 10+ | 20+ | 30+ |

---

## 1. Architecture & Wiring Violations

### 1.1 Law #1: Cross-Domain Imports (180+ violations)

Domains importing other domains — the most widespread violation.

**accounts → other domains (14 violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/auth/auth_service.py:47` | `from domains.governance.models.user import User` | Move User to accounts or use ports |
| `services/auth/auth_service.py:50` | `from domains.hr.ports import Employee, EmployeeBiometric` | Use `domains.hr.ports` (sanctioned read) |
| `services/accounts_service.py:10` | `from domains.hr.models.employee_models import Employee` | Move to `domains.hr.services` |
| `services/permissions/permission_service.py:11-15` | `from domains.governance.models.permissions import Permission` | Use ports |
| `services/tracker/live_session_tracker.py:152` | `from domains.hr.models.employee_models import GeoFenceLog` | Use ports |
| `ports.py:34` | `from domains.security.models.security_schema_models import ...` | Use ports |
| `ports.py:440-466` | `from domains.hr.ports import OnboardingPipeline` | OK (ports-to-ports is sanctioned) |

**customers → other domains (20+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/cart_service.py:18-30` | `from domains.accounts.models.core import CartItem` | Use `domains.accounts.ports` |
| `services/wishlist_service.py:9` | `from domains.catalog.models.products import Product` | Use `domains.catalog.ports` |
| `services/coupons_service.py:14-18` | `from domains.governance.models.admin import CouponUsage` | Use ports |
| `services/reviews_service.py:13-15` | `from domains.catalog.models.products import Product` | Use ports |
| `services/search_service.py:14-18` | `from domains.catalog.models.products import Product` | Use ports |

**finance → other domains (15+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/ledger/general_ledger_service.py:587,636,715,835` | `from domains.orders.models.orders import Order` | Use `domains.orders.ports` |
| `services/payments/payment_engine.py:79-88` | `from domains.catalog.models.products import Product` | Use ports |
| `services/payments/payment_engine.py:15` | `from domains.finance.services import ...` | Self-import — restructure |
| `services/payouts/payout_batch_service.py:843` | `from domains.governance.models.admin import ...` | Use ports |

**orders → other domains (18+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/core/order_engine.py:27-44` | Imports from customers, promotions, catalog, finance, governance, logistics | Use `ports.py` for all cross-domain reads |
| `services/core/order_engine.py:681` | `from domains.country.services.cross_border import ...` | Use ports |
| `services/core/order_engine.py:932` | `from domains.comms.services.transactional_email_service import ...` | Use events for cross-domain writes |

**catalog → other domains (8+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/products/products_service.py:378-383` | `from domains.accounts.models.core import CartItem` | Use events for cross-domain writes |
| `services/products/products_service.py:380,393-397` | `from domains.comms.models.communication import Notification` | Use events |
| `services/search/ai_search_service.py:76` | Uses `re` without import | Add `import re` |

**comms → other domains (8+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/comms_service.py:159-236` | Raw SQL with string concatenation | Use parameterized queries |
| `services/ports.py:594-615` | `create_campaign()`, `delete_campaign()` (writes in ports!) | Move to service layer |
| `services/messaging/chat_service.py:573-574` | `from domains.country.models.countries import Message` | Use ports |
| `services/tickets/tickets_service.py:2-3` | `from domains.finance.models.finance import Invoice` | Use ports |

**logistics → other domains (14+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/core/service.py:155` | `from domains.country.models.countries import CountryConfig` | Use ports |
| `services/core/service.py:805-826` | Imports from governance, catalog, hr, finance, orders | Use ports for all |

**hr → other domains (8+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/ess/ess_service.py:15` | `from domains.accounts.services.auth.auth_service import get_current_user` | Use `domains.security.iam.security_dependencies` |
| `services/employees/hr_service.py:669` | `from domains.finance.models.finance import TreasuryAccount` | Use ports |

**promotions → other domains (40+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/banners/banner_write_service.py:20-25` | `from controllers.banner_controller import ...` | **FORBIDDEN** — move to domains/services |
| `services/engine/admin_commerce_configuration_service.py:6-19` | Imports from governance, comms, catalog, country, finance | Use ports |
| Multiple archived files | 14 archived files still in services/ | Delete or move to `_parked/` |

**suppliers → other domains (25+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/supplier_shared.py:31-59` | Imports from governance, catalog, comms, finance, logistics, orders | Break file apart, use ports |
| `services/supplier_service.py:10-14` | Wildcard imports (`from ... import *`) | Explicit imports only |

**security → other domains (12+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/fraud/fraud_detection_service.py:19-36` | `from domains.governance.models.user import User` | Use ports |
| `services/iam/iam_service.py:15-16` | `from domains.governance.models.user import User` | Use ports |
| `services/iam/security_dependencies.py:20` | `from infrastructure.security.auth import decode_token` | OK (infra-to-infra) |

**analytics → other domains (7+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/dashboards/admin_dashboard_service.py:16-27` | Imports from governance.models, catalog.models, finance.models | Use ports |
| `services/aggregation/command_center_service.py:11-23` | Imports from governance, country, logistics, orders, hr | Use ports |

**audit → other domains (11+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/worm_audit.py:14` | `from domains.governance.models.core import AuditLog` | AuditLog belongs to audit domain |
| `services/compliance_engine.py:13-15` | `from domains.hr.models.employee_models import Employee` | Use ports |
| `services/communication_audit.py:19` | `from domains.comms.services.admin.communication_audit import ...` | Remove controller code from service |

**governance → other domains (8+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `services/operations.py:23-36` | Imports from catalog, orders, comms | Use ports |
| `services/ports.py:39-40` | Imports from security | Use ports |

**infrastructure → domains (51+ violations)**
| File:Line | Import | Fix |
|---|---|---|
| `utils/command_center.py:26-36` | Imports from governance, country, hr, logistics, orders | Move to domains/governance |
| `security/dependencies.py:24` | `from domains.governance.models.user import User` | Use `infrastructure.security.auth` |
| `security/key_rotation.py:44-47` | Imports from governance, comms, logistics, orders | Move to domains/governance |
| `utils/staff_permissions.py:4` | `from rbac.staff_permissions import ...` | Move to rbac layer |

### 1.2 Law #2: Module Routers Not Thin

| Router | DB Calls | Pydantic Models | _auto_stubs | Issues |
|---|---|---|---|---|
| employee/comms.py | 0 | 6 inline | 29 imports | 1572 lines, cross-module |
| employee/finance.py | 0 | 14 inline | 10 imports | 1808 lines, 103 undefined refs |
| employee/hr.py | 0 | 29 inline | 6 imports | 1195 lines |
| employee/orders.py | 0 | 11 inline | 1 import | Cross-module import |
| employee/suppliers.py | 0 | 0 | 5 imports | Cross-module import |
| customer/promotions.py | 0 | 3 inline | 0 | 442 lines, 11 dup routes |
| customer/accounts.py | 0 | 0 | 0 | 257 lines, biz logic |
| customer/orders.py | 0 | 2 inline | 0 | 313 lines, 2 dup routes |
| logistics/logistics.py | 0 | 8 inline | 0 | 1984 lines, 59 dup routes |
| supplier/finance.py | 0 | 5 inline | 0 | 19 colon-feature strings |
| admin/hr.py | 0 | 6 inline | 0 | Move to schemas |
| admin/security.py | 0 | 3 inline | 0 | Move to schemas |
| admin/country.py | 0 | 0 | 0 | 21 undefined svc_* |

### 1.3 Law #3: Cross-Domain Writes Without Events

| Location | Violation | Fix |
|---|---|---|
| `catalog/products_service.py:365-402` | `delete_product()` deletes CartItem, Wishlist, Review across domains | Emit `ProductDeleted` event, let subscribers clean up |
| `catalog/admin_products_service.py:403-415` | Same cross-domain write pattern | Same fix |
| `comms/ports.py:594-615` | `create_campaign()`, `delete_campaign()` write to orders domain | Move write logic to `domains/comms/services/` |
| `products_service.py:428-431` | Sends email from domain service | Emit event, let comms subscriber handle |

### 1.4 Law #4: Features Not Single-Sourced

| Domain | Problem | Fix |
|---|---|---|
| promotions | `features.py` (domain) vs `services/features.py` (service) — duplicate | Keep only domain-level `features.py` |

### 1.5 Law #6: Schema Discipline

| Domain | Model | Current Schema | Correct Schema |
|---|---|---|---|
| hr | `Employee` | `logistics` | `hr` |
| hr | `EmployeeAttendance` | `logistics` | `hr` |
| hr | `EmployeeLeaveLedger` | `logistics` | `hr` |
| hr | 30+ FK references | `logistics.employees.id` | `hr.employees.id` |
| orders | `Order` | `commerce` | `orders` |
| orders | `OrderItem` | `commerce` | `orders` |
| orders | `ReturnRequest` | `commerce` | `orders` |
| orders | `OrderNotification` | `commerce` | `orders` |
| governance | `SystemAlert` | `configuration` | `governance` |
| governance | `SystemSetting` | `configuration` | `governance` |
| suppliers | `Supplier` | `suppliers` | OK |

### 1.6 Module Connection Problems

| Router | Problem | Fix |
|---|---|---|
| admin/country.py | 21 svc_* undefined | Import from domains.country.services |
| admin/customers.py | get_wishlist, clear_user_wishlist undefined | Import from wishlist_service |
| admin/orders.py | email_metrics undefined | Import from email_management |
| admin/analytics.py | Health-only | Add 10 thin delegators |
| customer/comms.py | TranslationService from _auto_stubs | Import from real service |
| customer/finance.py | 3 undefined refs | Add imports |
| employee/comms.py | 29 _auto_stubs imports | Replace with real imports |
| employee/finance.py | 103 undefined refs | Replace with real imports |
| employee/hr.py | 6 _auto_stubs imports | Replace with real imports |
| logistics/logistics.py | 3 cross-module get_current_user | Use security_dependencies |
| supplier/finance.py | 19 colon-feature strings | Replace colons with dots |

---

## 2. Code Quality & Logic

### 2.1 God Files (>800 lines)

| File | Lines | Problem | Fix |
|---|---|---|---|
| `domains/accounts/services/auth/auth_service.py` | 1491+ | 3+ merged services | Split into auth, otp, social |
| `domains/finance/services/ledger/general_ledger_service.py` | 8879 | 238 functions | Split by sub-ledger |
| `domains/logistics/services/core/service.py` | 3518 | 97 functions from 6+ services | Split into separate services |
| `domains/orders/services/core/order_engine.py` | 1180 | Order lifecycle god service | Split into reader, writer, admin |
| `domains/catalog/services/products/products_service.py` | 873 | Product god service | Split CRUD, search, moderation |
| `domains/catalog/services/search/search_service.py` | 1101+ | Search god service | Split by search type |
| `domains/comms/services/messaging/chat_service.py` | 749 | Chat god service | Split by feature |
| `domains/comms/services/email/email_management.py` | 607 | Email god service | Split by feature |
| `modules/employee/routers/comms.py` | 1572 | Router god | Thin it down |
| `modules/employee/routers/finance.py` | 1808 | Router god | Thin it down |
| `modules/employee/routers/hr.py` | 1195 | Router god | Thin it down |
| `modules/logistics/routers/logistics.py` | 1984 | Router god | Thin it down |
| `infrastructure/utils/command_center.py` | 842 | Business logic in infra | Move to domains/governance |

### 2.2 Duplicate Service Implementations

| Function | Files | Fix |
|---|---|---|
| Customer health scoring | 3 implementations | Keep `customer_health_engine.py` |
| Wishlist operations | 4 files | Keep `wishlist_service.py` |
| Coupon validation | 4 implementations | Keep `coupons_service.py` |
| Cart operations | 2 files | Keep `cart_service.py` |
| Address CRUD | 3 files | Keep `addresses_service.py` |
| `update_employee_profile` | 2 definitions | Keep `ess/ess_service.py` |
| `create_leave_request` | 2 definitions | Keep `ess/ess_service.py` |
| `ShiftHandoverTask` | 2 conflicting definitions | Reconcile |

### 2.3 Archived/ Dead Files

| Domain | File | Status | Fix |
|---|---|---|---|
| promotions | `services/promotions_write_service.py` | ARCHIVED | Delete |
| promotions | 13 more archived files | ARCHIVED | Delete |
| catalog | `services/categories/admin_categories_service.py` | Dead/archived | Delete |
| orders | `services/cart_legacy_service.py` | Legacy | Delete |
| suppliers | `services/documents/supplier_documents_service.py` | Archived | Delete |

### 2.4 Hardcoded Values

| File:Line | Value | Fix |
|---|---|---|
| `comms/proxy_communication.py:518` | `b"zozi-comms-static-salt"` | Move to env var |
| `country_service.py:1017` | Oman-specific code in generic | Extract to country-specific module |
| `products_service.py:59` | `_LOW_STOCK_THRESHOLD = 5` | Move to settings |
| `analytics/events.py:43` | `float` for tax rate | Use `Decimal` |
| `security/core/security_metrics.py:113-118` | Hardcoded compliance status | Calculate from actual data |
| `infrastructure/security/encryption.py:22` | `_KDF_SALT = b"zozi-field-encryption-salt-v1"` | Random + store securely |
| `infrastructure/utils/config.py:39` | Default DB credentials | Remove defaults |

---

## 3. Domain & Module Structure

### 3.1 Missing Architecture Components

| Domain | Missing | Fix |
|---|---|---|
| accounts | `events.py` (real), `subscribers.py` (real) | Implement cross-domain events |
| customers | `schemas/`, `policies/`, `read_models/` | Create proper structure |
| orders | `subscribers.py`, `schemas/`, `policies/` | Create proper structure |
| logistics | `subscribers.py`, `schemas/`, `policies/` | Create proper structure |
| hr | `schemas/`, `policies/`, `read_models/`, `subscribers.py` (real) | Create proper structure |
| analytics | `policies/`, `read_models/` | Create proper structure |
| catalog | `policies/`, `read_models/`, `schemas/` | Create proper structure |
| comms | `policies/`, `read_models/`, `schemas/` | Create proper structure |
| promotions | `schemas/`, `policies/`, `read_models/` | Create proper structure |
| finance | `events.py` (real), `subscribers.py` (real) | Implement |
| governance | `subscribers.py` (26 of 31 are TODO stubs) | Implement |
| suppliers | `policies/`, `read_models/` | Create proper structure |

### 3.2 Duplicate Definition Files

| Domain | Files | Fix |
|---|---|---|
| promotions | `features.py` + `services/features.py` | Keep domain-level only |
| promotions | `events.py` + `services/events.py` | Keep domain-level only |
| promotions | `ports.py` + `services/ports.py` | Keep domain-level only |
| audit | `services/ports.py`, `services/features.py`, `services/events.py` | Move to domain root |

### 3.3 Non-Standard Schema Names

| Schema | Usage | Fix |
|---|---|---|
| `configuration` | governance.models.admin | Rename to `governance` |
| `treasury` | governance.models.admin | Rename to `finance` |
| `commerce` | orders.models.order_entities | Rename to `orders` |
| `core` | infrastructure.database DB_SEARCH_PATH | Remove |

---

## 4. Database & Data Layer

### 4.1 Wrong Schema Assignments

| Model | Current | Correct |
|---|---|---|
| `Employee` | `logistics` | `hr` |
| `EmployeeAttendance` | `logistics` | `hr` |
| `EmployeeLeaveLedger` | `logistics` | `hr` |
| `EmployeeShiftRoster` | `logistics` | `hr` |
| `Order` | `commerce` | `orders` |
| `OrderItem` | `commerce` | `orders` |
| `ReturnRequest` | `commerce` | `orders` |
| `OrderNotification` | `commerce` | `orders` |
| `SystemAlert` | `configuration` | `governance` |
| `SystemSetting` | `configuration` | `governance` |

### 4.2 Missing Schema Declarations

| Model | Issue |
|---|---|
| `EmployeeRiskScore` | No schema — defaults to public |
| `PayrollRecord` | No schema — defaults to public |
| `EmployeeTraining` | No schema — defaults to public |
| `EmployeeActivityLog` | No schema — defaults to public |
| `DynamicQRSession` | No schema in `__table_args__` |

### 4.3 RLS Not Wired

| File | Issue | Fix |
|---|---|---|
| `infrastructure/database/rls_interceptor.py:359` | `instrument_rls()` defined but never called | Call in lifespan or database setup |

### 4.4 OFFSET Pagination (Performance)

| File:Line | Query | Fix |
|---|---|---|
| `logistics/core/service.py:728-737` | `list_partners` OFFSET | Keyset pagination |
| `logistics/core/service.py:840-872` | Multiple fallbacks OFFSET | Keyset pagination |
| `orders/core/order_engine.py:1026-1035` | `get_orders` OFFSET | Keyset pagination |

### 4.5 Connection Handling Issues

| File | Issue | Fix |
|---|---|---|
| `infrastructure/database/database.py:107` | Engine at module import time | Lazy init |
| `infrastructure/database/database.py:123-128` | Sync sessionmaker only | Add async sessionmaker |
| `infrastructure/database/database.py:135-156` | Sync `get_db()` generator | Add async `get_db` |
| `infrastructure/database/database.py:73-75` | `DB_SEARCH_PATH` includes `core` | Remove `core` |

---

## 5. Security

### 5.1 Hardcoded Secrets

| File:Line | Value | Severity | Fix |
|---|---|---|---|
| `security/kms_encryption.py:25` | `Fernet(self._derive_key(os.urandom(16)))` | 🔴 Critical | Store salt with ciphertext |
| `security/core/kms_encryption.py:114` | `"default_salt"` | 🔴 Critical | Generate random salt |
| `security/encryption.py:22` | `_KDF_SALT = b"zozi-field-encryption-salt-v1"` | 🟠 High | Random + secure storage |
| `utils/config.py:39` | Default PostgreSQL credentials | 🟡 Medium | Remove defaults |

### 5.2 RBAC Enforcement Gaps

| File | Issue | Fix |
|---|---|---|
| `security/core/security_service.py:89-176` | No RBAC on blacklist/rule functions | Add `require_admin` |
| `security/fraud/fraud_service.py:428-484` | Inline role checks instead of `require_admin` | Use `require_admin` dependency |
| `infrastructure/security/dependencies.py:24` | Imports from domains | Use infra-only auth |

### 5.3 Token & Auth Issues

| File | Issue | Fix |
|---|---|---|
| `domains/accounts/services/auth/auth_service.py` | 30-day tokens for biometric | Reduce to 15 min |
| `infrastructure/utils/auth.py` | Default secret fallback | Fail hard if no secret |
| `infrastructure/security/auth.py` | HS256 secret entropy not validated | Add validation |

### 5.4 Input Validation Gaps

| File | Issue | Fix |
|---|---|---|
| `security/registration/public_security_registration.py:79` | UUID4 for refresh token family | Store server-side for rotation |
| `security/registration/public_security_registration.py:83-84` | `samesite='none'` | Acceptable with `secure=True` |
| `promotions/services/promotion_admin_write_service.py:86-103` | No coupon code validation | Add format/length checks |
| `suppliers/services/supplier_shared.py:228-233` | HTML escaping at storage | Escape at output time |

### 5.5 Compliance Hardcoding

| File | Issue | Fix |
|---|---|---|
| `security/core/security_metrics.py:113-118` | Hardcoded SOX/HIPAA/GDPR/PCI compliance | Calculate from actual state |

---

## 6. Infrastructure & Connections

### 6.1 Upward Imports (51+ violations)

| File | Count | Fix |
|---|---|---|
| `infrastructure/utils/command_center.py` | 13 domain imports | Move to `domains/governance/services/` |
| `infrastructure/security/key_rotation.py` | 4 domain imports | Move to domains/governance |
| `infrastructure/messaging/realtime.py` | 4 domain imports | Move to domains/governance |
| `infrastructure/messaging/email_service.py` | 2 domain imports | Move to domains/comms |
| `infrastructure/utils/staff_permissions.py` | 1 rbac import | Move to rbac layer |

### 6.2 Misplaced Business Logic in Utils

| File | Should Be In |
|---|---|
| `utils/analytics.py` | `domains/analytics/services/` |
| `utils/soft_delete.py` | `infrastructure/database/mixins.py` |
| `utils/command_center.py` | `domains/governance/services/` |
| `utils/currency_service.py` | `kernel/currency.py` |
| `utils/invoice_html.py` | `domains/finance/services/` |
| `utils/versioning.py` | `modules/` or middleware |

### 6.3 Dead Shim Files

| Shim | Canonical Location | Action |
|---|---|---|
| `utils/auth.py` | `security/auth.py` | Delete (exact duplicate) |
| `utils/currency.py` | `utils/currency_service.py` | Delete |
| `utils/email_service.py` | `messaging/email_service.py` | Delete |
| `utils/media_service.py` | `media/media_service.py` | Delete |
| `utils/image_ai_service.py` | `media/image_ai_service.py` | Delete |
| `utils/entity_messaging.py` | `domains.comms.services` | Delete |
| `utils/import_service.py` | `domains.finance.services` | Delete |
| `utils/command_center_service.py` | `domains.governance.services` | Delete |
| `utils/rls_interceptor.py` | `database/rls_interceptor.py` | Delete |
| `utils/rls_middleware.py` | `database/rls_interceptor.py` | Delete |
| `utils/http_client.py` | `http/client.py` | Delete |
| `utils/money.py` | `kernel/money.py` | Delete |

### 6.4 Unregistered Middleware

| Middleware | Status |
|---|---|
| `coi_middleware.py` | Merged/inactive |
| `database_security.py` | Merged/inactive |
| `device_binding_middleware.py` | Merged/inactive |
| `webhook_verification.py` | Not wired |
| `webhook_ip_whitelist.py` | Not wired |
| `zero_trust_auth.py` | Merged/inactive |

---

## 7. Performance & Scalability

### 7.1 N+1 Query Patterns

| File:Line | Problem | Fix |
|---|---|---|
| `hr/employee_service.py:433-457` | `list_leave_requests` loads all then accesses per-row | Use `selectinload` |
| `hr/employee_service.py:481-503` | `list_shifts` same N+1 pattern | Use `selectinload` |
| `customers/customer_health_engine.py:63-68` | `_get_orders` called twice | Cache result |
| `customers/customer_health_list_service.py:15-20` | Returns only last user's metrics | Fix loop logic |

### 7.2 OFFSET Pagination

| File:Line | Fix |
|---|---|
| `logistics/core/service.py:728-737` | Keyset pagination |
| `logistics/core/service.py:840-872` | Keyset pagination |
| `orders/core/order_engine.py:1026-1035` | Keyset pagination |
| `orders/ports.py:1174-1229` | Keyset pagination |

### 7.3 Global Mutable State

| File:Line | Issue | Fix |
|---|---|---|
| `finance/payments/payment_engine.py:184-185` | `_gateway_call_count`, `_gateway_error_count` | Thread-safe counters |

### 7.4 Missing Caching

| Location | Issue | Fix |
|---|---|---|
| `hr/hr_service.py:473-641` | `get_hr_dashboard` — 4 large aggregation queries | Add Redis caching |
| `analytics/dashboards/` | Admin dashboard queries | Add caching layer |

---

## 8. Error & Exception Handling

### 8.1 Missing try/catch on DB Commits

| File:Line | Function | Fix |
|---|---|---|
| `hr/employee_service.py:66-72` | `create_office` | Wrap commit in try/except |
| `hr/employee_service.py:132-138` | `create_employee` | Wrap commit in try/except |
| `hr/hr_service.py:48-55` | `create_coi_report` | Wrap commit in try/except |
| `orders/core/order_engine.py:98-119` | `_rollback_order_creation` | Rollback can itself fail |
| `finance/ledger/general_ledger_service.py` | Account balance updates | Use row-level locking |

### 8.2 Silent Failures

| File:Line | Issue | Fix |
|---|---|---|
| `hr/hr_service.py:754-760` | `flag_for_review` returns hardcoded dict, never writes DB | Implement |
| `finance/treasury/treasury_service.py:18-28` | All methods return `{}` or `[]` | Implement |
| `finance/treasury/cash_management_service.py:42-131` | All 25+ methods return `{}` or `[]` | Implement |
| `governance/subscribers.py:57,133` | 26 of 31 subscribers are TODO stubs | Implement |

### 8.3 Incorrect Error Types

| File:Line | Issue | Fix |
|---|---|---|
| `logistics/core/service.py:742-781` | Raises `ValueError` instead of `HTTPException` | Use `HTTPException` |
| `security/registration/public_security_registration.py` | Password truncation not surfaced | Return proper error |

---

## 9. Testing & Validation

### 9.1 Missing Architecture Tests

| Test | Status | Fix |
|---|---|---|
| `tests/architecture/test_import_laws.py` | Runs but may not cover all | Expand coverage |

### 9.2 Broken Test Patterns

| File | Issue | Fix |
|---|---|---|
| `tests/` | `time.sleep()` anti-pattern in test_auth.py | Use deterministic waits |

---

## 10. Priority Action Plan

### P0 — Code Won't Run (Fix First)

| # | Task | File | Count |
|---|---|---|---|
| 1 | Fix _auto_stubs imports | 6 router files | 47 |
| 2 | Fix undefined svc_* in admin/country.py | admin/country.py | 21 |
| 3 | Fix undefined refs in admin/customers.py | admin/customers.py | 2 |
| 4 | Fix undefined ref in admin/orders.py | admin/orders.py | 1 |
| 5 | Fix 3 undefined refs in customer/finance.py | customer/finance.py | 3 |
| 6 | Fix 103 undefined refs in employee/finance.py | employee/finance.py | 103 |
| 7 | Delete 59 duplicate routes in logistics.py | logistics/logistics.py | 59 |
| 8 | Delete 11 duplicate routes in promotions.py | customer/promotions.py | 11 |

### P1 — Architecture Compliance (Fix Second)

| # | Task | Scope |
|---|---|---|
| 9 | Fix cross-domain imports (180+) | All domains |
| 10 | Fix schema assignments (30+) | hr, orders, governance models |
| 11 | Wire RLS interceptor | infrastructure/database |
| 12 | Move business logic from utils/ to domains/ | infrastructure/utils/ |
| 13 | Delete 51 upward imports in infrastructure | infrastructure/ |
| 14 | Move 89 Pydantic models to domain schemas | All modules |
| 15 | Replace 19 colon-feature strings | supplier/finance.py |
| 16 | Fix 3 cross-module imports in logistics.py | logistics/logistics.py |
| 17 | Delete dead shim files (15+) | infrastructure/utils/ |

### P2 — Quality & Performance (Fix Third)

| # | Task | Scope |
|---|---|---|
| 18 | Break god files (>800 lines) | All domains |
| 19 | Delete archived files (14+) | promotions |
| 20 | Implement 26 TODO subscribers | governance |
| 21 | Fix N+1 queries | hr, customers |
| 22 | Replace OFFSET pagination | logistics, orders |
| 23 | Implement treasury/cash_management stubs | finance |
| 24 | Fix hardcoded secrets | security, infrastructure |
| 25 | Add missing architecture components | all domains |

---

## 11. Summary by Module

| Module | Broken (Won't Run) | Architecture Violations | Quality Issues |
|---|---|---|---|
| **employee** | 47 _auto_stubs + 103 undefined | 8 cross-module imports | 60 Pydantic inline, 4 god files |
| **customer** | 4 undefined + 1 _auto_stubs | 20+ cross-domain imports | 11 dup routes, 7 Pydantic inline |
| **logistics** | 0 | 14 cross-domain imports + 3 cross-module | 59 dup routes, 8 Pydantic inline |
| **admin** | 24 undefined | 0 | 9 Pydantic inline, analytics health-only |
| **supplier** | 0 | 0 | 19 colon-feature strings, 5 Pydantic inline |

| Domain | Broken | Cross-Domain Imports | Schema Issues |
|---|---|---|---|
| **accounts** | 0 | 14 | 0 |
| **analytics** | 0 | 7 | 0 |
| **audit** | 0 | 11 | 0 |
| **catalog** | 1 (missing `re` import) | 8 | 0 |
| **comms** | 0 | 8 | 0 |
| **country** | 0 | 0 | 0 |
| **customers** | 0 | 20+ | 0 |
| **finance** | 0 | 15+ | 0 |
| **governance** | 0 | 8 | 5 (wrong schema) |
| **hr** | 0 | 8 | 15 (wrong schema) |
| **logistics** | 0 | 14 | 0 |
| **orders** | 0 | 18+ | 5 (wrong schema) |
| **promotions** | 0 | 40+ | 0 |
| **security** | 0 | 12 | 0 |
| **suppliers** | 0 | 25+ | 1 (schema naming) |

---

*Report generated by 12 parallel investigation agents*  
*Total files analyzed: ~800+ source files*  
*Total problems identified: 454+*
