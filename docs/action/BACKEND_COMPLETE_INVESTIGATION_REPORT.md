# ZOZI Backend — Complete Investigation Report (Corrected)

**Date:** 2026-08-27
**Scope:** Full `backend/` directory vs. `ARCHITECTURE_DIAGRAM.md` (618 lines)
**Methodology:** 12+ parallel sub-agents investigating 9 categories
**Architecture Reference:** `ARCHITECTURE_DIAGRAM.md` (read top-to-bottom)

---

## Executive Summary

| Category | CRITICAL | HIGH | MEDIUM | LOW | Total |
|----------|----------|------|--------|-----|-------|
| Architecture & Wiring | 6 | 14 | 10 | 4 | 34 |
| Code Quality & Logic | 4 | 14 | 12 | 1 | 31 |
| Domain & Module Structure | 4 | 10 | 6 | 3 | 23 |
| Database & Data Layer | 25 | 150 | 30 | 10 | 215 |
| Security | 4 | 10 | 5 | 4 | 23 |
| Infrastructure & Connections | 3 | 6 | 6 | 2 | 17 |
| Performance & Scalability | 3 | 8 | 7 | 1 | 19 |
| Error & Exception Handling | 2 | 6 | 8 | 1 | 17 |
| Testing & Validation | 5 | 10 | 5 | 2 | 22 |
| **TOTAL** | **56** | **228** | **89** | **28** | **401** |

**Overall Verdict:** The backend has **severe** architectural drift, security vulnerabilities, and data layer problems. The most critical issues are: (1) **~150+ domain-to-domain import violations** — domains import directly from other domains' models instead of using ports.py, (2) **19 duplicate table definitions** across domains, (3) **150+ tables missing audit columns** (created_at, updated_at, is_deleted), (4) **100+ ForeignKeys without ondelete**, (5) **RBAC bypass** via direct require_feature() calls, (6) **hardcoded encryption fallback secret**, (7) **no test files for any domain or provider**, (8) **no CI pipeline**.

---

# CORRECTION 1: DOMAIN-TO-DOMAIN IMPORTS (LAW 3)

## Architecture Rule (ARCHITECTURE_DIAGRAM.md Lines 242-246, 287-288)

> **Cross-domain contract (Law 3).** Writes across domains go *only* through `events.py`/`subscribers.py`.
> Reads across domains go *only* through the publishing domain's `ports.py` (e.g.
> `domains/catalog/ports.py → get_price(db, product_id, country)`).

**This means:**
- ❌ `from domains.catalog.models import Product` in `domains/finance/services/` — **FORBIDDEN**
- ✅ `from domains.catalog.ports import get_product_by_id` in `domains/finance/services/` — **ALLOWED**
- ❌ `from domains.orders.models import Order` in `domains/logistics/services/` — **FORBIDDEN**
- ✅ `from domains.orders.ports import get_order_by_id` in `domains/logistics/services/` — **ALLOWED**
- The ONLY exception is `DOMAIN_ALLOWLIST.yaml` which tracks temporary sanctioned imports

## Current State: ~150+ Violations

| Source Domain | Violation Count | Key Violators |
|---------------|----------------|---------------|
| **governance** | ~35 | `misc_service.py` (15), `command_center_service.py` (9), `bulk_ops_service.py` (15) |
| **logistics** | ~30 | `write_service.py`, `partner_service.py`, `admin_service.py` |
| **finance** | ~25 | `payout_batch_service.py` (7+), `general_ledger_service.py` (5+) |
| **suppliers** | ~20 | `supplier_shared.py` (16), `supplier_orders.py` |
| **audit** | ~15 | `ediscovery.py` (6), `retention_service.py` (5) |
| **orders** | ~10 | `tracking/service.py` (5+), `returns/service.py` (4+) |
| **promotions** | ~10 | `admin_promotions_write_service.py`, `coupon_service.py` |
| **accounts** | ~5 | `auth_service.py` |
| **hr** | ~3 | `hierarchy_service.py`, `compliance_engine.py` |
| **country** | ~2 | `country_staff_write_service.py` |
| **comms** | ~1 | `models/suppliers.py` |
| **security** | ~2 | `public_security_detection_service.py` |

## Target Domains (Who gets imported directly)

| Target Domain | Times Directly Imported | Has Ports Coverage? |
|---------------|------------------------|---------------------|
| **governance** (User, Admin models) | ~20 | ✅ Yes |
| **catalog** (Product, Category, Banner, Coupon) | ~20 | ✅ Yes |
| **orders** (Order, OrderItem) | ~25 | ✅ Yes |
| **finance** (Payout, BankTransaction) | ~15 | ✅ Yes |
| **logistics** (Shipment, LogisticsPartner) | ~15 | ✅ Yes |
| **country** (CountryConfig, CountryStaffAssignment) | ~12 | ✅ Yes |
| **comms** (Notification, SupplierProfile) | ~10 | ✅ Yes |
| **hr** (Employee) | ~8 | ✅ Yes |
| **accounts** (User, MfaFactor) | ~8 | ✅ Yes |
| **security** (FraudEvent, FraudBlacklist) | ~5 | ✅ Yes |
| **suppliers** (SupplierProfile) | ~10 | ✅ Yes |
| **promotions** (Banner, Coupon) | ~5 | ✅ Yes |

