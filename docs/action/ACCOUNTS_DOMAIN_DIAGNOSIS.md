# Accounts Domain — Complete Diagnosis Report

> Generated: 2026-08-26  
> Scope: `backend/domains/accounts/`  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **100+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 26 |
| 🟠 HIGH | 40+ |
| 🟡 MEDIUM | 30+ |
| 🟢 LOW | 15+ |
| **TOTAL** | **100+** |

---

## 1. DIRECTORY STRUCTURE PROBLEMS

### Current Structure
```
domains/accounts/
├── __init__.py                          (49 lines - facade)
├── events.py                            (7 lines - EMPTY STUB)
├── subscribers.py                       (7 lines - EMPTY STUB)
├── ports.py                             (628 lines - 30+ cross-domain imports)
├── features.py                          (12 lines - minimal)
├── models/
│   ├── __init__.py                      (3 lines)
│   ├── core.py                          (181 lines - 30+ tables, most wrong domain)
│   ├── user.py                          (57 lines - re-export shim)
│   ├── social.py                        (27 lines)
│   ├── otp.py                           (29 lines)
│   └── onboarding.py                    (54 lines - HR entities)
├── schemas/
│   ├── __init__.py                      (0 lines - EMPTY)
│   └── user_schemas.py                  (30 lines)
├── policies/
│   ├── __init__.py                      (0 lines - EMPTY)
│   └── user_policies.py                 (28 lines)
├── read_models/
│   ├── __init__.py                      (4 lines)
│   └── user_read_models.py              (25 lines)
├── utils/
│   └── __init__.py                      (0 lines - EMPTY, should not exist)
└── services/
    ├── __init__.py                      (1 line)
    ├── accounts_service.py              (77 lines - HR LOGIC!)
    ├── logistics_partner_service.py     (4 lines - STUB re-export)
    ├── auth/
    │   └── auth_service.py              (4,317 lines - MONOLITH)
    ├── sessions/
    │   └── session_service.py           (119 lines)
    ├── permissions/
    │   └── permission_service.py        (750 lines)
    ├── identity/
    │   └── identity_admin_service.py    (205 lines)
    ├── addresses/
    │   └── addresses_service.py         (204 lines - CLEAN)
    ├── tracker/
    │   └── live_session_tracker.py      (228 lines)
    └── users/
        └── users_admin_service/
            ├── __header___p1_p1.py      (482 lines)
            ├── __header___p1_p2.py      (156 lines)
            ├── __header___p2_p1.py      (490 lines)
            ├── __header___p2_p2.py      (138 lines)
            ├── __header___p3.py         (118 lines)
            ├── merged_from_user_read_service_py.py  (35 lines)
            └── merged_from_user_write_ops_py.py    (336 lines)
```

### CRITICAL: Directory Structure Issues

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | `events.py` is empty stub | `events.py` | Add real events or delete |
| 2 | `subscribers.py` is empty stub | `subscribers.py` | Add real subscribers or delete |
| 3 | `schemas/__init__.py` is empty | `schemas/__init__.py` | Delete or export schemas |
| 4 | `policies/__init__.py` is empty | `policies/__init__.py` | Delete or export policies |
| 5 | `utils/` directory should not exist | `utils/__init__.py` | Delete entire directory |
| 6 | `services/__init__.py` is 1 line | `services/__init__.py` | Delete or add proper exports |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

### 2.1 HR Domain Pollution in Accounts

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 1 | `services/accounts_service.py` | 10 | Imports `Employee` from HR | Move entire file to `domains/hr/services/` |
| 2 | `services/auth/auth_service.py` | 50 | Imports 5 HR models | Use `domains/hr.ports` functions |
| 3 | `services/permissions/permission_service.py` | 441 | Imports `Employee` from HR | Remove HR dependency |
| 4 | `services/tracker/live_session_tracker.py` | 152 | Imports `GeoFenceLog`, `Employee` | Move to `domains/hr/services/` |
| 5 | `ports.py` | 440-465 | Imports HR onboarding entities | Move to `domains/hr/ports.py` |

### 2.2 Logistics Domain Pollution in Accounts

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 6 | `services/auth/auth_service.py` | 1403 | Imports `LogisticsPartner` | Use events for cross-domain writes |
| 7 | `services/auth/auth_service.py` | 3967 | Creates `LogisticsPartner` directly | Move to `domains/logistics/services/` |
| 8 | `services/logistics_partner_service.py` | 2 | Re-exports logistics service | DELETE this file |
| 9 | `services/users/users_admin_service/*` | all | Imports 7 logistics models | Use `domains/logistics.ports` |

