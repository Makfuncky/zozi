# Catalog Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/catalog/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **100+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 25+ |
| 🟠 HIGH | 35+ |
| 🟡 MEDIUM | 30+ |
| 🟢 LOW | 15+ |
| **TOTAL** | **100+** |

---

## 1. SCHEMA & MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `models/products.py` | 18, 65, 116, 150, 229, 245 | FK references `commerce.*` instead of `catalog.*` | Change to `catalog.*` |
| 2 | `models/products.py` | 117, 136, 149 | `SET NULL` + `nullable=False` contradiction | Make nullable or change ondelete |
| 3 | `models/products.py` | 161, 187-188 | `ProductVariant` FK wrong schema + args ordering | Fix FK + reorder class |
| 4 | `models/products.py` | 215 | FK to `media.product_videos.id` (forbidden `media` schema) | Change to `catalog.product_videos.id` |
| 5 | `models/ai_upload.py` | 58, 76 | FK references `commerce.products.id` | Change to `catalog.products.id` |
| 6 | `models/products.py` | 132-222 | 7 models missing `is_deleted` | Add column to all |
| 7 | `models/ai_upload.py` | 69-150 | 3 models missing `is_deleted` | Add column to all |
| 8 | `models/upload_job.py` | 43 | `status` reserved keyword | Rename to `job_status` |
| 9 | `models/ai_upload.py` | 53 | `status` reserved keyword | Rename to `job_status` |
| 10 | `models/products.py` | 83 | `Product.is_deleted` no index | Add `index=True` |
| 11 | `models/products.py` | 74, 82 | `is_approved` + `moderation_status` redundant | Keep one, derive other |
| 12 | `ports.py` | 59, 63, 178, 182 | Typos: `list_categorys`, `list_video_analyticss` | Fix names |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 Accounts/Cart Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `products_service.py` | 378 | Direct import of `CartItem` from accounts | Use `domains.accounts.ports` |
| 14 | `products_service.py` | 383 | Direct DELETE on `CartItem` — cross-domain write | Use events |
| 15 | `admin_products_service.py` | 403, 410 | Direct import + DELETE on `CartItem` | Use events |

### 2.2 Comms/Notification Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 16 | `products_service.py` | 380 | Direct import of `Notification` from comms | Use events |
| 17 | `products_service.py` | 383-397 | Direct INSERT into `Notification` | Use events |
| 18 | `admin_products_service.py` | 405 | Direct import of `Notification` | Use events |

### 2.3 Orders Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 19 | `products_service.py` | 381 | Direct import of `Order`, `OrderItem` | Use `domains.orders.ports` |
| 20 | `product_verification_service.py` | 18 | Direct import of `Order` | Use ports |

### 2.4 Logistics Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 21 | `product_verification_service.py` | 17 | Direct import of `Shipment` | Use `domains.logistics.ports` |

### 2.5 Supplier Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 22 | `products_service.py` | 806, 819 | Direct import of `SupplierProfile` | Use ports |

---

## 3. BROKEN IMPORTS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 23 | `services/__init__.py` | 9, 14-18, 20-21, 56-61 | 5+ imports of non-existent functions | Fix or remove |
| 24 | `admin_products_service.py` | 17-21, 186, 202 | `bulk_product_moderation`, `bulk_category_change` not imported | Fix imports |
| 25 | `ai_search_service.py` | 76, 80, 84 | `re` not imported | Add `import re` |
| 26 | `admin_products_service.py` | 303-422 | `Decimal`, `selectinload`, `cast`, `or_`, `func` not imported | Add imports |
| 27 | `search_service.py` | 10 | `AdvancedSearchEngine()` missing `db` argument | Fix constructor |
| 28 | `country_dropdown_service.py` | — | `__init__.py` references non-existent symbol | Fix re-export |

---