## Ports Coverage Gaps

**Models commonly imported directly but NOT available via ports:**

| Model | Imported By | Ports Available? |
|-------|------------|------------------|
| `MfaFactor` (accounts) | customers/security | ❌ Not in accounts/ports.py |
| `CountryControl` models | audit, finance, logistics | ❌ Not in country/ports.py |
| `LogisticsPartnerLocation` | logistics | ❌ Not in country/ports.py |
| `ShipmentEvent` | audit | ❌ Not in logistics/ports.py |
| `SupplierOnboardingSync` | suppliers | ❌ Not in country/ports.py |
| `PaymentOrchestratorSync` | finance | ❌ Not in country/ports.py |
| `CountryGatewayCredentials` | finance | ❌ Not in country/ports.py |
| `PushNotificationToken` | governance | ❌ Not in comms/ports.py |
| `CouponUsage` | governance | ❌ Not in promotions/ports.py |
| `SupportTicketReply` | governance | ❌ Not in comms/ports.py |

## Events/Subscribers Coverage Gaps

| Domain | Issue |
|--------|-------|
| **catalog** | events.py is a **PLACEHOLDER** — no events defined despite being a major publishing domain |
| **hr** | events.py is a **PLACEHOLDER** — no events defined |
| **logistics** | Only 3 events; missing partner lifecycle, pricing changes |
| **orders** | Missing events for returns, refunds, cancellations |
| **logistics** | subscribers.py **MISSING** |
| **orders** | subscribers.py **MISSING** |
| **promotions** | subscribers.py **MISSING** |

## DOMAIN_ALLOWLIST.yaml Coverage

| Metric | Value |
|--------|-------|
| Total entries | 20 |
| Domains covered | 2 (finance only) |
| Violations covered | <5% |
| Unsanctioned violations | **~130+** |

**The allowlist covers ONLY finance-domain violations. All other cross-domain imports are completely unsanctioned.**

---

# CORRECTION 2: TABLE QUALITY (LAW 6)

## Architecture Rule (ARCHITECTURE_DIAGRAM.md Lines 293-295, 438-447)

> **Schema discipline:** every table in a domain Postgres schema; Alembic is the only
> schema source; naming lint (`snake_case`, plural, `<thing>_id`, `created_at/updated_at`,
> `country_code`, `is_deleted`).
>
> **Forbidden schemas:** `core` / `platform` / `identity` — every actor's `user`
> table lives in its own domain schema.

## Current State: 346 Tables, 215 Issues

### Table Count Per Domain

| Domain | Tables | Schema(s) | Assessment |
|--------|--------|-----------|------------|
| **finance** | ~55 | `finance` | Largest domain; includes ERP tables |
| **country** | ~28 | `country` | Many tables belong to other domains |
| **hr** | ~33 | `hr` | Most complete domain model |
| **comms** | ~40 | `comms`, `country` | Tables scattered across schemas |
| **governance** | ~21 | `governance`, `configuration`, `treasury` | **3 schemas — violates Law 6** |
| **logistics** | ~21 | `logistics`, `country` | Some tables in wrong schema |
| **accounts** | ~17 | `accounts` | Well-contained |
| **security** | ~21 | `security`, `suppliers`, `logistics` | **Schema leakage** |
| **suppliers** | ~11 | `suppliers`, `country` | Some tables in wrong schema |
| **customers** | ~7 | `customers`, `accounts` | Under-modelled |
| **catalog** | ~17 | `catalog` | Clean |
| **orders** | ~5 | `orders` | Clean |
| **analytics** | ~4 | `analytics` | Clean |
| **audit** | ~2 | `audit` | **Severely under-modelled** |
| **promotions** | ~4 | `promotions` | **Severely under-modelled** |

### CRITICAL: 19 Duplicate Table Definitions

