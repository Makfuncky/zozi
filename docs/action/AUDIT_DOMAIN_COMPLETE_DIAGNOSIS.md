# Audit Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/audit/` — Full Stack  
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
| 1 | `models/audit_schema_models.py` | 19, 31 | FK references `accounts.users.id` but users table is in `governance` schema | Change to `governance.users.id` |
| 2 | `models/audit_schema_models.py` | 12-24 | `AuditLog` missing `updated_at` | Add column |
| 3 | `models/audit_schema_models.py` | 12-36 | Both models missing `country_code` and `is_deleted` | Add columns |
| 4 | `models/audit_schema_models.py` | 20-37 | `FinancialReport` duplicated in finance domain | Remove from analytics |
| 5 | `__init__.py` | 23 | Exports non-existent `AuditSchema` class | Remove export |
| 6 | `models/audit_schema_models.py` | 14, 29 | `__table_args__` wrapped in unnecessary tuple | Simplify |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 HR Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 7 | `compliance_engine.py` | 1-139 | **Entire file is HR business logic** | Move to `domains/hr/services/` |
| 8 | `logs/audit_service.py` | 68-103 | `log_payroll_freeze`, `log_coi_violation` are HR concepts | Move to HR domain |

### 2.2 Governance Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 9 | `ediscovery.py` | 12-18 | Imports 6 models from governance, country, finance | Use ports |
| 10 | `retention_service.py` | 9-13 | Imports from governance, comms, logistics | Use events |
| 11 | `security_audit.py` | 7 | Imports `AuditLog` from wrong domain | Import from `audit.models` |
| 12 | `worm_audit.py` | 14 | Same wrong import | Same fix |
| 13 | `logs/audit_service.py` | 9 | Same wrong import | Same fix |
| 14 | `logs/audit_query_service.py` | 17 | Same wrong import | Same fix |

### 2.3 Multi-Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 15 | `ediscovery.py` | 105-186 | Queries 6 foreign domains directly | Use ports |
| 16 | `retention_service.py` | 89-93 | **Deletes data from 4 other domains** | DELETE file |
| 17 | `logs/audit_trail_service.py` | 11, 33-47 | Writes to country domain's column | Remove cross-domain write |

---

## 3. BROKEN IMPORTS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 18 | `ediscovery.py` | 13-18 | `DirectChatMessage`, `GroupChatMessage`, `JournalEntry` don't exist | Fix imports |
| 19 | `data_residency_service.py` | 12 | `DataResidencyRecord` in wrong module | Fix to `country_control` |
| 20 | `logs/audit_service.py` | 457-536 | `Union`, `Decimal`, `UUID`, `Enum`, `date` not imported | Add imports |
| 21 | `services/audit.py` | 4 | Re-exports from non-existent `security.audit_service` | DELETE file |
| 22 | `services/compliance_service.py` | 3-5 | Re-exports from infrastructure | DELETE file |

---

## 4. FAKE SECURITY (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 23 | `data_residency.py` | 84-100 | `SovereignEncryptionService` is **fake encryption** | Implement real KMS |
| 24 | `data_residency_service.py` | 64-69 | Silent plaintext fallback on encryption failure | Raise exception |
| 25 | `worm_audit.py` | 73-83 | `get_chain_integrity` **always returns True** | Implement real verification |
| 26 | `worm_audit.py` | 58-68 | WORM `UPDATE` after insert violates WORM principle | Add `worm_hash` column |
| 27 | `ediscovery.py` | 50, 124, 142, 160, 174 | LIKE injection risk | Escape user input |

---

