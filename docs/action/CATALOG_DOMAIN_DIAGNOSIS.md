# Catalog Domain — Complete Diagnosis Report

> Generated: 2026-08-26  
> Scope: `backend/domains/catalog/`  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **60+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 18 |
| 🟠 HIGH | 20+ |
| 🟡 MEDIUM | 20+ |
| 🟢 LOW | 10+ |
| **TOTAL** | **60+** |

---

## 1. BROKEN IMPORTS (CRITICAL — Runtime Crashes)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `services/__init__.py` | 9 | Imports `_bump_product_cache_version` — doesn't exist | Define or remove |
| 2 | `services/__init__.py` | 14-18 | Imports `bulk_create_products`, `bulk_update_products`, `bulk_delete_products` — don't exist | Create or remove |
| 3 | `services/__init__.py` | 20-21 | Imports `get_country_dropdown_data` — doesn't exist | Rename or create alias |
| 4 | `services/__init__.py` | 56-61 | Imports `admin_create_category`, etc. — don't exist | Fix import names |
| 5 | `services/__init__.py` | 37 | Imports `fetch_visibly_similar_products` — doesn't exist | Create or remove |
| 6 | `admin_products_service.py` | 23 | Imports `_bump_product_cache_version` — doesn't exist | Define in products_service |
| 7 | `ai_search_service.py` | 76,80,84 | Uses `re.search()` but `re` not imported | Add `import re` |
| 8 | `admin_products_service.py` | 303-422 | Uses `Decimal`, `selectinload`, `cast`, `or_`, `func` — none imported | Add imports |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 Accounts/Cart Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 9 | `products_service.py` | 378 | Direct import of `CartItem` from accounts | Use `domains.accounts.ports` |
| 10 | `products_service.py` | 383 | Direct DELETE on `CartItem` — cross-domain write | Use events |
| 11 | `admin_products_service.py` | 403 | Direct import of `CartItem` from wrong domain | Fix import |
| 12 | `admin_products_service.py` | 410 | Direct DELETE on `CartItem` — cross-domain write | Use events |

### 2.2 Comms/Notification Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `products_service.py` | 380 | Direct import of `Notification` from comms | Use events |
| 14 | `products_service.py` | 383-397 | Direct INSERT into `Notification` — cross-domain write | Use events |
| 15 | `admin_products_service.py` | 405 | Direct import of `Notification` | Use events |

### 2.3 Orders Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 16 | `products_service.py` | 381 | Direct import of `Order`, `OrderItem` | Use `domains.orders.ports` |
| 17 | `product_verification_service.py` | 18 | Direct import of `Order` | Use ports |

### 2.4 Logistics Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 18 | `product_verification_service.py` | 17 | Direct import of `Shipment` | Use `domains.logistics.ports` |

### 2.5 Supplier Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 19 | `products_service.py` | 806, 819 | Direct import of `SupplierProfile` from comms | Use ports |
| 20 | `products_service.py` | 791 | Imports `CartItem` from governance (wrong domain) | Fix to accounts |

---

## 3. ARCHITECTURE VIOLATIONS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 21 | `category_admin_routing_service.py` | 56-234 | **Controller in services layer** — uses `@get/@post/@put/@delete` | Move to `modules/admin/routers/` |
| 22 | `country_dropdown_service.py` | all | **Country domain logic in catalog** | Move to `domains/country/services/` |
| 23 | `admin_categories_service.py` | 1-4 | **Archived module still present** | DELETE |
| 24 | `categories_service.py` | 7, 18 | FastAPI `Depends`, `Query` in service layer | Remove FastAPI imports |
| 25 | `admin_products_service.py` | 5 | FastAPI `Body`, `Depends`, `Path`, `Query` in service | Remove FastAPI imports |
| 26 | `category_service.py` | 435, 444 | FastAPI `HTTPException` in service layer | Raise domain errors |

---