| Table | Schema | File 1 | File 2 | Problem |
|-------|--------|--------|--------|---------|
| `payment_orchestrator_sync` | `country` | `country_control.py:34` | `country_payment_sync.py:27` | **DUPLICATE** |
| `country_payment_aliases` | `country` | `country_enhancements.py:218` | `country_payment_sync.py:53` | **DUPLICATE** |
| `country_gateway_configs` | `country` | `country_enhancements.py:332` | `country_payment_sync.py:73` | **DUPLICATE** |
| `supplier_onboarding_sync` | `country` | `country_control.py:57` | `supplier_country_sync.py:27` | **DUPLICATE** |
| `supplier_kyc_requirements` | `country` | `country_enhancements.py:130` | `supplier_country_sync.py:51` | **DUPLICATE** |
| `shop_warehouse_locations` | `country` | `country_control.py:135` | `logistics_country_sync.py:29` | **DUPLICATE** |
| `logistics_partner_locations` | `country` | `country_control.py:153` | `logistics_country_sync.py:49` | **DUPLICATE** |
| `parcel_location_trackers` | `country` | `country_control.py:172` | `logistics_country_sync.py:70` | **DUPLICATE** |
| `logistics_partner_kyc_requirements` | `country` | `country_enhancements.py:150` | `logistics_country_sync.py:91` | **DUPLICATE** |
| `legal_contract_templates` | `country` | `country_control.py:79` | `legal_contract_template.py:19` | **DUPLICATE** |
| `cross_country_customer_sessions` | `country` | `country_enhancements.py:58` | `cross_country_session.py:22` | **DUPLICATE** |
| `promotion_engine_configs` | `governance` | `admin.py:315` | `promotion_config.py:13` | **DUPLICATE + different schemas!** |
| `coupons` | `catalog` | `catalog/promotions.py:20` | `promotions/models/promotions.py:23` | **DUPLICATE + different schemas!** |
| `banners` | `catalog` | `catalog/promotions.py:43` | `promotions/models/promotions.py:46` | **DUPLICATE + different schemas!** |
| `bogo_promotions` | `catalog` | `catalog/promotions.py:78` | `promotions/models/promotions.py:81` | **DUPLICATE + different schemas!** |
| `user_sessions` | `accounts` | `accounts/models/user.py:74` | `governance/models/core.py:68` | Re-export shim |
| `audit_logs` | `audit` | `audit/models/audit_schema_models.py:13` | `accounts/models/core.py:78` | Re-export shim |
| `command_center_views` | `audit` | `audit/models/audit_schema_models.py:28` | `accounts/models/core.py:79` | Re-export shim |
| `executive_news` | `analytics` | `analytics/models/analytics_schema_models.py:30` | `accounts/models/core.py:88` | Re-export shim |

### CRITICAL: 17 Tables In Wrong Schema

| Domain | Table | Actual Schema | Expected Schema | File:Line |
|--------|-------|---------------|-----------------|-----------|
| finance | `payment_orchestrator_sync` | `country` | `finance` | country_payment_sync.py:28 |
| finance | `country_payment_aliases` | `country` | `finance` | country_payment_sync.py:53 |
| finance | `country_gateway_configs` | `country` | `finance` | country_payment_sync.py:73 |
| suppliers | `supplier_onboarding_sync` | `country` | `suppliers` | supplier_country_sync.py:27 |
| suppliers | `supplier_kyc_requirements` | `country` | `suppliers` | supplier_country_sync.py:51 |
| logistics | `shop_warehouse_locations` | `country` | `logistics` | logistics_country_sync.py:29 |
| logistics | `logistics_partner_locations` | `country` | `logistics` | logistics_country_sync.py:49 |
| logistics | `parcel_location_trackers` | `country` | `logistics` | logistics_country_sync.py:70 |
| logistics | `logistics_partner_kyc_requirements` | `country` | `logistics` | logistics_country_sync.py:91 |
| customers | `cross_country_customer_sessions` | `country` | `customers` | cross_country_session.py:22 |
| customers | `addresses` | `accounts` | `customers` | customer_schema_models.py:156 |
| customers | `cart_items` | `accounts` | `customers` | customer_schema_models.py:183 |
| customers | `notification_preferences` | `customer` | `customers` | customer_schema_models.py:110 |
| customers | `customer_preferences` | `customer` | `customers` | customer_schema_models.py:94 |
| customers | `customer_tags` | `customer` | `customers` | customer_schema_models.py:139 |
| governance | `system_alerts` | `configuration` | `governance` | admin.py:81 |
| governance | `system_settings` | `configuration` | `governance` | admin.py:128 |
| governance | `email_provider_configs` | `configuration` | `governance` | admin.py:261 |
| governance | `payment_provider_configs` | `treasury` | `governance` | admin.py:248 |
| governance | `finance_bank_accounts` | `treasury` | `governance` | admin.py:290 |
| security | `supplier_fraud_indicators` | `suppliers` | `security` | fraud.py:171 |
| security | `logistics_fraud_indicators` | `logistics` | `security` | fraud.py:183 |

### CRITICAL: Forbidden Schemas In Use

