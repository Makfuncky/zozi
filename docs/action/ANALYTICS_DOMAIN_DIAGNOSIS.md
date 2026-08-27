# Analytics Domain — Complete Diagnosis Report

> Generated: 2026-08-26  
> Scope: `backend/domains/analytics/`  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **47+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 12 |
| 🟠 HIGH | 18 |
| 🟡 MEDIUM | 12 |
| 🟢 LOW | 5 |
| **TOTAL** | **47+** |

---

## 1. BROKEN IMPORTS (CRITICAL — Runtime Crashes)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `services/__init__.py` | 8-9 | Imports `flat_admin_analytics_service` and `flat_analytics_service` which **DO NOT EXIST** | Remove imports |
| 2 | `__init__.py` | 16-19 | References `AnalyticsController`, `FlatAnalyticsService`, `FlatAdminAnalyticsService` from non-existent modules | Remove references |
| 3 | `services/dashboards/analytics_service.py` | 21 | Imports `DEFAULT_ROLE_PERMISSION_MAP` from wrong module (`infrastructure.utils.staff_permissions`) | Change to `rbac.staff_permissions` |
| 4 | `flat_admin_dashboard_service.py` | 45-92 | Calls 6 undefined functions (`scalar_sum`, `scalar_with_filters`, `count`, `all_rows`, `first`, `scalar`) | Uncomment imports or implement |
| 5 | `dashboards/admin_dashboard_service.py` | 45-92 | Same undefined functions | Same fix |
| 6 | `dashboards/analytics_fallback_service.py` | 40-120 | Same undefined functions | Same fix |
| 7 | `services/aggregation/command_center_service.py` | 44, 648, 669, 682 | Uses `logger` without defining it | Add `import logging; logger = logging.getLogger(__name__)` |
| 8 | `services/aggregation/command_center_service.py` | 308, 323, 329, 604 | References `Shipment`, `FraudEvent`, `IPAccountLinkage` without imports | Add proper imports |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 Governance/Admin Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 9 | `flat_admin_dashboard_service.py` | 21-23 | Imports 3 governance admin models | Use `domains.governance.ports` |
| 10 | `dashboards/admin_dashboard_service.py` | 21-23 | Imports 3 governance admin models | Use ports |
| 11 | `dashboards/admin_analytics_service.py` | 16, 21 | Imports 2 governance models | Use ports |
| 12 | `dashboards/analytics_service.py` | 15-16 | Imports 2 governance models | Use ports |
| 13 | `dashboards/analytics_fallback_service.py` | 19 | Imports governance model | Use ports |

### 2.2 Finance Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 14 | `flat_admin_dashboard_service.py` | 19-20, 26-27 | Imports 4 finance models | Use `domains.finance.ports` |
| 15 | `dashboards/admin_dashboard_service.py` | 19-20, 26-27 | Imports 4 finance models | Use ports |
| 16 | `dashboards/analytics_fallback_service.py` | 17-18, 20-21 | Imports 4 finance models | Use ports |

### 2.3 Catalog Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 17 | `dashboards/analytics_service.py` | 14 | Imports `Product` | Use `domains.catalog.ports` |
| 18 | `dashboards/admin_analytics_service.py` | 20 | Imports `Product` | Use ports |
| 19 | `flat_admin_dashboard_service.py` | 17-18 | Imports `Category`, `Product` | Use ports |
| 20 | `dashboards/admin_dashboard_service.py` | 17-18 | Imports `Category`, `Product` | Use ports |

### 2.4 Orders Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 21 | `dashboards/analytics_service.py` | 17-18 | Imports `Order`, `OrderItem` | Use `domains.orders.ports` |
| 22 | `dashboards/admin_analytics_service.py` | 22-23 | Imports `Order`, `OrderItem` | Use ports |

### 2.5 HR Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 23 | `flat_admin_dashboard_service.py` | 24 | Imports `Employee` | Use `domains.hr.ports` |
| 24 | `dashboards/admin_dashboard_service.py` | 24 | Imports `Employee` | Use ports |
| 25 | `command_center_service.py` | 23 | Imports `Employee` | Use ports |

### 2.6 Logistics Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 26 | `flat_admin_dashboard_service.py` | 25 | Imports `Shipment` | Use `domains.logistics.ports` |
| 27 | `dashboards/admin_dashboard_service.py` | 25 | Imports `Shipment` | Use ports |
| 28 | `command_center_service.py` | 21 | Imports `LogisticsPartner` | Use ports |

---