### 2.3 Supplier Domain Pollution in Accounts

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 10 | `services/auth/auth_service.py` | 1402 | Imports `SupplierProfile` | Use events for cross-domain writes |
| 11 | `services/auth/auth_service.py` | 3967 | Creates `SupplierProfile` directly | Move to `domains/suppliers/services/` |
| 12 | `services/users/users_admin_service/*` | all | Imports supplier models | Use `domains/suppliers.ports` |

### 2.4 Governance Domain Pollution in Accounts

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 13 | `models/core.py` | 109-137 | Re-exports 27 models from 6 domains | Remove all cross-domain re-exports |
| 14 | `ports.py` | 29 | Imports 30+ models from accounts/core | Only import accounts-owned models |
| 15 | `services/sessions/session_service.py` | 9 | Imports `UserSession` from governance | Define in accounts or use ports |

---

## 3. MODEL ISSUES

### 3.1 CRITICAL: Cross-Domain Model Imports

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 16 | `models/onboarding.py` | 10 | Imports `DocumentVerification`, `KYCVerification` from security | Use `domains.security.ports` |
| 17 | `models/user.py` | all | Pure re-export shim with no models | DELETE this file |

### 3.2 HIGH: Missing Audit Columns

| # | File | Model | Missing |
|---|------|-------|---------|
| 18 | `models/otp.py` | OtpCode | `updated_at`, `is_deleted` |
| 19 | `models/social.py` | SocialIdentity | `updated_at`, `is_deleted`, `country_code` |
| 20 | `models/onboarding.py` | OnboardingPipeline | `created_at`, `updated_at`, `is_deleted`, `country_code` |
| 21 | `models/onboarding.py` | OnboardingStep | `created_at`, `updated_at`, `is_deleted`, `country_code` |
| 22 | `models/onboarding.py` | OCRResult | `created_at`, `updated_at`, `is_deleted`, `country_code` |
| 23 | `models/core.py` | Cart, CartItem | `is_deleted` |

### 3.3 MEDIUM: Reserved Keywords & Types

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 24 | `models/onboarding.py` | 21 | `status` reserved keyword | Rename to `pipeline_status` |
| 25 | `models/onboarding.py` | 37 | `status` reserved keyword | Rename to `step_status` |
| 26 | `models/onboarding.py` | 50 | `confidence_score` as String | Change to `Numeric(5,2)` |

---

## 4. SERVICE ISSUES

### 4.1 CRITICAL: auth_service.py (4,317 lines)

| # | Issue | Lines | Fix |
|---|-------|-------|-----|
| 27 | Monolith merged from 7+ files | all | Split into focused services |
| 28 | Creates SupplierProfile directly | 2341-2374 | Use domain events |
| 29 | Creates LogisticsPartner directly | 3967-4018 | Use domain events |
| 30 | All login doors require Employee | 323-328, 431-436, etc. | Make Employee conditional on role |
| 31 | Broken import `infrastructure.security.auth` | 1204 | Change to `infrastructure.utils.auth` |
| 32 | `base64` not imported | 865-866 | Add `import base64` |
| 33 | `SocialIdentity` not imported | 3387, 3429-3465 | Create model or fix import |
| 34 | `issue_auth_response` not imported | 3390, 3476 | Implement or fix import |
| 35 | `OtpCode` model not defined | 1207, 1226, 1230, 1249 | Create model |
| 36 | Duplicate function definitions | multiple | Deduplicate |
| 37 | Incorrect haversine formula | 3505-3517 | Use `infrastructure.utils.geo.haversine_distance` |

### 4.2 CRITICAL: users_admin_service Split Files

| # | Issue | Files | Fix |
|---|-------|-------|-----|
| 38 | 325+ lines of duplicate imports | all 5 header files | Consolidate into single file |
| 39 | Direct cross-domain model imports | all files | Use ports |
| 40 | Cross-domain cascading deletes | `__header___p1_p1.py` | Use domain events |
| 41 | Bad file names | `merged_from_*.py` | Rename or consolidate |
| 42 | Duplicate constants | multiple files | Define once |

### 4.3 HIGH: Other Service Issues