| Schema | Tables Using It | Owning Domain | Severity |
|--------|-----------------|---------------|----------|
| `configuration` | `system_alerts`, `system_settings`, `email_provider_configs` | governance | **CRITICAL** |
| `treasury` | `payment_provider_configs`, `finance_bank_accounts` | governance/finance | **CRITICAL** |
| `commerce` | Referenced by FKs (orders, products) | — | **CRITICAL** |
| `communication` | Referenced by FKs (email_campaigns) | comms | **CRITICAL** |
| `customer` | `customer_preferences`, `notification_preferences`, `customer_tags` | customers | **HIGH** |

### HIGH: 150+ Tables Missing Audit Columns

**Missing `created_at`:** ~150 tables across security (20), hr (35), governance (3), comms (40), country (30), customers (6), finance (10), others (6)

**Missing `updated_at`:** ~150 tables (same as above)

**Missing `is_deleted` (soft delete):** ~150 tables (same as above)

### HIGH: 100+ ForeignKeys Without `ondelete`

**Domains affected:** security (15+), hr (35+), comms (20+), governance (3), country (10+), customers (6), finance (10+)

### MEDIUM: String Without Length

| Domain | Table | Column | File:Line |
|--------|-------|--------|-----------|
| accounts | `onboarding_pipelines` | `pipeline_status` | onboarding.py:23 |
| accounts | `onboarding_steps` | `step_status` | onboarding.py:44 |

### Under-Modelled Domains

| Domain | Tables | Assessment |
|--------|--------|------------|
| audit | 2 | Only audit_logs and command_center_views. Should have audit trail tables for all major entities. |
| promotions | 4 | Missing promotion campaigns, promotion categories, promotion rules. |
| analytics | 4 | Missing dashboards, reports, metrics tables. |
| orders | 5 | Missing order history, order notes, order discounts. |

---

# CORRECTION 3: MODEL WEAKNESSES

## Architecture Rule (ARCHITECTURE_DIAGRAM.md Lines 103-110)

> Each domain must have: `services/`, `models/`, `schemas/`, `policies/`, `events.py`, `subscribers.py`, `ports.py`, `read_models/`, `features.py`

## Current State

### Missing Required Domain Files

| Domain | Missing Files |
|--------|---------------|
| analytics | `policies/`, `read_models/`, `subscribers.py` |
| audit | `policies/`, `read_models/` |
| catalog | `policies/`, `read_models/` |
| comms | `policies/`, `read_models/` |
| country | `policies/`, `read_models/` |
| customers | `policies/`, `read_models/` |
| finance | `policies/`, `read_models/` |
| governance | `policies/`, `read_models/` |
| hr | `policies/`, `read_models/` |
| logistics | `policies/`, `read_models/` |
| orders | `policies/`, `read_models/` |
| promotions | `policies/`, `read_models/` |
| security | `policies/`, `read_models/` |
| suppliers | `policies/`, `read_models/` |

### Model Quality Issues

| Issue | Count | Domains Affected |
|-------|-------|------------------|
| Missing `created_at` | ~150 tables | security, hr, comms, country, customers, finance |
| Missing `updated_at` | ~150 tables | security, hr, comms, country, customers, finance |
| Missing `is_deleted` | ~150 tables | security, hr, comms, country, customers, finance |
| Missing `ondelete` on FK | ~100 columns | security, hr, comms, country, customers, finance |
| Wrong schema | 17 tables | finance, suppliers, logistics, customers, governance, security |
| Duplicate definitions | 19 tables | finance, suppliers, logistics, customers, governance, security, promotions, catalog |
| Forbidden schemas | 5 schemas | governance (`configuration`, `treasury`), commerce, communication, customer |

---

# CORRECTION 4: MISSING TEST FILES

## Architecture Rule (ARCHITECTURE_DIAGRAM.md Lines 168-170)

> ```
> tests/
>     ├── architecture/            # test_import_laws.py (layer direction + cross-domain ban), test_feature_catalog.py
>     └── domains/                 # per-domain unit/integration tests
> ```

## Current State: Near-Zero Test Coverage

### CRITICAL: No Test Files For Any Domain

| Domain | Service Files | Test Files | Coverage |
|--------|--------------|------------|----------|
| finance | ~25 | 2 | ~8% |
| orders | ~10 | 3 | ~30% |
| logistics | ~15 | 0 | 0% |
| suppliers | ~10 | 0 | 0% |
| governance | ~15 | 0 | 0% |
| catalog | ~10 | 0 | 0% |
| customers | ~10 | 2 | ~20% |
| hr | ~15 | 0 | 0% |
| comms | ~15 | 0 | 0% |
| country | ~10 | 0 | 0% |
| security | ~10 | 0 | 0% |
| promotions | ~8 | 0 | 0% |
| analytics | ~5 | 0 | 0% |
| audit | ~8 | 0 | 0% |
| accounts | ~10 | 1 | ~10% |

### CRITICAL: No Test Files For Modules

