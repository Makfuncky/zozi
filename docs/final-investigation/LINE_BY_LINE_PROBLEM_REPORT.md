# ZOZI Backend — Complete Line-by-Line Problem Report

> **Generated:** 2026-08-27  
> **Source:** 10 parallel investigation agents  
> **Scope:** All 16 domains + infrastructure + providers + kernel + rbac  
> **Total problems found:** 1,000+

---

## TABLE OF CONTENTS

1. [CRITICAL Security Issues (4)](#1-critical-security-issues)
2. [HIGH Security Issues (6)](#2-high-security-issues)
3. [MEDIUM Security Issues (7)](#3-medium-security-issues)
4. [Law #1: Upward Imports (5+)](#4-law-1-upward-imports)
5. [Law #2: Fat Routers (47+)](#5-law-2-fat-routers)
6. [Law #3: Cross-Domain Imports (90+)](#6-law-3-cross-domain-imports)
7. [Law #5: Missing country_code (21+)](#7-law-5-missing-country_code)
8. [Law #6: Schema Mismatches (12)](#8-law-6-schema-mismatches)
9. [Missing Audit Columns (28+)](#9-missing-audit-columns)
10. [Router Wiring Gaps (16 files)](#10-router-wiring-gaps)
11. [Bare require_feature() Calls (582)](#11-bare-require_feature-calls)
12. [Float Money Casts (100+)](#12-float-money-casts)
13. [Missing HAS_<SDK> Exports (11)](#13-missing-hassdk-exports)
14. [Unexported Provider Flags (11)](#14-unexported-provider-flags)
15. [Kernel Underuse (3 modules)](#15-kernel-underuse)
16. [Duplicate Files & Dead Code](#16-duplicate-files--dead-code)
17. [Infrastructure Issues (5)](#17-infrastructure-issues)

---

## 1. CRITICAL SECURITY ISSUES

### 1.1 Hardcoded JWT Secret
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/.env` | 4 | `SECRET_KEY=6cf7982e47ff50f6cfb71e2475885f37382126b3ff30d8c10cc109b97c9e9c99` | Move to environment variable, rotate key |

### 1.2 Rate Limiting Fails OPEN
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/domains/accounts/services/auth/auth_service.py` | 101-133 | `_check_login_rate_limit()` returns without raising on Redis failure | Raise HTTPException(429) on Redis failure |

### 1.3 Token Type Not Verified
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/utils/auth.py` | 343-350 | `decode_token()` doesn't check `type` claim | Add `if payload.get("type") != expected_type: raise` |
| `backend/domains/comms/services/messaging/websocket_handlers.py` | 179 | Uses `decode_token()` without type check | Use `verify_token()` instead |
| `backend/domains/comms/services/public_comms_status_service.py` | 181 | Same issue | Use `verify_token()` |
| `backend/domains/customers/services/public_comms_status_service.py` | 211 | Same issue | Use `verify_token()` |

### 1.4 Password >72 Bytes Not Rejected
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/utils/auth.py` | 294-308 | `validate_password_complexity()` warns but doesn't reject | Change `warnings.warn()` to `raise ValueError()` |

---

## 2. HIGH SECURITY ISSUES

### 2.1 CORS Wildcard Default
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/utils/versioning.py` | 34, 202 | `"cors_origins": ["*"]` | Remove wildcard, use specific origins |

### 2.2 SQL Injection in Key Rotation
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/security/key_rotation.py` | 90, 124 | f-string interpolation of table/column names | Use allowlist for table names |

### 2.3 SQL Injection in Vault
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/security/vault.py` | 165 | f-string interpolation of field name | Use allowlist for field names |

### 2.4 DB Pool Size Too Small
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/.env` | 13-14 | `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10` | Change to `DB_POOL_SIZE=50`, `DB_MAX_OVERFLOW=100` |

### 2.5 No Concurrent Session Limit
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/domains/accounts/services/sessions/session_service.py` | — | No max sessions per user | Add check: `if active_count >= MAX: raise` |

---

## 3. MEDIUM SECURITY ISSUES

### 3.1 Webhook Middleware Global
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/middleware/orchestrator.py` | 107-110 | Webhook middleware registered globally | Scope to webhook paths only |

### 3.2 RLS Context Fragile
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/main.py` | 40 | RLS depends on middleware being called | Add fallback default context |

### 3.3 QR Ephemeral Key
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/security/qr_service.py` | 34-37 | Falls back to ephemeral key | Require SECRET_KEY, raise if missing |

### 3.4 HMAC Key Truncated
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/domains/governance/services/auth/iam_service_accounts.py` | 39, 68 | HMAC key truncated to 16 hex chars | Use full 32 bytes |

### 3.5 Stack Traces in Logs
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/var/uvicorn.out` | 92-121 | Full tracebacks in log files | Sanitize log output |

### 3.6 Test Fake Secrets
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `tests/providers/test_payments_providers.py` | 695 | Realistic-looking fake key | Use clearly invalid placeholder |
| `tests/providers/test_news_analytics_automation_finance_base_providers.py` | 1405 | AWS example key format | Use clearly invalid placeholder |
| `tests/providers/test_auth_providers.py` | 406 | Realistic-looking private key | Use clearly invalid placeholder |

### 3.7 print() in Production
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `backend/infrastructure/utils/config.py` | — | Debug print statements | Remove or use logger |

---

## 4. LAW #1: UPWARD IMPORTS

### 4.1 Infrastructure → Domains (4 violations)
| File | Line | Import | Fix |
|------|------|--------|-----|
| `backend/infrastructure/messaging/email_service.py` | 392 | `from domains.comms.services.email_event_service import ...` | Move to domains/comms |
| `backend/infrastructure/database/seed/_common.py` | 326 | `from domains.logistics.services.partners.service import ...` | Move to domains/logistics |
| `backend/infrastructure/security/security_audit.py` | 67 | `from domains.governance import ports as governance_ports` | Move to domains/governance |
| `backend/infrastructure/utils/user_context.py` | 5 | `from domains.governance.models.user import User` | Use TYPE_CHECKING only |

### 4.2 Domains → RBAC (25 violations)
| Domain | Files |
|--------|-------|
| accounts | `services/users/user_management_service.py`, `services/permissions/permission_service.py`, `services/auth/auth_service.py` |
| governance | `services/operations.py` |
| logistics | `services/tracking/service.py`, `services/shipping/shipments_service.py`, `services/shipping/service.py`, `services/partners/service.py`, `services/health/service.py`, `services/core/logistics_service.py`, `services/core/service.py` |
| country | `services/core/country_service.py` (4 occurrences) |
| hr | `services/hr_employee_service.py`, `services/hr_permissions.py` |
| promotions | `services/coupons/coupon_service.py`, `services/coupons/coupons_legacy_write_service.py` |

---

## 5. LAW #2: FAT ROUTERS

### 5.1 db.commit() in Routers (9 violations)
| File | Line |
|------|------|
| `modules/supplier/routers/accounts.py` | 246 |
| `modules/admin/services/admin_suppliers_service.py` | 258, 269, 278, 295, 314, 360, 386, 397 |

### 5.2 db.query() in Routers (38 violations)
| File | Count |
|------|-------|
| `modules/supplier/routers/accounts.py` | 1 |
| `modules/supplier/routers/suppliers.py` | 2 |
| `modules/admin/services/admin_suppliers_service.py` | 33 |
| `modules/admin/routers/orders.py` | 1 |

---

## 6. LAW #3: CROSS-DOMAIN IMPORTS (90+ violations)

### 6.1 Suppliers Domain (11 files)
| File | Line | Import |
|------|------|--------|
| `domains/suppliers/services/tier/tier_service.py` | 12 | `from domains.comms.models.suppliers import SupplierProfile, SupplierBadge` |
| `domains/suppliers/services/tier/tier_service.py` | 70 | `from domains.orders.models.order_entities import Order, OrderItem` |
| `domains/suppliers/services/settlement/multi_currency_settlement.py` | 12 | `from domains.comms.models.suppliers import SupplierProfile` |
| `domains/suppliers/services/quality/quality_control_service.py` | 13-15 | `from domains.comms.models.suppliers`, `from domains.catalog.models.products`, `from domains.orders.models.order_entities` |
| `domains/suppliers/services/profile/supplier_profile_service.py` | 12 | `from domains.governance.models.user import User` |
| `domains/suppliers/services/profile/supplier_product_image_service.py` | 14 | `from domains.catalog.models.products import Product` |
| `domains/suppliers/services/profile/supplier_payouts_service.py` | 13-15 | `from domains.governance.models.user`, `from domains.comms.models.suppliers`, `from domains.finance.models.payments` |
| `domains/suppliers/services/profile/supplier_bank_account_service.py` | 10 | `from domains.governance.models.admin import SupplierBankAccount` |
| `domains/suppliers/services/orders/supplier_orders_verify_service.py` | 16-19 | `from domains.governance.models.user`, `from domains.comms.models.suppliers`, `from domains.orders.models.order_entities` |
| `domains/suppliers/services/onboarding/supplier_onboarding_service.py` | 12 | `from domains.country.models.countries import CountryConfig` |
| `domains/suppliers/services/onboarding/onboarding_workflow.py` | 11 | `from domains.comms.models.suppliers import SupplierProfile` |

### 6.2 Finance Domain (15+ violations)
| File | Line | Import |
|------|------|--------|
| `domains/finance/services/treasury/cash_management_service.py` | 21 | `from domains.governance.models.admin import LogisticsSettlement` |
| `domains/finance/services/payouts/payout_batch_service.py` | 357, 509, 688, 856, 947, 1238, 1752, 2124, 2238, 2582, 2615, 2836, 3060, 3261 | Multiple cross-domain imports |

### 6.3 Orders Domain (13+ violations)
| File | Line | Import |
|------|------|--------|
| `domains/orders/services/tracking/service.py` | 33-38 | `from domains.comms.models`, `from domains.finance.models`, `from domains.governance.models`, `from domains.logistics.models` |
| `domains/orders/services/returns/service.py` | 20-23 | `from domains.governance.models`, `from domains.catalog.models`, `from domains.comms.models`, `from domains.logistics.models` |
| `domains/orders/services/packing/service.py` | 24-25, 237, 261 | `from domains.governance.models`, `from domains.logistics.models`, `from domains.comms.models` |
| `domains/orders/services/orders_service.py` | 238-239, 480, 562 | `from domains.governance.models`, `from domains.logistics.models`, `from domains.comms.models` |

### 6.4 Catalog Domain (9+ violations)
| File | Line | Import |
|------|------|--------|
| `domains/catalog/services/products/product_verification_service.py` | 16-18 | `from domains.governance.models`, `from domains.logistics.models`, `from domains.orders.models` |
| `domains/catalog/services/products/product_moderation_service.py` | 18 | `from domains.country.models.countries import CountryConfig` |
| `domains/catalog/services/products/products_service.py` | 400-403, 828, 841 | `from domains.accounts.models`, `from domains.comms.models`, `from domains.orders.models` |
| `domains/catalog/services/products/country_dropdown_service.py` | 16-17, 51 | `from domains.country.models` |

### 6.5 Audit Domain (14+ violations)
| File | Line | Import |
|------|------|--------|
| `domains/audit/services/worm_audit.py` | 14 | `from domains.governance.models.core import AuditLog` |
| `domains/audit/services/security_audit.py` | 7 | `from domains.governance.models.core import AuditLog` |
| `domains/audit/services/retention_service.py` | 9-13 | `from domains.governance.models`, `from domains.comms.models`, `from domains.logistics.models` |
| `domains/audit/services/ediscovery.py` | 12-18 | `from domains.governance.models`, `from domains.country.models`, `from domains.finance.models` |

### 6.6 Security Domain (5+ violations)
| File | Line | Import |
|------|------|--------|
| `domains/security/services/iam/iam_service.py` | 17 | `from domains.governance.models.user import User, UserDevice` |
| `domains/security/services/fraud/fraud_detection_service.py` | 21-33 | `from domains.governance.models`, `from domains.suppliers.models`, `from domains.logistics.models` |

### 6.7 Cross-Domain Writes (7 violations)
| File | Line | Problem |
|------|------|---------|
| `domains/catalog/services/products/products_service.py` | 415 | `db.add(Notification(...))` — creates comms model directly |
| `domains/orders/services/packing/service.py` | 238-239, 262 | `db.add(ShipmentEvent(...))`, `db.add(Notification(...))` |
| `domains/orders/services/orders_service.py` | 480, 562 | `db.add(Notification(...))` |
| `domains/suppliers/services/disputes_service.py` | 251-254, 417-420 | `db.add(Notification(...))` |
| `domains/suppliers/services/supplier_shared.py` | 251 | `db.add(ProductVideo(...))` |
| `domains/comms/services/tickets/tickets_service.py` | 101 | `db.add(SupportTicket(...))` |
| `domains/comms/services/comms_service.py` | 490-493 | `db.add(SupportTicket(...))`, `db.add(TicketMessage(...))` |

---

## 7. LAW #5: MISSING country_code (21+ models)

| Domain | Model File | Missing Column |
|--------|-----------|---------------|
| accounts | `read_models/user_read_models.py` | `country_code` |
| audit | `models/audit_schema_models.py` | `country_code` |
| catalog | `models/promotions.py` | `country_code` |
| comms | `models/fraud.py` | `country_code` |
| comms | `models/incident.py` | `country_code` |
| comms | `models/suppliers.py` | `country_code` |
| comms | `read_models/notification_read_models.py` | `country_code` |
| country | `models/country_basics.py` | `country_code` |
| finance | `models/country_payment_sync.py` | `country_code` |
| finance | `models/erp.py` | `country_code` |
| finance | `models/finance.py` | `country_code` |
| governance | `models/fraud.py` | `country_code` |
| governance | `models/incident.py` | `country_code` |
| governance | `models/user.py` | `country_code` |
| hr | `models/hr_schema_models.py` | `country_code` |
| logistics | `models/logistics.py` | `country_code` |
| logistics | `models/logistics_country_sync.py` | `country_code` |
| promotions | `models/loyalty_points.py` | `country_code` |
| security | `read_models/security_read_models.py` | `country_code` |
| suppliers | `models/supplier_country_sync.py` | `country_code` |

---

## 8. LAW #6: SCHEMA MISMATCHES (12 violations)

| File | Line | Current Schema | Correct Schema |
|------|------|----------------|----------------|
| `domains/finance/models/payments.py` | 176 | `governance` | `finance` |
| `domains/finance/models/payments.py` | 189 | `governance` | `finance` |
| `domains/finance/models/tax_rules.py` | 32 | `country` | `finance` |
| `domains/finance/models/tax_rules.py` | 53 | `country` | `finance` |
| `domains/finance/models/tax_rules.py` | 72 | `country` | `finance` |
| `domains/finance/models/tax_rules.py` | 93 | `country` | `finance` |
| `domains/governance/models/legal_contract_template.py` | 23 | `country` | `governance` |
| `domains/comms/models/message.py` | 32 | `country` | `comms` |
| `domains/comms/models/marketing.py` | 55 | `commerce.flash_sales` | `promotions.flash_sales` |
| `domains/comms/models/marketing.py` | 56 | `commerce.products` | `catalog.products` |
| `domains/customers/models/customer_schema_models.py` | 191 | `commerce.products` | `catalog.products` |
| `domains/finance/models/commission.py` | 108 | `commerce.categories` | `catalog.categories` |

---

## 9. MISSING AUDIT COLUMNS (28+ models)

| Domain | Model File | Missing Columns |
|--------|-----------|----------------|
| analytics | `models/analytics_schema_models.py` | `is_deleted` on ExecutiveNews |
| audit | `models/audit_schema_models.py` | `updated_at`, `is_deleted` on AuditLog |
| audit | `models/audit_schema_models.py` | `is_deleted` on CommandCenterView |
| comms | `models/chat.py` | `country_code`, `is_deleted`, `updated_at` on 11 models |
| comms | `models/news.py` | `is_deleted` on NewsArticle |
| comms | `models/incident.py` | `updated_at`, `is_deleted` on 4 models |
| comms | `models/fraud.py` | `updated_at`, `is_deleted` on MeetingRecording |
| comms | `models/communication_schema_models.py` | `is_deleted`, `updated_at` on 6 models |
| comms | `models/communication.py` | `country_code` on Notification |

---

## 10. ROUTER WIRING GAPS (16 missing files)

### 10.1 Missing Router Files
| Module | Missing Routers |
|--------|-----------------|
| customer | `country.py`, `hr.py`, `security.py`, `suppliers.py` |
| employee | `promotions.py` |
| logistics | `catalog.py`, `country.py`, `hr.py`, `orders.py`, `promotions.py`, `security.py`, `suppliers.py` |
| supplier | `country.py`, `hr.py`, `promotions.py`, `security.py` |

### 10.2 Missing Pagination (6 routers)
| Router | Issue |
|--------|-------|
| `customer/governance.py` | No pagination on list endpoints |
| `employee/analytics.py` | No pagination on list endpoints |
| `employee/country.py` | No pagination on list endpoints |
| `supplier/accounts.py` | No pagination on list endpoints |
| `supplier/suppliers.py` | No pagination on list endpoints |

### 10.3 Missing Error Handling (25 routers)
| Module | Routers |
|--------|---------|
| admin | accounts, analytics, audit, catalog, customers, finance, governance, hr |
| customer | analytics, catalog, governance |
| employee | analytics, catalog, governance, logistics |
| logistics | analytics, finance, governance |
| supplier | analytics, catalog, finance, governance, logistics, orders |

---

## 11. BARE require_feature() CALLS (582 violations)

**Problem:** 582 route handlers call `require_feature()` as a bare function instead of using `Depends(require_feature(...))`. Bare calls don't enforce the gate at the FastAPI dependency-injection level.

**Pattern to fix:**
```python
# WRONG (bare call inside function body):
def endpoint(...):
    require_feature("atom.name")

# CORRECT (Depends at decorator level):
def endpoint(_: None = Depends(require_feature("atom.name"))):
    ...
```

**Affected modules:** All 5 modules (admin, customer, employee, logistics, supplier)

---

## 12. FLOAT MONEY CASTS (100+ violations)

| Domain | Count | Example Files |
|--------|-------|---------------|
| analytics | 10+ | `services/dashboards/analytics_service.py` |
| customers | 15+ | `services/coupons_service.py`, `services/cart_service.py` |
| catalog | 20+ | `services/products/products_service.py` |
| country | 30+ | `services/core/country_service.py` |
| suppliers | 20+ | `services/profile/supplier_profile.py` |
| finance | 10+ | `services/payments/payment_engine.py` |
| orders | 5+ | `services/orders_service.py` |

**Fix:** Replace `float(value)` with `kernel.money.to_decimal(value)` for all money operations.

---

## 13. MISSING HAS_<SDK> EXPORTS (11 packages)

| Provider | Flag Defined | Exported? |
|----------|-------------|-----------|
| `security/encryption.py` | `HAS_CRYPTOGRAPHY` | ❌ |
| `security/threat_intel.py` | `HAS_THREAT_INTEL` | ❌ |
| `security/watchlist.py` | `HAS_WATCHLIST` | ❌ |
| `automation/scheduler.py` | `HAS_APSCHEDULER` | ❌ |
| `voice/voice_to_text.py` | `HAS_VOICE` | ❌ |
| `news/rss_provider.py` | `HAS_FEEDPARSER`, `HAS_HTTPX` | ❌ |
| `ocr/ocr_parser.py` | `HAS_OCR_PARSER` | ❌ |
| `finance/bank_api.py` | `HAS_BANK_API` | ❌ |
| `geography/geo.py` | `HAS_GEO` | ❌ |
| `geography/geoip.py` | `HAS_GEOIP` | ❌ |
| `geography/map.py` | `HAS_MAP` | ❌ |

---

## 14. UNEXPORTED PROVIDER FLAGS (11 packages)

| Provider | Issue |
|----------|-------|
| `image/bg_remover/` | Uses `_HAS_REMBG` (private) instead of public `HAS_REMBG` |
| `image/free_image_tools.py` | `HAS_FREE_IMAGE` not exported from `image/__init__.py` |
| `image/parcel_verification.py` | `HAS_PARCEL_VERIFY` not exported from `image/__init__.py` |
| `storage/__init__.py` | `HAS_STORAGE` not in `__all__` |

---

## 15. KERNEL UNDERUSE (3 modules)

| Kernel Module | Status | Fix |
|---------------|--------|-----|
| `kernel/currency` | Empty module | Implement or use `infrastructure/utils/currency_service.py` |
| `kernel/period` | Completely unused | Implement period/fiscal operations |
| `kernel/numbering` | Completely unused | Implement sequence generation |

---

## 16. DUPLICATE FILES & DEAD CODE

### 16.1 Duplicate Events/Subscribers/Ports
| Domain | Files | Fix |
|--------|-------|-----|
| comms | `services/events.py` + root `events.py` | Delete `services/events.py` |
| customers | `services/events.py` + root `events.py` | Delete `services/events.py` |
| promotions | `services/events.py` + root `events.py` | Delete `services/events.py` |
| suppliers | `services/events.py` + root `events.py` | Delete `services/events.py` |

### 16.2 Empty Stub Subpackages
| Domain | Directory | Fix |
|--------|-----------|-----|
| promotions | `marketing/` | Implement or delete |

### 16.3 Duplicate Column Definitions
| File | Line | Problem |
|------|------|---------|
| `comms/models/communication.py` | 464-465 | `PushNotificationToken.is_deleted` defined twice |
| `comms/models/marketing.py` | 32-33 | `FlashSale.deleted_by` and `deleted_by_id` duplicate |
| `suppliers/models/suppliers.py` | 83 | `SupplierDocument.__table_args__` defined twice |
| `hr/models/employee_models.py` | 481 | `AlumniNetwork.__table_args__` defined twice |

---

## 17. INFRASTRUCTURE ISSUES (5)

### 17.1 Direct SDK Imports in Domains
| File | Line | Import | Fix |
|------|------|--------|-----|
| `domains/accounts/services/auth/auth_service.py` | 31 | `import jwt` | Use `providers.auth.jwt` |
| `domains/accounts/services/auth/auth_service.py` | 32 | `import requests` | Use provider wrapper |
| `domains/finance/services/payments/payment_engine.py` | 57 | `import httpx` | Use provider wrapper |

### 17.2 Broken Import
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `domains/finance/services/payments/payment_engine.py` | 98 | `from kernel.money import convert_from_aed, ...` — functions don't exist | Fix to `infrastructure/utils/currency_service.py` |

### 17.3 Graceful Degradation Missing
| File | Line | Problem | Fix |
|------|------|---------|-----|
| All domains | — | Only 4 `HAS_*` checks in 100+ provider calls | Add `if not HAS_XXX: raise HTTPException(503)` |

### 17.4 Unbounded In-Memory Fallback
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `infrastructure/utils/auth.py` | 28-29 | `_memory_blacklist`, `_memory_failed_logins` grow unbounded | Add max size/TTL |

### 17.5 Webhook Middleware Global
| File | Line | Problem | Fix |
|------|------|---------|-----|
| `middleware/orchestrator.py` | 107-110 | Webhook middleware runs for every request | Scope to webhook paths |

---

## APPENDIX: SUMMARY STATISTICS

| Category | Count |
|----------|-------|
| CRITICAL security | 4 |
| HIGH security | 6 |
| MEDIUM security | 7 |
| Law #1 violations | 5+ |
| Law #2 violations | 47+ |
| Law #3 violations | 90+ |
| Law #5 violations | 21+ |
| Law #6 violations | 12 |
| Missing audit columns | 28+ |
| Missing router files | 16 |
| Bare require_feature() | 582 |
| Float money casts | 100+ |
| Missing HAS exports | 11 |
| Kernel underuse | 3 |
| Infrastructure issues | 5 |
| **TOTAL** | **1,000+** |

---

*Report generated by 10 parallel investigation agents*  
*Next step: Run targeted fix agents for each category above*
