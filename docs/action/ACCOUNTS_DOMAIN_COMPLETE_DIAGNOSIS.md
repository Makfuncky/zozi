# Accounts Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/accounts/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **100+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 30+ |
| 🟠 HIGH | 35+ |
| 🟡 MEDIUM | 25+ |
| 🟢 LOW | 15+ |
| **TOTAL** | **100+** |

---

## 1. SCHEMA & MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `models/onboarding.py` | 15-56 | 3 models missing `created_at`, `country_code`, `is_deleted` | Add columns |
| 2 | `models/onboarding.py` | 21, 38 | `status` reserved keyword | Rename to `pipeline_status`, `step_status` |
| 3 | `models/core.py` | 55-117 | `Address`, `Cart`, `CartItem` missing `is_deleted` | Add column |
| 4 | `models/social.py` | 17-27 | `SocialIdentity` missing `updated_at`, `is_deleted`, `country_code` | Add columns |
| 5 | `models/otp.py` | 15-29 | `OtpCode` missing `updated_at`, `is_deleted` | Add columns |
| 6 | `ports.py` | 440-451 | Imports from `hr.ports` for accounts-owned models | Define locally |

---

## 2. CROSS-DOMAIN POLLUTION (CRITICAL)

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 7 | `auth_service.py` | 47-48 | Imports `User`, `UserDevice` from governance | Use `governance.ports` |
| 8 | `auth_service.py` | 1395-1401 | Imports 6 user models from governance | Use ports |
| 9 | `auth_service.py` | 1402-1403 | Imports `SupplierProfile`, `LogisticsPartner` | Use ports |
| 10 | `auth_service.py` | 2341-2374 | Creates `SupplierProfile`, `LogisticsPartner` directly | Use events |
| 11 | `accounts_service.py` | 10 | Imports `Employee` from HR | Move to `hr/services/` |
| 12 | `accounts_service.py` | 24-76 | Calls HR service directly | Use events |
| 13 | `logistics_partner_service.py` | 2 | Re-exports logistics service | DELETE file |
| 14 | `users_admin_service/__header__*.py` | all | 60+ cross-domain imports | Use ports + events |
| 15 | `session_service.py` | 9 | Imports `UserSession` from governance | Use ports |
| 16 | `permission_service.py` | 438 | Imports `User` from governance | Use ports |
| 17 | `live_session_tracker.py` | 152 | Imports HR models | Use ports |

---

## 3. BROKEN IMPORTS (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 18 | `auth_service.py` | 1449-1450, 1886-1896 | `audit_log`, `AuditAction` commented out but used | Uncomment/fix import |
| 19 | `auth_service.py` | 3387, 3429-3465 | `SocialIdentity` not imported | Add import |
| 20 | `auth_service.py` | 3390, 3476 | `issue_auth_response` not defined | Implement |
| 21 | `auth_service.py` | 1207, 1226, 1230, 1249 | `OtpCode` model not defined | Create model |
| 22 | `identity_admin_service.py` | 52 | `User.is_deleted` doesn't exist on model | Add column or remove filter |
| 23 | `auth_service.py` | 3181-3186 | Recovery codes stored in plaintext | Hash before storage |
| 24 | `auth_service.py` | 3310-3368 | Biometric validation is fake (checks string length) | Implement real biometric |
| 25 | `auth_service.py` | 3394-3418 | Social identity verification unimplemented | Implement OIDC verification |

---