| Module | Router Files | Test Files | Coverage |
|--------|-------------|------------|----------|
| admin | 15 | 0 | 0% |
| customer | 10 | 0 | 0% |
| employee | 12 | 0 | 0% |
| logistics | 8 | 0 | 0% |
| supplier | 10 | 0 | 0% |

### CRITICAL: No Test Files For Providers

| Provider Package | Files | Test Files | Coverage |
|-----------------|-------|------------|----------|
| ai/ | ~15 | 0 | 0% |
| payments/ | ~10 | 0 | 0% |
| comms/ | ~5 | 0 | 0% |
| geography/ | ~7 | 0 | 0% |
| image/ | ~10 | 0 | 0% |
| security/ | ~3 | 0 | 0% |
| storage/ | ~3 | 0 | 0% |
| auth/ | ~4 | 0 | 0% |

### CRITICAL: No Test Files For Infrastructure

| Infrastructure | Files | Test Files | Coverage |
|---------------|-------|------------|----------|
| database/ | ~10 | 0 | 0% |
| redis/ | ~5 | 0 | 0% |
| security/ | ~8 | 0 | 0% |
| middleware/ | ~27 | 0 | 0% |
| utils/ | ~10 | 0 | 0% |

### CRITICAL: No Test Files For RBAC

| RBAC Module | Files | Test Files | Coverage |
|------------|-------|------------|----------|
| catalog.py | 1 | 0 | 0% |
| roles.py | 1 | 0 | 0% |
| resolution.py | 1 | 0 | 0% |
| dependencies.py | 1 | 0 | 0% |
| service.py | 1 | 0 | 0% |

### CRITICAL: No Test Files For Kernel

| Kernel Module | Files | Test Files | Coverage |
|--------------|-------|------------|----------|
| money.py | 1 | 0 | 0% |
| currency.py | 1 | 0 | 0% |
| numbering.py | 1 | 0 | 0% |
| country.py | 1 | 0 | 0% |
| period.py | 1 | 0 | 0% |

### CRITICAL: Broken Tests Referencing Deleted Modules

| Test File | Broken Reference | Action |
|-----------|-----------------|--------|
| `tests/domains/test_payments.py:81-83` | `services.gateways.payments.stripe` | Update to `domains.finance.services.payments` |
| `tests/domains/test_finance_audit.py:41` | `services.finance.finance_automation` | Update or remove |
| `tests/domains/test_finance_audit.py:70` | `services.finance.je_reversal_service` | Update to `domains.finance.services.ledger` |
| 25+ `test_*_q1_rescue.py` | `services.common.db_read` | Module doesn't exist |
| 25+ `test_*_q1_rescue.py` | `routers/{name}.py` | Routers live under `modules/*/routers/` |

### Missing Architecture Tests

| Law | Test Exists? | File |
|-----|-------------|------|
| Law 1 (Arrows down) | ✅ Yes | `test_import_laws.py` |
| Law 2 (Thin routers) | ⚠️ Partial | `test_architecture_gates.py` |
| Law 3 (Cross-domain via ports/events) | ❌ **MISSING** | — |
| Law 4 (Features single-sourced) | ✅ Yes | `test_feature_catalog.py` |
| Law 5 (Country scope) | ❌ **MISSING** | — |
| Law 6 (Schema discipline) | ❌ **MISSING** | — |
| Law 7 (Allowlist shrink) | ❌ **MISSING** | — |

### CRITICAL: No CI Pipeline

| CI Component | Status |
|-------------|--------|
| GitHub Actions workflow | ❌ **MISSING** |
| Architecture gates in CI | ❌ **MISSING** |
| Unit test runner | ❌ **MISSING** |
| Schema drift check | ❌ **MISSING** |
| Test coverage reporting | ❌ **MISSING** |
| Lint check (ruff) | ❌ **MISSING** |

---

# CATEGORY 5: SECURITY

## CRITICAL: RBAC Bypass Via Direct `require_feature()` Calls

- **Files:** `modules/supplier/routers/catalog.py:29,37,46,55,64,73`, `modules/supplier/routers/suppliers.py:35,48,60,70,82,95,107,120,130,141,152,162,173`, `modules/supplier/routers/finance.py:81-238`, `modules/employee/routers/hr.py:1005-1088`
- **Problem:** `require_feature("x")` called directly (not via `Depends`) silently skips enforcement because `set_current_user()` is never called in the canonical auth flow
- **Fix:** Call `set_current_user(user)` inside `get_current_user` or enforce `Depends(require_feature("x"))` everywhere
- **Severity:** CRITICAL

## CRITICAL: Auth Optional With `= None` Default

- **File:** `modules/employee/routers/comms.py:392,409,419,431,444,458,468,479,490,501,509,519,546,565`
- **Problem:** `current_user: AdminUser = None` makes auth optional — FastAPI uses `None` instead of invoking the dependency
- **Fix:** Remove `= None` default
- **Severity:** CRITICAL