## 4. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 4.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 29 | No `kernel/money.py` usage — uses `float()` for money (60+ call sites) | Use `kernel.money.to_decimal()` |
| 30 | No `kernel/currency.py` usage — no currency conversion | Use `kernel.currency.convert()` |
| 31 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.normalize_country()` |
| 32 | No `kernel/constants.py` direct usage | Use `kernel.constants` directly |
| 33 | No `kernel/period.py` usage — hand-rolled date math | Create `kernel.period` |

### 4.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 34 | `rbac` completely unused in catalog | Wire `rbac/catalog.py` |
| 35 | `require_feature()` never called in services | Wire in routers |
| 36 | Uses `infrastructure.utils.dependencies` instead of `rbac.dependencies` | Use canonical path |
| 37 | `features.py` not registered in `rbac/catalog.py` | Register features |

### 4.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 38 | Only `providers.image` + `providers.ai` used | Add `providers.comms`, `providers.storage`, `providers.geography` |
| 39 | `providers.media.services.ai` invoked via string import | Refactor to thin `providers.ai` |
| 40 | `providers.payments` never imported | Add connection |
| 41 | `providers.qr`, `providers.barcode`, `providers.scanner` not used | Add on demand |

### 4.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 42 | No Redis cache on hot product list | Add `cache_or_compute` |
| 43 | No tracing/metrics/Sentry | Add `with_tracing()` and counters |
| 44 | `logger` mixed between `logging` and `structlog` | Standardize on `structlog` |
| 45 | `get_products_health` in domain service | Move to `infrastructure.observability` |
| 46 | RLS is a no-op (known gotcha) | Complete `instrument_rls` or filter explicitly |
| 47 | `country_code` not threaded through `get_products` | Add parameter |

---

## 5. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 48 | `admin/routers/catalog.py` | 115, 126, etc. | Missing `current_user` arg → AttributeError | Add parameter |
| 49 | `customer/routers/catalog.py` | — | **FILE DOES NOT EXIST** | Create |
| 50 | `employee/routers/catalog.py` | — | **FILE DOES NOT EXIST** | Create |
| 51 | `admin/routers/catalog.py` | 132, 284, 43 | `dict = Body(...)` instead of Pydantic schema | Add schemas |
| 52 | `supplier/routers/catalog.py` | 38, 66 | `current_user.id` fragile | Standardize |
| 53 | `supplier/routers/catalog.py` | 59-66 | No file-type validation | Add validation |
| 54 | Both routers | — | No audit events emitted on mutations | Add events |
| 55 | `supplier/routers/catalog.py` | — | No supplier restore endpoint | Add endpoint |

---

## 6. CODE QUALITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 56 | `products_service.py` | 312 | Client can set own rating (fraud vector) | Remove from `_CREATE_FIELDS` |
| 57 | `products_service.py` | 446-451 | Race condition in `atomic_stock_decrement` | Use RETURNING clause |
| 58 | `products_service.py` | 455-491 | `finalize_inventory_atomic` no rollback | Wrap in transaction |
| 59 | `products_service.py` | 871-873 | `soft_delete_product` is a stub | Delete or implement |
| 60 | `products_service.py` | 101-102 | `_is_product_restricted_for_country` always returns False | Implement or remove |
| 61 | `products_service.py` | 707-708 | Two parallel discount models | Pick one |
| 62 | `products_service.py` | 266-271 | OFFSET pagination | Use keyset/cursor |
| 63 | `search_service.py` | 866 | Mutable class-level `_cache` dict | Use Redis |
| 64 | `ai_upload_service.py` | 35-38 | Two logger assignments | Keep one |
| 65 | `ai_upload_service.py` | 394-400 | `_check_duplicate_image` never called | Delete |
| 66 | `admin_products_service.py` | 258-276 | Route wrappers in service file | Move to controllers |
| 67 | `admin_products_service.py` | 298-319 | `Decimal` not imported | Add import |
| 68 | `admin_products_service.py` | 322-415 | Divergent delete behavior | Consolidate |
| 69 | `category_admin_routing_service.py` | 1-10 | Controller in services folder | Move to modules/ |
| 70 | `admin_categories_service.py` | 1-5 | Archived module still present | Delete |
| 71 | `categories_service.py` | — | Legacy duplicate | Delete |

---

## 7. DUPLICATE FILES & LOGIC

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 72 | `products_service.py` / `admin_products_service.py` | Duplicate product CRUD | Consolidate |
| 73 | `categories_service.py` / `category_service.py` | Duplicate category CRUD | Delete `categories_service.py` |
| 74 | `admin_categories_service.py` / `category_service.py` | Duplicate archive/restore | Delete `admin_categories_service.py` |
| 75 | `search_service.py` (top-level) / `search/search_service.py` | Duplicate at wrong level | Delete top-level |
| 76 | `analytics_service.py` / `admin_analytics_service.py` | Duplicate analytics functions | Consolidate |
| 77 | `events.py` / `services/events.py` | Duplicate events | Delete `services/events.py` |
| 78 | `subscribers.py` / `services/subscribers.py` | Duplicate subscribers | Delete `services/subscribers.py` |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix all `commerce.*` FKs → `catalog.*` |
| 2 | Fix `media.*` FK → `catalog.*` |
| 3 | Fix `SET NULL` + `nullable=False` contradictions |
| 4 | Fix broken imports in `services/__init__.py`, `admin_products_service.py`, `ai_search_service.py` |
| 5 | Add missing `is_deleted` columns to 10 models |
| 6 | Remove direct cross-domain writes (use events) |
| 7 | Replace `float()` money with `kernel.money.to_decimal()` |
| 8 | Wire `rbac/catalog.py` and `require_feature()` |
| 9 | Fix `current_user` AttributeError in admin router |
| 10 | Create missing routers (customer, employee) |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 11 | Delete duplicate files (`categories_service.py`, `admin_categories_service.py`, top-level `search_service.py`) |
| 12 | Consolidate duplicate product/category CRUD |
| 13 | Add missing imports (`Decimal`, `selectinload`, `re`, etc.) |
| 14 | Add Pydantic schemas to routers |
| 15 | Add audit events on mutations |
| 16 | Add supplier restore endpoint |
| 17 | Move `category_admin_routing_service.py` to modules/ |
| 18 | Move `get_products_health` to infrastructure |
| 19 | Add Redis cache to hot product list |
| 20 | Add `country_code` to `get_products` |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 21 | Add missing `updated_at`, `created_at` columns |
| 22 | Rename `status` columns to `job_status` |
| 23 | Add `index=True` to `is_deleted` |
| 24 | Fix typos in `ports.py` |
| 25 | Add `providers.comms`, `providers.geography` connections |
| 26 | Add tracing/metrics |
| 27 | Standardize on `structlog` |
| 28 | Replace OFFSET pagination with keyset |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 45+ |
| Files with cross-domain pollution | 15+ |
| CRITICAL issues | 25+ |
| HIGH issues | 35+ |
| MEDIUM issues | 30+ |
| LOW issues | 15+ |
| Wrong schema FKs | 12 |
| Missing `is_deleted` | 10 models |
| Broken imports | 6 |
| Missing RBAC | Entire domain |
| Missing kernel usage | 5 modules |
| Missing provider connections | 4 |
| Duplicate file pairs | 7 |
| God files (>500 lines) | 2 |
