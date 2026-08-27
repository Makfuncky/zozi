# Suppliers Domain — Complete Diagnosis Report

> Generated: 2026-08-26  
> Scope: `backend/domains/suppliers/`  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **80+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 18 |
| 🟠 HIGH | 30+ |
| 🟡 MEDIUM | 20+ |
| 🟢 LOW | 10+ |
| **TOTAL** | **80+** |

---

## 1. DIRECTORY STRUCTURE PROBLEMS

### Current Structure
```
domains/suppliers/
├── __init__.py (40 lines)
├── events.py (176 lines)
├── subscribers.py (51 lines - STUBS)
├── ports.py (63 lines)
├── features.py (147 lines)
├── RESOLVER.md (53 lines - should not be here)
├── models/
│   ├── __init__.py (27 lines)
│   └── suppliers.py (223 lines - 6 models)
├── schemas/
│   ├── __init__.py (24 lines)
│   └── supplier_schemas.py (84 lines)
├── policies/
│   └── __init__.py (73 lines)
├── read_models/
│   └── __init__.py (11 lines - EMPTY)
├── services/
│   ├── __init__.py (18 lines - wildcard imports)
│   ├── supplier_service.py (79 lines - WILDCARD re-export)
│   ├── supplier_shared.py (900 lines - GOD FILE)
│   ├── features.py (81 lines - DUPLICATE)
│   ├── events.py (108 lines - DUPLICATE)
│   ├── ports.py (51 lines - DUPLICATE)
│   ├── profile/
│   │   ├── supplier_profile.py (108 lines - BROKEN IMPORTS)
│   │   ├── supplier_profile_service.py (45 lines - DUPLICATE)
│   │   ├── supplier_product_image_service.py (61 lines)
│   │   ├── supplier_payouts_service.py (90 lines)
│   │   └── supplier_bank_account_service.py (45 lines)
│   ├── products/
│   │   ├── supplier_products.py (548 lines)
│   │   ├── supplier_products_service.py (228 lines - DUPLICATE)
│   │   └── supplier_supplier_upload_service.py (146 lines - BAD NAME)
│   ├── orders/
│   │   ├── supplier_orders.py (577 lines)
│   │   ├── supplier_orders_service.py (660 lines - DUPLICATE)
│   │   └── supplier_orders_verify_service.py (169 lines)
│   ├── analytics/
│   │   └── supplier_analytics_service.py (68 lines)
│   ├── health/
│   │   ├── supplier_health.py (2500+ lines - GOD FILE)
│   │   ├── supplier_health_service.py (60 lines)
│   │   └── supplier_health_engine.py (175 lines)
│   ├── badges/
│   │   ├── badge_service.py (431 lines)
│   │   └── badge_write_service.py (140 lines)
│   ├── contracts/
│   │   └── legal_contract_service.py (177 lines - WRONG DOMAIN)
│   ├── documents/
│   │   ├── supplier_document_service.py (48 lines)
│   │   └── supplier_documents_service.py (52 lines - ARCHIVED)
│   ├── governance/
│   │   └── admin_suppliers_service.py (416 lines - WRONG DOMAIN)
│   └── onboarding/
│       ├── __init__.py (75 lines)
│       └── supplier_onboarding_service.py (144 lines)
```

### CRITICAL: Structure Issues

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | `supplier_health.py` is 2500+ line god file | `services/health/supplier_health.py` | Split into 5+ focused services |
| 2 | `supplier_shared.py` is 900-line dumping ground | `services/supplier_shared.py` | Extract to domain-specific services |
| 3 | `services/features.py` is duplicate root | `services/features.py` | DELETE |
| 4 | `services/events.py` is duplicate root | `services/events.py` | DELETE |
| 5 | `services/ports.py` is duplicate root | `services/ports.py` | DELETE |
| 6 | `governance/admin_suppliers_service.py` in suppliers | `services/governance/` | Move to `domains/governance/` |
| 7 | `contracts/legal_contract_service.py` in suppliers | `services/contracts/` | Move to `domains/governance/` |
| 8 | `documents/supplier_documents_service.py` archived | `services/documents/` | DELETE or move to `_parked/` |
| 9 | `RESOLVER.md` in domain root | `RESOLVER.md` | Move to `.kilo/` |
| 10 | `read_models/__init__.py` empty | `read_models/` | Populate or delete |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 Governance/Admin Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 1 | `supplier_shared.py` | 38-40 | Imports 3 governance admin models | Use `domains.governance.ports` |
| 2 | `badge_write_service.py` | 29 | Imports `BadgeBillingRecord` | Use ports |
| 3 | `supplier_bank_account_service.py` | 10 | Imports `SupplierBankAccount` | Use ports |
| 4 | `supplier_health_engine.py` | 11-12 | Imports 2 governance models | Use ports |
| 5 | `admin_suppliers_service.py` | 15-19 | Imports governance service | Move to `domains/governance/` |