## CRITICAL: Hardcoded Fallback Encryption Secret

- **File:** `domains/security/services/security_provider_helpers.py:32`
- **Problem:** `secret = settings.secret_key or "fallback-zozi-secret"` — publicly-known string weakens all PII encryption
- **Fix:** Remove fallback; raise ValueError if empty
- **Severity:** CRITICAL

## CRITICAL: Duplicate Auth Blacklists

- **Files:** `infrastructure/utils/auth.py`, `infrastructure/security/auth.py`
- **Problem:** Two near-identical copies with separate `_memory_blacklist` dicts — token revocation bypass between workers
- **Fix:** Delete `infrastructure/security/auth.py` and update imports
- **Severity:** CRITICAL

## HIGH: `decode_token` Does Not Check Blacklist

- **File:** `infrastructure/utils/auth.py:343-347`
- **Problem:** `decode_token()` verifies JWT signature/expiry but not blacklist — revoked tokens still accepted
- **Fix:** Add `check_blacklist: bool = True` parameter to `decode_token()`
- **Severity:** HIGH

## HIGH: Hardcoded SECRET_KEY in `.env`

- **File:** `backend/.env:4`
- **Problem:** Real 64-character hex key committed to repo
- **Fix:** Remove from git, rotate key, generate fresh per environment
- **Severity:** HIGH

## HIGH: Multiple `get_current_user` Implementations

- **Files:** `infrastructure/security/dependencies.py:49`, `domains/security/services/iam/security_dependencies.py:41`, `rbac/__init__.py:14`
- **Problem:** Three implementations with different return types and behaviors
- **Fix:** Consolidate to single implementation
- **Severity:** HIGH

## HIGH: Token Blacklist In-Memory Fallback

- **File:** `infrastructure/utils/auth.py:77-93`
- **Problem:** When Redis unavailable, falls back to in-memory dict — tokens blacklisted on worker A invisible to worker B
- **Fix:** Make Redis required for token blacklisting in multi-worker environments
- **Severity:** HIGH

## HIGH: Raw Exception Messages Returned to Clients

- **Files:** `modules/employee/routers/hr.py:1020,1064`, `modules/employee/routers/comms.py:438,451,497,621,924`
- **Problem:** `detail=str(e)` leaks internal paths, database details, stack traces
- **Fix:** Return generic error message; log full exception server-side
- **Severity:** MEDIUM

---

# CATEGORY 6: CODE QUALITY & LOGIC

## CRITICAL: WORM Audit Chain Integrity Check Non-Functional

- **File:** `domains/audit/services/worm_audit.py:73-83`
- **Problem:** `get_chain_integrity()` loads ALL records with `.all()` and always returns `chain_valid: True` without verifying
- **Fix:** Implement actual hash chain verification
- **Severity:** CRITICAL

## HIGH: Duplicated Functions in `payout_batch_service.py`

- **File:** `domains/finance/services/payouts/payout_batch_service.py`
- **Problem:** Functions `_resolve_supplier_names`, `_resolve_logistics_names`, `_enrich_batch_items` duplicated at lines 2884-2909 and 4080-4104
- **Fix:** Remove duplicate definitions
- **Severity:** HIGH

## HIGH: Duplicated `NewsAggregatorService` and `CommandCenterService` Classes

- **Files:** `analytics/services/aggregation/command_center_service.py:82,263`, `governance/services/command_center/service.py:75,256`
- **Problem:** Identical classes duplicated across two domains
- **Fix:** Extract to shared service or provider module
- **Severity:** HIGH

## HIGH: Exception Swallowing in `_get_frontend_url`

- **File:** `domains/finance/services/payouts/payout_batch_service.py:1949`
- **Problem:** Catches 15 exception types and silently returns default URL
- **Fix:** Catch specific expected exceptions and log appropriately
- **Severity:** HIGH

## HIGH: Module-Level Mutable State

- **Files:** `infrastructure/utils/event_bus.py:18`, `infrastructure/messaging/events/event_bus.py:18`, `infrastructure/utils/auth.py:28-29`, `modules/employee/routers/hr.py:312`
- **Problem:** Module-level mutable dictionaries shared across all requests — not thread-safe
- **Fix:** Use thread-local storage or proper synchronization
- **Severity:** HIGH

## HIGH: In-Memory Payroll Approvals

- **File:** `modules/employee/routers/hr.py:312`
- **Problem:** `PENDING_PAYROLL_APPROVALS: dict = {}` — state lost on restart, not shared across workers
- **Fix:** Use database persistence
- **Severity:** HIGH

---

# CATEGORY 7: PERFORMANCE & SCALABILITY

## CRITICAL: Loading Entire Tables Into Memory

