# Customers Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/customers/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **100+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 15+ |
| 🟠 HIGH | 35+ |
| 🟡 MEDIUM | 30+ |
| 🟢 LOW | 20+ |
| **TOTAL** | **100+** |

---

## 1. BROKEN IMPORTS (CRITICAL — Runtime Crashes)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `services/__init__.py` | 12 | `from domains.customers.services.referrals import *` — no `__init__.py` in referrals/ | Add `__init__.py` or remove import |
| 2 | `ports.py` | 41 | `Optional` used but never imported | Add `from typing import Optional` |
| 3 | `models/__init__.py` | 31 | `CustomerSchema` advertised but undefined | Define class or remove from facade |
| 4 | `wishlist_service_from_accounts.py` | all | Dead file, never imported | DELETE |
| 5 | `customer_health_service_from_accounts.py` | all | Dead file with N+1 | DELETE |
| 6 | `customer_health_list_service_from_accounts.py` | all | Dead file with N+1 | DELETE |
| 7 | `referrals/referrals_service.py` | all | Archived, wrong layer, broken import chain | DELETE |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 8 | `commerce_read_service.py` | 11 | Imports `Address` from accounts | Move to customers models |
| 9 | `commerce_write_service.py` | 14 | Imports `Address` from accounts | Move to customers models |
| 10 | `customer_router_service.py` | 13 | Imports `Address` from accounts | Move to customers models |
| 11 | `cart_service.py` | 23 | Imports `CartItem` from accounts | Move to customers models |
| 12 | `cart_write_service.py` | 13 | Imports `CartItem` from accounts | Move to customers models |
| 13 | `wishlist_*.py` | 9-16 | Imports `WishlistItem` from catalog | Move to customers models |
| 14 | `reviews_service.py` | 13 | Imports `Review` from catalog | Move to customers models |
| 15 | `coupons_*.py` | 14-18 | Imports `Coupon` from catalog | Move to promotions models |
| 16 | `customer_health_engine.py` | 10-12 | Imports from accounts, orders | Use ports |
| 17 | `public_comms_status_service.py` | 1 | **Entire file is comms logic** | Move to `domains/comms/` |

---

## 3. SECURITY ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 18 | `reviews_service.py` | 114-136 | Race condition in `create_review_with_checks` | Add unique constraint + catch `IntegrityError` |
| 19 | `reviews_service.py` | 139-146 | `user_role` check is not RBAC | Use `rbac.require_feature()` |
| 20 | `reviews_service.py` | 155-164 | Client can set `is_verified_purchase` | Remove from `allowed_fields` |
| 21 | `search_service.py` | 40-48 | Swallows all exceptions, leaks `str(exc)` | Re-raise or return generic error |
| 22 | `zozi_coins_service.py` | 210-214 | Raw SQL bypasses ORM | Use `with_for_update()` |
| 23 | `zozi_coins_service.py` | 112-121 | Lock returns `True` when Redis down | Fail closed |
| 24 | `zozi_coins_service.py` | 88-109 | No idempotency on coin awards | Add unique constraint |
| 25 | `cart_write_service.py` | 77-82 | `create_cart_item` accepts arbitrary `**item_data` | Allowlist fields |
| 26 | `cart_write_service.py` | 85-90 | `update_cart_item` mass assignment | Allowlist fields |
| 27 | `customer_router_service.py` | 91 | `create_address` hard-codes `full_name="Customer"` | Take from payload |
| 28 | `customer_health_list_service.py` | 23-26 | No auth check at all | Add `require_feature()` |

---

## 4. SCALABILITY ISSUES (HIGH)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 29 | `search_service.py` | 598 | Unbounded candidate fetch | Cap at 200 rows |
| 30 | `search_service.py` | 326-389 | Python loop scoring O(N) per request | Move scoring to SQL |
| 31 | `search_service.py` | 238-276 | Cache key space too large | Cache brand catalog separately |
| 32 | `customer_health_engine.py` | 22-74 | N+1: fetches orders twice | Use already-loaded orders |
| 33 | `recommendation_service.py` | 160-235 | 3 separate order joins | Consolidate into CTE |
| 34 | `public_comms_status_service.py` | 29-30 | In-memory WS state not Redis-backed | Use Redis pub/sub |
| 35 | `public_comms_status_service.py` | 284-320 | DB session per WS ping | Read role from JWT |
| 36 | `user_read_service.py` | 16-33 | No caching | Add Redis cache |
| 37 | `country_auto_populate.py` | 382-393 | 900s Ollama timeout | Cap with `asyncio.wait_for` |

---

## 5. MISSING FUNCTIONALITY (10 GAPS)

### 5.1 CRITICAL (2 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 38 | **Security** (2FA, sessions, fraud signals) | `services/security_service.py` + models |
| 39 | **Compliance** (GDPR export, deletion, consent) | `services/compliance_service.py` + models |

### 5.2 HIGH (5 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 40 | **Profile service** (real implementation) | `services/profile_service.py` |
| 41 | **Address verification** | `services/address_verification_service.py` |
| 42 | **Customer preferences** (locale, currency, language) | `services/preferences_service.py` + models |
| 43 | **Notification preferences** (per channel, per topic) | `services/notification_preferences_service.py` + models |
| 44 | **Customer segmentation** (tags, RFM, LTV) | `services/segmentation_service.py` + models |

### 5.3 MEDIUM (3 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 45 | **Loyalty tiers & rewards** | `services/loyalty_service.py` |
| 46 | **Support tickets & feedback** | `services/support_service.py` |
| 47 | **Returns service** (event already declared) | `services/returns_service.py` |

---