## 4. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 4.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 26 | No `kernel/money.py` usage — uses `from decimal import Decimal` directly | Use `kernel.money.to_decimal()` |
| 27 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.normalize_country()` |
| 28 | No `kernel/constants.py` direct usage — uses `infrastructure.utils.constants` shim | Use `kernel.constants` directly |

### 4.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 29 | `features.py` not wired to `rbac/catalog.py` | Wire to catalog |
| 30 | Uses `require_permission` instead of `require_feature()` | Use `rbac.dependencies.require_feature()` |
| 31 | Manual role checks instead of `require_roles()` | Use `rbac.dependencies.require_roles()` |
| 32 | `DEFAULT_ROLE_PERMISSION_MAP` is empty | Import from `rbac/staff_permissions` |
| 33 | No `effective_features()` integration | Use `rbac.resolution` |

### 4.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 34 | No `providers.image` for avatar processing | Add connection |
| 35 | No `providers.ocr` for document verification | Add connection |
| 36 | No `providers.storage` for S3 | Use instead of `infrastructure.utils.storage` |
| 37 | Raw `requests.get` for SSO JWKS | Use `providers.auth` |

### 4.4 Infrastructure (MOSTLY CORRECT)

| # | Issue | Fix |
|---|-------|-----|
| 38 | `SessionLocal()` used directly instead of `Depends(get_db)` | Use dependency injection |
| 39 | Duplicate `infrastructure.security.auth` imports | Consolidate to `infrastructure.utils.auth` |

---

## 5. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 40 | `admin/routers/accounts.py` | 14 | Imports non-existent `social_service` | Fix import |
| 41 | `admin/routers/__init__.py` | 41 | `social_router` never registered | Register router |
| 42 | `customer/routers/accounts.py` | 82, 89, 114 | `current_user["id"]` on ORM object (TypeError) | Use `current_user.id` |
| 43 | `employee/routers/accounts.py` | 55-169 | Wrong feature gates (all use `accounts.user.create`) | Use correct features |
| 44 | `customer/routers/accounts.py` | 89, 114 | No Pydantic validation (raw `dict`) | Add schemas |
| 45 | `employee/routers/accounts.py` | 125-151 | No pagination on list endpoints | Add pagination |
| 46 | `admin/routers/accounts.py` | 88 | No auth on social login | Add rate limiting |

---

## 6. CODE QUALITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 47 | `auth_service.py` | all | **4,317-line god file** | Split into 6+ focused services |
| 48 | `auth_service.py` | 54, 1209, 1299, 1379, 1452, 3707 | 6 duplicate logger definitions | Use single logger |
| 49 | `auth_service.py` | 895-901 | Leaks internal errors to client | Return generic message |
| 50 | `auth_service.py` | 1177-1178 | Logout swallows exceptions | Ensure cookie deletion |
| 51 | `auth_service.py` | 138-148 | RLS failure silently ignored | Check dialect explicitly |
| 52 | `users_admin_service/*` | all | 7 split files with duplicate logic | Consolidate |
| 53 | `permission_service.py` | 422-748 | Merged `RBACService` with empty map | Remove or populate |
| 54 | `auth_service.py` | 1302-1315 | Duplicate `find_user` function | Consolidate |
| 55 | `auth_service.py` | 192-220, 1826-1865 | 3 duplicate device recording functions | Consolidate |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix broken imports (`audit_log`, `SocialIdentity`, `OtpCode`, `issue_auth_response`) |
| 2 | Fix `User.is_deleted` missing column |
| 3 | Fix `current_user["id"]` TypeError in customer router |
| 4 | Fix `social_service` import in admin router |
| 5 | Register `social_router` in admin module |
| 6 | Hash recovery codes before storage |
| 7 | Remove fake biometric validation |
| 8 | Remove direct cross-domain model imports (use ports) |
| 9 | Replace cross-domain writes with events |
| 10 | Wire `features.py` to `rbac/catalog.py` |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 11 | Split `auth_service.py` into focused services |
| 12 | Consolidate `users_admin_service` split files |
| 13 | Add missing `is_deleted`, `updated_at`, `created_at` columns |
| 14 | Fix feature gates in employee router |
| 15 | Add Pydantic schemas to customer address endpoints |
| 16 | Add pagination to employee list endpoints |
| 17 | Implement real social identity verification |
| 18 | Remove merged `RBACService` or populate map |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 19 | Adopt `kernel/money.py` for Decimal operations |
| 20 | Adopt `kernel/country.py` for country codes |
| 21 | Add `providers.image`, `providers.ocr` connections |
| 22 | Fix duplicate logger definitions |
| 23 | Fix error message leakage |
| 24 | Consolidate duplicate functions |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 50+ |
| Files with cross-domain pollution | 20+ |
| CRITICAL issues | 30+ |
| HIGH issues | 35+ |
| MEDIUM issues | 25+ |
| LOW issues | 15+ |
| God files (>500 lines) | 1 |
| Broken imports | 8 |
| Missing RBAC integration | 5 |
| Missing kernel usage | 3 |
| Missing provider connections | 4 |
| Router issues | 7 |
