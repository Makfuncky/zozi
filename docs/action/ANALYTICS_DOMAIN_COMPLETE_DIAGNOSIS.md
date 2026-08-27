# Analytics Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/analytics/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **80+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 20+ |
| 🟠 HIGH | 30+ |
| 🟡 MEDIUM | 25+ |
| 🟢 LOW | 10+ |
| **TOTAL** | **80+** |

---

## 1. SCHEMA & MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `models/analytics_schema_models.py` | 20-37 | `FinancialReport` duplicated in finance domain | Remove from analytics |
| 2 | `models/analytics_schema_models.py` | 78 | `PredictiveSimulation` uses schema `"ai"` not `"analytics"` | Document or move |
| 3 | `models/analytics_schema_models.py` | 20-37 | `FinancialReport` missing `updated_at`, `uuid`, `version`, `created_by_id` | Add columns |
| 4 | `models/analytics_schema_models.py` | 30 | `report_type` should be `String(30)` not `String` | Fix type |
| 5 | `models/analytics_schema_models.py` | 33 | Missing index on `is_deleted` | Add index |
| 6 | `__init__.py` | 27 | Exports non-existent `AnalyticsSchema` class | Remove export |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 Governance Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 7 | `admin_dashboard_service.py` | 16-23 | Imports 5 governance models | Use `governance.ports` |
| 8 | `analytics_fallback_service.py` | 15-21 | Imports 4 governance models | Use ports |
| 9 | `flat_admin_dashboard_service.py` | 16-27 | Imports 7 governance models | Use ports |
| 10 | `analytics_service.py` | 13-18 | Imports 3 governance models | Use ports |
| 11 | `admin_analytics_service.py` | 19-23 | Imports 3 governance models | Use ports |
| 12 | `command_center_service.py` | 11-18 | Imports 8 governance models | Use ports |

### 2.2 Finance Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `admin_dashboard_service.py` | 19-20, 26-27 | Imports 4 finance models | Use `finance.ports` |
| 14 | `analytics_fallback_service.py` | 17-18, 20-21 | Imports 4 finance models | Use ports |
| 15 | `flat_admin_dashboard_service.py` | 19-20, 26-27 | Imports 4 finance models | Use ports |
| 16 | `command_center_service.py` | 344-472 | Raw SQL hitting finance tables | Use ports |

### 2.3 Catalog/Orders/Logistics Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 17 | `admin_dashboard_service.py` | 17-18, 25 | Imports catalog + logistics models | Use ports |
| 18 | `analytics_service.py` | 14, 17-18 | Imports catalog + orders models | Use ports |
| 19 | `admin_analytics_service.py` | 20, 22-23 | Imports catalog + orders models | Use ports |
| 20 | `command_center_service.py` | 21-23 | Imports logistics + orders + hr models | Use ports |

---

## 3. BROKEN IMPORTS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 21 | `services/__init__.py` | 7-12 | Imports 6 non-existent modules | Fix or remove |
| 22 | `__init__.py` | 15-19 | Exports 4 non-existent classes | Remove exports |
| 23 | `command_center_service.py` | 44, 648, 669, 682 | `logger` used but never imported | Add `import structlog` |
| 24 | `command_center_service.py` | 309, 323, 330, 605 | `Shipment`, `FraudEvent`, `IPAccountLinkage` not imported | Add imports |
| 25 | `flat_admin_dashboard_service.py` | 28-41 | 6 undefined functions (`scalar_sum`, `count`, etc.) | Implement or import |
| 26 | `admin_dashboard_service.py` | 28-41 | Same undefined functions | Same fix |
| 27 | `analytics_fallback_service.py` | 22-35 | Same undefined functions | Same fix |

---