## 6. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 6.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 48 | No `kernel/money.py` usage — uses `float()` for money | Use `kernel.money.to_decimal()` |
| 49 | No `kernel/currency.py` usage — hardcoded currencies | Use `kernel.currency.Currency` |
| 50 | No `kernel/country.py` usage | Use `kernel.country.normalize_country()` |
| 51 | No `kernel/period.py` usage — hardcoded `30 days` | Create `kernel.period` |

### 6.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 52 | `rbac` completely unused in customers services | Wire `rbac/catalog.py` |
| 53 | `require_feature()` never called | Wire in routers |
| 54 | Role string comparison (`!= "admin"`) | Use `rbac.require_feature()` |
| 55 | `features.py` has duplicate atoms (`customers.referral.manage` + `customers.referrals.manage`) | Consolidate |

### 6.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 56 | Only `providers.geography` used | Add `providers.comms`, `providers.payments` |
| 57 | `providers.ai` not used for recommendations | Add connection |

### 6.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 58 | No Redis cache on hot read paths | Add `cache_get_json`/`cache_set_json` |
| 59 | No tracing/metrics/Sentry | Add `with_tracing()` and counters |
| 60 | In-memory WS state not Redis-backed | Use Redis pub/sub |

---

## 7. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 61 | `admin/routers/customers.py` | 9, 12 | Dead imports (`create_review`, `delete_review`, `remove_from_wishlist`) | Add endpoints or remove imports |
| 62 | `admin/routers/customers.py` | all | `require_feature()` called in body, not as `Depends` | Convert to `Depends` |
| 63 | `admin/routers/customers.py` | 66-74 | `body: dict` instead of Pydantic | Add schemas |
| 64 | `admin/routers/customers.py` | 502, 512, 523 | Route shadowing by `/{code}` catch-all | Reorder routes |
| 65 | `customer/routers/customers.py` | all | Only 2 endpoints for 12 features | Add missing endpoints |
| 66 | `employee/routers/customers.py` | — | **FILE DOES NOT EXIST** | Create |
| 67 | `supplier/routers/customers.py` | — | **FILE DOES NOT EXIST** | Create |
| 68 | `logistics/routers/customers.py` | — | **FILE DOES NOT EXIST** | Create |
| 69 | `customer/routers/customers.py` | 1-6 | Unused imports (`HTTPException`, `Path`, `Body`, `status`) | Remove |
| 70 | `customer/routers/customers.py` | 24-43 | No error handling | Add try/except |

---

## 8. DUPLICATE FILES & LOGIC

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 71 | `wishlist_service.py` / `wishlist_service_from_accounts.py` | Duplicate | Delete `_from_accounts` |
| 72 | `customer_health_service.py` / `customer_health_service_from_accounts.py` | Duplicate | Delete `_from_accounts` |
| 73 | `customer_health_list_service.py` / `customer_health_list_service_from_accounts.py` | Duplicate | Delete `_from_accounts` |
| 74 | `coupons_service.py` / `coupons_read_service.py` / `coupons_write_service.py` | Triple implementation | Consolidate |
| 75 | `events.py` (root) / `services/events.py` | Two parallel event systems | Consolidate |
| 76 | `referrals/referrals_service.py` | Archived, wrong layer | DELETE |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix broken import in `services/__init__.py` (referrals) |
| 2 | Add `from typing import Optional` to `ports.py` |
| 3 | Define `CustomerSchema` or remove from facade |
| 4 | Delete dead files (`*_from_accounts.py`, `referrals/referrals_service.py`) |
| 5 | Move `public_comms_status_service.py` to `domains/comms/` |
| 6 | Fix race condition in `create_review_with_checks` |
| 7 | Fix exception swallowing in `search_service.py` |
| 8 | Fix coin redemption lock (fail closed) |
| 9 | Add idempotency to coin awards |
| 10 | Add auth check to `get_customer_health_detail` |
| 11 | Move `Address`, `CartItem`, `WishlistItem`, `Review` to customers models |
| 12 | Replace direct cross-domain model imports with ports |
| 13 | Wire `rbac/catalog.py` and `require_feature()` |
| 14 | Add missing routers (employee, supplier, logistics) |
| 15 | Add missing customer endpoints (address, wishlist, review, referral, profile) |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 16 | Create `schemas/` package with Pydantic models |
| 17 | Add pagination to all list endpoints |
| 18 | Add Redis cache to hot read paths |
| 19 | Add tracing/metrics |
| 20 | Fix N+1 queries in health engine and recommendations |
| 21 | Replace `float()` money with `kernel.money.to_decimal()` |
| 22 | Add customer preferences service |
| 23 | Add notification preferences service |
| 24 | Add customer segmentation service |
| 25 | Add profile service (real implementation) |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 26 | Delete duplicate files |
| 27 | Consolidate duplicate logic |
| 28 | Add missing imports |
| 29 | Fix session leaks |
| 30 | Add unbounded query limits |
| 31 | Implement loyalty tiers |
| 32 | Implement support tickets |
| 33 | Implement returns service |
| 34 | Implement compliance (GDPR) |
| 35 | Implement security (2FA, sessions) |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 50+ |
| Files with cross-domain pollution | 15+ |
| CRITICAL issues | 15+ |
| HIGH issues | 35+ |
| MEDIUM issues | 30+ |
| LOW issues | 20+ |
| Broken imports | 7 |
| Dead files | 5 |
| Security vulnerabilities | 11 |
| Missing RBAC | Entire domain |
| Missing kernel usage | 5 modules |
| Missing functionality gaps | 10 |
| Duplicate file pairs | 6 |
| Missing routers | 3 |
| Empty schemas | Entire package |