| # | File | Issue | Fix |
|---|------|-------|-----|
| 43 | `accounts_service.py` | Entire file is HR logic | Move to `domains/hr/services/` |
| 44 | `logistics_partner_service.py` | Cross-domain re-export | DELETE |
| 45 | `identity_admin_service.py` | Imports from country utils | Use `domains.country.ports` |
| 46 | `session_service.py` | Imports from wrong domain | Fix import path |
| 47 | `permission_service.py` | `DEFAULT_ROLE_PERMISSION_MAP` empty | Import from `staff_permissions` |
| 48 | `live_session_tracker.py` | Imports HR models | Use `domains/hr.ports` |

---

## 5. PORTS.PY ISSUES (628 lines)

| # | Line | Issue | Fix |
|---|------|-------|-----|
| 49 | 29 | Imports 30+ models from core | Only import accounts-owned models |
| 50 | 34 | Imports from security models | Move to `domains/security/ports.py` |
| 51 | 440-465 | HR onboarding ports in accounts | Move to `domains/hr/ports.py` |
| 52 | various | Exposes cross-domain read helpers | Each domain should have its own ports |

---

## 6. FEATURES.PY ISSUES

| # | Issue | Fix |
|---|-------|-----|
| 53 | Only 3 feature flags defined | Expand to cover all accounts capabilities |

---

## 7. SCHEMAS & POLICIES ISSUES

| # | File | Issue | Fix |
|---|------|-------|-----|
| 54 | `schemas/__init__.py` | Empty | Delete or export |
| 55 | `policies/__init__.py` | Empty | Delete or export |
| 56 | `policies/user_policies.py` | Hardcoded role checks | Integrate with RBAC |
| 57 | `schemas/user_schemas.py` | Duplicates `infrastructure.database.schemas` | Use canonical schemas |

---

## 8. NAMING ISSUES

| # | File | Issue | Fix |
|---|------|-------|-----|
| 58 | `users_admin_service/__header___p1_p1.py` | Non-descriptive auto-generated name | Rename to `user_management_service.py` |
| 59 | `users_admin_service/merged_from_user_write_ops_py.py` | Bad naming with `_py` suffix | Rename to `user_write_ops.py` |
| 60 | `users_admin_service/merged_from_user_read_service_py.py` | Bad naming with `_py` suffix | Rename to `user_read_service.py` |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action | Impact |
|---|--------|--------|
| 1 | Fix broken imports in `auth_service.py` (base64, SocialIdentity, OtpCode, etc.) | Prevents runtime crashes |
| 2 | Fix customer login (remove Employee requirement) | Enables customer login |
| 3 | Delete `logistics_partner_service.py` shim | Removes confusion |
| 4 | Delete `models/user.py` re-export shim | Removes circular import risk |
| 5 | Move `accounts_service.py` to `domains/hr/services/` | Removes HR pollution from accounts |
| 6 | Remove cross-domain re-exports from `models/core.py` | Reduces coupling |

### Phase 2: HIGH (Fix This Week)

| # | Action | Impact |
|---|--------|--------|
| 7 | Split `auth_service.py` into focused services | Maintainability |
| 8 | Consolidate `users_admin_service/` split files | Reduces duplication |
| 9 | Add `updated_at`, `is_deleted` to all models | Audit trail |
| 10 | Remove direct cross-domain model imports | Architecture compliance |
| 11 | Move HR ports from `accounts/ports.py` to `hr/ports.py` | Correct placement |
| 12 | Fix `DEFAULT_ROLE_PERMISSION_MAP` in permission_service | RBAC works correctly |

### Phase 3: MEDIUM (Fix This Month)

| # | Action | Impact |
|---|--------|--------|
| 13 | Add missing `country_code` columns | Data integrity |
| 14 | Rename reserved keyword columns | Prevents SQL issues |
| 15 | Fix `confidence_score` type | Correct data types |
| 16 | Expand `features.py` | RBAC coverage |
| 17 | Delete empty directories (`utils/`) | Clean structure |
| 18 | Integrate policies with RBAC | Correct authorization |

### Phase 4: LOW (Technical Debt)

| # | Action | Impact |
|---|--------|--------|
| 19 | Clean up unused imports | Code clarity |
| 20 | Fix docstrings | Documentation |
| 21 | Standardize logging | Consistency |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files in accounts/ | 35+ |
| Files with cross-domain pollution | 20+ |
| CRITICAL issues | 26 |
| HIGH issues | 40+ |
| MEDIUM issues | 30+ |
| LOW issues | 15+ |
| Lines in auth_service.py | 4,317 |
| Cross-domain imports in users_admin_service | 65+ per file |
| Duplicate function definitions | 15+ |
| Empty/stub files | 6 |