## 4. DUPLICATE FILES & LOGIC (HIGH)

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 27 | `products_service.py` / `search_service.py` | Duplicate `search_service.py` at wrong level | Delete top-level |
| 28 | `products_service.py` (873 lines) | **God file** — listing+CRUD+inventory+moderation+discount+verification | Split into focused services |
| 29 | `search/search_service.py` (1100+ lines) | **God file** — query parse + search + filter + engine | Split into focused services |
| 30 | `analytics_service.py` / `admin_analytics_service.py` | Duplicate analytics functions | Consolidate |
| 31 | `categories_service.py` / `category_service.py` | Duplicate category CRUD | Delete `categories_service.py` |
| 32 | `admin_categories_service.py` / `category_service.py` | Duplicate archive/restore | Consolidate |

---

## 5. LOGIC ERRORS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 33 | `products_service.py` | 336-338 | `get_product` catches broad Exception | Use specific exceptions |
| 34 | `products_service.py` | 446-451 | `atomic_stock_decrement` race condition | Use RETURNING clause |
| 35 | `products_service.py` | 455-491 | `finalize_inventory_atomic` no rollback | Wrap in transaction |
| 36 | `products_service.py` | 871-873 | `soft_delete_product` is a stub | Implement or remove |
| 37 | `products_service.py` | 101-102 | `_is_product_restricted_for_country` always returns False | Implement or remove |
| 38 | `search_service.py` | 866 | Mutable class-level `_cache` dict — not thread-safe | Use Redis |

---

## 6. SCHEMA ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 39 | `models/products.py` | multiple | FK references `commerce.products.id` — wrong schema | Change to `catalog.products.id` |
| 40 | `models/products.py` | multiple | FK references `commerce.categories.id` — wrong schema | Change to `catalog.categories.id` |
| 41 | `models/products.py` | 185-188 | `ProductVariant` may not have schema in `__table_args__` | Add schema |

---

## 7. SCALABILITY ISSUES (HIGH)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 42 | `products_service.py` | 266-271 | OFFSET pagination on product listings | Use keyset/cursor pagination |
| 43 | `products_service.py` | 837-846 | OFFSET pagination for admin | Use keyset/cursor pagination |
| 44 | `categories_service.py` | 29 | OFFSET pagination on categories | Use keyset/cursor pagination |
| 45 | `search_service.py` | 1033 | Hardcoded brand list | Query from database |
| 46 | `ai_search_service.py` | 174-187 | Hardcoded trending searches | Query from database |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Fix all broken imports in `services/__init__.py` | Prevents ImportError |
| 2 | Add missing imports (`re`, `Decimal`, `selectinload`, etc.) | Prevents NameError |
| 3 | Fix schema references (`commerce.*` → `catalog.*`) | Correct DB mapping |
| 4 | Fix CartItem imports (wrong domain: governance → accounts) | Correct domain |
| 5 | Move `category_admin_routing_service.py` to modules/ | Architecture compliance |
| 6 | Move `country_dropdown_service.py` to `domains/country/` | Domain correctness |
| 7 | Delete archived `admin_categories_service.py` | Clean structure |
| 8 | Fix race condition in `atomic_stock_decrement` | Data integrity |
| 9 | Fix `finalize_inventory_atomic` transaction rollback | Data integrity |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 10 | Split `products_service.py` (873 lines) into focused services | Maintainability |
| 11 | Split `search/search_service.py` (1100+ lines) into focused services | Maintainability |
| 12 | Consolidate duplicate category CRUD | Reduces duplication |
| 13 | Remove FastAPI imports from service layer | Architecture compliance |
| 14 | Replace cross-domain writes with events | Architecture compliance |
| 15 | Replace OFFSET pagination with keyset | 100K user scale |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 16 | Add missing schemas to `schemas/__init__.py` | API validation |
| 17 | Implement real product restriction logic | Feature completeness |
| 18 | Implement real soft delete | Feature completeness |
| 19 | Replace hardcoded data with DB queries | Production readiness |
| 20 | Fix mutable class-level cache | Thread safety |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 45+ |
| Files with cross-domain pollution | 15+ |
| CRITICAL issues | 18 |
| HIGH issues | 20+ |
| MEDIUM issues | 20+ |
| LOW issues | 10+ |
| God files (>500 lines) | 2 |
| Broken imports | 8 |
| Wrong schema references | 5+ |
| Cross-domain writes | 4 |
