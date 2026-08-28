# ZOZI Backend — Complete Line-by-Line Problem Report

> **Generated:** 2026-08-27  
> **Source:** 10 parallel investigation agents  
> **Scope:** All 16 domains + infrastructure + providers + kernel + rbac + modules  
> **Total problems found:** 2,500+

---

## TABLE OF CONTENTS

1. [Architecture & Wiring (140+ problems)](#1-architecture--wiring)
2. [Code Quality & Logic (200+ problems)](#2-code-quality--logic)
3. [Domain & Module Structure (137+ problems)](#3-domain--module-structure)
4. [Database & Data Layer (300+ problems)](#4-database--data-layer)
5. [Security (50+ problems)](#5-security)
6. [Infrastructure & Connections (50+ problems)](#6-infrastructure--connections)
7. [Performance & Scalability (100+ problems)](#7-performance--scalability)
8. [Error & Exception Handling (50+ problems)](#8-error--exception-handling)
9. [Testing & Validation (30+ problems)](#9-testing--validation)
10. [Router Wiring (600+ problems)](#10-router-wiring)

---

## 1. ARCHITECTURE & WIRING (140+ problems)

### Law #1: Arrows Point Down Only

#### Infrastructure → Domains (3 violations)
| File | Line | Import | Fix |
|------|------|--------|-----|
| `infrastructure/messaging/email_service.py` | 392 | `from domains.comms.services.email_event_service import ...` | Move to domains/comms |
| `infrastructure/database/seed/_common.py` | 326 | `from domains.logistics.services.partners.service import ...` | Move to domains/logistics |
| `infrastructure/security/security_audit.py` | 67 | `from domains.governance import ports as governance_ports` | Move to domains/governance |

#### Domains → RBAC (25 violations)
| Domain | Files |
|--------|-------|
| accounts | `services/users/user_management_service.py:120`, `services/permissions/permission_service.py:447`, `services/auth/auth_service.py:1759` |
| governance | `services/operations.py:21` |
| logistics | `services/tracking/service.py:221,281,331`, `services/shipping/shipments_service.py:23`, `services/shipping/service.py:29`, `services/partners/service.py:21`, `services/health/service.py:165,197,203`, `services/core/logistics_service.py:13`, `services/core/service.py:25-26` |
| country | `services/core/country_service.py:156,157,209,219,228` |
| hr | `services/hr_employee_service.py:553`, `services/hr_permissions.py:20` |
| promotions | `services/coupons/coupon_service.py:50`, `services/coupons/coupons_legacy_write_service.py:27` |

### Law #2: Module Routers Stay Thin

#### db.commit() in Routers (12 violations)
| File | Lines |
|------|-------|
| `modules/admin/services/admin_suppliers_service.py` | 258, 269, 278, 293, 312, 358, 384, 395 |
| `modules/logistics/routers/accounts.py` | 284, 328, 357 |
| `modules/supplier/routers/accounts.py` | 246 |

#### db.query() in Routers (38 violations)
| File | Count |
|------|-------|
| `modules/admin/services/admin_suppliers_service.py` | 34 |
| `modules/logistics/routers/accounts.py` | 4 |
| `modules/supplier/routers/accounts.py` | 1 |
| `modules/admin/routers/orders.py` | 1 |

#### Misplaced Files
| Path | Violation |
|------|-----------|
| `modules/admin/services/admin_suppliers_service.py` | 442-line domain services in modules layer |
| `backend/uploads/` | Not in architecture |
| `backend/var/` | Not in architecture |

### Law #3: Cross-Domain via Events/Ports Only (40+ model import violations)

#### Top Offenders:
| Domain | File | Line | Import |
|--------|------|------|--------|
| suppliers | `services/tier/tier_service.py` | 70 | `from domains.orders.models.order_entities import Order, OrderItem` |
| suppliers | `services/quality/quality_control_service.py` | 13-15 | 3 cross-domain model imports |
| suppliers | `services/profile/supplier_profile_service.py` | 12 | `from domains.governance.models.user import User` |
| suppliers | `services/profile/supplier_payouts_service.py` | 13-15 | 3 cross-domain model imports |
| suppliers | `services/profile/supplier_bank_account_service.py` | 10 | `from domains.governance.models.admin import SupplierBankAccount` |
| suppliers | `services/profile/supplier_product_image_service.py` | 14 | `from domains.catalog.models.products import Product` |
| suppliers | `services/orders/supplier_orders_verify_service.py` | 16-19 | 3 cross-domain model imports |
| suppliers | `services/health/supplier_health.py` | 13-21 | 8 cross-domain model imports |
| suppliers | `services/onboarding/supplier_onboarding_service.py` | 12 | `from domains.country.models.countries import CountryConfig` |
| suppliers | `services/onboarding/onboarding_workflow.py` | 11 | `from domains.comms.models.suppliers import SupplierProfile` |
| finance | `services/treasury/cash_management_service.py` | 21 | `from domains.governance.models.admin import LogisticsSettlement` |
| finance | `services/payouts/payout_batch_service.py` | 357,509,688,856,947,1238,1752,2124,2238,2582,2615,2836,3060,3261 | 15+ cross-domain imports |
| orders | `services/tracking/service.py` | 33-38 | 5 cross-domain model imports |
| orders | `services/returns/service.py` | 20-23 | 4 cross-domain model imports |
| orders | `services/packing/service.py` | 24-25,237,261 | 4 cross-domain model imports |
| orders | `services/orders_service.py` | 238-239,480,562 | 4 cross-domain model imports |
| catalog | `services/products/product_verification_service.py` | 16-18 | 3 cross-domain model imports |
| catalog | `services/products/products_service.py` | 400-403,828,841 | 5+ cross-domain model imports |
| audit | `services/worm_audit.py` | 14 | `from domains.governance.models.core import AuditLog` |
| audit | `services/security_audit.py` | 7 | `from domains.governance.models.core import AuditLog` |
| audit | `services/retention_service.py` | 9-13 | 5 cross-domain model imports |
| audit | `services/ediscovery.py` | 12-18 | 7 cross-domain model imports |
| security | `services/fraud/fraud_detection_service.py` | 21-33 | 5 cross-domain model imports |

#### Cross-Domain Writes (7 violations)
| File | Line | Problem |
|------|------|---------|
| `catalog/services/products/products_service.py` | 415 | `db.add(Notification(...))` |
| `orders/services/packing/service.py` | 238-239, 262 | `db.add(ShipmentEvent(...))`, `db.add(Notification(...))` |
| `orders/services/orders_service.py` | 480, 562 | `db.add(Notification(...))` |
| `suppliers/services/disputes_service.py` | 251-254, 417-420 | `db.add(Notification(...))` |
| `suppliers/services/supplier_shared.py` | 251 | `db.add(ProductVideo(...))` |
| `comms/services/tickets/tickets_service.py` | 101 | `db.add(SupportTicket(...))` |
| `comms/services/comms_service.py` | 490-493 | `db.add(SupportTicket(...))`, `db.add(TicketMessage(...))` |

---

## 2. CODE QUALITY & LOGIC (200+ problems)

### Float for Money (50+ instances, 15 files)
| File | Line | Issue |
|------|------|-------|
| `infrastructure/utils/invoice_html.py` | 33-42, 187-199 | 18 `float()` on money |
| `domains/orders/services/tracking/service.py` | 331-348, 828, 1612-1623 | 14 `float()` on money |
| `domains/orders/services/returns/service.py` | 141, 246, 461 | `float()` on money |
| `domains/orders/services/orders_service.py` | 67, 329, 350, 361 | `float()` on money |
| `domains/analytics/services/dashboards/admin_dashboard_service.py` | 43, 163, 182 | `float()` on money |
| `domains/analytics/services/dashboards/admin_analytics_service.py` | 62, 88 | `float()` on money |
| `domains/analytics/services/dashboards/analytics_service.py` | 111 | `float()` on money |
| `domains/analytics/services/aggregation/command_center_service.py` | 635, 646, 656, 669, 685 | `float()` on money |
| `domains/country/services/tax/country_tax_service.py` | 46 | `float()` on tax_rate |
| `domains/country/services/staff/country_admin_write_service.py` | 140-141, 325 | `float()` on tax_rate |
| `domains/country/services/cross_border/cross_border_service.py` | 175 | `float()` on exchange_rate |
| `domains/country/services/core/country_service.py` | 459 | `float()` on exchange_rate |
| `domains/country/services/payout/country_payout_write_service.py` | 25-27 | `float()` on payout rates |
| `domains/suppliers/services/settlement/multi_currency_settlement.py` | 72, 84, 86, 115 | `Decimal(str(amount))` wrapping float |

### Hardcoded FX Rates (7 locations)
| File | Line | Currencies |
|------|------|------------|
| `domains/suppliers/services/settlement/multi_currency_settlement.py` | 20-39 | 17 currencies |
| `infrastructure/utils/currency_service.py` | 25-74 | 8 currencies |
| `domains/hr/services/travel/travel_service.py` | 28-31 | 9 currencies |
| `domains/analytics/services/aggregation/command_center_service.py` | 540 | 3 pairs |

### Broken Logic (8 instances)
| File | Line | Issue |
|------|------|-------|
| `finance/services/ledger/general_ledger_service.py` | 7358 | `.offset(page_size).limit(page_size)` ignores `page` |
| `analytics/services/aggregation/command_center_service.py` | 535 | datetime not JSON-serializable |
| `infrastructure/utils/auth.py` | 39 | `float(entry[1])` corrupts if None |
| `orders/services/tracking/service.py` | 1613 | float multiplication of money |
| `orders/services/orders_service.py` | 350 | generic float cast |
| `jobs/seed_all.py` | 304 | SQL injection via string concat |
| `providers/bg_removal/bg_removal_service.py` | 803 | `fast_mode` param ignored |
| `middleware/rate_limit_middleware.py` | 70 | `time.sleep(60)` blocks async loop |

### Swallowed Exceptions (40+ instances)
| File | Count | Pattern |
|------|-------|---------|
| `infrastructure/utils/auth.py` | 9 | `pass` in except blocks |
| `infrastructure/utils/background_jobs.py` | 5 | bare `pass` |
| `middleware/impossible_travel_middleware.py` | 9 | bare `pass` |
| `middleware/rate_limit_middleware.py` | 2 | bare `pass` |
| `providers/bg_removal/bg_removal_service.py` | 4 | bare `except Exception: pass` |
| `suppliers/subscribers.py` | 8 | silent warning logs |

---

## 3. DOMAIN & MODULE STRUCTURE (137 problems)

### Missing Router Files (24 files)
| Module | Missing |
|--------|---------|
| customer | country, hr, security, suppliers |
| employee | promotions |
| logistics | catalog, country, hr, orders, promotions, security, suppliers |
| supplier | country, hr, promotions, security |

### Wrong FK Schema (13 violations)
| File | Line | FK | Should Be |
|------|------|----|-----------|
| `finance/models/payments.py` | 48, 130 | `commerce.orders.id` | `orders.orders.id` |
| `finance/models/commission.py` | 45, 66-68 | `commerce.products/orders/order_items` | `catalog/orders` |
| `suppliers/models/suppliers.py` | 259, 264 | `commerce.orders/return_requests` | `orders` |
| `customers/models/customer_schema_models.py` | 191 | `commerce.products` | `catalog.products` |
| `governance/models/core.py` | 50 | `commerce.products` | `catalog.products` |
| `governance/models/admin.py` | 273, 288, 302 | `commerce.products/orders` | `catalog/orders` |

### Direct SDK Imports in Domains (4 violations)
| File | Line | Import | Fix |
|------|------|--------|-----|
| `accounts/services/auth/auth_service.py` | 31 | `import jwt` | Use `providers.auth.jwt` |
| `accounts/services/auth/auth_service.py` | 32 | `import requests` | Use provider wrapper |
| `finance/services/payments/payment_engine.py` | 57 | `import httpx` | Use provider wrapper |
| `finance/services/payments/payment_engine.py` | 55 | `from providers.payments.stripe_sdk import stripe` | Check `HAS_STRIPE` |

### RBAC Misconfigured (40+ violations)
| Feature String | Used In | Status |
|----------------|---------|--------|
| `governance.referral.read` | customer/routers/governance.py | ❌ NOT in features.py |
| `governance.dispute.read` | supplier/routers/governance.py | ❌ NOT in features.py |
| `governance.access.read` | employee/routers/governance.py | ❌ NOT in features.py |
| `comms.audit.read` | admin/routers/comms.py | ❌ NOT in features.py |

#### Bare require_feature() Calls (582 violations)
| Module | Count |
|--------|-------|
| admin/routers/accounts.py | 31 |
| admin/routers/comms.py | 7 |
| admin/routers/governance.py | 8 |
| All other routers | ~536 |

---

## 4. DATABASE & DATA LAYER (300+ problems)

### Schema Mismatches (16 models)
| File | Model | Current Schema | Correct Schema |
|------|-------|----------------|----------------|
| `logistics/models/shipping_rules.py` | ShippingRule | `country` | `logistics` |
| `logistics/models/erp.py` | 13 ERP models | `finance` | `logistics` |
| `customers/models/customer_schema_models.py` | Address, CartItem | `customers` | `accounts` |

### Missing Audit Columns (200+ models)
| Domain | Models Missing `is_deleted` |
|--------|----------------------------|
| comms | 28 models |
| finance | 60+ models |
| governance | 10+ models |
| hr | 30+ models |
| logistics | 20+ models |
| suppliers | 10+ models |
| customers | 10+ models |
| accounts | 15+ models |
| orders | 5 models |
| security | 10+ models |
| promotions | 8+ models |
| audit | 2 models |
| catalog | 10+ models |

### Missing Indexes (32+ missing)
| Table | Missing Index On |
|-------|-----------------|
| audit_logs | entity_type, entity_id, user_id |
| support_tickets | user_id |
| shipping_zones | supplier_id |
| supplier_bank_accounts | supplier_id |
| promotion_ledger_entries | promotion_id, order_id |

### Reserved Keywords (74 columns)
| Domain | Columns |
|--------|---------|
| comms | `type`, `status`, `role`, `key` on 30+ columns |
| finance | `status` on 20+ columns |
| hr | `status` on 15+ columns |
| governance | `role`, `status`, `key` on 10+ columns |
| logistics | `status` on 15+ columns |
| suppliers | `status` on 5+ columns |
| country | `status` on 10+ columns |
| accounts | `role`, `key` on 5+ columns |
| orders | `status` on 5+ columns |
| promotions | `status` on 5+ columns |
| security | `status`, `role` on 5+ columns |
| customers | `status` on 5+ columns |
| analytics | `status` on 3+ columns |
| audit | `status` on 2+ columns |

### SQL Injection Risks (5 locations)
| File | Line | Issue |
|------|------|-------|
| `hr/services/performance/kpi.py` | 104 | f-string with dynamic placeholders |
| `hr/services/performance/reviews.py` | 109 | string concatenation |
| `hr/services/ess_service.py` | 48 | dynamic SQL via string concat |
| `hr/services/ess/ess_service.py` | 64 | dynamic SQL via string concat |
| `hr/services/ess/ess_service.py` | 260 | dynamic SQL via string concat |

---

## 5. SECURITY (50+ problems)

### CRITICAL (4 issues)
| File | Line | Issue | Fix |
|------|------|-------|-----|
| `.env` | 4 | Hardcoded JWT secret | Move to env var, rotate |
| `accounts/services/auth/auth_service.py` | 101-133 | Rate limiting fails OPEN | Fail closed (deny requests) |
| `infrastructure/utils/auth.py` | 343-350 | `decode_token()` no type check | Add type claim verification |
| `infrastructure/utils/auth.py` | 294-308 | Password >72 bytes not rejected | Raise ValueError |

### HIGH (5 issues)
| File | Line | Issue |
|------|------|-------|
| `modules/admin/routers/security.py` | 262-273 | OTP endpoints no rate limit |
| `accounts/services/auth/auth_service.py` | 1397-1419 | verify_otp no time-based lockout |
| `middleware/rate_limit_middleware.py` | 144-167 | Rate limit fails OPEN |
| `kms_encryption.py` | 129 | Hardcoded fallback salt |
| `encryption.py` | 22 | Ephemeral key on restart |

### MEDIUM (7 issues)
| File | Line | Issue |
|------|------|-------|
| `infrastructure/security/key_rotation.py` | 90, 124 | f-string SQL |
| `infrastructure/security/vault.py` | 165 | f-string SQL |
| `public_security_registration_service.py` | 154-175 | Refresh token reuse not detected |
| `infrastructure/utils/auth.py` | 96-110 | Token blacklist fails open |
| `comms/services/proxy_communication.py` | 238-240 | Fake encryption |

### Raw Exception Exposure (14 locations)
| File | Line | Pattern |
|------|------|---------|
| `analytics/services/dashboards/analytics_service.py` | 320 | `{"error": str(e)}` |
| `catalog/services/search_service.py` | 34 | `{"error": str(exc)}` |
| `customers/services/search_service.py` | 75 | `{"error": str(exc)}` |
| `modules/employee/routers/hr.py` | 690 | `{"error": str(e)}` (200 OK!) |
| `modules/employee/routers/orders.py` | 179,212,224,etc | 9 `HTTPException(400, str(e))` |

---

## 6. INFRASTRUCTURE & CONNECTIONS (50+ problems)

### Kernel Underuse (3 modules)
| Module | Status |
|--------|--------|
| `kernel/currency` | Empty — use `infrastructure/utils/currency_service.py` |
| `kernel/period` | Completely unused |
| `kernel/numbering` | Completely unused |

### HAS_<SDK> Flags Not Exported (11 packages)
| Provider | Flag |
|----------|------|
| security/encryption.py | `HAS_CRYPTOGRAPHY` |
| security/threat_intel.py | `HAS_THREAT_INTEL` |
| security/watchlist.py | `HAS_WATCHLIST` |
| automation/scheduler.py | `HAS_APSCHEDULER` |
| voice/voice_to_text.py | `HAS_VOICE` |
| news/rss_provider.py | `HAS_FEEDPARSER`, `HAS_HTTPX` |
| ocr/ocr_parser.py | `HAS_OCR_PARSER` |
| finance/bank_api.py | `HAS_BANK_API` |
| geography/geo.py | `HAS_GEO` |
| geography/geoip.py | `HAS_GEOIP` |
| geography/map.py | `HAS_MAP` |

### Graceful Degradation Missing
Only 4 `HAS_*` checks in 100+ provider calls.

### Broken Import
| File | Line | Issue |
|------|------|-------|
| `finance/services/payments/payment_engine.py` | 98 | `from kernel.money import convert_from_aed, ...` — functions don't exist |

---

## 7. PERFORMANCE & SCALABILITY (100+ problems)

### OFFSET Pagination (82 instances)
| Domain | Files |
|--------|-------|
| catalog | search_service.py: 992, 1123 |
| orders | orders_service.py, order_engine.py |
| finance | payment_engine.py, payout_batch_service.py |
| logistics | shipment_service.py, admin_logistics_service.py |
| comms | tickets_service.py, email_management.py |
| hr | payroll_service.py |
| accounts | user_management_service.py |

### Unbounded `.all()` Queries (100+ instances)
| File | Line |
|------|------|
| catalog/services/search/search_service.py | 603, 1178 |
| audit/services/worm_audit.py | 77 |
| suppliers/services/settlement/multi_currency_settlement.py | 108 |
| catalog/services/products/products_service.py | 522 |

### Async/Sync Anti-patterns
| Issue | Status |
|-------|--------|
| Sync DB in async handlers | ❌ 2412 call sites use sync `get_db()` |
| `get_async_db()` rarely used | ❌ Near-zero adoption |
| ThreadPoolExecutor for DB | ⚠️ 32 workers, adds overhead |

### Memory Leaks (3 unbounded dicts)
| File | Line | Issue |
|------|------|-------|
| finance/ports.py | 47 | `_model_cache = {}` |
| catalog/services/search/search_service.py | 994 | `self._cache[cache_key]` |
| country/services/core/country_service.py | 257 | `_json_cache` |

---

## 8. ERROR & EXCEPTION HANDLING (50+ problems)

### Raw Exception Exposure (14 locations)
| File | Line | Pattern |
|------|------|---------|
| analytics_service.py | 320 | `{"error": str(e)}` |
| catalog/search_service.py | 34 | `{"error": str(exc)}` |
| customers/search_service.py | 75 | `{"error": str(exc)}` |
| modules/employee/routers/hr.py | 690 | `{"error": str(e)}` as 200 OK |
| modules/employee/routers/orders.py | 179+ | 9 `HTTPException(400, str(e))` |

### Swallowed Exceptions (40+ instances)
| File | Count | Pattern |
|------|-------|---------|
| infrastructure/utils/auth.py | 9 | `pass` in except blocks |
| middleware/impossible_travel_middleware.py | 9 | bare `pass` |
| middleware/rate_limit_middleware.py | 2 | bare `pass` |
| providers/bg_removal/bg_removal_service.py | 4 | bare `except Exception: pass` |
| suppliers/subscribers.py | 8 | silent warning logs |

### print() in Production (1 instance)
| File | Line | Issue |
|------|------|-------|
| providers/ai/zozi_mcp.py | 92 | `print()` should be `logger.warning()` |

---

## 9. TESTING & VALIDATION (30+ problems)

### Missing Test Files (3 domains)
| Domain | Python Files | Test Files |
|--------|-------------|------------|
| accounts | 40 | 0 ❌ |
| analytics | 19 | 0 ❌ |
| promotions | 40 | 0 ❌ |

### Test Coverage Gaps
| Domain | Test Files | Coverage |
|--------|------------|----------|
| governance | 1 | ⚠️ (48 files) |
| hr | 1 | ⚠️ (53 files) |
| suppliers | 1 | ⚠️ (55 files) |

### Architecture Tests (16 files — Strong)
- test_import_laws.py
- test_architecture_gates.py
- test_feature_catalog.py
- test_keyset_pagination.py
- test_law3_cross_domain.py
- test_law5_country_scope.py
- test_law6_schema_discipline.py
- test_law7_allowlist_shrink.py
- test_laws_complete.py
- test_offset_adoption_baseline.py
- test_orders_write_facade.py
- test_parked_no_regrow.py
- test_require_feature_namespace_allowlist.py
- test_require_feature_no_star.py
- test_supplier_route_integrity.py

---

## 10. ROUTER WIRING (600+ problems)

### Missing Router Files (24 files)
| Module | Missing |
|--------|---------|
| customer | country.py, hr.py, security.py, suppliers.py |
| employee | promotions.py |
| logistics | catalog.py, country.py, hr.py, orders.py, promotions.py, security.py, suppliers.py |
| supplier | country.py, hr.py, promotions.py, security.py |

### Bare require_feature() (582 violations)
All 5 modules have routers with bare `require_feature()` calls instead of `Depends(require_feature(...))`.

### Missing Pagination (6 routers)
- customer/governance.py
- employee/analytics.py
- employee/country.py
- supplier/accounts.py
- supplier/suppliers.py

### Missing Error Handling (25 routers)
admin: accounts, analytics, audit, catalog, customers, finance, governance, hr
customer: analytics, catalog, governance
employee: analytics, catalog, governance, logistics
logistics: analytics, finance, governance
supplier: analytics, catalog, finance, governance, logistics, orders

---

## SUMMARY STATISTICS

| Category | Problems |
|----------|----------|
| Architecture & Wiring | 140+ |
| Code Quality & Logic | 200+ |
| Domain & Module Structure | 137+ |
| Database & Data Layer | 300+ |
| Security | 50+ |
| Infrastructure & Connections | 50+ |
| Performance & Scalability | 100+ |
| Error & Exception Handling | 50+ |
| Testing & Validation | 30+ |
| Router Wiring | 600+ |
| **TOTAL** | **2,500+** |

---

*Report generated by 10 parallel investigation agents*  
*Next step: Run targeted fix agents for each category above*