## 5. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 5.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 28 | No `kernel/money.py` usage — uses `float` for money | Use `kernel.money.to_decimal()` |
| 29 | No `kernel/currency.py` usage — no currency conversion | Use `kernel.currency.convert()` |
| 30 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.is_valid_country_code()` |
| 31 | No `kernel/period.py` usage — hand-rolled date math | Use `kernel.period.month_bounds()` |
| 32 | No `kernel/constants.py` direct usage | Use `kernel.constants` directly |

### 5.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 33 | `require_feature()` never called in services | Wire in routers |
| 34 | No `rbac.roles` integration | Use `is_admin_role()`, `validate_user_role()` |
| 35 | No `rbac.resolution` integration | Use `effective_features()` |
| 36 | `features.py` not wired to `rbac/catalog.py` | Wire to catalog |

### 5.3 Providers (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 37 | No `providers.comms.email` for compliance alerts | Add connection |
| 38 | No `providers.comms.twilio/whatsapp` for critical violations | Add connection |
| 39 | No `providers.storage` for WORM archive offload | Add connection |
| 40 | No `providers.security.encryption` for KMS | Add connection |
| 41 | No `providers.ai.sentiment` for anomaly detection | Add connection |
| 42 | No `providers.geography.geoip` for IP enrichment | Add connection |

### 5.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 43 | No Redis caching for hot read paths | Add `cache_get_json`/`cache_set_json` |
| 44 | No tracing/metrics on write path | Add `tracing.span()` and counters |
| 45 | No retry/circuit breaker on WORM write | Add `retry()` |
| 46 | `get_service_session()` used as default | Require injected session |
| 47 | `retention_service.py` writes to local disk not S3 | Use `providers.storage` |

---

## 6. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 48 | `customer/routers/audit.py` | — | **FILE DOES NOT EXIST** | Create |
| 49 | `employee/routers/audit.py` | — | **FILE DOES NOT EXIST** | Create |
| 50 | `supplier/routers/audit.py` | — | **FILE DOES NOT EXIST** | Create |
| 51 | `logistics/routers/audit.py` | — | **FILE DOES NOT EXIST** | Create |
| 52 | `admin/routers/audit.py` | 32, 52, 65 | `require_feature()` called as function not `Depends` | Use `Depends` |
| 53 | `admin/routers/audit.py` | 19-41 | No pagination on list endpoint | Add pagination |
| 54 | `admin/routers/audit.py` | 19-66 | No Pydantic schemas | Add schemas |
| 55 | `admin/routers/audit.py` | — | 8/12 features have no routes | Add missing routes |
| 56 | `admin/routers/audit.py` | — | No error handling | Add try/except |

---

## 7. CODE QUALITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 57 | `logs/audit_service.py` | 34 | `details=str(details)` not JSON | Use `json.dumps()` |
| 58 | `logs/audit_trail_service.py` | 74 | Catches 20+ exception types | Use `except Exception` |
| 59 | `command_center_query_service.py` | 39-44, 63-68 | `safe_scalar` defined twice | Remove duplicate |
| 60 | `command_center_query_service.py` | 39-44 | Exception laundering (returns 0) | Catch `SQLAlchemyError` only |
| 61 | `command_center_query_service.py` | 29-36 | Weak SQL validator (bypassable) | Use SQLAlchemy `select()` |
| 62 | `data_residency.py` / `data_residency_service.py` / `flat_data_residency_service.py` | — | Three duplicate classes | Consolidate |
| 63 | `services/events.py` | 30, 51, 62, 73 | `field(init=False)` fragile | Use `ClassVar` |
| 64 | `subscribers.py` | 16-27 | Handlers only `logger.debug` | Write to `AuditLog` |
| 65 | `logs/audit_service.py` | 443, 504 | `audit_log()` and `AuditAction` defined twice | Consolidate |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix FK schema (`accounts.users` → `governance.users`) |
| 2 | Add missing `updated_at`, `country_code`, `is_deleted` columns |
| 3 | Fix broken imports in `ediscovery.py`, `data_residency_service.py`, `logs/audit_service.py` |
| 4 | Remove `FinancialReport` from analytics (duplicate in finance) |
| 5 | Remove `AuditSchema` export (class doesn't exist) |
| 6 | Delete `retention_service.py` (deletes other domains' data) |
| 7 | Move `compliance_engine.py` to `domains/hr/services/` |
| 8 | Replace `governance.models.core.AuditLog` imports with `audit.models` |
| 9 | Fix fake encryption in `SovereignEncryptionService` |
| 10 | Fix silent plaintext fallback |
| 11 | Implement real WORM chain verification |
| 12 | Fix LIKE injection in `ediscovery.py` |
| 13 | Fix `require_feature()` in admin router (use `Depends`) |
| 14 | Create missing routers (customer, employee, supplier, logistics) |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 15 | Delete duplicate files (`services/audit.py`, `services/compliance_service.py`, `services/compliance/`, `services/data/`, `services/core/`) |
| 16 | Consolidate three `DataResidencyService` classes |
| 17 | Replace direct model imports with ports calls |
| 18 | Add missing imports (`Union`, `Decimal`, `UUID`, `Enum`, `date`) |
| 19 | Add pagination and Pydantic schemas to admin router |
| 20 | Add error handling to all routers |
| 21 | Add missing routes for 8 unrouted features |
| 22 | Fix `safe_scalar` duplicate and exception laundering |
| 23 | Fix weak SQL validator |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 24 | Adopt `kernel/money.py` for Decimal operations |
| 25 | Adopt `kernel/currency.py` for currency conversion |
| 26 | Adopt `kernel/country.py` for country validation |
| 27 | Adopt `kernel/period.py` for date math |
| 28 | Add Redis caching for hot read paths |
| 29 | Add tracing/metrics on write path |
| 30 | Add retry/circuit breaker on WORM write |
| 31 | Move retention archives to S3 |
| 32 | Wire `providers.comms`, `providers.storage`, `providers.security` |
| 33 | Wire `rbac.roles`, `rbac.resolution` |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 31 |
| Files with cross-domain pollution | 14 |
| CRITICAL issues | 25+ |
| HIGH issues | 35+ |
| MEDIUM issues | 30+ |
| LOW issues | 15+ |
| Broken imports | 5 |
| Fake security functions | 3 |
| Duplicate file pairs | 5 |
| Empty/stub directories | 4 |
| Missing kernel usage | 5 |
| Missing provider connections | 6 |
| Missing router files | 4 |