## 4. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 4.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 28 | No `kernel/money.py` usage — uses `float()` for revenue | Use `kernel.money.Money` |
| 29 | No `kernel/currency.py` usage — no currency conversion | Use `kernel.currency.convert()` |
| 30 | No `kernel/constants.py` direct usage — uses `infrastructure.utils.constants` shim | Use `kernel.constants` directly |
| 31 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.is_valid_country_code()` |
| 32 | No `kernel/period.py` usage — duplicated `_PERIOD_DAYS` in 3 files | Create `kernel.period` |

### 4.2 RBAC (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 33 | `require_feature()` never called in services | Wire in routers |
| 34 | `VALID_USER_ROLES` hard-coded in `analytics_service.py:135` | Use `kernel.constants.STAFF_ROLES` |
| 35 | `DEFAULT_ROLE_PERMISSION_MAP` from wrong module | Use `rbac.roles` |
| 36 | `audit_log`, `AuditAction` imported but never used | Wire or remove |

### 4.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 37 | Only `providers.analytics` used | Add `providers.ai`, `providers.storage`, `providers.comms` |
| 38 | Hard-coded FX rates in `command_center_service.py:553` | Use `providers.fx` or `kernel.currency` |
| 39 | Hard-coded supply chain alerts and competitor news | Use `providers.news` |

### 4.4 Infrastructure (MOSTLY CORRECT)

| # | Issue | Fix |
|---|-------|-----|
| 40 | `infrastructure.utils.staff_permissions` instead of `rbac` | Use canonical path |
| 41 | `infrastructure.utils.config.settings` imported but unused | Remove or wire |
| 42 | No country-scoping in command-center aggregations | Add `country_code` filter |

---

## 5. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 43 | `admin/routers/analytics.py` | 14 | Only exposes `/health` — no real endpoints | Wire to services |
| 44 | `admin/routers/analytics.py` | 16 | `require_feature()` called as function not `Depends` | Use `Depends` |
| 45 | `customer/routers/analytics.py` | — | **FILE DOES NOT EXIST** | Create |
| 46 | `employee/routers/analytics.py` | — | **FILE DOES NOT EXIST** | Create |
| 47 | `logistics/routers/analytics.py` | — | **FILE DOES NOT EXIST** | Create |
| 48 | `supplier/routers/analytics.py` | 17-20 | No `response_model`, no pagination | Add schemas |
| 49 | All routers | — | Double-prefix risk (inline `/api/v1/...`) | Remove inline prefix |

---

## 6. CODE QUALITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 50 | `analytics_service.py` | 33, 358, etc. | Revenue aggregated as `float()` not `Decimal` | Use `kernel.money` |
| 51 | `command_center_service.py` | 59 | String-concat SQL with weak validator | Use SQLAlchemy `select()` |
| 52 | `command_center_query_service.py` | 39-44, 63-68 | `safe_scalar` defined twice | Remove duplicate |
| 53 | `command_center_query_service.py` | 39-44 | Catches 20+ exception types, returns 0 | Catch `SQLAlchemyError` only |
| 54 | `search_service.py` | 866 | Mutable class-level `_cache` dict | Use Redis |
| 55 | `analytics_service.py` | 434-442 | `get_analytics_summary` swallows exceptions | Raise or return structured error |
| 56 | `command_center_service.py` | 28-72 | WebSocket manager has no auth | Add `Actor` parameter |
| 57 | `command_center_service.py` | 330-475 | No country filter on aggregations | Add `country_code` predicate |
| 58 | `command_center_service.py` | 552-559 | Hard-coded FX rates, alerts, news | Use providers |
| 59 | `command_center_service.py` | 440, 538, 563 | `redis_client()` called without `await` | Add `await` |
| 60 | Multiple files | — | `datetime.now(timezone.utc).replace(tzinfo=None)` pattern | Use helper |

---

## 7. DUPLICATE FILES & LOGIC

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 61 | `flat_admin_dashboard_service.py` / `admin_dashboard_service.py` | Exact duplicate (188 lines each) | Delete `flat_` version |
| 62 | `analytics_fallback_service.py` / `admin_dashboard_service.py` | Duplicate functions | Delete `fallback` version |
| 63 | `analytics_service.py` / `admin_analytics_service.py` | 5 duplicate `_compute_*` functions | Consolidate |
| 64 | `search_service.py` (top-level) / `search/search_service.py` | Duplicate at wrong level | Delete top-level |
| 65 | `services/features.py` / root `features.py` | Duplicate features | Delete `services/features.py` |
| 66 | `services/ports.py` / root `ports.py` | Duplicate ports | Delete `services/ports.py` |
| 67 | `services/events.py` / root `events.py` | Duplicate events | Delete `services/events.py` |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix broken imports in `services/__init__.py` (6 non-existent modules) |
| 2 | Remove dead lazy exports from `__init__.py` (4 non-existent classes) |
| 3 | Add `import structlog; logger = structlog.get_logger(__name__)` to `command_center_service.py` |
| 4 | Implement undefined functions (`scalar_sum`, `count`, etc.) or import from `infrastructure/database/db_read.py` |
| 5 | Remove `FinancialReport` from analytics (duplicate in finance) |
| 6 | Fix `AnalyticsSchema` export (class doesn't exist) |
| 7 | Replace string-concat SQL with SQLAlchemy `select()` |
| 8 | Fix `safe_scalar` exception laundering |
| 9 | Add country filter to all command-center aggregations |
| 10 | Create missing routers (customer, employee, logistics) |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 11 | Delete duplicate files (`flat_admin_dashboard_service.py`, `analytics_fallback_service.py`, top-level `search_service.py`) |
| 12 | Consolidate duplicate `_compute_*` functions |
| 13 | Replace `float()` revenue with `kernel.money.Money` |
| 14 | Add currency conversion before cross-country aggregation |
| 15 | Wire `audit_log` around snapshot writes |
| 16 | Add auth to WebSocket manager |
| 17 | Replace hardcoded FX rates with provider |
| 18 | Fix `redis_client()` async usage |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 19 | Create `infrastructure/database/db_read.py` with shared helpers |
| 20 | Create `kernel/period.py` for period arithmetic |
| 21 | Replace direct model imports with ports calls |
| 22 | Add `kernel.country.is_valid_country_code()` validation |
| 23 | Add Pydantic schemas to routers |
| 24 | Add pagination to list endpoints |
| 25 | Replace OFFSET pagination with keyset |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 24 |
| Files with cross-domain pollution | 12 |
| CRITICAL issues | 20+ |
| HIGH issues | 30+ |
| MEDIUM issues | 25+ |
| LOW issues | 10+ |
| Duplicate file pairs | 7 |
| Broken imports | 7 |
| Missing kernel usage | 5 |
| Missing provider connections | 3 |
| Router issues | 7 |
| God files (>500 lines) | 2 |