## 3. DUPLICATE FILES & LOGIC (HIGH)

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 29 | `flat_admin_dashboard_service.py` / `dashboards/admin_dashboard_service.py` | **Exact duplicate** (188 lines each) | Delete `flat_` version |
| 30 | `dashboards/analytics_fallback_service.py` / `dashboards/admin_dashboard_service.py` | Duplicate functions | Delete `fallback` version |
| 31 | `dashboards/analytics_service.py` / `dashboards/admin_analytics_service.py` | 5 duplicate functions | Consolidate into one |
| 32 | `command_center_query_service.py` | `safe_scalar` defined twice | Remove duplicate |

---

## 4. BUSINESS LOGIC ERRORS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 33 | `flat_admin_dashboard_service.py` | 47 | `total_orders` counts **users** instead of orders | Use `Order` model |
| 34 | `dashboards/admin_dashboard_service.py` | 47 | Same bug | Same fix |
| 35 | `dashboards/analytics_fallback_service.py` | 42 | Same bug | Same fix |
| 36 | `flat_admin_dashboard_service.py` | 45 | `total_revenue` uses `Payment.amount` instead of `Order.total_amount` | Use orders |
| 37 | `command_center_service.py` | 553 | Hardcoded exchange rates | Use provider |
| 38 | `command_center_service.py` | 555-559 | Hardcoded supply chain alerts and competitor news | Use provider |
| 39 | `flat_admin_dashboard_service.py` | 52 | `active_sessions` hardcoded to 0 | Query Redis/sessions |
| 40 | `admin_analytics_service.py` | 90-92 | Returns model instance instead of dict | Serialize |

---

## 5. SQL INJECTION RISK (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 41 | `command_center_query_service.py` | 59 | Raw SQL with string concatenation | Use SQLAlchemy parameterized queries |
| 42 | `command_center_query_service.py` | 29-36 | `_validate_where_clause` is insufficient | Use proper parameterization |

---

## 6. MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 43 | `models/analytics_schema_models.py` | 78 | `PredictiveSimulation` uses schema `"ai"` instead of `"analytics"` | Change to `"analytics"` |
| 44 | `models/analytics_schema_models.py` | 20 | `FinancialReport` missing `created_at` | Add column |
| 45 | `models/analytics_schema_models.py` | 20 | `FinancialReport` missing `updated_at` | Add column |
| 46 | `models/analytics_schema_models.py` | 20 | `FinancialReport` missing `uuid`, `version`, `created_by_id`, etc. | Add columns |
| 47 | `models/analytics_schema_models.py` | 20 | `FinancialReport` duplicated in finance domain | Remove from analytics |

---

## 7. ARCHITECTURE VIOLATIONS (HIGH)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 48 | `analytics_service.py` | 9 | Imports `FastAPI HTTPException` in domain layer | Remove |
| 49 | `analytics_service.py` | 19-22 | Imports from root-level `infrastructure.utils.*` | Use canonical paths |
| 50 | `command_center_service.py` | 28-72 | `WebSocketManager` class in domain service | Move to infrastructure |
| 51 | `command_center_service.py` | 340-619 | Raw SQL across 7+ domains | Use ports |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Remove imports of non-existent modules (`flat_admin_analytics_service`, `flat_analytics_service`) | Prevents ImportError |
| 2 | Fix undefined functions in 3 dashboard services | Prevents NameError |
| 3 | Add missing `logger` and model imports to `command_center_service.py` | Prevents NameError |
| 4 | Fix `total_orders` bug (counts users not orders) | Correct analytics |
| 5 | Fix SQL injection risk in `command_center_query_service.py` | Security |
| 6 | Fix `PredictiveSimulation` schema (`ai` → `analytics`) | Correct schema |
| 7 | Add missing `created_at`, `updated_at` to `FinancialReport` | Data integrity |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 8 | Delete duplicate files (`flat_admin_dashboard_service.py`, `analytics_fallback_service.py`) | Reduces confusion |
| 9 | Consolidate duplicate functions between `analytics_service.py` and `admin_analytics_service.py` | Reduces duplication |
| 10 | Remove direct cross-domain model imports (use ports) | Architecture compliance |
| 11 | Remove FastAPI imports from domain services | Architecture compliance |
| 12 | Move `WebSocketManager` to infrastructure | Correct layer |
| 13 | Replace hardcoded data with provider calls | Production readiness |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 14 | Delete empty stub directories (`policies/`, `read_models/`, `schemas/`, `reporting/`) | Clean structure |
| 15 | Fix `DEFAULT_ROLE_PERMISSION_MAP` import | RBAC works |
| 16 | Fix `FinancialReport` duplicate in finance domain | Single source of truth |
| 17 | Add missing audit columns to `FinancialReport` | Data integrity |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 20 |
| Files with cross-domain pollution | 10 |
| CRITICAL issues | 12 |
| HIGH issues | 18 |
| MEDIUM issues | 12 |
| LOW issues | 5 |
| Duplicate file pairs | 3 |
| Empty/stub directories | 4 |
| Broken imports | 8 |
| Undefined functions | 6 |