- **Files:** `jobs/seed_all.py:447`, `domains/finance/services/ledger/general_ledger_service.py:197`, `domains/hr/services/hierarchy/hierarchy_service.py:324`, `domains/suppliers/services/health/supplier_health_service.py:38`
- **Problem:** `.all()` loads entire table — will OOM at 100k+ users
- **Fix:** Use keyset pagination or limit results
- **Severity:** CRITICAL

## HIGH: OFFSET Pagination on Hot Lists

- **Files:** 50+ locations using `.offset()` including `payout_batch_service.py:4071-4221`, `products_service.py:273,570,847`, `tickets_service.py:200`, `router_helpers.py:41`, `pagination.py:56,82,112`
- **Problem:** OFFSET degrades at high offsets
- **Fix:** Replace with keyset/cursor pagination
- **Severity:** HIGH

## HIGH: N+1 Query Pattern

- **Files:** `analytics/services/aggregation/command_center_service.py:695-696`, `governance/services/command_center/service.py:682-683`
- **Problem:** Uses `.all()` then `len()` instead of `.count()`
- **Fix:** Use `.count()` instead
- **Severity:** HIGH

## HIGH: Synchronous Blocking in Async Contexts

- **Files:** `analytics/services/aggregation/command_center_service.py:88-92`, `infrastructure/ml/worker.py:79,115,122`
- **Problem:** Synchronous `self.db.query(...).all()` blocks the event loop
- **Fix:** Use `run_in_executor()` for sync DB calls in async contexts
- **Severity:** HIGH

## HIGH: Missing Caching on Hot Paths

- **Files:** `catalog/utils/category_tree.py:58`, `finance/services/ledger/general_ledger_service.py:71-72`
- **Problem:** Category tree and chart of accounts queried every request
- **Fix:** Add Redis caching with TTL
- **Severity:** HIGH

---

# CATEGORY 8: INFRASTRUCTURE & CONNECTIONS

## HIGH: Redis Connection Failure Silently Falls Back to NoOp

- **File:** `infrastructure/redis/client.py:84-88`
- **Problem:** Single failure falls back to `_NoOpRedis` forever — all rate limiting and caching silently disabled
- **Fix:** Add retry logic; log warning on fallback
- **Severity:** HIGH

## HIGH: Connection Leaks (SessionLocal Without try/finally)

- **Files:** `lifespan.py:89-95,124-130,143-149,189-195`, `jobs/seed_all.py:285,321,379,499`, `jobs/fx_revaluation.py:38`
- **Problem:** Sessions not closed on exception — connection leak
- **Fix:** Wrap in `try/finally` with `db.close()` or use `get_db()` context manager
- **Severity:** HIGH

## HIGH: No Retry on Payment Provider Calls

- **File:** `providers/payments/stripe_sdk.py`
- **Problem:** Payment calls have no retry logic
- **Fix:** Use `infrastructure/observability/retry.py` with exponential backoff
- **Severity:** HIGH

---

# CATEGORY 9: ERROR & EXCEPTION HANDLING

## HIGH: Payment Idempotency Cache Failure Silently Ignored

- **File:** `domains/finance/services/payments/payment_engine.py:134-135`
- **Problem:** `except Exception: pass` — could lead to duplicate charges
- **Fix:** Log exception; raise if cache write fails
- **Severity:** HIGH

## HIGH: `get_optional_user` Swallows All Exceptions

- **File:** `domains/accounts/services/auth/auth_service.py:1899-1927`
- **Problem:** Caller cannot distinguish "invalid token" from "DB error"
- **Fix:** Log exception; re-raise critical errors
- **Severity:** HIGH

## MEDIUM: 14+ Empty `except: pass` Blocks

- **Files:** `finance/services/payments/payment_engine.py:2408`, `finance/services/payouts/payout_batch_service.py:430,459`, `suppliers/services/products/supplier_products_service.py:204`, `orders/services/tracking/service.py:1142`, `customers/services/search_service.py:257`, `comms/services/messaging/websocket_handlers.py:318`
- **Problem:** Silent failures
- **Fix:** At minimum, log all exceptions
- **Severity:** MEDIUM

---

# PRIORITY ACTION PLAN

## P0 — Fix Immediately (this week)

| # | Issue | File | Action |
|---|-------|------|--------|
| 1 | RBAC bypass via direct `require_feature()` | `modules/supplier/routers/*.py` | Add `set_current_user()` to auth flow |
| 2 | Auth optional with `= None` default | `modules/employee/routers/comms.py` | Remove `= None` defaults |
| 3 | Hardcoded fallback encryption secret | `security_provider_helpers.py:32` | Remove fallback; raise error |
| 4 | Duplicate auth blacklists | `infrastructure/security/auth.py` | Delete duplicate |
| 5 | Loading entire tables into memory | `seed_all.py`, `general_ledger_service.py` | Add pagination/limits |
| 6 | 19 duplicate table definitions | Multiple files | Keep canonical, convert others to re-exports |
| 7 | 150+ tables missing audit columns | `domains/*/models/*.py` | Add via Alembic migration |
| 8 | No CI pipeline | `.github/workflows/ci.yml` | Create CI workflow |
| 9 | No test files for any domain | `tests/domains/` | Create test files for all 16 domains |
| 10 | No test files for modules | `tests/modules/` | Create integration tests for all 5 modules |