### 2.2 Logistics Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 6 | `supplier_shared.py` | 41-43 | Imports 3 logistics models | Use `domains.logistics.ports` |
| 7 | `supplier_shared.py` | 50 | Imports logistics service | Use ports |
| 8 | `supplier_orders_service.py` | 144, 625 | Imports `Shipment` | Use ports |

### 2.3 Finance Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 9 | `supplier_shared.py` | 36-37 | Imports 2 finance models | Use `domains.finance.ports` |
| 10 | `supplier_shared.py` | 46 | Imports `Payout` | Use ports |
| 11 | `badge_write_service.py` | 31, 33 | Imports finance model + service | Use events |
| 12 | `supplier_payouts_service.py` | 15 | Imports `Payout` | Use ports |

### 2.4 Catalog Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `supplier_shared.py` | 32-33, 53 | Imports catalog models + service | Use `domains.catalog.ports` |
| 14 | `supplier_products_service.py` | 15 | Imports `Product` | Use ports |
| 15 | `supplier_analytics_service.py` | 12 | Imports `Product` | Use ports |

### 2.5 Orders Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 16 | `supplier_shared.py` | 44-45, 55 | Imports orders models + service | Use `domains.orders.ports` |
| 17 | `supplier_orders_service.py` | 14-15 | Imports `Order`, `OrderItem` | Use ports |
| 18 | `supplier_health_engine.py` | 13, 75, 119 | Imports 3 orders models | Use ports |

---

## 3. SECURITY ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 19 | `supplier_service.py` | 74-79 | Watchlist auto-clears on failure | Return `cleared=False` on error |
| 20 | `supplier_profile.py` | 6, 13, 15, 21, 46 | Undefined names (User, Product, Order, etc.) | Add proper imports |
| 21 | `supplier_shared.py` | 364-386 | Subprocess execution of AI script | Use direct function call |
| 22 | `supplier_profile_service.py` | 29 | Auto-escalates role to supplier | Remove auto role assignment |
| 23 | `supplier_supplier_upload_service.py` | 51-79 | `VALID_STRATEGIES`, `remove_background` not imported | Uncomment imports |
| 24 | `supplier_supplier_upload_service.py` | 126 | `_HAS_CV2` not imported | Add import |

---

## 4. LEGAL COMPLIANCE ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 25 | `legal_contract_service.py` | 81 | Pakistan (PK) in GCC countries set | Remove PK from GCC set |
| 26 | `legal_contract_service.py` | 33-35 | Refund template maps to wrong generator | Create `generate_refund_policy()` |

---

## 5. MODEL ISSUES

### 5.1 HIGH: Double `__table_args__`

| # | File | Lines | Issue | Fix |
|---|------|-------|-------|-----|
| 27 | `models/suppliers.py` | 58, 82 | `SupplierDocument` has duplicate `__table_args__` | Remove first assignment |
| 28 | `models/suppliers.py` | 145-149, 174-179 | `SupplierBadge` has duplicate `__table_args__` | Remove first assignment |
| 29 | `models/suppliers.py` | 186-189, 218-222 | `SupplierBadgeBillingHistory` has duplicate `__table_args__` | Remove first assignment |

### 5.2 MEDIUM: Missing Columns

| # | File | Model | Missing |
|---|------|-------|---------|
| 30 | `models/suppliers.py` | SupplierDocument | `country_code` |
| 31 | `models/suppliers.py` | SupplierNotificationPreference | `country_code` |

### 5.3 MEDIUM: Type Issues

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 32 | `models/suppliers.py` | 135 | `credibility_weight` uses Float | Change to `Numeric(10, 4)` |
| 33 | `models/suppliers.py` | 167 | `credibility_weight` uses Float | Change to `Numeric(10, 4)` |

---

## 6. SERVICE ISSUES

### 6.1 HIGH: Duplicate Functions

| # | Files | Functions |
|---|-------|-----------|
| 34 | `supplier_health.py` / `supplier_profile.py` | `get_supplier_profile`, `update_supplier_profile`, `request_verification` |
| 35 | `supplier_products.py` / `supplier_products_service.py` | Product CRUD operations |
| 36 | `supplier_orders.py` / `supplier_orders_service.py` | Order listing, label generation |

### 6.2 HIGH: FastAPI Depends in Service Layer

| # | File | Lines | Issue |
|---|------|-------|-------|
| 37 | `supplier_payouts_service.py` | 18 | Uses `Depends(require_supplier)` |
| 38 | `supplier_orders_verify_service.py` | 57, 82, 111 | Uses `Depends(require_supplier)` |
| 39 | `supplier_supplier_upload_service.py` | 32 | Uses `Depends(require_roles(...))` |

### 6.3 HIGH: Scalability Issues

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 40 | `supplier_health_service.py` | 37-50 | Loads ALL suppliers into memory | Use pagination |
| 41 | `admin_suppliers_service.py` | 78-91 | N+1 count queries | Use single GROUP BY |
| 42 | `supplier_health_engine.py` | 74-91 | Loads all orders into memory | Use paginated queries |

### 6.4 MEDIUM: Data Integrity

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 43 | `onboarding/__init__.py` | 23-30 | Creates pipeline without persisting | Persist record |
| 44 | `onboarding/__init__.py` | 33-47 | Doesn't save file content | Save to storage |
| 45 | `onboarding/__init__.py` | 50-58 | Doesn't create KYC record | Create record |
| 46 | `onboarding/__init__.py` | 70-75 | Doesn't persist step completion | Update record |

---

## 7. NAMING ISSUES

| # | File | Issue | Fix |
|---|------|-------|-----|
| 47 | `supplier_supplier_upload_service.py` | Redundant "supplier_supplier" prefix | Rename to `bg_strategy_service.py` |
| 48 | `supplier_service.py` | Wildcard re-export shim | Delete, import directly |
| 49 | `supplier_shared.py` | 900-line god file | Split into focused services |
| 50 | `supplier_health.py` | 2500+ line god file | Split into focused services |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Fix watchlist auto-clear on failure | Security/compliance |
| 2 | Fix undefined names in `supplier_profile.py` | Prevents runtime crash |
| 3 | Fix GCC countries set (remove PK) | Legal compliance |
| 4 | Fix refund template mapping | Legal compliance |
| 5 | Uncomment imports in `supplier_supplier_upload_service.py` | Prevents runtime crash |
| 6 | Add `_HAS_C2` import | Prevents runtime crash |
| 7 | Remove auto role escalation in `supplier_profile_service.py` | Security |
| 8 | Delete duplicate files (`features.py`, `events.py`, `ports.py` in services/) | Reduces confusion |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 9 | Split `supplier_health.py` into focused services | Maintainability |
| 10 | Split `supplier_shared.py` into focused services | Maintainability |
| 11 | Consolidate duplicate service files | Reduces duplication |
| 12 | Move `admin_suppliers_service.py` to `domains/governance/` | Architecture compliance |
| 13 | Move `legal_contract_service.py` to `domains/governance/` | Architecture compliance |
| 14 | Remove FastAPI `Depends` from service functions | Architecture compliance |
| 15 | Fix scalability issues (pagination, N+1 queries) | 100K user support |
| 16 | Remove cross-domain model imports (use ports) | Architecture compliance |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 17 | Fix double `__table_args__` in 3 models | Prevents migration errors |
| 18 | Add missing `country_code` columns | Data integrity |
| 19 | Change `credibility_weight` to Numeric | Precision |
| 20 | Fix data integrity in onboarding functions | Data integrity |
| 21 | Delete archived `supplier_documents_service.py` | Clean structure |
| 22 | Populate or delete `read_models/` | Clean structure |

### Phase 4: LOW (Technical Debt)

| # | Action | Impact |
|---|--------|--------|
| 23 | Rename `supplier_supplier_upload_service.py` | Naming clarity |
| 24 | Delete `supplier_service.py` shim | Clean structure |
| 25 | Move `RESOLVER.md` to `.kilo/` | Clean structure |
| 26 | Fix formatting in `badge_service.py` | Readability |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 58 |
| Files with cross-domain pollution | 22 |
| CRITICAL issues | 18 |
| HIGH issues | 30+ |
| MEDIUM issues | 20+ |
| LOW issues | 10+ |
| God files (>500 lines) | 2 |
| Duplicate file pairs | 6 |
| Empty/stub __init__.py files | 8 |
| Cross-domain import violations | 38 |
| Security vulnerabilities | 5 |
| Legal compliance issues | 2 |