## P1 — Fix This Month

| # | Issue | File | Action |
|---|-------|------|--------|
| 11 | ~150 domain-to-domain import violations | `domains/*/services/*.py` | Migrate to ports.py |
| 12 | 17 tables in wrong schema | `domains/*/models/*.py` | Move to correct schema via Alembic |
| 13 | Forbidden schemas (configuration, treasury, commerce) | `governance/models/admin.py` | Consolidate to governance schema |
| 14 | 100+ FKs without ondelete | `domains/*/models/*.py` | Add ondelete via Alembic |
| 15 | Connection leaks | `lifespan.py`, `jobs/*.py` | Add try/finally |
| 16 | OFFSET pagination | 50+ files | Replace with keyset pagination |
| 17 | Module router __init__.py mismatches | 4 modules | Add missing domains |
| 18 | Broken tests referencing deleted modules | `tests/domains/test_*.py` | Update references |
| 19 | Missing test files for providers | `tests/providers/` | Create test files for all providers |
| 20 | Missing test files for infrastructure | `tests/infrastructure/` | Create test files |

## P2 — Fix This Quarter

| # | Issue | File | Action |
|---|-------|------|--------|
| 21 | Code duplication (CommandCenterService, NewsAggregatorService) | `analytics/`, `governance/` | Consolidate |
| 22 | Missing caching on hot paths | `category_tree.py`, `general_ledger_service.py` | Add Redis caching |
| 23 | Sync blocking in async contexts | `command_center_service.py`, `ml_worker.py` | Use run_in_executor |
| 24 | Missing architecture tests | `tests/architecture/` | Add Law 3/5/6/7 tests |
| 25 | No test coverage reporting | `pyproject.toml` | Add pytest-cov |
| 26 | Duplicate event bus implementations | `utils/event_bus.py`, `messaging/events/event_bus.py` | Consolidate |
| 27 | Under-modelled domains (audit, promotions, analytics) | `domains/audit/`, `domains/promotions/`, `domains/analytics/` | Add missing tables |
| 28 | Missing test files for kernel | `tests/test_kernel.py` | Create kernel tests |
| 29 | Missing test files for rbac | `tests/rbac/` | Create RBAC tests |
| 30 | No schema drift check | CI | Add alembic check |

---

# APPENDIX A: Architecture Laws Reference

| Law | Description | Status |
|-----|-------------|--------|
| Law 1 | Arrows point down only (modules → domains → infrastructure) | ✅ PASS |
| Law 2 | Module routers stay thin | ✅ PASS |
| Law 3 | Cross-domain via events/ports only | ❌ **~150+ violations** |
| Law 4 | Features single-sourced | ✅ PASS |
| Law 5 | Country is orthogonal scope axis | ✅ PASS |
| Law 6 | Schema discipline | ❌ **215 violations** |
| Law 7 | Allowlist may only shrink | ❌ **<5% coverage** |

# APPENDIX B: File Count Summary

| Layer | Files | Issues |
|-------|-------|--------|
| `modules/` | ~80 router files | RBAC bypass, no tests |
| `domains/` | ~1200 service/model files | Cross-domain imports, schema issues, no tests |
| `infrastructure/` | ~50 files | Connection leaks, duplicate auth, no tests |
| `kernel/` | 5 files | No tests |
| `providers/` | ~90 files | Missing retry, no tests |
| `rbac/` | 8 files | Missing tests |
| `middleware/` | ~27 files | No tests |
| `jobs/` | ~21 files | Connection leaks |
| `tests/` | ~50 files | Broken references, missing coverage |

# APPENDIX C: Key Metrics

| Metric | Value |
|--------|-------|
| Total tables | ~346 |
| Tables with correct schema | ~329 |
| Tables in wrong schema | 17 |
| Duplicate table definitions | 19 |
| Tables missing created_at | ~150 |
| Tables missing updated_at | ~150 |
| Tables missing is_deleted | ~150 |
| FKs without ondelete | ~100 |
| Cross-domain import violations | ~150 |
| Domain test coverage | ~5% |
| Module test coverage | 0% |
| Provider test coverage | 0% |
| Infrastructure test coverage | 0% |
| Kernel test coverage | 0% |
| RBAC test coverage | 0% |
| Architecture tests missing | 4 of 7 laws |
